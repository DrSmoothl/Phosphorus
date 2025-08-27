"""Hydro OJ integration service."""

import asyncio
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..api.hydro_models import (
    ContestPlagiarismRequest,
    ContestProblemSelectionRequest,
    HydroSubmission,
    PlagiarismResult,
    SubmissionStatus,
    ContestInfo,
    ProblemInfo,
    LanguageStats,
)
from ..api.jplag_models import PlagiarismAnalysisRequest, ProgrammingLanguage
from ..common import get_logger
from .jplag_service import JPlagService

logger = get_logger()

# Constants
MIN_SUBMISSIONS_FOR_ANALYSIS = 2

# Language mappings
HYDRO_TO_JPLAG_LANGUAGE = {
    # C++ variants
    "cc": ProgrammingLanguage.CPP,
    "cc.cc98": ProgrammingLanguage.CPP,
    "cc.cc98o2": ProgrammingLanguage.CPP,
    "cc.cc11": ProgrammingLanguage.CPP,
    "cc.cc11o2": ProgrammingLanguage.CPP,
    "cc.cc14": ProgrammingLanguage.CPP,
    "cc.cc14o2": ProgrammingLanguage.CPP,
    "cc.cc17": ProgrammingLanguage.CPP,
    "cc.cc17o2": ProgrammingLanguage.CPP,
    "cc.cc20": ProgrammingLanguage.CPP,
    "cc.cc20o2": ProgrammingLanguage.CPP,
    # C variants
    "c": ProgrammingLanguage.C,
    # Pascal
    "pas": ProgrammingLanguage.TEXT,  # JPlag doesn't support Pascal, use TEXT
    # Java
    "java": ProgrammingLanguage.JAVA,
    # Kotlin
    "kt": ProgrammingLanguage.KOTLIN,
    "kt.jvm": ProgrammingLanguage.KOTLIN,
    # Python variants
    "py": ProgrammingLanguage.PYTHON3,
    "py.py2": ProgrammingLanguage.PYTHON3,  # Use Python3 for Python2 as well
    "py.py3": ProgrammingLanguage.PYTHON3,
    "py.pypy3": ProgrammingLanguage.PYTHON3,
    # PHP
    "php": ProgrammingLanguage.TEXT,  # JPlag doesn't support PHP, use TEXT
    # Rust
    "rs": ProgrammingLanguage.RUST,
    # Haskell
    "hs": ProgrammingLanguage.TEXT,  # JPlag doesn't support Haskell, use TEXT
    # JavaScript/Node.js
    "js": ProgrammingLanguage.JAVASCRIPT,
    # Golang
    "go": ProgrammingLanguage.GO,
    # Ruby
    "rb": ProgrammingLanguage.TEXT,  # JPlag doesn't support Ruby, use TEXT
    # C#
    "cs": ProgrammingLanguage.CSHARP,
    # Bash
    "bash": ProgrammingLanguage.TEXT,  # JPlag doesn't support Bash, use TEXT
}

# File extension mappings
HYDRO_TO_FILE_EXTENSION = {
    # C++ variants
    "cc": ".cpp",
    "cc.cc98": ".cpp",
    "cc.cc98o2": ".cpp",
    "cc.cc11": ".cpp",
    "cc.cc11o2": ".cpp",
    "cc.cc14": ".cpp",
    "cc.cc14o2": ".cpp",
    "cc.cc17": ".cpp",
    "cc.cc17o2": ".cpp",
    "cc.cc20": ".cpp",
    "cc.cc20o2": ".cpp",
    # C variants
    "c": ".c",
    # Pascal
    "pas": ".pas",
    # Java
    "java": ".java",
    # Kotlin
    "kt": ".kt",
    "kt.jvm": ".kt",
    # Python variants
    "py": ".py",
    "py.py2": ".py",
    "py.py3": ".py",
    "py.pypy3": ".py",
    # PHP
    "php": ".php",
    # Rust
    "rs": ".rs",
    # Haskell
    "hs": ".hs",
    # JavaScript/Node.js
    "js": ".js",
    # Golang
    "go": ".go",
    # Ruby
    "rb": ".rb",
    # C#
    "cs": ".cs",
    # Bash
    "bash": ".sh",
}


