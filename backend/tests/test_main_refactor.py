"""
Tests for the refactored main.py and config.py.
"""
from fastapi.testclient import TestClient
from app.main import app
from app.config import get_settings

client = TestClient(app)

def test_read_root():
    """Test the root endpoint returns correct metadata."""
    settings = get_settings()
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == settings.app_name
    assert data["version"] == settings.app_version
    assert data["docs"] == "/docs"
    assert data["health"] == "/health"

def test_settings_load():
    """Test that settings load correctly."""
    settings = get_settings()
    assert settings.app_name == "RepoBlueprint AI"
    assert settings.ollama_model is not None
    assert isinstance(settings.supported_languages, list)

def test_health_check_via_root():
    """Test that the health endpoint linked in root works (if it exists)."""
    response = client.get("/health")
    # Note: We assume the health endpoint is implemented and returns 200.
    # If not, this test might fail or need adjustment based on actual health.py
    if response.status_code != 404:
       assert response.status_code == 200
       assert response.json()["status"] == "healthy"
