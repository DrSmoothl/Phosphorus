"""Tests for JPlag API routes."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.jplag_models import PlagiarismAnalysisResult
from src.core import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def mock_jplag_service():
    """Create mock JPlag service."""
    service = MagicMock()
    service.analyze_submissions = AsyncMock()
    service.get_detailed_comparison = AsyncMock()
    return service


class TestJPlagAPI:
    """Test cases for JPlag API."""

    def test_get_supported_languages(self, client):
        """Test getting supported languages."""
        response = client.get("/api/v1/jplag/languages")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "java" in data["data"]
        assert "python3" in data["data"]

    @patch("src.api.jplag.get_jplag_service")
    def test_analyze_plagiarism_success(
        self, mock_get_service, client, mock_jplag_service
    ):
        """Test successful plagiarism analysis."""
        # Setup mock
        mock_get_service.return_value = mock_jplag_service
        mock_result = PlagiarismAnalysisResult(
            analysis_id="test-id",
            total_submissions=2,
            total_comparisons=1,
            execution_time_ms=1000,
            high_similarity_pairs=[],
            clusters=[],
            submission_stats=[],
            failed_submissions=[],
        )
        mock_jplag_service.analyze_submissions.return_value = mock_result

        # Prepare test files
        files = [
            ("files", ("test1.java", b"public class Test1 {}", "text/plain")),
            ("files", ("test2.java", b"public class Test2 {}", "text/plain")),
        ]

        response = client.post(
            "/api/v1/jplag/analyze",
            files=files,
            data={
                "language": "java",
                "min_tokens": 9,
                "similarity_threshold": 0.0,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["analysis_id"] == "test-id"

    def test_analyze_plagiarism_no_files(self, client):
        """Test analysis with no files."""
        response = client.post("/api/v1/jplag/analyze", data={"language": "java"})
        assert response.status_code == 400

    def test_analyze_plagiarism_insufficient_files(self, client):
        """Test analysis with insufficient files."""
        files = [
            ("files", ("test1.java", b"public class Test1 {}", "text/plain")),
        ]

        response = client.post(
            "/api/v1/jplag/analyze", files=files, data={"language": "java"}
        )
        assert response.status_code == 400

    @patch("src.api.jplag.get_jplag_service")
    def test_analyze_plagiarism_service_error(
        self, mock_get_service, client, mock_jplag_service
    ):
        """Test analysis with service error."""
        mock_get_service.return_value = mock_jplag_service
        mock_jplag_service.analyze_submissions.side_effect = Exception("Service error")

        files = [
            ("files", ("test1.java", b"public class Test1 {}", "text/plain")),
            ("files", ("test2.java", b"public class Test2 {}", "text/plain")),
        ]

        response = client.post(
            "/api/v1/jplag/analyze", files=files, data={"language": "java"}
        )
        assert response.status_code == 500

    @patch("src.api.jplag.get_jplag_service")
    def test_get_detailed_comparison_success(
        self, mock_get_service, client, mock_jplag_service
    ):
        """Test successful detailed comparison retrieval."""
        mock_get_service.return_value = mock_jplag_service
        mock_result = MagicMock()
        mock_result.model_dump.return_value = {"comparison": "data"}
        mock_jplag_service.get_detailed_comparison.return_value = mock_result

        response = client.post(
            "/api/v1/jplag/comparison/detailed",
            json={
                "analysis_id": "test-id",
                "first_submission": "sub1",
                "second_submission": "sub2",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @patch("src.api.jplag.get_jplag_service")
    def test_get_detailed_comparison_not_found(
        self, mock_get_service, client, mock_jplag_service
    ):
        """Test detailed comparison not found."""
        mock_get_service.return_value = mock_jplag_service
        mock_jplag_service.get_detailed_comparison.return_value = None

        response = client.post(
            "/api/v1/jplag/comparison/detailed",
            json={
                "analysis_id": "test-id",
                "first_submission": "sub1",
                "second_submission": "sub2",
            },
        )

        assert response.status_code == 404
