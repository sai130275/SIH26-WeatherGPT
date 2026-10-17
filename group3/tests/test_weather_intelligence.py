"""
tests/test_weather_intelligence.py
----------------------------------
Integration and end-to-end tests for WeatherIntelligenceService and HTTP routes (Module 1.2).
"""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.unified_weather import (
    CurrentWeather,
    ForecastPoint,
    ForecastWeather,
    ProviderInfo,
)
from app.services.weather_intelligence import (
    WeatherIntelligenceService,
    default_intelligence_service,
)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def sample_current() -> CurrentWeather:
    return CurrentWeather(
        location="Warangal",
        latitude=17.9689,
        longitude=79.5941,
        timestamp=datetime.now(tz=timezone.utc),
        temperature=35.0,
        humidity=78.0,
        rainfall=14.0,
        wind_speed=30.0,
        visibility=8.0,
        pressure=1004.0,
        dew_point=28.0,
        provider=ProviderInfo(name="open_meteo"),
    )


@pytest.fixture
def sample_forecast() -> ForecastWeather:
    now = datetime.now(tz=timezone.utc)
    points = [
        ForecastPoint(
            timestamp=now,
            temperature=35.0,
            rainfall=14.0,
            wind_speed=30.0,
            humidity=78.0,
            precipitation_probability=80.0,
        ),
        ForecastPoint(
            timestamp=now,
            temperature=33.0,
            rainfall=8.0,
            wind_speed=25.0,
            humidity=80.0,
            precipitation_probability=70.0,
        ),
    ]
    return ForecastWeather(
        location="Warangal",
        latitude=17.9689,
        longitude=79.5941,
        hourly=points,
        daily=[],
        provider=ProviderInfo(name="open_meteo"),
    )


# --------------------------------------------------------------------------- #
# Service Unit / Integration Tests                                            #
# --------------------------------------------------------------------------- #

def test_intelligence_service_full_pipeline(
    sample_current: CurrentWeather, sample_forecast: ForecastWeather
):
    service = WeatherIntelligenceService()
    response = service.generate_intelligence(
        current_observations=sample_current,
        forecast=sample_forecast,
        forecast_days=1,
    )

    assert response.location == "Warangal"
    assert response.current_analysis is not None
    assert response.current_analysis.thermal_comfort in ("extreme_caution", "danger", "extreme_danger")
    assert response.current_analysis.precipitation_probability_rating in ("likely", "very_likely")

    # Forecast intelligence
    assert response.forecast_intelligence is not None
    assert response.forecast_intelligence.rain_expected is True

    # Trends
    assert response.trends is not None

    # Risk Assessment
    assert response.risk_assessment is not None
    assert response.risk_assessment.classification == "HEURISTIC_RISK"
    assert "not an official" in response.risk_assessment.disclaimer.lower()

    # Data Quality & Confidence
    assert response.data_quality is not None
    assert response.confidence is not None
    assert 0 <= response.confidence.confidence_score <= 100


# --------------------------------------------------------------------------- #
# HTTP Endpoint Integration Tests                                             #
# --------------------------------------------------------------------------- #

def test_post_intelligence_analyze_route(client: TestClient, sample_current: CurrentWeather):
    payload = {
        "current": sample_current.model_dump(mode="json"),
        "forecast": None,
    }

    res = client.post("/weather/intelligence/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["location"] == "Warangal"
    assert "current_analysis" in data
    assert "risk_assessment" in data
    assert data["risk_assessment"]["classification"] == "HEURISTIC_RISK"
    assert "confidence" in data
    assert "data_quality" in data


def test_get_weather_intelligence_route(client: TestClient, monkeypatch):
    # Mock default_aggregator.get_current and get_forecast to avoid live network requests
    now = datetime.now(tz=timezone.utc)
    mock_current = CurrentWeather(
        location="Warangal",
        latitude=17.9689,
        longitude=79.5941,
        timestamp=now,
        temperature=32.0,
        rainfall=0.0,
        wind_speed=15.0,
        humidity=60.0,
        pressure=1012.0,
        visibility=10.0,
        provider=ProviderInfo(name="open_meteo"),
    )

    mock_forecast = ForecastWeather(
        location="Warangal",
        latitude=17.9689,
        longitude=79.5941,
        hourly=[
            ForecastPoint(timestamp=now, temperature=32.0, rainfall=0.0, wind_speed=15.0)
        ],
        daily=[],
        provider=ProviderInfo(name="open_meteo"),
    )

    from app.services.weather_aggregator import default_aggregator

    async def mock_get_all_current(*args, **kwargs):
        return [mock_current]

    async def mock_get_forecast(*args, **kwargs):
        return mock_forecast

    monkeypatch.setattr(default_aggregator, "get_all_current", mock_get_all_current)
    monkeypatch.setattr(default_aggregator, "get_forecast", mock_get_forecast)

    res = client.get("/weather/intelligence?lat=17.9689&lon=79.5941")
    assert res.status_code == 200
    data = res.json()
    assert data["location"] == "Warangal"
    assert data["current_analysis"]["thermal_comfort"] in ("caution", "extreme_caution")
    assert data["risk_assessment"]["overall_level"] in ("LOW", "MODERATE")
    assert data["confidence"]["confidence_score"] >= 80


def test_get_weather_intelligence_invalid_coords(client: TestClient):
    res = client.get("/weather/intelligence?lat=95.0&lon=79.5941")
    assert res.status_code == 422  # Latitude > 90 is rejected


def test_multi_provider_fusion_pipeline():
    now = datetime.now(tz=timezone.utc)
    obs1 = CurrentWeather(
        location="Warangal",
        latitude=17.9,
        longitude=79.5,
        timestamp=now,
        temperature=31.0,
        rainfall=0.0,
        provider=ProviderInfo(name="provider_1"),
    )
    obs2 = CurrentWeather(
        location="Warangal",
        latitude=17.9,
        longitude=79.5,
        timestamp=now,
        temperature=32.0,
        rainfall=0.0,
        pressure=1010.0,
        provider=ProviderInfo(name="provider_2"),
    )

    service = WeatherIntelligenceService()
    resp = service.generate_intelligence([obs1, obs2])
    assert resp.fusion_summary is not None
    assert len(resp.fusion_summary.providers_evaluated) == 2
    assert "pressure" in resp.fusion_summary.fields_imputed
    assert len(resp.providers_used) == 2


def test_empty_observations_in_service_raises_error():
    service = WeatherIntelligenceService()
    with pytest.raises(ValueError, match="At least one"):
        service.generate_intelligence([])

