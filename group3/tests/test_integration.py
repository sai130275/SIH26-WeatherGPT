"""
tests/test_integration.py
--------------------------
Integration tests validating the HTTP contract between Group 2 and Group 3.

Ensures Group 2 can reliably call Group 3 endpoints:
  - GET /health
  - POST /analyze
  - POST /risk
  - POST /advisory
  - POST /chat

Tests focus on HTTP status codes, JSON validation, and response schema shapes.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


# --------------------------------------------------------------------------- #
# Valid payload samples representing what Group 2 will send                    #
# --------------------------------------------------------------------------- #

_VALID_WEATHER_PAYLOAD = {
    "location": "Warangal",
    "latitude": 17.9689,
    "longitude": 79.5941,
    "timestamp": "2026-09-28T10:00:00Z",
    "temperature": 42.0,
    "humidity": 90.0,
    "rainfall": 72.0,
    "wind_speed": 85.0,
    "visibility": 0.5,
    "pressure": 995.0,
}

_MINIMAL_WEATHER_PAYLOAD = {
    "location": "Warangal",
    "latitude": 17.9689,
    "longitude": 79.5941,
    "timestamp": "2026-09-28T10:00:00Z",
    # Optional fields omitted
}

_INVALID_WEATHER_PAYLOAD = {
    "location": "Warangal",
    "latitude": 900.0,  # Invalid latitude (>90)
    "longitude": 79.5941,
    "timestamp": "2026-09-28T10:00:00Z",
}

_VALID_RISK_PAYLOAD = {
    "weather": _VALID_WEATHER_PAYLOAD,
    "risk": {
        "risks": [],
        "overall_score": 100,
        "overall_level": "SEVERE"
    }
}


# =========================================================================== #
# Integration tests                                                            #
# =========================================================================== #

class TestIntegrationContract:

    # ------------------------------------------------------------------ #
    # GET /health                                                          #
    # ------------------------------------------------------------------ #
    
    def test_health_check(self, client: TestClient) -> None:
        """Verify health check responds with 200 OK and expected body."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    # ------------------------------------------------------------------ #
    # POST /analyze                                                        #
    # ------------------------------------------------------------------ #
    
    def test_analyze_valid_payload(self, client: TestClient) -> None:
        """Verify /analyze accepts full weather data and returns ProcessedWeather + Conditions."""
        response = client.post("/analyze", json=_VALID_WEATHER_PAYLOAD)
        assert response.status_code == 200
        data = response.json()
        assert "location" in data
        assert "conditions" in data
        assert isinstance(data["conditions"], list)

    def test_analyze_minimal_payload(self, client: TestClient) -> None:
        """Verify /analyze accepts minimal weather data without crashing."""
        response = client.post("/analyze", json=_MINIMAL_WEATHER_PAYLOAD)
        assert response.status_code == 200
        assert "conditions" in response.json()

    def test_analyze_invalid_payload_returns_422(self, client: TestClient) -> None:
        """Verify /analyze returns 422 Unprocessable Entity on validation failure."""
        response = client.post("/analyze", json=_INVALID_WEATHER_PAYLOAD)
        assert response.status_code == 422
        # FastAPI standardized validation error shape
        assert "detail" in response.json()

    # ------------------------------------------------------------------ #
    # POST /risk                                                           #
    # ------------------------------------------------------------------ #
    
    def test_risk_valid_payload(self, client: TestClient) -> None:
        """Verify /risk accepts full weather data and returns RiskAnalysis."""
        response = client.post("/risk", json=_VALID_WEATHER_PAYLOAD)
        assert response.status_code == 200
        data = response.json()
        assert "risks" in data
        assert "overall_score" in data
        assert "overall_level" in data
        assert isinstance(data["risks"], list)

    def test_risk_invalid_payload_returns_422(self, client: TestClient) -> None:
        response = client.post("/risk", json=_INVALID_WEATHER_PAYLOAD)
        assert response.status_code == 422

    # ------------------------------------------------------------------ #
    # POST /advisory                                                       #
    # ------------------------------------------------------------------ #
    
    def test_advisory_valid_payload(self, client: TestClient) -> None:
        """Verify /advisory accepts Weather + Risk and returns AdvisoryResponse."""
        response = client.post("/advisory", json=_VALID_RISK_PAYLOAD)
        assert response.status_code == 200
        data = response.json()
        assert "location" in data
        assert "overall_risk_level" in data
        assert "impacts" in data
        assert "advisories" in data
        assert isinstance(data["advisories"], list)

    def test_advisory_missing_fields_returns_422(self, client: TestClient) -> None:
        """Verify /advisory rejects requests missing required root fields."""
        response = client.post("/advisory", json={"weather": _VALID_WEATHER_PAYLOAD})
        # Missing 'risk' field
        assert response.status_code == 422

    # ------------------------------------------------------------------ #
    # POST /chat                                                           #
    # ------------------------------------------------------------------ #

    def test_chat_valid_payload(self, client: TestClient) -> None:
        """Verify /chat accepts natural language and optional context."""
        payload = {
            "message": "Can I travel tomorrow evening?",
            "location": {
                "latitude": 17.9689,
                "longitude": 79.5941
            },
            "conversation_id": "integration-test-001",
            "weather_data": _VALID_WEATHER_PAYLOAD
        }
        response = client.post("/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == "integration-test-001"
        assert "answer" in data
        assert "sources" in data
        assert "mode" in data
        assert "intent" in data
        # In testing without API key, mode falls back predictably
        assert data["mode"] == "fallback"
        assert data["intent"] in {"activity", "advisory", "forecast"}

    def test_chat_missing_message_returns_422(self, client: TestClient) -> None:
        payload = {
            "conversation_id": "integration-test-001",
            "weather_data": _VALID_WEATHER_PAYLOAD
        }
        response = client.post("/chat", json=payload)
        assert response.status_code == 422

    def test_chat_no_context(self, client: TestClient) -> None:
        """Verify /chat works even if Group 2 only sends a message."""
        payload = {
            "message": "What is the capital of France?"
        }
        response = client.post("/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        # Generated a conversation_id since it was absent
        assert len(data["conversation_id"]) > 0

    # ------------------------------------------------------------------ #
    # Documentation Endpoints                                              #
    # ------------------------------------------------------------------ #
    
    def test_openapi_schema(self, client: TestClient) -> None:
        """Verify OpenAPI schema is successfully generated and exposed."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
        # Verify our endpoints are documented
        assert "/analyze" in data["paths"]
        assert "/risk" in data["paths"]
        assert "/advisory" in data["paths"]
        assert "/chat" in data["paths"]

    def test_swagger_ui(self, client: TestClient) -> None:
        """Verify Swagger UI docs page is available."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "swagger-ui" in response.text.lower()
