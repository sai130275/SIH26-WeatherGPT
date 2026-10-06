"""
tests/test_weather_bridge.py
----------------------------
Unit tests for the weather_bridge adapter function.
Verifies conversion from canonical unified schemas to legacy WeatherData schemas.
"""

from datetime import datetime, timezone

from app.schemas.unified_weather import (
    CurrentWeather,
    ForecastPoint,
    ForecastWeather,
    ProviderInfo,
)
from app.services.weather_bridge import current_weather_to_weather_data


def test_bridge_full_conversion():
    now = datetime.now(tz=timezone.utc)
    provider = ProviderInfo(name="open_meteo")
    current = CurrentWeather(
        location="Warangal",
        latitude=17.97,
        longitude=79.59,
        timestamp=now,
        temperature=31.5,
        humidity=72.0,
        rainfall=5.4,
        wind_speed=18.2,
        wind_direction=240.0,
        pressure=1008.5,
        visibility=8.5,
        provider=provider,
    )

    forecast = ForecastWeather(
        location="Warangal",
        latitude=17.97,
        longitude=79.59,
        hourly=[
            ForecastPoint(
                timestamp=now,
                temperature=32.0,
                rainfall=0.0,
                humidity=60.0,
                wind_speed=12.0,
                weather_condition="Clear sky",
            )
        ],
        daily=[],
        provider=provider,
    )

    legacy = current_weather_to_weather_data(current, forecast)
    assert legacy.location == "Warangal"
    assert legacy.latitude == 17.97
    assert legacy.longitude == 79.59
    assert legacy.temperature == 31.5
    assert legacy.humidity == 72.0
    assert legacy.rainfall == 5.4
    assert legacy.wind_speed == 18.2
    assert legacy.wind_direction == 240.0
    assert legacy.pressure == 1008.5
    assert legacy.visibility == 8.5
    assert legacy.forecast is not None
    assert len(legacy.forecast) == 1
    assert legacy.forecast[0].temperature == 32.0
    assert legacy.forecast[0].weather_condition == "Clear sky"


def test_bridge_partial_data_and_no_forecast():
    now = datetime.now(tz=timezone.utc)
    current = CurrentWeather(
        location="Hyderabad",
        latitude=17.38,
        longitude=78.48,
        timestamp=now,
        temperature=28.0,
        provider=ProviderInfo(name="open_meteo"),
    )

    legacy = current_weather_to_weather_data(current)
    assert legacy.location == "Hyderabad"
    assert legacy.temperature == 28.0
    assert legacy.humidity is None
    assert legacy.rainfall is None
    assert legacy.forecast is None
