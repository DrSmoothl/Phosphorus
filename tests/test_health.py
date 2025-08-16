"""Tests for health API."""

import pytest
from fastapi.testclient import TestClient

from src.core import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["message"] == "Service is healthy"
    assert data["status"] == "healthy"
    assert "timestamp" in data
