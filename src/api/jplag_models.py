"""JPlag related data models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ProgrammingLanguage(str, Enum):
    """Supported programming languages for JPlag."""

    JAVA = "java"
    PYTHON3 = "python3"
    CPP = "cpp"
    C = "c"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    CSHARP = "csharp"
    GO = "go"
    KOTLIN = "kotlin"
    RUST = "rust"
    SCALA = "scala"
    SWIFT = "swift"
    TEXT = "text"


class SimilarityMetric(str, Enum):
    """Similarity metrics used by JPlag."""

    AVG = "AVG"
    MAX = "MAX"
    LONGEST_MATCH = "LONGEST_MATCH"
    MAXIMUM_LENGTH = "MAXIMUM_LENGTH"


class CodePosition(BaseModel):
    """Position information in source code."""

    line: int = Field(..., description="Line number (1-based)")
    column: int = Field(..., description="Column number (0-based)")
    token_index: int = Field(..., description="Token index (0-based)")


class CodeLine(BaseModel):
    """A line of code with metadata."""

    line_number: int = Field(..., description="Line number in file")
    content: str = Field(..., description="Line content")
    is_match: bool = Field(default=False, description="Whether this line is part of a match")
    match_type: str | None = Field(None, description="Type of match (exact, similar, etc.)")
    match_id: str | None = Field(None, description="Unique match identifier")


class FileContent(BaseModel):
    """Content of a source code file."""
    
    filename: str = Field(..., description="Name of the file")
    content: str = Field(..., description="Full file content")
    lines: list[CodeLine] = Field(..., description="Lines with metadata")
    language: str = Field(..., description="Programming language")
    total_lines: int = Field(..., description="Total number of lines")
    total_tokens: int = Field(..., description="Total number of tokens")


class Match(BaseModel):
    """Represents a code match between two submissions."""

    first_file_name: str = Field(..., description="File name in first submission")
    second_file_name: str = Field(..., description="File name in second submission")
    start_in_first: CodePosition = Field(
        ..., description="Start position in first file"
    )
    end_in_first: CodePosition = Field(..., description="End position in first file")
    start_in_second: CodePosition = Field(
        ..., description="Start position in second file"
    )
    end_in_second: CodePosition = Field(..., description="End position in second file")
    length_of_first: int = Field(..., description="Match length in first submission")
    length_of_second: int = Field(..., description="Match length in second submission")
    
    # Enhanced fields for detailed analysis
    matched_tokens: int = Field(default=0, description="Number of matched tokens")
    similarity_score: float = Field(default=0.0, description="Similarity score for this match")
    match_id: str = Field(default="", description="Unique match identifier")


class ComparisonResult(BaseModel):
    """Detailed comparison result between two submissions."""

    first_submission_id: str = Field(..., description="First submission identifier")
    second_submission_id: str = Field(..., description="Second submission identifier")
    similarities: dict[str, float] = Field(
        ..., description="Similarity scores by metric"
    )
    matches: list[Match] = Field(
        default_factory=list, description="List of matched code segments"
    )
    first_similarity: float = Field(
        ..., description="Similarity of first to second submission"
    )
    second_similarity: float = Field(
        ..., description="Similarity of second to first submission"
    )
    
    # Enhanced fields for detailed comparison
    first_files: list[FileContent] = Field(default=[], description="Files from first submission")
    second_files: list[FileContent] = Field(default=[], description="Files from second submission")
    match_coverage: float = Field(default=0.0, description="Percentage of code covered by matches")
    longest_match: int = Field(default=0, description="Length of longest match")
    total_matched_lines: int = Field(default=0, description="Total lines involved in matches")


class TopComparison(BaseModel):
    """Summary comparison result."""

    first_submission: str = Field(..., description="First submission name")
    second_submission: str = Field(..., description="Second submission name")
    similarities: dict[str, float] = Field(
        ..., description="Similarity scores by metric"
    )
    
    # Enhanced fields
    user_names: dict[str, str] | None = Field(None, description="User display names")
    submission_times: dict[str, datetime] | None = Field(None, description="Submission timestamps")
    file_counts: dict[str, int] | None = Field(None, description="Number of files per submission")
    languages: dict[str, str] | None = Field(None, description="Programming languages used")


class ClusterInfo(BaseModel):
    """Information about a plagiarism cluster."""

    index: int = Field(..., description="Cluster index")
    average_similarity: float = Field(
        ..., description="Average similarity within cluster"
    )
    strength: float = Field(..., description="Cluster strength")
    members: list[str] = Field(..., description="Submission IDs in cluster")
    
    # Enhanced fields
    size: int = Field(default=0, description="Number of members in cluster")
    dominant_language: str | None = Field(None, description="Most common language in cluster")
    member_details: list[SubmissionStats] = Field(default=[], description="Detailed member information")
    similarity_matrix: dict[str, dict[str, float]] = Field(default={}, description="Pairwise similarities")


class FailedSubmission(BaseModel):
    """Information about a failed submission."""

    name: str = Field(..., description="Submission name")
    state: str = Field(..., description="Failure state")
    error_message: str | None = Field(None, description="Error message")


class DistributionData(BaseModel):
    """Distribution data for similarity scores."""
    
    buckets: list[dict[str, Any]] = Field(..., description="Distribution buckets")
    total_comparisons: int = Field(..., description="Total number of comparisons")
    average_similarity: float = Field(..., description="Average similarity")
    median_similarity: float = Field(..., description="Median similarity")
    max_similarity: float = Field(..., description="Maximum similarity")
    min_similarity: float = Field(..., description="Minimum similarity")


class RunInformation(BaseModel):
    """Information about JPlag execution run."""

    report_viewer_version: str = Field(..., description="JPlag version")
    failed_submissions: list[FailedSubmission] = Field(default_factory=list)
    submission_date: str = Field(..., description="Analysis date")
    duration: int = Field(..., description="Execution duration in milliseconds")
    total_comparisons: int = Field(..., description="Total number of comparisons")
    
    # Enhanced fields
    jplag_version: str | None = Field(None, description="JPlag version used")
    options: dict[str, Any] | None = Field(None, description="Analysis options")


class PlagiarismAnalysisRequest(BaseModel):
    """Request model for plagiarism analysis."""

    language: ProgrammingLanguage = Field(
        default=ProgrammingLanguage.JAVA,
        description="Programming language of submissions",
    )
    min_tokens: int = Field(
        default=9, ge=1, le=100, description="Minimum token match threshold"
    )
    similarity_threshold: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum similarity threshold for reporting",
    )
    base_code_included: bool = Field(
        default=False, description="Whether base code is included in submissions"
    )
    normalize_tokens: bool = Field(
        default=False, description="Whether to normalize tokens"
    )


class SubmissionStats(BaseModel):
    """Statistics for a single submission."""

    submission_id: str = Field(..., description="Submission identifier")
    display_name: str = Field(..., description="Display name")
    file_count: int = Field(..., description="Number of files")
    total_tokens: int = Field(..., description="Total token count")
    
    # Enhanced fields
    language: str | None = Field(None, description="Programming language")
    lines_of_code: int | None = Field(None, description="Total lines of code")
    submission_time: datetime | None = Field(None, description="Submission timestamp")
    user_id: str | None = Field(None, description="User identifier")


class PlagiarismAnalysisResult(BaseModel):
    """Result of plagiarism analysis."""

    analysis_id: str = Field(..., description="Unique analysis identifier")
    total_submissions: int = Field(..., description="Total number of submissions")
    total_comparisons: int = Field(..., description="Total number of comparisons")
    execution_time_ms: int = Field(..., description="Execution time in milliseconds")
    high_similarity_pairs: list[TopComparison] = Field(
        default_factory=list, description="Pairs with high similarity"
    )
    clusters: list[ClusterInfo] = Field(
        default_factory=list, description="Detected plagiarism clusters"
    )
    submission_stats: list[SubmissionStats] = Field(
        default_factory=list, description="Per-submission statistics"
    )
    failed_submissions: list[FailedSubmission] = Field(
        default_factory=list, description="Submissions that failed to process"
    )
    
    # Enhanced fields
    distribution: DistributionData | None = Field(None, description="Similarity distribution")
    language_distribution: dict[str, int] = Field(default={}, description="Language usage statistics")
    options: dict[str, Any] | None = Field(None, description="Analysis options used")
    run_information: RunInformation | None = Field(None, description="Detailed run information")


class DetailedComparisonRequest(BaseModel):
    """Request for detailed comparison between two submissions."""

    analysis_id: str = Field(..., description="Analysis identifier")
    first_submission: str = Field(..., description="First submission identifier")
    second_submission: str = Field(..., description="Second submission identifier")


class PlagiarismDetectionStats(BaseModel):
    """Overall statistics for plagiarism detection."""

    suspicious_pairs_count: int = Field(..., description="Number of suspicious pairs")
    max_similarity: float = Field(..., description="Maximum similarity found")
    avg_similarity: float = Field(..., description="Average similarity")
    cluster_count: int = Field(..., description="Number of clusters found")
    processing_time_ms: int = Field(..., description="Total processing time")


class ProblemPlagiarismData(BaseModel):
    """Comprehensive plagiarism data for a problem."""
    
    problem_id: int = Field(..., description="Problem identifier")
    contest_id: str = Field(..., description="Contest identifier")
    analysis_id: str = Field(..., description="Analysis identifier")
    total_submissions: int = Field(..., description="Total submissions analyzed")
    high_similarity_count: int = Field(..., description="Number of high similarity pairs")
    max_similarity: float = Field(..., description="Maximum similarity score")
    avg_similarity: float = Field(..., description="Average similarity score")
    
    # Detailed breakdown
    top_comparisons: list[TopComparison] = Field(..., description="Top similarity pairs")
    clusters: list[ClusterInfo] = Field(..., description="Detected clusters")
    language_stats: dict[str, dict[str, Any]] = Field(default={}, description="Statistics by language")
    distribution: DistributionData | None = Field(None, description="Similarity distribution")
    
    # Metadata
    created_at: datetime = Field(..., description="Analysis creation time")
    updated_at: datetime = Field(..., description="Last update time")
    status: str = Field(default="completed", description="Analysis status")
