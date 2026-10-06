"""
services/weather_bridge.py
--------------------------
Bridge between canonical unified schemas and legacy internal WeatherData schemas.

Allows services expecting app.schemas.weather.WeatherData (such as the existing
ConditionDetector, RiskEngine, and AdvisoryGenerator) to consume data from
the new Unified Weather Provider / Aggregator layer seamlessly.
"""

from __future__ import annotations

from typing import Optional

from app.schemas.unified_weather import CurrentWeather, ForecastWeather
from app.schemas.weather import ForecastItem, WeatherData


def current_weather_to_weather_data(
    cw: CurrentWeather,
    fw: Optional[ForecastWeather] = None,
) -> WeatherData:
    """
    Bridge: convert canonical CurrentWeather (and optional ForecastWeather)
    into legacy WeatherData schema used by internal intelligence engines.
    """
    forecast_items: Optional[list[ForecastItem]] = None

    if fw and fw.hourly:
        forecast_items = []
        for point in fw.hourly:
            # WeatherData requires non-None temperature, rainfall, humidity, wind_speed, condition
            forecast_items.append(
                ForecastItem(
                    timestamp=point.timestamp,
                    temperature=point.temperature if point.temperature is not None else 25.0,
                    rainfall=point.rainfall if point.rainfall is not None and point.rainfall >= 0 else 0.0,
                    humidity=point.humidity if point.humidity is not None and 0 <= point.humidity <= 100 else 50.0,
                    wind_speed=point.wind_speed if point.wind_speed is not None and point.wind_speed >= 0 else 0.0,
                    weather_condition=point.weather_condition or "Unknown",
                )
            )

    return WeatherData(
        location=cw.location,
        latitude=cw.latitude,
        longitude=cw.longitude,
        timestamp=cw.timestamp,
        temperature=cw.temperature,
        humidity=cw.humidity,
        rainfall=cw.rainfall,
        wind_speed=cw.wind_speed,
        wind_direction=cw.wind_direction,
        pressure=cw.pressure,
        visibility=cw.visibility,
        forecast=forecast_items,
    )
