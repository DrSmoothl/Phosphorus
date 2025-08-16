"""JPlag related data models."""

from enum import Enum

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


class TopComparison(BaseModel):
    """Summary comparison result."""

    first_submission: str = Field(..., description="First submission name")
    second_submission: str = Field(..., description="Second submission name")
    similarities: dict[str, float] = Field(
        ..., description="Similarity scores by metric"
    )


class ClusterInfo(BaseModel):
    """Information about a plagiarism cluster."""

    index: int = Field(..., description="Cluster index")
    average_similarity: float = Field(
        ..., description="Average similarity within cluster"
    )
    strength: float = Field(..., description="Cluster strength")
    members: list[str] = Field(..., description="Submission IDs in cluster")


class FailedSubmission(BaseModel):
    """Information about a failed submission."""

    name: str = Field(..., description="Submission name")
    state: str = Field(..., description="Failure state")


class RunInformation(BaseModel):
    """Information about JPlag execution run."""

    report_viewer_version: str = Field(..., description="JPlag version")
    failed_submissions: list[FailedSubmission] = Field(default_factory=list)
    submission_date: str = Field(..., description="Analysis date")
    duration: int = Field(..., description="Execution duration in milliseconds")
    total_comparisons: int = Field(..., description="Total number of comparisons")


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