class HydroService:
    """Service for Hydro OJ integration."""

    def __init__(self, database: AsyncIOMotorDatabase, jplag_service: JPlagService):
        """Initialize Hydro service.

        Args:
            database: MongoDB database instance
            jplag_service: JPlag service instance
        """
        self.db = database
        self.jplag_service = jplag_service

    async def check_contest_plagiarism(
        self, request: ContestPlagiarismRequest
    ) -> PlagiarismResult:
        """Check plagiarism for a contest.

        Args:
            request: Contest plagiarism check request

        Returns:
            Plagiarism analysis result

        Raises:
            ValueError: If contest not found or no submissions
        """
        contest_id = ObjectId(request.contest_id)
        logger.info(f"Starting plagiarism check for contest {contest_id}")

        # Get all accepted submissions for this contest
        submissions = await self._get_contest_submissions(contest_id)
        if not submissions:
            raise ValueError(f"No accepted submissions found for contest {contest_id}")

        # Group submissions by problem
        problems = self._group_submissions_by_problem(submissions)

        # Analyze each problem separately
        all_results = []
        for problem_id, problem_submissions in problems.items():
            if len(problem_submissions) < MIN_SUBMISSIONS_FOR_ANALYSIS:
                logger.info(
                    f"Skipping problem {problem_id}: only {len(problem_submissions)} submissions"
                )
                continue

            logger.info(
                f"Analyzing problem {problem_id} with {len(problem_submissions)} submissions"
            )

            # Create analysis for this problem
            problem_result = await self._analyze_problem_submissions(
                contest_id, problem_id, problem_submissions, request
            )
            all_results.append(problem_result)

        if not all_results:
            raise ValueError("No problems with sufficient submissions for analysis")

        # For now, return the first result (could be combined later)
        return all_results[0]

    async def _get_contest_submissions(
        self, contest_id: ObjectId
    ) -> list[HydroSubmission]:
        """Get all accepted submissions for a contest.

        Args:
            contest_id: Contest ObjectId

        Returns:
            List of accepted submissions
        """
        cursor = self.db.record.find(
            {
                "contest": contest_id,
                "status": SubmissionStatus.ACCEPTED,
                "code": {"$ne": ""},  # Ensure code is not empty
            }
        )

        submissions = []
        async for doc in cursor:
            try:
                submission = HydroSubmission(**doc)
                submissions.append(submission)
            except Exception as e:
                logger.warning(f"Failed to parse submission {doc.get('_id')}: {e}")

        logger.info(
            f"Found {len(submissions)} accepted submissions for contest {contest_id}"
        )
        return submissions

    def _group_submissions_by_problem(
        self, submissions: list[HydroSubmission]
    ) -> dict[int, list[HydroSubmission]]:
        """Group submissions by problem ID.

        Args:
            submissions: List of submissions

        Returns:
            Dictionary mapping problem ID to submissions
        """
        problems: dict[int, list[HydroSubmission]] = {}
        for submission in submissions:
            if submission.pid not in problems:
                problems[submission.pid] = []
            problems[submission.pid].append(submission)

        return problems

    async def _analyze_problem_submissions(
        self,
        contest_id: ObjectId,
        problem_id: int,
        submissions: list[HydroSubmission],
        request: ContestPlagiarismRequest,
    ) -> PlagiarismResult:
        """Analyze submissions for a single problem.

        Args:
            contest_id: Contest ID
            problem_id: Problem ID
            submissions: List of submissions
            request: Analysis request

        Returns:
            Plagiarism analysis result
        """
        analysis_id = str(uuid.uuid4())

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files for JPlag analysis
            await self._create_submission_files(submissions, temp_dir)

            # Determine programming language
            language = self._detect_programming_language(submissions[0].lang)

            # Create JPlag request
            jplag_request = PlagiarismAnalysisRequest(
                language=language,
                min_tokens=request.min_tokens,
                similarity_threshold=request.similarity_threshold,
            )

            # Run JPlag analysis on the directory
            jplag_result = await self._run_jplag_on_directory(
                temp_dir, jplag_request, analysis_id
            )

            # Create result record
            result = PlagiarismResult(
                contest_id=str(contest_id),
                problem_id=problem_id,
                analysis_id=analysis_id,
                total_submissions=jplag_result.total_submissions,
                total_comparisons=jplag_result.total_comparisons,
                execution_time_ms=jplag_result.execution_time_ms,
                high_similarity_pairs=[
                    pair.model_dump() for pair in jplag_result.high_similarity_pairs
                ],
                clusters=[cluster.model_dump() for cluster in jplag_result.clusters],
                submission_stats=[
                    stat.model_dump() for stat in jplag_result.submission_stats
                ],
                failed_submissions=[
                    fail.model_dump() for fail in jplag_result.failed_submissions
                ],
            )

            # Save to database
            await self._save_plagiarism_result(result)

            return result

    async def _create_submission_files(
        self, submissions: list[HydroSubmission], base_dir: str
    ) -> None:
        """Create files for submissions.

        Args:
            submissions: List of submissions
            base_dir: Base directory path
        """
        for i, submission in enumerate(submissions):
            # Create submission directory
            sub_dir = Path(base_dir) / f"submission_{submission.uid}_{i}"
            sub_dir.mkdir(exist_ok=True)

            # Determine file extension
            extension = self._get_file_extension(submission.lang)

            # Create source file
            file_path = sub_dir / f"solution{extension}"
            file_path.write_text(submission.code, encoding="utf-8")

    def _get_file_extension(self, lang: str) -> str:
        """Get file extension for language.

        Args:
            lang: Language identifier

        Returns:
            File extension with dot
        """
        return HYDRO_TO_FILE_EXTENSION.get(lang, ".txt")

    def _detect_programming_language(self, lang: str) -> ProgrammingLanguage:
        """Detect programming language from Hydro language ID.

        Args:
            lang: Hydro language identifier

        Returns:
            JPlag programming language
        """
        # Try exact match first
        if lang in HYDRO_TO_JPLAG_LANGUAGE:
            return HYDRO_TO_JPLAG_LANGUAGE[lang]

        # Fallback mappings for unknown variations
        prefix_mapping = {
            "cc.": ProgrammingLanguage.CPP,
            "c++": ProgrammingLanguage.CPP,
            "c.": ProgrammingLanguage.C,
            "python": ProgrammingLanguage.PYTHON3,
            "javascript": ProgrammingLanguage.JAVASCRIPT,
            "typescript": ProgrammingLanguage.TYPESCRIPT,
        }

        for prefix, language in prefix_mapping.items():
            if lang.startswith(prefix):
                return language

        logger.warning(f"Unknown language {lang}, defaulting to TEXT")
        return ProgrammingLanguage.TEXT

    async def _run_jplag_on_directory(
        self,
        directory: str,
        request: PlagiarismAnalysisRequest,
        analysis_id: str,
    ) -> Any:
        """Run JPlag on a directory of submissions.

        Args:
            directory: Directory containing submissions
            request: JPlag analysis request
            analysis_id: Analysis ID

        Returns:
            JPlag analysis result
        """
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                result_file = os.path.join(temp_dir, f"result_{analysis_id}")

                # Build JPlag command
                cmd = [
                    "java",
                    "-jar",
                    self.jplag_service.jplag_jar_path,
                    "--mode",
                    "run",  # Prevent GUI launcher in server environment
                    "-l",
                    request.language.value,
                    "-r",
                    result_file,
                    "-t",
                    str(request.min_tokens),
                    "-m",
                    str(request.similarity_threshold),
                    directory,
                ]

                if request.normalize_tokens:
                    cmd.append("--normalize")

                logger.info(f"Running JPlag: {' '.join(cmd)}")

                # Run JPlag asynchronously
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                stdout, stderr = await process.communicate()

                if process.returncode != 0:
                    error_msg = stderr.decode() if stderr else "Unknown error"
                    logger.error(f"JPlag failed: {error_msg}")
                    raise RuntimeError(f"JPlag execution failed: {error_msg}")

                logger.info("JPlag completed successfully")

                # Parse results using JPlag service
                jplag_file = f"{result_file}.jplag"
                logger.info(f"Parsing JPlag results from: {jplag_file}")
                return await self.jplag_service._parse_jplag_results(
                    jplag_file, analysis_id, request
                )
        except Exception as e:
            logger.error(f"Error in _run_jplag_on_directory: {e}", exc_info=True)
            raise

    async def _save_plagiarism_result(self, result: PlagiarismResult) -> None:
        """Save plagiarism result to database.

        Args:
            result: Plagiarism result to save
        """
        collection = self.db.check_plagiarism_results
        await collection.insert_one(result.model_dump(by_alias=True, exclude={"id"}))
        logger.info(f"Saved plagiarism result for analysis {result.analysis_id}")

    async def get_contest_plagiarism_results(
        self, contest_id: str
    ) -> list[PlagiarismResult]:
        """Get plagiarism results for a contest.

        Args:
            contest_id: Contest ID

        Returns:
            List of plagiarism results
        """
        logger.info(f"Searching for plagiarism results with contest_id: {contest_id}")
        collection = self.db.check_plagiarism_results

        # Debug: check if collection exists and count total documents
        total_docs = await collection.count_documents({})
        logger.info(f"Total documents in check_plagiarism_results collection: {total_docs}")

        # Debug: check documents with any contest_id
        sample_docs = []
        async for doc in collection.find({}).limit(5):
            sample_docs.append(doc.get('contest_id', 'NO_CONTEST_ID'))
        logger.info(f"Sample contest_ids in collection: {sample_docs}")

        cursor = collection.find({"contest_id": contest_id})

        results = []
        async for doc in cursor:
            try:
                result = PlagiarismResult(**doc)
                results.append(result)
                logger.info(f"Found plagiarism result: {result.analysis_id}")
            except Exception as e:
                logger.warning(f"Failed to parse result {doc.get('_id')}: {e}")

        logger.info(f"Returning {len(results)} plagiarism results for contest {contest_id}")
        return results

    async def check_contest_problems_plagiarism(
        self, request: ContestProblemSelectionRequest
    ) -> list[PlagiarismResult]:
        """Check plagiarism for selected contest problems.

        Args:
            request: Contest problem selection request

        Returns:
            List of plagiarism analysis results
        """
        contest_id = ObjectId(request.contest_id)
        logger.info(f"Starting plagiarism check for contest {contest_id} with problems {request.problem_ids}")

        # Get all accepted submissions for this contest
        submissions = await self._get_contest_submissions(contest_id)
        if not submissions:
            raise ValueError(f"No accepted submissions found for contest {contest_id}")

        # Filter submissions by selected problems
        filtered_submissions = [s for s in submissions if s.pid in request.problem_ids]
        if not filtered_submissions:
            raise ValueError(f"No submissions found for selected problems {request.problem_ids}")

        # Group submissions by problem
        problems = self._group_submissions_by_problem(filtered_submissions)

        # Analyze each problem separately
        results = []
        for problem_id in request.problem_ids:
            if problem_id not in problems:
                logger.info(f"No submissions found for problem {problem_id}")
                continue

            problem_submissions = problems[problem_id]
            if len(problem_submissions) < MIN_SUBMISSIONS_FOR_ANALYSIS:
                logger.info(
                    f"Skipping problem {problem_id}: only {len(problem_submissions)} submissions"
                )
                continue

            logger.info(
                f"Analyzing problem {problem_id} with {len(problem_submissions)} submissions"
            )

            # Create analysis request
            analysis_request = ContestPlagiarismRequest(
                contest_id=request.contest_id,
                min_tokens=request.min_tokens,
                similarity_threshold=request.similarity_threshold
            )

            # Create analysis for this problem
            problem_result = await self._analyze_problem_submissions(
                contest_id, problem_id, problem_submissions, analysis_request
            )
            results.append(problem_result)

        if not results:
            raise ValueError("No problems with sufficient submissions for analysis")

        return results

    async def get_contests_with_plagiarism(self) -> list[ContestInfo]:
        """Get all contests with plagiarism results.

        Returns:
            List of contest information
        """
        logger.info("Getting all contests with plagiarism results")
        
        # Get unique contest IDs from plagiarism results
        collection = self.db.check_plagiarism_results
        pipeline = [
            {"$group": {"_id": "$contest_id", "count": {"$sum": 1}, "last_check": {"$max": "$created_at"}}},
            {"$sort": {"last_check": -1}}
        ]
        
        contest_results = []
        async for doc in collection.aggregate(pipeline):
            contest_id = doc["_id"]
            
            # Get contest information from contest collection
            contest_doc = await self.db.contest.find_one({"_id": ObjectId(contest_id)})
            if contest_doc:
                # Count problems that have been checked
                checked_problems = await collection.count_documents({"contest_id": contest_id})
                
                contest_info = ContestInfo(
                    id=contest_id,
                    title=contest_doc.get("title", "Unknown Contest"),
                    description=contest_doc.get("content", ""),
                    begin_at=contest_doc.get("beginAt"),
                    end_at=contest_doc.get("endAt"),
                    total_problems=len(contest_doc.get("pids", [])),
                    checked_problems=checked_problems,
                    last_check_at=doc["last_check"]
                )
                contest_results.append(contest_info)

        return contest_results

    async def get_contest_problems(self, contest_id: str) -> list[ProblemInfo]:
        """Get contest problems with submission statistics.

        Args:
            contest_id: Contest ID

        Returns:
            List of problem information
        """
        logger.info(f"Getting problems for contest {contest_id}")
        
        contest_oid = ObjectId(contest_id)
        
        # Get contest document to get problem IDs
        contest_doc = await self.db.contest.find_one({"_id": contest_oid})
        if not contest_doc:
            raise ValueError(f"Contest {contest_id} not found")

        problem_ids = contest_doc.get("pids", [])
        problems = []

        for problem_id in problem_ids:
            # Get problem document
            problem_doc = await self.db.problem.find_one({"pid": problem_id})
            if not problem_doc:
                continue

            # Count submissions for this problem in this contest
            total_submissions = await self.db.record.count_documents({
                "contest": contest_oid,
                "pid": problem_id
            })

            accepted_submissions = await self.db.record.count_documents({
                "contest": contest_oid,
                "pid": problem_id,
                "status": SubmissionStatus.ACCEPTED
            })

            # Get distinct languages used
            pipeline = [
                {"$match": {"contest": contest_oid, "pid": problem_id, "status": SubmissionStatus.ACCEPTED}},
                {"$group": {"_id": "$lang"}},
                {"$sort": {"_id": 1}}
            ]
            languages = []
            async for doc in self.db.record.aggregate(pipeline):
                languages.append(doc["_id"])

            # Check if there's a plagiarism result for this problem
            last_check = None
            plagiarism_result = await self.db.check_plagiarism_results.find_one(
                {"contest_id": contest_id, "problem_id": problem_id},
                sort=[("created_at", -1)]
            )
            if plagiarism_result:
                last_check = plagiarism_result["created_at"]

            problem_info = ProblemInfo(
                id=problem_id,
                title=problem_doc.get("title", f"Problem {problem_id}"),
                total_submissions=total_submissions,
                accepted_submissions=accepted_submissions,
                languages=languages,
                last_check_at=last_check
            )
            problems.append(problem_info)

        return problems

    async def get_problem_language_stats(self, contest_id: str, problem_id: int) -> list[LanguageStats]:
        """Get language usage statistics for a problem.

        Args:
            contest_id: Contest ID
            problem_id: Problem ID

        Returns:
            List of language statistics
        """
        logger.info(f"Getting language stats for problem {problem_id} in contest {contest_id}")
        
        contest_oid = ObjectId(contest_id)
        
        # Aggregate language usage
        pipeline = [
            {
                "$match": {
                    "contest": contest_oid,
                    "pid": problem_id,
                    "status": SubmissionStatus.ACCEPTED
                }
            },
            {
                "$group": {
                    "_id": "$lang",
                    "submission_count": {"$sum": 1},
                    "unique_users": {"$addToSet": "$uid"}
                }
            },
            {
                "$project": {
                    "language": "$_id",
                    "submission_count": 1,
                    "unique_users": {"$size": "$unique_users"}
                }
            },
            {
                "$sort": {"submission_count": -1}
            }
        ]

        stats = []
        async for doc in self.db.record.aggregate(pipeline):
            language = doc["language"]
            jplag_language = self._detect_programming_language(language)
            can_analyze = jplag_language != ProgrammingLanguage.TEXT and doc["submission_count"] >= MIN_SUBMISSIONS_FOR_ANALYSIS

            stat = LanguageStats(
                language=language,
                submission_count=doc["submission_count"],
                unique_users=doc["unique_users"],
                jplag_language=jplag_language.value,
                can_analyze=can_analyze
            )
            stats.append(stat)

        return stats

    async def get_problem_plagiarism_result(self, contest_id: str, problem_id: int) -> PlagiarismResult | None:
        """Get plagiarism result for a specific problem.

        Args:
            contest_id: Contest ID
            problem_id: Problem ID

        Returns:
            Plagiarism result or None if not found
        """
        logger.info(f"Getting plagiarism result for problem {problem_id} in contest {contest_id}")
        
        collection = self.db.check_plagiarism_results
        doc = await collection.find_one(
            {"contest_id": contest_id, "problem_id": problem_id},
            sort=[("created_at", -1)]  # Get the most recent result
        )
        
        if doc:
            return PlagiarismResult(**doc)
        return None
