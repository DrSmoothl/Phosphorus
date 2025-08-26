"""JPlag service for running plagiarism detection and parsing results."""

import asyncio
import json
import os
import tempfile
import uuid
import zipfile
from typing import Any

from fastapi import UploadFile

from ..api.jplag_models import (
    ClusterInfo,
    CodePosition,
    ComparisonResult,
    FailedSubmission,
    Match,
    PlagiarismAnalysisRequest,
    PlagiarismAnalysisResult,
    RunInformation,
    SubmissionStats,
    TopComparison,
)
from ..common import get_logger

logger = get_logger()


class JPlagService:
    """Service for JPlag operations."""

    def __init__(self, jplag_jar_path: str):
        """Initialize JPlag service.

        Args:
            jplag_jar_path: Path to JPlag JAR file
        """
        self.jplag_jar_path = jplag_jar_path
        if not os.path.exists(jplag_jar_path):
            raise FileNotFoundError(f"JPlag JAR not found: {jplag_jar_path}")

    async def analyze_submissions(
        self,
        files: list[UploadFile],
        request: PlagiarismAnalysisRequest,
    ) -> PlagiarismAnalysisResult:
        """Analyze submissions for plagiarism.

        Args:
            files: List of uploaded files
            request: Analysis configuration

        Returns:
            Analysis result
        """
        analysis_id = str(uuid.uuid4())
        logger.info(f"Starting plagiarism analysis {analysis_id}")

        with tempfile.TemporaryDirectory() as temp_dir:
            # Save uploaded files
            submission_dir = await self._save_uploads(files, temp_dir)

            # Run JPlag
            jplag_result_path = await self._run_jplag(
                submission_dir, request, temp_dir, analysis_id
            )

            # Parse results
            result = await self._parse_jplag_results(
                jplag_result_path, analysis_id, request
            )

        logger.info(f"Completed plagiarism analysis {analysis_id}")
        return result

    async def get_detailed_comparison(
        self, analysis_id: str, _first_submission: str, _second_submission: str
    ) -> ComparisonResult | None:
        """Get detailed comparison between two submissions.

        Args:
            analysis_id: Analysis identifier
            first_submission: First submission ID
            second_submission: Second submission ID

        Returns:
            Detailed comparison result or None if not found
        """
        # This would typically load from a persistent store
        # For now, return None as we don't persist results
        logger.warning(f"Detailed comparison not available for {analysis_id}")
        return None

    async def _save_uploads(self, files: list[UploadFile], base_dir: str) -> str:
        """Save uploaded files to temporary directory.

        Args:
            files: List of uploaded files
            base_dir: Base temporary directory

        Returns:
            Path to submissions directory
        """
        submission_dir = os.path.join(base_dir, "submissions")
        os.makedirs(submission_dir, exist_ok=True)

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

        logger.info(f"Saved {len(files)} files to {submission_dir}")
        return submission_dir

    async def _run_jplag(
        self,
        submission_dir: str,
        request: PlagiarismAnalysisRequest,
        temp_dir: str,
        analysis_id: str,
    ) -> str:
        """Run JPlag analysis.

        Args:
            submission_dir: Directory containing submissions
            request: Analysis configuration
            temp_dir: Temporary directory
            analysis_id: Analysis identifier

        Returns:
            Path to JPlag result file
        """
        result_file = os.path.join(temp_dir, f"result_{analysis_id}")

        # Build JPlag command
        cmd = [
            "java",
            "-jar",
            self.jplag_jar_path,
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
            submission_dir,
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

        _, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            logger.error(f"JPlag failed: {error_msg}")
            raise RuntimeError(f"JPlag execution failed: {error_msg}")

        logger.info("JPlag completed successfully")

        # Return path to .jplag file
        jplag_file = f"{result_file}.jplag"
        if not os.path.exists(jplag_file):
            raise RuntimeError(f"JPlag result file not found: {jplag_file}")

        return jplag_file

    async def _parse_jplag_results(
        self,
        jplag_file_path: str,
        analysis_id: str,
        _request: PlagiarismAnalysisRequest,
    ) -> PlagiarismAnalysisResult:
        """Parse JPlag results file.

        Args:
            jplag_file_path: Path to .jplag file
            analysis_id: Analysis identifier
            request: Original request

        Returns:
            Parsed analysis result
        """
        logger.info(f"Parsing JPlag results from {jplag_file_path}")

        if not zipfile.is_zipfile(jplag_file_path):
            raise ValueError(f"Invalid JPlag file: {jplag_file_path}")

        data = {}
        with zipfile.ZipFile(jplag_file_path, "r") as zip_file:
            # Parse all JSON files
            data.update(await self._parse_zip_contents(zip_file))

        # Build result
        result = await self._build_analysis_result(data, analysis_id)
        logger.info(f"Parsed {result.total_comparisons} comparisons")

        return result

    async def _parse_zip_contents(self, zip_file: zipfile.ZipFile) -> dict[str, Any]:
        """Parse contents of JPlag ZIP file.

        Args:
            zip_file: Opened ZIP file

        Returns:
            Parsed data dictionary
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
            f
            for f in zip_file.namelist()
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

        return data

    async def _build_analysis_result(  # pylint: disable=too-many-locals
        self, data: dict[str, Any], analysis_id: str
    ) -> PlagiarismAnalysisResult:
        """Build analysis result from parsed data.

        Args:
            data: Parsed data from JPlag file
            analysis_id: Analysis identifier

        Returns:
            Structured analysis result
        """
        # Parse run information
        run_info_data = data.get("runInformation", {})
        run_info = RunInformation(
            report_viewer_version=run_info_data.get("reportViewerVersion", "unknown"),
            failed_submissions=[
                FailedSubmission(name=fs["name"], state=fs["state"])
                for fs in run_info_data.get("failedSubmissions", [])
            ],
            submission_date=run_info_data.get("submissionDate", ""),
            duration=run_info_data.get("duration", 0),
            total_comparisons=run_info_data.get("totalComparisons", 0),
        )

        # Parse top comparisons
        top_comparisons_data = data.get("topComparisons", [])
        high_similarity_pairs = [
            TopComparison(
                first_submission=tc["firstSubmission"],
                second_submission=tc["secondSubmission"],
                similarities=tc["similarities"],
            )
            for tc in top_comparisons_data
        ]

        # Parse clusters
        cluster_data = data.get("cluster", [])
        clusters = [
            ClusterInfo(
                index=cluster["index"],
                average_similarity=cluster["averageSimilarity"],
                strength=cluster["strength"],
                members=cluster["members"],
            )
            for cluster in cluster_data
        ]

        # Parse submission statistics
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
                )
            )

        return PlagiarismAnalysisResult(
            analysis_id=analysis_id,
            total_submissions=len(submission_stats),
            total_comparisons=run_info.total_comparisons,
            execution_time_ms=run_info.duration,
            high_similarity_pairs=high_similarity_pairs,
            clusters=clusters,
            submission_stats=submission_stats,
            failed_submissions=run_info.failed_submissions,
        )

    def _parse_code_position(self, pos_data: dict[str, Any]) -> CodePosition:
        """Parse code position from JSON data.

        Args:
            pos_data: Position data from JSON

        Returns:
            CodePosition object
        """
        return CodePosition(
            line=pos_data["line"],
            column=pos_data["column"],
            token_index=pos_data["tokenListIndex"],
        )

    def _parse_match(self, match_data: dict[str, Any]) -> Match:
        """Parse match from JSON data.

        Args:
            match_data: Match data from JSON

        Returns:
            Match object
        """
        return Match(
            first_file_name=match_data["firstFileName"],
            second_file_name=match_data["secondFileName"],
            start_in_first=self._parse_code_position(match_data["startInFirst"]),
            end_in_first=self._parse_code_position(match_data["endInFirst"]),
            start_in_second=self._parse_code_position(match_data["startInSecond"]),
            end_in_second=self._parse_code_position(match_data["endInSecond"]),
            length_of_first=match_data["lengthOfFirst"],
            length_of_second=match_data["lengthOfSecond"],
        )

    def _parse_comparison_result(self, comp_data: dict[str, Any]) -> ComparisonResult:
        """Parse detailed comparison result.

        Args:
            comp_data: Comparison data from JSON

        Returns:
            ComparisonResult object
        """
        matches = [
            self._parse_match(match_data) for match_data in comp_data.get("matches", [])
        ]

        return ComparisonResult(
            first_submission_id=comp_data["firstSubmissionId"],
            second_submission_id=comp_data["secondSubmissionId"],
            similarities=comp_data["similarities"],
            matches=matches,
            first_similarity=comp_data["firstSimilarity"],
            second_similarity=comp_data["secondSimilarity"],
        )
