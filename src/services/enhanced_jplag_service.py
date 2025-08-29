"""Enhanced JPlag service with comprehensive result parsing and code analysis."""

import asyncio
import json
import os
import tempfile
import uuid
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import UploadFile

from ..api.jplag_models import (
    ClusterInfo,
    CodeLine,
    CodePosition,
    ComparisonResult,
    DistributionData,
    FailedSubmission,
    FileContent,
    Match,
    PlagiarismAnalysisRequest,
    PlagiarismAnalysisResult,
    ProblemPlagiarismData,
    RunInformation,
    SubmissionStats,
    TopComparison,
)
from ..common import get_logger

logger = get_logger()


class EnhancedJPlagService:
    """Enhanced service for JPlag operations with comprehensive parsing."""

    def __init__(self, jplag_jar_path: str):
        """Initialize Enhanced JPlag service.

        Args:
            jplag_jar_path: Path to JPlag JAR file
        """
        self.jplag_jar_path = jplag_jar_path
        if not os.path.exists(jplag_jar_path):
            raise FileNotFoundError(f"JPlag JAR not found: {jplag_jar_path}")

    async def analyze_submissions_enhanced(
        self,
        files: list[UploadFile],
        request: PlagiarismAnalysisRequest,
    ) -> PlagiarismAnalysisResult:
        """Analyze submissions with enhanced parsing and detailed results.

        Args:
            files: List of uploaded files
            request: Analysis configuration

        Returns:
            Enhanced analysis result with detailed code comparisons
        """
        analysis_id = str(uuid.uuid4())
        logger.info(f"Starting enhanced plagiarism analysis {analysis_id}")

        with tempfile.TemporaryDirectory() as temp_dir:
            # Save uploaded files and preserve metadata
            submission_dir, file_metadata = await self._save_uploads_with_metadata(
                files, temp_dir
            )

            # Run JPlag
            jplag_result_path = await self._run_jplag(
                submission_dir, request, temp_dir, analysis_id
            )

            # Parse results with enhanced capabilities
            result = await self._parse_jplag_results_enhanced(
                jplag_result_path, analysis_id, request, file_metadata
            )

        logger.info(f"Completed enhanced plagiarism analysis {analysis_id}")
        return result

    async def get_detailed_comparison_enhanced(
        self, 
        analysis_id: str, 
        first_submission: str, 
        second_submission: str,
        jplag_result_path: str | None = None
    ) -> ComparisonResult | None:
        """Get enhanced detailed comparison between two submissions.

        Args:
            analysis_id: Analysis identifier
            first_submission: First submission ID
            second_submission: Second submission ID
            jplag_result_path: Path to JPlag result file

        Returns:
            Enhanced detailed comparison result or None if not found
        """
        if not jplag_result_path or not os.path.exists(jplag_result_path):
            logger.warning(f"JPlag result file not found for analysis {analysis_id}")
            return None

        try:
            with zipfile.ZipFile(jplag_result_path, "r") as zip_file:
                # Find the specific comparison file
                comparison_file = f"comparisons/{first_submission}-{second_submission}.json"
                if comparison_file not in zip_file.namelist():
                    # Try reverse order
                    comparison_file = f"comparisons/{second_submission}-{first_submission}.json"
                
                if comparison_file not in zip_file.namelist():
                    logger.warning(f"Comparison file not found: {comparison_file}")
                    return None

                # Parse the comparison
                with zip_file.open(comparison_file) as f:
                    comparison_data = json.load(f)

                # Parse file contents for both submissions
                first_files = await self._parse_submission_files(
                    zip_file, first_submission
                )
                second_files = await self._parse_submission_files(
                    zip_file, second_submission
                )

                # Enhance matches with detailed information
                enhanced_matches = await self._enhance_matches_with_code(
                    comparison_data.get("matches", []),
                    first_files,
                    second_files
                )

                # Calculate additional metrics
                match_coverage = self._calculate_match_coverage(
                    enhanced_matches, first_files, second_files
                )
                longest_match = max(
                    (match.length_of_first for match in enhanced_matches),
                    default=0
                )
                total_matched_lines = sum(
                    match.end_in_first.line - match.start_in_first.line + 1
                    for match in enhanced_matches
                )

                return ComparisonResult(
                    first_submission_id=comparison_data["firstSubmissionId"],
                    second_submission_id=comparison_data["secondSubmissionId"],
                    similarities=comparison_data["similarities"],
                    matches=enhanced_matches,
                    first_similarity=comparison_data["firstSimilarity"],
                    second_similarity=comparison_data["secondSimilarity"],
                    first_files=first_files,
                    second_files=second_files,
                    match_coverage=match_coverage,
                    longest_match=longest_match,
                    total_matched_lines=total_matched_lines,
                )

        except Exception as e:
            logger.error(f"Failed to parse detailed comparison: {e}")
            return None

    async def parse_problem_plagiarism_data(
        self, jplag_result_path: str, problem_id: int, contest_id: str
    ) -> ProblemPlagiarismData:
        """Parse comprehensive plagiarism data for a problem.

        Args:
            jplag_result_path: Path to JPlag result file
            problem_id: Problem identifier
            contest_id: Contest identifier

        Returns:
            Comprehensive problem plagiarism data
        """
        analysis_id = str(uuid.uuid4())
        
        with zipfile.ZipFile(jplag_result_path, "r") as zip_file:
            # Parse all data
            data = await self._parse_zip_contents_enhanced(zip_file)

        # Build enhanced analysis result
        analysis_result = await self._build_enhanced_analysis_result(data, analysis_id)

        # Create comprehensive problem data
        problem_data = ProblemPlagiarismData(
            problem_id=problem_id,
            contest_id=contest_id,
            analysis_id=analysis_id,
            total_submissions=analysis_result.total_submissions,
            high_similarity_count=len(analysis_result.high_similarity_pairs),
            max_similarity=self._get_max_similarity(analysis_result.high_similarity_pairs),
            avg_similarity=self._get_avg_similarity(analysis_result.high_similarity_pairs),
            top_comparisons=analysis_result.high_similarity_pairs,
            clusters=analysis_result.clusters,
            language_stats=self._analyze_language_statistics(
                analysis_result.submission_stats, analysis_result.high_similarity_pairs
            ),
            distribution=analysis_result.distribution,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            status="completed"
        )

        return problem_data

    async def _save_uploads_with_metadata(
        self, files: list[UploadFile], base_dir: str
    ) -> tuple[str, dict[str, Any]]:
        """Save uploaded files and collect metadata.

        Args:
            files: List of uploaded files
            base_dir: Base temporary directory

        Returns:
            Tuple of (submissions directory path, file metadata)
        """
        submission_dir = os.path.join(base_dir, "submissions")
        os.makedirs(submission_dir, exist_ok=True)
        
        file_metadata = {}

        for i, file in enumerate(files):
            if not file.filename:
                continue

            # Create submission subdirectory
            sub_dir = os.path.join(submission_dir, f"submission_{i + 1}")
            os.makedirs(sub_dir, exist_ok=True)

            # Save file
            file_path = os.path.join(sub_dir, file.filename)
            content = await file.read()
            
            with open(file_path, "wb") as f:
                f.write(content)

            # Collect metadata
            try:
                text_content = content.decode('utf-8', errors='ignore')
                file_metadata[f"submission_{i + 1}"] = {
                    "filename": file.filename,
                    "size": len(content),
                    "lines": len(text_content.splitlines()),
                    "language": self._detect_language(file.filename),
                    "content": text_content
                }
            except Exception as e:
                logger.warning(f"Failed to process metadata for {file.filename}: {e}")

        logger.info(f"Saved {len(files)} files with metadata to {submission_dir}")
        return submission_dir, file_metadata

    async def _run_jplag(
        self,
        submission_dir: str,
        request: PlagiarismAnalysisRequest,
        temp_dir: str,
        analysis_id: str,
    ) -> str:
        """Run JPlag analysis with enhanced configuration.

        Args:
            submission_dir: Directory containing submissions
            request: Analysis configuration
            temp_dir: Temporary directory
            analysis_id: Analysis identifier

        Returns:
            Path to JPlag result file
        """
        result_file = os.path.join(temp_dir, f"result_{analysis_id}")

        # Build comprehensive JPlag command
        cmd = [
            "java",
            "-jar",
            self.jplag_jar_path,
            "--mode",
            "run",
            "-l",
            request.language.value,
            "-r",
            result_file,
            "-t",
            str(request.min_tokens),
            "-m",
            str(request.similarity_threshold),
            "--cluster-enable",  # Enable clustering
            "--cluster-alg", "spectral",  # Use spectral clustering
            submission_dir,
        ]

        if request.normalize_tokens:
            cmd.append("--normalize")

        logger.info(f"Running enhanced JPlag: {' '.join(cmd)}")

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

        logger.info("Enhanced JPlag completed successfully")

        # Return path to .jplag file
        jplag_file = f"{result_file}.jplag"
        if not os.path.exists(jplag_file):
            raise RuntimeError(f"JPlag result file not found: {jplag_file}")

        return jplag_file

    async def _parse_jplag_results_enhanced(
        self,
        jplag_file_path: str,
        analysis_id: str,
        request: PlagiarismAnalysisRequest,
        file_metadata: dict[str, Any],
    ) -> PlagiarismAnalysisResult:
        """Parse JPlag results with enhanced capabilities.

        Args:
            jplag_file_path: Path to .jplag file
            analysis_id: Analysis identifier
            request: Original request
            file_metadata: File metadata collected during upload

        Returns:
            Enhanced parsed analysis result
        """
        logger.info(f"Parsing enhanced JPlag results from {jplag_file_path}")

        if not zipfile.is_zipfile(jplag_file_path):
            raise ValueError(f"Invalid JPlag file: {jplag_file_path}")

        with zipfile.ZipFile(jplag_file_path, "r") as zip_file:
            # Parse all JSON files with enhanced parsing
            data = await self._parse_zip_contents_enhanced(zip_file)

        # Build enhanced result
        result = await self._build_enhanced_analysis_result(data, analysis_id)
        
        # Add file metadata to submission stats
        for submission_stat in result.submission_stats:
            if submission_stat.submission_id in file_metadata:
                metadata = file_metadata[submission_stat.submission_id]
                submission_stat.language = metadata.get("language")
                submission_stat.lines_of_code = metadata.get("lines")

        logger.info(f"Parsed {result.total_comparisons} comparisons with enhanced data")
        return result

    async def _parse_zip_contents_enhanced(
        self, zip_file: zipfile.ZipFile
    ) -> dict[str, Any]:
        """Parse contents of JPlag ZIP file with enhanced capabilities.

        Args:
            zip_file: Opened ZIP file

        Returns:
            Enhanced parsed data dictionary
        """
        data = {}

        # Parse each JSON file
        json_files = [
            "topComparisons.json",
            "runInformation.json", 
            "submissionMappings.json",
            "submissionFileIndex.json",
            "distribution.json",
            "cluster.json",
            "options.json",
        ]

        for json_file in json_files:
            if json_file in zip_file.namelist():
                try:
                    with zip_file.open(json_file) as f:
                        content = json.load(f)
                        key = json_file.replace(".json", "")
                        data[key] = content
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse {json_file}: {e}")

        # Parse detailed comparisons
        comparison_files = [
            f for f in zip_file.namelist()
            if f.startswith("comparisons/") and f.endswith(".json")
        ]

        detailed_comparisons = {}
        for comp_file in comparison_files:
            try:
                with zip_file.open(comp_file) as f:
                    content = json.load(f)
                    detailed_comparisons[comp_file] = content
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse {comp_file}: {e}")

        data["detailed_comparisons"] = detailed_comparisons

        # Parse source files for code content
        source_files = {}
        for file_path in zip_file.namelist():
            if file_path.startswith("files/") and not file_path.endswith("/"):
                try:
                    with zip_file.open(file_path) as f:
                        content = f.read().decode('utf-8', errors='ignore')
                        source_files[file_path] = content
                except Exception as e:
                    logger.warning(f"Failed to read source file {file_path}: {e}")

        data["source_files"] = source_files

        return data

    async def _build_enhanced_analysis_result(
        self, data: dict[str, Any], analysis_id: str
    ) -> PlagiarismAnalysisResult:
        """Build enhanced analysis result from parsed data.

        Args:
            data: Parsed data from JPlag file
            analysis_id: Analysis identifier

        Returns:
            Enhanced structured analysis result
        """
        # Parse run information
        run_info_data = data.get("runInformation", {})
        failed_submissions_data = run_info_data.get("failedSubmissions", [])

        failed_submissions = []
        for fs in failed_submissions_data:
            try:
                failed_submission = FailedSubmission(
                    name=fs.get("submissionId", fs.get("name", "unknown")),
                    state=fs.get("submissionState", fs.get("state", "unknown")),
                    error_message=fs.get("errorMessage")
                )
                failed_submissions.append(failed_submission)
            except Exception as e:
                logger.warning(f"Failed to parse failed submission {fs}: {e}")

        run_info = RunInformation(
            report_viewer_version=run_info_data.get("reportViewerVersion", "unknown"),
            failed_submissions=failed_submissions,
            submission_date=run_info_data.get(
                "dateOfExecution", run_info_data.get("submissionDate", "")
            ),
            duration=run_info_data.get(
                "executionTime", run_info_data.get("duration", 0)
            ),
            total_comparisons=run_info_data.get("totalComparisons", 0),
            jplag_version=run_info_data.get("version", {}).get("major", "unknown"),
            options=data.get("options", {})
        )

        # Parse enhanced top comparisons
        top_comparisons_data = data.get("topComparisons", [])
        high_similarity_pairs = []
        
        for tc in top_comparisons_data:
            try:
                comparison = TopComparison(
                    first_submission=tc["firstSubmission"],
                    second_submission=tc["secondSubmission"],
                    similarities=tc["similarities"],
                    user_names=self._extract_user_names(tc),
                    file_counts=self._extract_file_counts(tc, data),
                    languages=self._extract_languages(tc, data)
                )
                high_similarity_pairs.append(comparison)
            except Exception as e:
                logger.warning(f"Failed to parse top comparison {tc}: {e}")

        # Parse enhanced clusters
        cluster_data = data.get("cluster", [])
        clusters = []
        
        for i, cluster in enumerate(cluster_data):
            try:
                cluster_info = ClusterInfo(
                    index=cluster.get("index", i),
                    average_similarity=cluster.get("averageSimilarity", 0.0),
                    strength=cluster.get("strength", 0.0),
                    members=cluster.get("members", []),
                    size=len(cluster.get("members", [])),
                    dominant_language=self._get_dominant_language(cluster.get("members", []), data),
                    similarity_matrix=self._build_similarity_matrix(cluster.get("members", []), data)
                )
                clusters.append(cluster_info)
            except Exception as e:
                logger.warning(f"Failed to parse cluster {cluster}: {e}")

        # Parse enhanced submission statistics
        submission_mappings = data.get("submissionMappings", {})
        file_index = data.get("submissionFileIndex", {}).get("fileIndexes", {})

        submission_stats = []
        for sub_id, display_name in submission_mappings.get(
            "submissionIdToDisplayName", {}
        ).items():
            files_info = file_index.get(sub_id, {})
            file_count = len(files_info)
            total_tokens = sum(
                file_info.get("tokenCount", 0) for file_info in files_info.values()
            )

            submission_stats.append(
                SubmissionStats(
                    submission_id=sub_id,
                    display_name=display_name,
                    file_count=file_count,
                    total_tokens=total_tokens,
                    language=self._detect_submission_language(sub_id, data),
                    lines_of_code=self._count_submission_lines(sub_id, data)
                )
            )

        # Parse distribution data
        distribution_data = data.get("distribution", {})
        distribution = None
        if distribution_data:
            try:
                distribution = DistributionData(
                    buckets=distribution_data.get("buckets", []),
                    total_comparisons=run_info.total_comparisons,
                    average_similarity=self._calculate_average_similarity(high_similarity_pairs),
                    median_similarity=self._calculate_median_similarity(high_similarity_pairs),
                    max_similarity=self._get_max_similarity(high_similarity_pairs),
                    min_similarity=self._get_min_similarity(high_similarity_pairs)
                )
            except Exception as e:
                logger.warning(f"Failed to parse distribution data: {e}")

        # Build language distribution
        language_distribution = {}
        for stat in submission_stats:
            if stat.language:
                language_distribution[stat.language] = language_distribution.get(stat.language, 0) + 1

        return PlagiarismAnalysisResult(
            analysis_id=analysis_id,
            total_submissions=len(submission_stats),
            total_comparisons=run_info.total_comparisons,
            execution_time_ms=run_info.duration,
            high_similarity_pairs=high_similarity_pairs,
            clusters=clusters,
            submission_stats=submission_stats,
            failed_submissions=run_info.failed_submissions,
            distribution=distribution,
            language_distribution=language_distribution,
            options=data.get("options", {}),
            run_information=run_info
        )

    async def _parse_submission_files(
        self, zip_file: zipfile.ZipFile, submission_id: str
    ) -> list[FileContent]:
        """Parse files for a specific submission.

        Args:
            zip_file: Opened ZIP file
            submission_id: Submission identifier

        Returns:
            List of file contents with metadata
        """
        files = []
        
        # Find files for this submission
        for file_path in zip_file.namelist():
            if file_path.startswith(f"files/{submission_id}/") and not file_path.endswith("/"):
                try:
                    with zip_file.open(file_path) as f:
                        content = f.read().decode('utf-8', errors='ignore')
                    
                    filename = Path(file_path).name
                    lines = content.splitlines()
                    
                    # Create code lines with metadata
                    code_lines = [
                        CodeLine(
                            line_number=i + 1,
                            content=line,
                            is_match=False,  # Will be updated with match information
                            match_type=None,
                            match_id=None
                        )
                        for i, line in enumerate(lines)
                    ]
                    
                    file_content = FileContent(
                        filename=filename,
                        content=content,
                        lines=code_lines,
                        language=self._detect_language(filename),
                        total_lines=len(lines),
                        total_tokens=len(content.split())  # Simple token count
                    )
                    
                    files.append(file_content)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse file {file_path}: {e}")
        
        return files

    async def _enhance_matches_with_code(
        self,
        matches_data: list[dict[str, Any]],
        first_files: list[FileContent], 
        second_files: list[FileContent]
    ) -> list[Match]:
        """Enhance matches with detailed code information.

        Args:
            matches_data: Raw match data from JPlag
            first_files: Files from first submission
            second_files: Files from second submission

        Returns:
            Enhanced matches with additional metadata
        """
        enhanced_matches = []
        
        for i, match_data in enumerate(matches_data):
            try:
                # Parse basic match information
                match = Match(
                    first_file_name=match_data["firstFileName"],
                    second_file_name=match_data["secondFileName"],
                    start_in_first=CodePosition(
                        line=match_data["startInFirst"]["line"],
                        column=match_data["startInFirst"]["column"],
                        token_index=match_data["startInFirst"]["tokenListIndex"]
                    ),
                    end_in_first=CodePosition(
                        line=match_data["endInFirst"]["line"],
                        column=match_data["endInFirst"]["column"],
                        token_index=match_data["endInFirst"]["tokenListIndex"]
                    ),
                    start_in_second=CodePosition(
                        line=match_data["startInSecond"]["line"],
                        column=match_data["startInSecond"]["column"],
                        token_index=match_data["startInSecond"]["tokenListIndex"]
                    ),
                    end_in_second=CodePosition(
                        line=match_data["endInSecond"]["line"],
                        column=match_data["endInSecond"]["column"],
                        token_index=match_data["endInSecond"]["tokenListIndex"]
                    ),
                    length_of_first=match_data["lengthOfFirst"],
                    length_of_second=match_data["lengthOfSecond"],
                    matched_tokens=match_data.get("matchedTokens", 0),
                    similarity_score=match_data.get("similarity", 0.0),
                    match_id=f"match_{i}"
                )
                
                # Update file lines with match information
                self._mark_matching_lines(match, first_files, second_files, f"match_{i}")
                
                enhanced_matches.append(match)
                
            except Exception as e:
                logger.warning(f"Failed to enhance match {match_data}: {e}")
        
        return enhanced_matches

    def _mark_matching_lines(
        self, 
        match: Match, 
        first_files: list[FileContent], 
        second_files: list[FileContent],
        match_id: str
    ) -> None:
        """Mark lines that are part of a match.

        Args:
            match: Match information
            first_files: Files from first submission
            second_files: Files from second submission
            match_id: Unique match identifier
        """
        # Find the relevant files
        first_file = next(
            (f for f in first_files if f.filename == match.first_file_name), None
        )
        second_file = next(
            (f for f in second_files if f.filename == match.second_file_name), None
        )
        
        if first_file and second_file:
            # Mark lines in first file
            for line_num in range(match.start_in_first.line, match.end_in_first.line + 1):
                if 1 <= line_num <= len(first_file.lines):
                    first_file.lines[line_num - 1].is_match = True
                    first_file.lines[line_num - 1].match_type = "exact"
                    first_file.lines[line_num - 1].match_id = match_id
            
            # Mark lines in second file
            for line_num in range(match.start_in_second.line, match.end_in_second.line + 1):
                if 1 <= line_num <= len(second_file.lines):
                    second_file.lines[line_num - 1].is_match = True
                    second_file.lines[line_num - 1].match_type = "exact"
                    second_file.lines[line_num - 1].match_id = match_id

    def _calculate_match_coverage(
        self,
        matches: list[Match],
        first_files: list[FileContent],
        second_files: list[FileContent]
    ) -> float:
        """Calculate the percentage of code covered by matches.

        Args:
            matches: List of matches
            first_files: Files from first submission
            second_files: Files from second submission

        Returns:
            Match coverage percentage
        """
        if not first_files and not second_files:
            return 0.0
        
        total_lines = sum(f.total_lines for f in first_files + second_files)
        if total_lines == 0:
            return 0.0
        
        matched_lines = sum(
            (match.end_in_first.line - match.start_in_first.line + 1) +
            (match.end_in_second.line - match.start_in_second.line + 1)
            for match in matches
        )
        
        return min(100.0, (matched_lines / total_lines) * 100.0)

    # Helper methods for data processing
    def _detect_language(self, filename: str) -> str:
        """Detect programming language from filename."""
        ext = Path(filename).suffix.lower()
        language_map = {
            '.py': 'python',
            '.java': 'java',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.cs': 'csharp',
            '.go': 'go',
            '.kt': 'kotlin',
            '.rs': 'rust',
            '.swift': 'swift',
            '.scala': 'scala'
        }
        return language_map.get(ext, 'text')

    def _extract_user_names(self, comparison_data: dict[str, Any]) -> dict[str, str]:
        """Extract user names from comparison data."""
        # This would need to be customized based on your submission naming convention
        return {
            comparison_data["firstSubmission"]: comparison_data["firstSubmission"],
            comparison_data["secondSubmission"]: comparison_data["secondSubmission"]
        }

    def _extract_file_counts(self, comparison_data: dict[str, Any], data: dict[str, Any]) -> dict[str, int]:
        """Extract file counts for submissions."""
        file_index = data.get("submissionFileIndex", {}).get("fileIndexes", {})
        return {
            comparison_data["firstSubmission"]: len(file_index.get(comparison_data["firstSubmission"], {})),
            comparison_data["secondSubmission"]: len(file_index.get(comparison_data["secondSubmission"], {}))
        }

    def _extract_languages(self, comparison_data: dict[str, Any], data: dict[str, Any]) -> dict[str, str]:
        """Extract programming languages for submissions."""
        # This would analyze the files to determine languages
        return {
            comparison_data["firstSubmission"]: "cpp",  # Default
            comparison_data["secondSubmission"]: "cpp"   # Default
        }

    def _get_dominant_language(self, members: list[str], data: dict[str, Any]) -> str | None:
        """Get the dominant programming language in a cluster."""
        # Analyze the submissions in the cluster to find the most common language
        return "cpp"  # Default implementation

    def _build_similarity_matrix(self, members: list[str], data: dict[str, Any]) -> dict[str, dict[str, float]]:
        """Build pairwise similarity matrix for cluster members."""
        matrix = {}
        top_comparisons = data.get("topComparisons", [])
        
        for member1 in members:
            matrix[member1] = {}
            for member2 in members:
                if member1 == member2:
                    matrix[member1][member2] = 1.0
                else:
                    # Find similarity from top comparisons
                    similarity = 0.0
                    for comp in top_comparisons:
                        if ((comp["firstSubmission"] == member1 and comp["secondSubmission"] == member2) or
                            (comp["firstSubmission"] == member2 and comp["secondSubmission"] == member1)):
                            similarity = comp["similarities"].get("AVG", 0.0)
                            break
                    matrix[member1][member2] = similarity
        
        return matrix

    def _detect_submission_language(self, submission_id: str, data: dict[str, Any]) -> str | None:
        """Detect the programming language for a submission."""
        file_index = data.get("submissionFileIndex", {}).get("fileIndexes", {})
        files = file_index.get(submission_id, {})
        
        # Analyze file extensions to determine language
        languages = set()
        for filename in files.keys():
            lang = self._detect_language(filename)
            if lang != 'text':
                languages.add(lang)
        
        return next(iter(languages), None) if languages else None

    def _count_submission_lines(self, submission_id: str, data: dict[str, Any]) -> int | None:
        """Count lines of code for a submission."""
        source_files = data.get("source_files", {})
        total_lines = 0
        
        for file_path, content in source_files.items():
            if f"/{submission_id}/" in file_path:
                total_lines += len(content.splitlines())
        
        return total_lines if total_lines > 0 else None

    def _calculate_average_similarity(self, comparisons: list[TopComparison]) -> float:
        """Calculate average similarity from comparisons."""
        if not comparisons:
            return 0.0
        
        similarities = [comp.similarities.get("AVG", 0.0) for comp in comparisons]
        return sum(similarities) / len(similarities)

    def _calculate_median_similarity(self, comparisons: list[TopComparison]) -> float:
        """Calculate median similarity from comparisons."""
        if not comparisons:
            return 0.0
        
        similarities = sorted([comp.similarities.get("AVG", 0.0) for comp in comparisons])
        n = len(similarities)
        
        if n % 2 == 0:
            return (similarities[n // 2 - 1] + similarities[n // 2]) / 2.0
        else:
            return similarities[n // 2]

    def _get_max_similarity(self, comparisons: list[TopComparison]) -> float:
        """Get maximum similarity from comparisons."""
        if not comparisons:
            return 0.0
        
        return max(comp.similarities.get("AVG", 0.0) for comp in comparisons)

    def _get_min_similarity(self, comparisons: list[TopComparison]) -> float:
        """Get minimum similarity from comparisons."""
        if not comparisons:
            return 0.0
        
        return min(comp.similarities.get("AVG", 0.0) for comp in comparisons)

    def _get_avg_similarity(self, comparisons: list[TopComparison]) -> float:
        """Get average similarity from comparisons."""
        return self._calculate_average_similarity(comparisons)

    def _analyze_language_statistics(
        self, 
        submission_stats: list[SubmissionStats], 
        comparisons: list[TopComparison]
    ) -> dict[str, dict[str, Any]]:
        """Analyze statistics by programming language."""
        lang_stats = {}
        
        # Group submissions by language
        by_language = {}
        for stat in submission_stats:
            if stat.language:
                if stat.language not in by_language:
                    by_language[stat.language] = []
                by_language[stat.language].append(stat)
        
        # Calculate statistics for each language
        for language, stats in by_language.items():
            # Find comparisons involving this language
            lang_comparisons = []
            for comp in comparisons:
                # This would need better language detection per comparison
                lang_comparisons.append(comp)
            
            lang_stats[language] = {
                "submission_count": len(stats),
                "total_tokens": sum(s.total_tokens for s in stats),
                "avg_tokens": sum(s.total_tokens for s in stats) / len(stats) if stats else 0,
                "high_similarity_pairs": len(lang_comparisons),
                "max_similarity": self._get_max_similarity(lang_comparisons),
                "avg_similarity": self._get_avg_similarity(lang_comparisons)
            }
        
        return lang_stats
