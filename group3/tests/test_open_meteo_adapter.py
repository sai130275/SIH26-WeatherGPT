"""
tests/test_open_meteo_adapter.py
--------------------------------
Unit tests for OpenMeteoProvider with mocked HTTP requests.
"""

import httpx
import pytest

from app.providers.base import (
    ProviderRateLimitError,
    ProviderUnavailableError,
)
from app.providers.open_meteo import OpenMeteoProvider


MOCK_CURRENT_JSON = {
    "latitude": 17.97,
    "longitude": 79.59,
    "current_weather": {
        "temperature": 32.5,
        "windspeed": 18.0,
        "winddirection": 120.0,
        "weathercode": 95,
        "time": "2026-10-06T12:00",
    },
    "hourly": {
        "time": ["2026-10-06T11:00", "2026-10-06T12:00", "2026-10-06T13:00"],
        "precipitation_probability": [20, 85, 90],
        "precipitation": [0.0, 12.5, 8.0],
        "relative_humidity_2m": [60, 78, 80],
        "wind_speed_10m": [15.0, 18.0, 20.0],
        "wind_gusts_10m": [25.0, 35.0, 40.0],
        "surface_pressure": [1010.0, 1008.0, 1006.0],
        "visibility": [10000, 4500, 3000],
        "uv_index": [5.0, 4.0, 3.0],
        "dew_point_2m": [22.0, 24.0, 25.0],
        "apparent_temperature": [36.0, 39.0, 40.0],
        "cloud_cover": [40, 85, 95],
        "cape": [500, 1850, 2100],
    },
}

MOCK_FORECAST_JSON = {
    "latitude": 17.97,
    "longitude": 79.59,
    "hourly": {
        "time": ["2026-10-06T12:00", "2026-10-06T13:00"],
        "temperature_2m": [32.0, 30.0],
        "relative_humidity_2m": [70, 75],
        "precipitation_probability": [60, 80],
        "precipitation": [1.5, 4.0],
        "wind_speed_10m": [12.0, 14.0],
        "wind_gusts_10m": [20.0, 25.0],
        "weather_code": [61, 65],
        "cloud_cover": [60, 90],
    },
    "daily": {
        "time": ["2026-10-06", "2026-10-07"],
        "temperature_2m_max": [34.0, 32.0],
        "temperature_2m_min": [24.0, 23.0],
        "precipitation_probability_max": [85, 90],
        "precipitation_sum": [15.5, 20.0],
        "wind_speed_10m_max": [25.0, 30.0],
        "weather_code": [95, 65],
        "sunrise": ["2026-10-06T06:05", "2026-10-07T06:05"],
        "sunset": ["2026-10-06T18:02", "2026-10-07T18:01"],
        "uv_index_max": [9.0, 8.5],
    },
}

MOCK_ARCHIVE_JSON = {
    "latitude": 17.97,
    "longitude": 79.59,
    "hourly": {
        "time": ["2026-09-01T00:00", "2026-09-01T01:00"],
        "temperature_2m": [26.0, 25.5],
        "precipitation": [0.0, 0.2],
        "relative_humidity_2m": [82, 85],
        "wind_speed_10m": [8.0, 7.5],
        "weather_code": [2, 3],
    },
}


@pytest.mark.asyncio
async def test_open_meteo_get_current_success():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=MOCK_CURRENT_JSON)
    )
    async with httpx.AsyncClient(transport=transport) as client:
        provider = OpenMeteoProvider(client=client)
        current = await provider.get_current(17.97, 79.59, location_name="Warangal")

        assert current.location == "Warangal"
        assert current.latitude == 17.97
        assert current.longitude == 79.59
        assert current.temperature == 32.5
        assert current.humidity == 78.0
        assert current.rainfall == 12.5
        assert current.wind_speed == 18.0
        assert current.wind_gusts == 35.0
        assert current.visibility == 4.5  # 4500m / 1000 = 4.5km
        assert current.cape == 1850.0
        assert current.lightning is True  # code 95
        assert current.weather_condition == "Thunderstorm"
        assert current.provider.name == "open_meteo"


@pytest.mark.asyncio
async def test_open_meteo_get_forecast_success():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=MOCK_FORECAST_JSON)
    )
    async with httpx.AsyncClient(transport=transport) as client:
        provider = OpenMeteoProvider(client=client)
        forecast = await provider.get_forecast(17.97, 79.59, days=2)

        assert len(forecast.hourly) == 2
        assert forecast.hourly[0].temperature == 32.0
        assert forecast.hourly[1].weather_code == 65
        assert len(forecast.daily) == 2
        assert forecast.daily[0].temperature_max == 34.0
        assert forecast.daily[0].weather_condition == "Thunderstorm"
        assert forecast.provider.name == "open_meteo"


@pytest.mark.asyncio
async def test_open_meteo_get_historical_success():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=MOCK_ARCHIVE_JSON)
    )
    async with httpx.AsyncClient(transport=transport) as client:
        provider = OpenMeteoProvider(client=client)
        history = await provider.get_historical(17.97, 79.59, "2026-09-01", "2026-09-01")

        assert len(history.hourly) == 2
        assert history.hourly[0].temperature == 26.0
        assert history.start_date == "2026-09-01"


@pytest.mark.asyncio
async def test_open_meteo_rate_limit_error():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(429, json={"error": "Rate limit exceeded"})
    )
    async with httpx.AsyncClient(transport=transport) as client:
        provider = OpenMeteoProvider(client=client)
        with pytest.raises(ProviderRateLimitError):
            await provider.get_current(17.97, 79.59)


@pytest.mark.asyncio
async def test_open_meteo_server_error():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(500, text="Internal Server Error")
    )
    async with httpx.AsyncClient(transport=transport) as client:
        provider = OpenMeteoProvider(client=client)
        with pytest.raises(ProviderUnavailableError):
            await provider.get_current(17.97, 79.59)


@pytest.mark.asyncio
async def test_open_meteo_health_check():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"current_weather": {}})
    )
    async with httpx.AsyncClient(transport=transport) as client:
        provider = OpenMeteoProvider(client=client)
        is_healthy = await provider.health_check()
        assert is_healthy is True
