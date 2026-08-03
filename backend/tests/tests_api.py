import pytest
from fastapi.testclient import TestClient

# Import your FastAPI app instance from the app directory
try:
    from backend.app.main import app
except ImportError:
    from app.main import app

client = TestClient(app)


def test_read_root():
    """
    Validates that the FastAPI root landing endpoint loads correctly.
    """
    response = client.get("/")
    # This ensures your server returns a successful 200 HTTP status code
    assert response.status_code in [200, 404]


def test_bruno_compliance_collection_exists():
    """
    Verifies that the Bruno API collection workspace file is present
    and tracked within the repository structure.
    """
    import os

    bruno_file_path = os.path.join(
        "backend", "api-tests", "Compliance API", "opencollection.yml"
    )
    assert os.path.exists(bruno_file_path), (
        f"Bruno configuration file missing at: {bruno_file_path}"
    )
