import pytest
from fastapi.testclient import TestClient
from src.main import app

client: TestClient = TestClient(app)

def test_read_root() -> None:
    """Test the root endpoint returns the hello world message."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, world!"} 