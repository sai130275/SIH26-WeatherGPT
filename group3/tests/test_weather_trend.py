"""
tests/test_weather_trend.py
---------------------------
Unit tests for WeatherTrendEngine.
"""

from datetime import datetime, timedelta, timezone
import pytest

from app.schemas.unified_weather import ForecastPoint
from app.services.weather_trend import (
    WeatherTrendEngine,
    compute_linear_rate_per_hour,
)


@pytest.fixture
def engine() -> WeatherTrendEngine:
    return WeatherTrendEngine()


def test_compute_linear_rate_per_hour():
    t0 = datetime(2026, 10, 8, 10, 0, tzinfo=timezone.utc)
    t1 = t0 + timedelta(hours=2)

    rate = compute_linear_rate_per_hour([t0, t1], [20.0, 26.0])
    assert rate == 3.0  # +6°C in 2 hours = 3.0°C/h


def test_temperature_increasing_trend(engine: WeatherTrendEngine):
    t0 = datetime(2026, 10, 8, 10, 0, tzinfo=timezone.utc)
    points = [
        ForecastPoint(timestamp=t0 + timedelta(hours=i), temperature=25.0 + (i * 0.8))
        for i in range(5)
    ]

    trends = engine.analyze_trends_from_forecast(points)
    assert trends.temperature is not None
    assert trends.temperature.state == "increasing"
    assert trends.temperature.rate_per_hour == 0.8


def test_temperature_decreasing_trend(engine: WeatherTrendEngine):
    t0 = datetime(2026, 10, 8, 10, 0, tzinfo=timezone.utc)
    points = [
        ForecastPoint(timestamp=t0 + timedelta(hours=i), temperature=30.0 - (i * 1.0))
        for i in range(4)
    ]

    trends = engine.analyze_trends_from_forecast(points)
    assert trends.temperature is not None
    assert trends.temperature.state == "decreasing"
    assert trends.temperature.rate_per_hour == -1.0


def test_rapidly_changing_trend(engine: WeatherTrendEngine):
    t0 = datetime(2026, 10, 8, 10, 0, tzinfo=timezone.utc)
    points = [
        ForecastPoint(timestamp=t0 + timedelta(hours=i), temperature=25.0 + (i * 3.5))
        for i in range(3)
    ]

    trends = engine.analyze_trends_from_forecast(points)
    assert trends.temperature is not None
    assert trends.temperature.state == "rapidly_changing"
    assert "spiking" in trends.temperature.description.lower() or "rapidly" in trends.temperature.description.lower()


def test_stable_trend(engine: WeatherTrendEngine):
    t0 = datetime(2026, 10, 8, 10, 0, tzinfo=timezone.utc)
    points = [
        ForecastPoint(timestamp=t0 + timedelta(hours=i), wind_speed=15.0 + (i * 0.1))
        for i in range(4)
    ]

    trends = engine.analyze_trends_from_forecast(points)
    assert trends.wind is not None
    assert trends.wind.state == "stable"
    assert "steady" in trends.wind.description.lower()


def test_empty_forecast_points(engine: WeatherTrendEngine):
    trends = engine.analyze_trends_from_forecast([])
    assert trends.temperature is None
    assert trends.rainfall is None
