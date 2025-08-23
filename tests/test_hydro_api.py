"""Tests for Hydro OJ API endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.hydro_models import PlagiarismResult
from src.core.app import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def mock_hydro_service():
    """Create mock Hydro service."""
    service = MagicMock()
    service.check_contest_plagiarism = AsyncMock()
    service.get_contest_plagiarism_results = AsyncMock()
    return service


@pytest.fixture
def sample_plagiarism_result():
    """Create sample plagiarism result."""
    return PlagiarismResult(
        contest_id="689ede86bfd7f1255f21e643",
        problem_id=2630,
        analysis_id="test-analysis-id",
        total_submissions=10,
        total_comparisons=45,
        execution_time_ms=5000,
        high_similarity_pairs=[
            {
                "first_submission": "submission_1",
                "second_submission": "submission_2",
                "similarities": {"AVG": 0.85, "MAX": 0.92},
            }
        ],
        clusters=[
            {
                "index": 0,
                "average_similarity": 0.88,
                "strength": 0.75,
                "members": ["submission_1", "submission_2"],
            }
        ],
    )


class TestContestPlagiarismAPI:
    """Test contest plagiarism API endpoints."""

    @patch("src.api.hydro.get_hydro_service")
    def test_check_contest_plagiarism_success(
        self, mock_get_service, client, mock_hydro_service, sample_plagiarism_result
    ):
        """Test successful contest plagiarism check."""
        mock_get_service.return_value = mock_hydro_service
        mock_hydro_service.check_contest_plagiarism.return_value = (
            sample_plagiarism_result
        )

        response = client.post(
            "/api/v1/contest/plagiarism",
            json={"contest_id": "689ede86bfd7f1255f21e643"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Contest plagiarism check completed successfully"
        assert data["data"]["contest_id"] == "689ede86bfd7f1255f21e643"
        assert data["data"]["problem_id"] == 2630
        assert data["data"]["total_submissions"] == 10

    @patch("src.api.hydro.get_hydro_service")
    def test_check_contest_plagiarism_invalid_contest(
        self, mock_get_service, client, mock_hydro_service
    ):
        """Test plagiarism check with invalid contest."""
        mock_get_service.return_value = mock_hydro_service
        mock_hydro_service.check_contest_plagiarism.side_effect = ValueError(
            "Contest not found"
        )

        response = client.post(
            "/api/v1/contest/plagiarism",
            json={"contest_id": "invalid-contest-id"},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "Contest not found" in data["message"]

    @patch("src.api.hydro.get_hydro_service")
    def test_check_contest_plagiarism_service_error(
        self, mock_get_service, client, mock_hydro_service
    ):
        """Test plagiarism check with service error."""
        mock_get_service.return_value = mock_hydro_service
        mock_hydro_service.check_contest_plagiarism.side_effect = Exception(
            "Database connection failed"
        )

        response = client.post(
            "/api/v1/contest/plagiarism",
            json={"contest_id": "689ede86bfd7f1255f21e643"},
        )

        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "Plagiarism check failed" in data["message"]

    @patch("src.api.hydro.get_hydro_service")
    def test_get_contest_plagiarism_results_success(
        self, mock_get_service, client, mock_hydro_service, sample_plagiarism_result
    ):
        """Test successful retrieval of plagiarism results."""
        mock_get_service.return_value = mock_hydro_service
        mock_hydro_service.get_contest_plagiarism_results.return_value = [
            sample_plagiarism_result
        ]

        response = client.get("/api/v1/contest/689ede86bfd7f1255f21e643/plagiarism")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Found 1 plagiarism results"
        assert len(data["data"]) == 1
        assert data["data"][0]["contest_id"] == "689ede86bfd7f1255f21e643"

    @patch("src.api.hydro.get_hydro_service")
    def test_get_contest_plagiarism_results_empty(
        self, mock_get_service, client, mock_hydro_service
    ):
        """Test retrieval of plagiarism results when none exist."""
        mock_get_service.return_value = mock_hydro_service
        mock_hydro_service.get_contest_plagiarism_results.return_value = []

        response = client.get("/api/v1/contest/689ede86bfd7f1255f21e643/plagiarism")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Found 0 plagiarism results"
        assert data["data"] == []

    @patch("src.api.hydro.get_hydro_service")
    def test_get_contest_plagiarism_results_service_error(
        self, mock_get_service, client, mock_hydro_service
    ):
        """Test retrieval of plagiarism results with service error."""
        mock_get_service.return_value = mock_hydro_service
        mock_hydro_service.get_contest_plagiarism_results.side_effect = Exception(
            "Database connection failed"
        )

        response = client.get("/api/v1/contest/689ede86bfd7f1255f21e643/plagiarism")

        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "Failed to get results" in data["message"]

    def test_check_contest_plagiarism_request_validation(self, client):
        """Test request validation for contest plagiarism check."""
        # Test missing contest_id
        response = client.post("/api/v1/contest/plagiarism", json={})
        assert response.status_code == 422

        # Test invalid min_tokens
        response = client.post(
            "/api/v1/contest/plagiarism",
            json={"contest_id": "test", "min_tokens": 0},
        )
        assert response.status_code == 422

        # Test invalid similarity_threshold
        response = client.post(
            "/api/v1/contest/plagiarism",
            json={"contest_id": "test", "similarity_threshold": 1.5},
        )
        assert response.status_code == 422
