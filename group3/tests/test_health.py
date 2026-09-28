"""
tests/test_health.py
--------------------
pytest integration tests for GET /health.

Uses FastAPI's built-in TestClient (backed by httpx) so no live server is
needed – tests run entirely in-process.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Provide a reusable test client for the FastAPI app."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_returns_200(self, client: TestClient) -> None:
        """The endpoint must respond with HTTP 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}"
        )

    def test_health_returns_json(self, client: TestClient) -> None:
        """The response must be valid JSON."""
        response = client.get("/health")
        # Will raise if the body is not parseable JSON
        data = response.json()
        assert isinstance(data, dict), "Response body must be a JSON object"

    def test_health_status_ok(self, client: TestClient) -> None:
        """The JSON body must contain exactly {'status': 'ok'}."""
        response = client.get("/health")
        data = response.json()
        assert "status" in data, "Response must contain a 'status' key"
        assert data["status"] == "ok", (
            f"Expected status='ok', got status='{data['status']}'"
        )

    def test_health_content_type(self, client: TestClient) -> None:
        """Content-Type header must be application/json."""
        response = client.get("/health")
        assert "application/json" in response.headers.get("content-type", ""), (
            "Expected Content-Type: application/json"
        )

    def test_health_no_extra_keys(self, client: TestClient) -> None:
        """The response must not contain unexpected keys (keep it minimal)."""
        response = client.get("/health")
        data = response.json()
        assert set(data.keys()) == {"status"}, (
            f"Unexpected keys in response: {set(data.keys()) - {'status'}}"
        )
