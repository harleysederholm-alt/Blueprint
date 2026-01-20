"""
Basic tests for the backend API
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_root(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "RepoBlueprint AI"
    assert "version" in data


def test_health(client):
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_analyze_validation(client):
    """Test analysis endpoint validation."""
    # Missing repo_url
    response = client.post("/api/analyze", json={})
    assert response.status_code == 422
    
    # Invalid audience
    response = client.post("/api/analyze", json={
        "repo_url": "https://github.com/test/repo",
        "audience": "invalid_audience",
    })
    assert response.status_code == 400


def test_get_nonexistent_analysis(client):
    """Test getting a non-existent analysis."""
    response = client.get("/api/analyze/nonexistent-id")
    assert response.status_code == 404
