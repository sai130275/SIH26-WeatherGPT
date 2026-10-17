"""
tests/test_forecast_intelligence.py
-----------------------------------
Unit tests for ForecastIntelligenceEngine (Module 1.2).
"""

from datetime import datetime, timedelta, timezone
import pytest

from app.schemas.unified_weather import ForecastPoint, ForecastWeather, ProviderInfo
from app.services.forecast_intelligence import ForecastIntelligenceEngine


@pytest.fixture
def provider() -> ProviderInfo:
    return ProviderInfo(name="test_provider")


@pytest.fixture
def engine() -> ForecastIntelligenceEngine:
    return ForecastIntelligenceEngine()


def test_rain_onset_and_duration_detection(engine: ForecastIntelligenceEngine, provider: ProviderInfo):
    t0 = datetime(2026, 10, 8, 12, 0, tzinfo=timezone.utc)

    # Hourly sequence: 2 dry hours, then 3 rainy hours, then 2 dry hours
    points = [
        ForecastPoint(timestamp=t0 + timedelta(hours=0), rainfall=0.0, temperature=28.0),
        ForecastPoint(timestamp=t0 + timedelta(hours=1), rainfall=0.0, temperature=28.0),
        ForecastPoint(timestamp=t0 + timedelta(hours=2), rainfall=5.0, temperature=26.0),
        ForecastPoint(timestamp=t0 + timedelta(hours=3), rainfall=12.0, temperature=24.0),
        ForecastPoint(timestamp=t0 + timedelta(hours=4), rainfall=3.0, temperature=24.0),
        ForecastPoint(timestamp=t0 + timedelta(hours=5), rainfall=0.0, temperature=25.0),
    ]

    fw = ForecastWeather(
        location="Warangal",
        latitude=17.9689,
        longitude=79.5941,
        hourly=points,
        daily=[],
        provider=provider,
    )

    intel = engine.analyze(fw, base_time=t0)

    assert intel.rain_expected is True
    assert intel.rain_onset == t0 + timedelta(hours=2)
    assert intel.rain_onset_hours_from_now == 2.0
    assert intel.total_rain_duration_hours == 3.0
    assert intel.total_precipitation_expected_mm == 20.0
    assert intel.peak_rain_period is not None
    assert intel.peak_rain_period.peak_rate_mm_h == 12.0
    assert intel.peak_rain_period.accumulated_mm == 20.0


def test_dry_forecast_behavior(engine: ForecastIntelligenceEngine, provider: ProviderInfo):
    t0 = datetime(2026, 10, 8, 12, 0, tzinfo=timezone.utc)
    points = [
        ForecastPoint(timestamp=t0 + timedelta(hours=i), rainfall=0.0, temperature=30.0 + i)
        for i in range(5)
    ]

    fw = ForecastWeather(
        location="DryZone",
        latitude=20.0,
        longitude=78.0,
        hourly=points,
        provider=provider,
    )

    intel = engine.analyze(fw, base_time=t0)

    assert intel.rain_expected is False
    assert intel.rain_onset is None
    assert intel.rain_onset_hours_from_now is None
    assert intel.total_rain_duration_hours == 0.0
    assert intel.peak_rain_period is None


def test_temperature_dynamics_and_swings(engine: ForecastIntelligenceEngine, provider: ProviderInfo):
    t0 = datetime(2026, 10, 8, 6, 0, tzinfo=timezone.utc)
    # 20°C in morning up to 34°C in afternoon
    points = [
        ForecastPoint(timestamp=t0 + timedelta(hours=0), temperature=20.0),
        ForecastPoint(timestamp=t0 + timedelta(hours=3), temperature=26.0),
        ForecastPoint(timestamp=t0 + timedelta(hours=6), temperature=34.0),
        ForecastPoint(timestamp=t0 + timedelta(hours=9), temperature=28.0),
    ]

    fw = ForecastWeather(location="Warangal", latitude=17.9, longitude=79.5, hourly=points, provider=provider)
    intel = engine.analyze(fw, base_time=t0)

    assert intel.temperature_dynamics is not None
    assert intel.temperature_dynamics.min_temp == 20.0
    assert intel.temperature_dynamics.max_temp == 34.0
    assert intel.temperature_dynamics.diurnal_swing == 14.0


def test_rapid_change_cold_front_detection(engine: ForecastIntelligenceEngine, provider: ProviderInfo):
    t0 = datetime(2026, 10, 8, 12, 0, tzinfo=timezone.utc)
    # Temperature drops from 30°C to 23°C in 3 hours (> 5°C drop)
    points = [
        ForecastPoint(timestamp=t0 + timedelta(hours=0), temperature=30.0, wind_speed=15.0),
        ForecastPoint(timestamp=t0 + timedelta(hours=1), temperature=28.0, wind_speed=20.0),
        ForecastPoint(timestamp=t0 + timedelta(hours=2), temperature=25.0, wind_speed=25.0),
        ForecastPoint(timestamp=t0 + timedelta(hours=3), temperature=23.0, wind_speed=30.0),
    ]

    fw = ForecastWeather(location="Front", latitude=17.9, longitude=79.5, hourly=points, provider=provider)
    intel = engine.analyze(fw, base_time=t0)

    assert len(intel.rapid_changes) >= 1
    ch = intel.rapid_changes[0]
    assert ch.metric == "temperature"
    assert ch.magnitude == -7.0
    assert "drop" in ch.description.lower()
