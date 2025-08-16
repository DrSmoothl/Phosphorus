"""Integration tests for JPlag functionality."""

import pytest
from fastapi.testclient import TestClient

from src.core import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


class TestJPlagIntegration:
    """Integration tests for JPlag API."""

    def test_get_supported_languages(self, client):
        """Test getting supported languages endpoint."""
        response = client.get("/api/v1/jplag/languages")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert "java" in data["data"]
        assert "python3" in data["data"]

    def test_analyze_plagiarism_no_files(self, client):
        """Test analysis endpoint with no files."""
        response = client.post("/api/v1/jplag/analyze", data={"language": "java"})
        # FastAPI returns 422 for validation errors (missing required field)
        assert response.status_code == 422

    def test_analyze_plagiarism_insufficient_files(self, client):
        """Test analysis endpoint with insufficient files."""
        files = [
            ("files", ("test1.java", b"public class Test1 {}", "text/plain")),
        ]

        response = client.post(
            "/api/v1/jplag/analyze", files=files, data={"language": "java"}
        )
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "At least 2 files are required" in data["message"]

    def test_detailed_comparison_endpoint_exists(self, client):
        """Test that detailed comparison endpoint exists."""
        response = client.post(
            "/api/v1/jplag/comparison/detailed",
            json={
                "analysis_id": "test-id",
                "first_submission": "sub1",
                "second_submission": "sub2",
            },
        )
        # Should be 404 due to comparison not found (which is expected behavior)
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "Comparison not found" in data["message"]
