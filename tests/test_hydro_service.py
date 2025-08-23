"""Tests for Hydro OJ service."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId

from src.api.hydro_models import (
    ContestPlagiarismRequest,
    HydroSubmission,
    PlagiarismResult,
    SubmissionStatus,
)
from src.api.jplag_models import ProgrammingLanguage
from src.services.hydro_service import HydroService


@pytest.fixture
def mock_database():
    """Create mock database."""
    db = MagicMock()
    db.record = MagicMock()
    db.check_plagiarism_results = MagicMock()
    return db


@pytest.fixture
def mock_jplag_service():
    """Create mock JPlag service."""
    service = MagicMock()
    service.analyze_submissions = AsyncMock()
    return service


@pytest.fixture
def hydro_service(mock_database, mock_jplag_service):
    """Create HydroService instance."""
    return HydroService(mock_database, mock_jplag_service)


@pytest.fixture
def sample_submissions():
    """Create sample submissions."""
    contest_id = ObjectId()
    return [
        HydroSubmission(
            _id=ObjectId(),
            status=SubmissionStatus.ACCEPTED,
            uid=21,
            code="print('hello world')",
            lang="python.python3",
            pid=2630,
            domainId="system",
            score=100,
            time=163.77976,
            memory=408,
            judger=1,
            judgeAt=datetime.utcnow(),
            contest=contest_id,
        ),
        HydroSubmission(
            _id=ObjectId(),
            status=SubmissionStatus.ACCEPTED,
            uid=22,
            code="print('hello world')",
            lang="python.python3",
            pid=2630,
            domainId="system",
            score=100,
            time=150.0,
            memory=400,
            judger=1,
            judgeAt=datetime.utcnow(),
            contest=contest_id,
        ),
    ]


class TestHydroService:
    """Test HydroService class."""

    def test_group_submissions_by_problem(self, hydro_service, sample_submissions):
        """Test grouping submissions by problem."""
        # Add submission for different problem
        different_problem = sample_submissions[1].model_copy()
        different_problem.pid = 2631
        submissions = [*sample_submissions, different_problem]

        result = hydro_service._group_submissions_by_problem(submissions)

        assert len(result) == 2
        assert 2630 in result
        assert 2631 in result
        assert len(result[2630]) == 2
        assert len(result[2631]) == 1

    def test_get_file_extension(self, hydro_service):
        """Test file extension detection."""
        assert hydro_service._get_file_extension("python.python3") == ".py"
        assert hydro_service._get_file_extension("cc.cc20o2") == ".cpp"
        assert hydro_service._get_file_extension("java") == ".java"
        assert hydro_service._get_file_extension("c.c11o2") == ".c"
        assert hydro_service._get_file_extension("unknown") == ".txt"

    def test_detect_programming_language(self, hydro_service):
        """Test programming language detection."""
        assert (
            hydro_service._detect_programming_language("python.python3")
            == ProgrammingLanguage.PYTHON3
        )
        assert (
            hydro_service._detect_programming_language("cc.cc20o2")
            == ProgrammingLanguage.CPP
        )
        assert (
            hydro_service._detect_programming_language("java")
            == ProgrammingLanguage.JAVA
        )
        assert (
            hydro_service._detect_programming_language("c.c11o2")
            == ProgrammingLanguage.C
        )
        assert (
            hydro_service._detect_programming_language("unknown")
            == ProgrammingLanguage.TEXT
        )

    @pytest.mark.asyncio
    async def test_get_contest_submissions_empty(self, hydro_service, mock_database):
        """Test getting contest submissions when none exist."""
        contest_id = ObjectId()
        mock_database.record.find.return_value.__aiter__ = AsyncMock(
            return_value=iter([])
        )

        result = await hydro_service._get_contest_submissions(contest_id)

        assert result == []
        mock_database.record.find.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_contest_submissions_success(
        self, hydro_service, mock_database, sample_submissions
    ):
        """Test getting contest submissions successfully."""
        contest_id = ObjectId()

        # Mock the cursor and async iteration
        mock_cursor = MagicMock()
        submission_docs = [sub.model_dump(by_alias=True) for sub in sample_submissions]
        mock_cursor.__aiter__ = AsyncMock(return_value=iter(submission_docs))
        mock_database.record.find.return_value = mock_cursor

        result = await hydro_service._get_contest_submissions(contest_id)

        assert len(result) == 2
        assert all(isinstance(sub, HydroSubmission) for sub in result)
        mock_database.record.find.assert_called_once_with(
            {
                "contest": contest_id,
                "status": SubmissionStatus.ACCEPTED,
                "code": {"$ne": ""},
            }
        )

    @pytest.mark.asyncio
    async def test_check_contest_plagiarism_no_submissions(
        self, hydro_service, mock_database
    ):
        """Test plagiarism check with no submissions."""
        contest_id = "689ede86bfd7f1255f21e643"
        request = ContestPlagiarismRequest(contest_id=contest_id)

        mock_database.record.find.return_value.__aiter__ = AsyncMock(
            return_value=iter([])
        )

        with pytest.raises(ValueError, match="No accepted submissions found"):
            await hydro_service.check_contest_plagiarism(request)

    @pytest.mark.asyncio
    async def test_check_contest_plagiarism_insufficient_submissions(
        self, hydro_service, mock_database, sample_submissions
    ):
        """Test plagiarism check with insufficient submissions per problem."""
        contest_id = "689ede86bfd7f1255f21e643"
        request = ContestPlagiarismRequest(contest_id=contest_id)

        # Only one submission per problem
        single_submission = [sample_submissions[0]]
        submission_docs = [sub.model_dump(by_alias=True) for sub in single_submission]

        mock_cursor = MagicMock()
        mock_cursor.__aiter__ = AsyncMock(return_value=iter(submission_docs))
        mock_database.record.find.return_value = mock_cursor

        with pytest.raises(ValueError, match="No problems with sufficient submissions"):
            await hydro_service.check_contest_plagiarism(request)

    @pytest.mark.asyncio
    async def test_save_plagiarism_result(self, hydro_service, mock_database):
        """Test saving plagiarism result."""
        result = PlagiarismResult(
            contest_id="689ede86bfd7f1255f21e643",
            problem_id=2630,
            analysis_id="test-analysis-id",
            total_submissions=10,
            total_comparisons=45,
            execution_time_ms=5000,
        )

        mock_database.check_plagiarism_results.insert_one = AsyncMock()

        await hydro_service._save_plagiarism_result(result)

        mock_database.check_plagiarism_results.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_contest_plagiarism_results_empty(
        self, hydro_service, mock_database
    ):
        """Test getting plagiarism results when none exist."""
        contest_id = "689ede86bfd7f1255f21e643"

        mock_cursor = MagicMock()
        mock_cursor.__aiter__ = AsyncMock(return_value=iter([]))
        mock_database.check_plagiarism_results.find.return_value = mock_cursor

        result = await hydro_service.get_contest_plagiarism_results(contest_id)

        assert result == []
        mock_database.check_plagiarism_results.find.assert_called_once_with(
            {"contest_id": contest_id}
        )
