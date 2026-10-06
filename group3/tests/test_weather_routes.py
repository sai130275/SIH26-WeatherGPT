"""
tests/test_weather_routes.py
----------------------------
Integration tests for the /weather API endpoints.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.providers.base import (
    ProviderRateLimitError,
    ProviderUnavailableError,
)
from app.schemas.unified_weather import (
    CurrentWeather,
    DailyForecast,
    ForecastPoint,
    ForecastWeather,
    HistoricalWeather,
    ProviderInfo,
)


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def sample_current():
    provider = ProviderInfo(name="open_meteo", display_name="Open-Meteo")
    return CurrentWeather(
        location="Warangal",
        latitude=17.97,
        longitude=79.59,
        timestamp=datetime.now(tz=timezone.utc),
        temperature=31.5,
        humidity=65.0,
        rainfall=0.0,
        wind_speed=12.0,
        provider=provider,
    )


@pytest.fixture
def sample_forecast():
    provider = ProviderInfo(name="open_meteo", display_name="Open-Meteo")
    return ForecastWeather(
        location="Warangal",
        latitude=17.97,
        longitude=79.59,
        hourly=[
            ForecastPoint(
                timestamp=datetime.now(tz=timezone.utc),
                temperature=30.0,
            )
        ],
        daily=[
            DailyForecast(
                date="2026-10-06",
                temperature_max=33.0,
                temperature_min=23.0,
            )
        ],
        provider=provider,
    )


@pytest.fixture
def sample_historical():
    provider = ProviderInfo(name="open_meteo", display_name="Open-Meteo")
    return HistoricalWeather(
        location="Warangal",
        latitude=17.97,
        longitude=79.59,
        start_date="2026-09-01",
        end_date="2026-09-10",
        hourly=[],
        provider=provider,
    )


def test_get_current_weather_success(client, sample_current):
    with patch("app.api.routes.weather.default_aggregator.get_current", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = sample_current
        res = client.get("/weather/current?lat=17.97&lon=79.59&location=Warangal")
        assert res.status_code == 200
        data = res.json()
        assert "current" in data
        assert data["current"]["temperature"] == 31.5
        assert data["current"]["location"] == "Warangal"
        assert len(data["providers_used"]) == 1
        assert data["providers_used"][0]["name"] == "open_meteo"


def test_get_current_weather_validation_errors(client):
    # Missing lat/lon
    res1 = client.get("/weather/current")
    assert res1.status_code == 422

    # Latitude out of bounds
    res2 = client.get("/weather/current?lat=120.0&lon=79.59")
    assert res2.status_code == 422


def test_get_forecast_weather_success(client, sample_forecast):
    with patch("app.api.routes.weather.default_aggregator.get_forecast", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = sample_forecast
        res = client.get("/weather/forecast?lat=17.97&lon=79.59&days=5")
        assert res.status_code == 200
        data = res.json()
        assert "forecast" in data
        assert len(data["forecast"]["daily"]) == 1
        assert data["forecast"]["daily"][0]["temperature_max"] == 33.0


def test_get_forecast_validation_errors(client):
    # Days exceeded max
    res = client.get("/weather/forecast?lat=17.97&lon=79.59&days=20")
    assert res.status_code == 422


def test_get_historical_weather_success(client, sample_historical):
    with patch("app.api.routes.weather.default_aggregator.get_historical", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = sample_historical
        res = client.get("/weather/historical?lat=17.97&lon=79.59&start_date=2026-09-01&end_date=2026-09-10")
        assert res.status_code == 200
        data = res.json()
        assert "historical" in data
        assert data["historical"]["start_date"] == "2026-09-01"


def test_get_historical_date_validation_error(client):
    # Invalid date pattern
    res = client.get("/weather/historical?lat=17.97&lon=79.59&start_date=01-09-2026&end_date=2026-09-10")
    assert res.status_code == 422


def test_get_providers_status(client):
    with patch("app.api.routes.weather.default_aggregator.get_provider_status", new_callable=AsyncMock) as mock_status:
        mock_status.return_value = [
            {
                "name": "open_meteo",
                "display_name": "Open-Meteo",
                "supported_features": ["current", "forecast", "historical"],
                "is_available": True,
            }
        ]
        res = client.get("/weather/providers")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["name"] == "open_meteo"
        assert data[0]["is_available"] is True


def test_provider_outage_error_mapping(client):
    with patch("app.api.routes.weather.default_aggregator.get_current", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = ProviderUnavailableError("All current weather providers failed")
        res = client.get("/weather/current?lat=17.97&lon=79.59")
        assert res.status_code == 503
        assert "All current weather providers failed" in res.json()["detail"]


def test_provider_rate_limit_error_mapping(client):
    with patch("app.api.routes.weather.default_aggregator.get_current", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = ProviderRateLimitError("Rate limit exceeded")
        res = client.get("/weather/current?lat=17.97&lon=79.59")
        assert res.status_code == 429
        assert "Rate limit exceeded" in res.json()["detail"]
