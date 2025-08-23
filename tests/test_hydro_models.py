"""Tests for Hydro OJ models."""

from datetime import datetime

import pytest
from bson import ObjectId

from src.api.hydro_models import (
    ContestPlagiarismRequest,
    HydroSubmission,
    PlagiarismResult,
    SubmissionStatus,
)


class TestHydroSubmission:
    """Test HydroSubmission model."""

    def test_hydro_submission_creation(self):
        """Test creating a HydroSubmission."""
        submission_data = {
            "_id": ObjectId(),
            "status": SubmissionStatus.ACCEPTED,
            "uid": 21,
            "code": "print('hello world')",
            "lang": "python.python3",
            "pid": 2630,
            "domainId": "system",
            "score": 100,
            "time": 163.77976,
            "memory": 408,
            "judger": 1,
            "judgeAt": datetime.utcnow(),
            "rejudged": False,
            "contest": ObjectId(),
        }

        submission = HydroSubmission(**submission_data)

        assert submission.status == SubmissionStatus.ACCEPTED
        assert submission.uid == 21
        assert submission.code == "print('hello world')"
        assert submission.lang == "python.python3"
        assert submission.pid == 2630
        assert submission.domain_id == "system"
        assert submission.score == 100

    def test_hydro_submission_with_defaults(self):
        """Test HydroSubmission with default values."""
        minimal_data = {
            "status": SubmissionStatus.ACCEPTED,
            "uid": 21,
            "code": "print('hello world')",
            "lang": "python.python3",
            "pid": 2630,
            "domainId": "system",
            "score": 100,
            "time": 163.77976,
            "memory": 408,
            "judger": 1,
            "judgeAt": datetime.utcnow(),
        }

        submission = HydroSubmission(**minimal_data)

        assert submission.rejudged is False
        assert submission.judge_texts == []
        assert submission.compiler_texts == []
        assert submission.test_cases == []
        assert submission.files == {}
        assert submission.subtasks == {}


class TestContestPlagiarismRequest:
    """Test ContestPlagiarismRequest model."""

    def test_contest_plagiarism_request_creation(self):
        """Test creating a ContestPlagiarismRequest."""
        request = ContestPlagiarismRequest(contest_id="689ede86bfd7f1255f21e643")

        assert request.contest_id == "689ede86bfd7f1255f21e643"
        assert request.min_tokens == 9
        assert request.similarity_threshold == 0.0

    def test_contest_plagiarism_request_with_custom_values(self):
        """Test ContestPlagiarismRequest with custom values."""
        request = ContestPlagiarismRequest(
            contest_id="689ede86bfd7f1255f21e643",
            min_tokens=15,
            similarity_threshold=0.8,
        )

        assert request.contest_id == "689ede86bfd7f1255f21e643"
        assert request.min_tokens == 15
        assert request.similarity_threshold == 0.8

    def test_contest_plagiarism_request_validation(self):
        """Test ContestPlagiarismRequest validation."""
        with pytest.raises(ValueError):
            ContestPlagiarismRequest(
                contest_id="test",
                min_tokens=0,  # min_tokens must be >= 1
            )

        with pytest.raises(ValueError):
            ContestPlagiarismRequest(
                contest_id="test",
                similarity_threshold=1.5,  # must be <= 1.0
            )


class TestPlagiarismResult:
    """Test PlagiarismResult model."""

    def test_plagiarism_result_creation(self):
        """Test creating a PlagiarismResult."""
        result = PlagiarismResult(
            contest_id="689ede86bfd7f1255f21e643",
            problem_id=2630,
            analysis_id="test-analysis-id",
            total_submissions=10,
            total_comparisons=45,
            execution_time_ms=5000,
        )

        assert result.contest_id == "689ede86bfd7f1255f21e643"
        assert result.problem_id == 2630
        assert result.analysis_id == "test-analysis-id"
        assert result.total_submissions == 10
        assert result.total_comparisons == 45
        assert result.execution_time_ms == 5000
        assert result.high_similarity_pairs == []
        assert result.clusters == []
        assert result.submission_stats == []
        assert result.failed_submissions == []
        assert isinstance(result.created_at, datetime)

    def test_plagiarism_result_with_data(self):
        """Test PlagiarismResult with similarity data."""
        similarity_pair = {
            "first_submission": "submission_1",
            "second_submission": "submission_2",
            "similarities": {"AVG": 0.85, "MAX": 0.92},
        }

        cluster = {
            "index": 0,
            "average_similarity": 0.88,
            "strength": 0.75,
            "members": ["submission_1", "submission_2", "submission_3"],
        }

        result = PlagiarismResult(
            contest_id="689ede86bfd7f1255f21e643",
            problem_id=2630,
            analysis_id="test-analysis-id",
            total_submissions=10,
            total_comparisons=45,
            execution_time_ms=5000,
            high_similarity_pairs=[similarity_pair],
            clusters=[cluster],
        )

        assert len(result.high_similarity_pairs) == 1
        assert result.high_similarity_pairs[0]["first_submission"] == "submission_1"
        assert len(result.clusters) == 1
        assert result.clusters[0]["index"] == 0


class TestSubmissionStatus:
    """Test SubmissionStatus constants."""

    def test_submission_status_constants(self):
        """Test submission status constants."""
        assert SubmissionStatus.WAITING == 0
        assert SubmissionStatus.ACCEPTED == 1
        assert SubmissionStatus.WRONG_ANSWER == 2
        assert SubmissionStatus.TIME_EXCEEDED == 3
        assert SubmissionStatus.MEMORY_EXCEEDED == 4
        assert SubmissionStatus.OUTPUT_EXCEEDED == 5
        assert SubmissionStatus.RUNTIME_ERROR == 6
        assert SubmissionStatus.COMPILE_ERROR == 7
        assert SubmissionStatus.SYSTEM_ERROR == 8
        assert SubmissionStatus.CANCELLED == 9
        assert SubmissionStatus.UNKNOWN_ERROR == 10
        assert SubmissionStatus.RUNNING == 20
        assert SubmissionStatus.COMPILING == 21
        assert SubmissionStatus.FETCHED == 22
        assert SubmissionStatus.IGNORED == 30
