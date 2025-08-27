"""Hydro OJ related data models."""

from datetime import datetime
from typing import Any, ClassVar

from bson import ObjectId
from pydantic import BaseModel, Field


class PyObjectId(ObjectId):
    """Pydantic compatible ObjectId."""

    @classmethod
    def __get_validators__(cls):
        """Get validators for Pydantic."""
        yield cls.validate

    @classmethod
    def validate(cls, v: Any, field=None) -> ObjectId:
        """Validate ObjectId."""
        if isinstance(v, ObjectId):
            return v
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(
        cls, field_schema: dict[str, Any]
    ) -> dict[str, Any]:
        """Get JSON schema for Pydantic."""
        field_schema.update(type="string")
        return field_schema


class HydroSubmission(BaseModel):
    """Hydro submission record."""

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    status: int = Field(..., description="Submission status")
    uid: int = Field(..., description="User ID")
    code: str = Field(..., description="Source code")
    lang: str = Field(..., description="Programming language")
    pid: int = Field(..., description="Problem ID")
    domain_id: str = Field(..., alias="domainId", description="Domain ID")
    score: int = Field(..., description="Score")
    time: float = Field(..., description="Execution time in ms")
    memory: int = Field(..., description="Memory usage")
    judge_texts: list[str] = Field(default_factory=list, alias="judgeTexts")
    compiler_texts: list[str] = Field(default_factory=list, alias="compilerTexts")
    test_cases: list[dict[str, Any]] = Field(default_factory=list, alias="testCases")
    judger: int = Field(..., description="Judger ID")
    judge_at: datetime = Field(..., alias="judgeAt", description="Judge timestamp")
    rejudged: bool = Field(default=False, description="Whether rejudged")
    contest: PyObjectId | None = Field(None, description="Contest ID")
    files: dict[str, Any] = Field(default_factory=dict, description="Files")
    subtasks: dict[str, Any] = Field(default_factory=dict, description="Subtasks")

    class Config:
        """Pydantic config."""

        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders: ClassVar = {ObjectId: str}


class ContestPlagiarismRequest(BaseModel):
    """Request for contest plagiarism check."""

    contest_id: str = Field(..., description="Contest ID")
    min_tokens: int = Field(default=9, ge=1, le=100, description="Minimum token match")
    similarity_threshold: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Similarity threshold"
    )


class ContestProblemSelectionRequest(BaseModel):
    """Request for contest problem selection plagiarism check."""

    contest_id: str = Field(..., description="Contest ID")
    problem_ids: list[int] = Field(..., description="Selected problem IDs to check")
    min_tokens: int = Field(default=9, ge=1, le=100, description="Minimum token match")
    similarity_threshold: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Similarity threshold"
    )


class ContestInfo(BaseModel):
    """Contest information."""

    id: str = Field(..., description="Contest ID")
    title: str = Field(..., description="Contest title")
    description: str = Field(..., description="Contest description")
    begin_at: datetime = Field(..., description="Contest start time")
    end_at: datetime = Field(..., description="Contest end time")
    total_problems: int = Field(..., description="Total number of problems")
    checked_problems: int = Field(default=0, description="Number of checked problems")
    last_check_at: datetime | None = Field(None, description="Last check timestamp")


class ProblemInfo(BaseModel):
    """Problem information."""

    id: int = Field(..., description="Problem ID")
    title: str = Field(..., description="Problem title")
    total_submissions: int = Field(..., description="Total submissions")
    accepted_submissions: int = Field(..., description="Accepted submissions")
    languages: list[str] = Field(..., description="Programming languages used")
    last_check_at: datetime | None = Field(None, description="Last check timestamp")


class LanguageStats(BaseModel):
    """Language statistics for a problem."""

    language: str = Field(..., description="Programming language")
    submission_count: int = Field(..., description="Number of submissions")
    unique_users: int = Field(..., description="Number of unique users")
    jplag_language: str = Field(..., description="Corresponding JPlag language")
    can_analyze: bool = Field(..., description="Whether this language can be analyzed")


class PlagiarismResult(BaseModel):
    """Plagiarism check result."""

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    contest_id: str = Field(..., description="Contest ID")
    problem_id: int = Field(..., description="Problem ID")
    analysis_id: str = Field(..., description="JPlag analysis ID")
    total_submissions: int = Field(..., description="Total submissions analyzed")
    total_comparisons: int = Field(..., description="Total comparisons made")
    execution_time_ms: int = Field(..., description="Execution time")
    high_similarity_pairs: list[dict[str, Any]] = Field(
        default_factory=list, description="High similarity pairs"
    )
    clusters: list[dict[str, Any]] = Field(
        default_factory=list, description="Detected clusters"
    )
    submission_stats: list[dict[str, Any]] = Field(
        default_factory=list, description="Submission statistics"
    )
    failed_submissions: list[dict[str, Any]] = Field(
        default_factory=list, description="Failed submissions"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    jplag_file_path: str | None = Field(None, description="Path to JPlag result file")

    class Config:
        """Pydantic config."""

        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders: ClassVar = {ObjectId: str, datetime: lambda v: v.isoformat()}


class SubmissionStatus:
    """Hydro submission status constants."""

    WAITING = 0
    ACCEPTED = 1
    WRONG_ANSWER = 2
    TIME_EXCEEDED = 3
    MEMORY_EXCEEDED = 4
    OUTPUT_EXCEEDED = 5
    RUNTIME_ERROR = 6
    COMPILE_ERROR = 7
    SYSTEM_ERROR = 8
    CANCELLED = 9
    UNKNOWN_ERROR = 10
    RUNNING = 20
    COMPILING = 21
    FETCHED = 22
    IGNORED = 30
