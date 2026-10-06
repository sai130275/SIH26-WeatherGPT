"""
tests/test_unified_weather_schemas.py
-------------------------------------
Unit tests for the canonical unified weather data schemas.
Validates field constraints, optionality, quality tracking, and serialization.
"""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from app.schemas.unified_weather import (
    CurrentWeather,
    DailyForecast,
    ForecastPoint,
    ForecastWeather,
    HistoricalWeather,
    ProviderInfo,
    WeatherResponse,
)


def test_provider_info_creation():
    provider = ProviderInfo(
        name="open_meteo",
        model="ECMWF",
        api_version="v1",
    )
    assert provider.name == "open_meteo"
    assert provider.model == "ECMWF"
    assert provider.api_version == "v1"
    assert provider.fetched_at is not None


def test_current_weather_defaults_and_validation():
    provider = ProviderInfo(name="open_meteo")
    current = CurrentWeather(
        location="Warangal, India",
        latitude=17.97,
        longitude=79.59,
        timestamp=datetime.now(tz=timezone.utc),
        temperature=32.5,
        humidity=65.0,
        rainfall=0.0,
        wind_speed=12.4,
        provider=provider,
    )
    assert current.location == "Warangal, India"
    assert current.temperature == 32.5
    assert current.humidity == 65.0
    assert "temperature" in current.available_fields
    assert "pressure" in current.missing_fields
    assert current.provider.name == "open_meteo"


def test_current_weather_bounds_validation():
    provider = ProviderInfo(name="test")
    # Invalid latitude
    with pytest.raises(ValidationError):
        CurrentWeather(
            location="Invalid Lat",
            latitude=95.0,
            longitude=0.0,
            timestamp=datetime.now(tz=timezone.utc),
            provider=provider,
        )

    # Invalid humidity (> 100)
    with pytest.raises(ValidationError):
        CurrentWeather(
            location="Invalid Humidity",
            latitude=0.0,
            longitude=0.0,
            humidity=150.0,
            timestamp=datetime.now(tz=timezone.utc),
            provider=provider,
        )

    # Invalid negative rainfall
    with pytest.raises(ValidationError):
        CurrentWeather(
            location="Negative Rain",
            latitude=0.0,
            longitude=0.0,
            rainfall=-5.0,
            timestamp=datetime.now(tz=timezone.utc),
            provider=provider,
        )


def test_forecast_point_and_daily():
    fp = ForecastPoint(
        timestamp=datetime.now(tz=timezone.utc),
        temperature=28.0,
        rainfall=2.5,
        precipitation_probability=60.0,
    )
    assert fp.temperature == 28.0
    assert fp.precipitation_probability == 60.0

    daily = DailyForecast(
        date="2026-10-06",
        temperature_max=34.0,
        temperature_min=24.0,
        precipitation_sum=5.0,
        precipitation_probability_max=80.0,
        weather_code=61,
        weather_condition="Slight rain",
    )
    assert daily.date == "2026-10-06"
    assert daily.temperature_max == 34.0


def test_weather_response_wrapper():
    provider = ProviderInfo(name="open_meteo")
    current = CurrentWeather(
        location="Warangal",
        latitude=17.97,
        longitude=79.59,
        timestamp=datetime.now(tz=timezone.utc),
        provider=provider,
    )
    resp = WeatherResponse(
        current=current,
        providers_used=[provider],
    )
    assert resp.current is not None
    assert len(resp.providers_used) == 1
    assert resp.fetched_at is not None
