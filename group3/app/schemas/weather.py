"""
schemas/weather.py
------------------
Pydantic models that define the canonical weather data contract for
Group 3.  These schemas are shared between:
  - incoming payloads sent by Group 2 (Node.js backend)
  - internal service layer objects
  - outgoing API responses

Units
-----
temperature    → °C
rainfall       → mm
wind_speed     → km/h
wind_direction → degrees (0–360, meteorological)
pressure       → hPa
visibility     → km
humidity       → % (0–100)
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# --------------------------------------------------------------------------- #
# ForecastItem                                                                 #
# --------------------------------------------------------------------------- #

class ForecastItem(BaseModel):
    """A single hourly or daily forecast data-point."""

    timestamp: datetime = Field(
        ...,
        description="UTC timestamp for this forecast interval (ISO-8601).",
        examples=["2026-09-28T11:00:00Z"],
    )
    temperature: float = Field(
        ...,
        description="Forecast temperature in °C.",
        examples=[30.1],
    )
    rainfall: float = Field(
        ...,
        ge=0,
        description="Forecast rainfall in mm. Must be ≥ 0.",
        examples=[5.2],
    )
    humidity: float = Field(
        ...,
        ge=0,
        le=100,
        description="Forecast relative humidity in % (0–100).",
        examples=[75.0],
    )
    wind_speed: float = Field(
        ...,
        ge=0,
        description="Forecast wind speed in km/h. Must be ≥ 0.",
        examples=[20.0],
    )
    weather_condition: str = Field(
        ...,
        description="Human-readable weather condition label.",
        examples=["Partly Cloudy", "Heavy Rain", "Thunderstorm"],
    )

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_timestamp(cls, v: object) -> datetime:
        """Accept ISO-8601 strings and pass through datetime objects."""
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        return v  # type: ignore[return-value]


# --------------------------------------------------------------------------- #
# WeatherData                                                                  #
# --------------------------------------------------------------------------- #

class WeatherData(BaseModel):
    """
    Full weather observation for a single location at a specific moment,
    optionally accompanied by a forecast sequence.

    All meteorological fields are Optional so that partial payloads (e.g.
    from weather sources that do not expose every variable) are accepted
    without validation errors.  Downstream services must handle None values.
    """

    # -- Location ----------------------------------------------------------- #
    location: str = Field(
        ...,
        min_length=1,
        description="Human-readable place name.",
        examples=["Warangal"],
    )
    latitude: float = Field(
        ...,
        ge=-90,
        le=90,
        description="Decimal latitude (−90 to +90).",
        examples=[17.9689],
    )
    longitude: float = Field(
        ...,
        ge=-180,
        le=180,
        description="Decimal longitude (−180 to +180).",
        examples=[79.5941],
    )

    # -- Observation time --------------------------------------------------- #
    timestamp: datetime = Field(
        ...,
        description="UTC observation timestamp (ISO-8601).",
        examples=["2026-09-28T10:00:00Z"],
    )

    # -- Meteorological fields (all Optional) ------------------------------- #
    temperature: Optional[float] = Field(
        default=None,
        description="Observed temperature in °C.",
        examples=[31.5],
    )
    humidity: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Relative humidity in % (0–100).",
        examples=[72.0],
    )
    rainfall: Optional[float] = Field(
        default=None,
        ge=0,
        description="Precipitation in mm. Must be ≥ 0.",
        examples=[12.4],
    )
    wind_speed: Optional[float] = Field(
        default=None,
        ge=0,
        description="Wind speed in km/h. Must be ≥ 0.",
        examples=[18.2],
    )
    wind_direction: Optional[float] = Field(
        default=None,
        ge=0,
        lt=360,
        description="Wind direction in meteorological degrees (0–359).",
        examples=[240.0],
    )
    pressure: Optional[float] = Field(
        default=None,
        gt=0,
        description="Atmospheric pressure in hPa.",
        examples=[1008.5],
    )
    visibility: Optional[float] = Field(
        default=None,
        ge=0,
        description="Horizontal visibility in km. Must be ≥ 0.",
        examples=[8.5],
    )

    # -- Forecast ----------------------------------------------------------- #
    forecast: Optional[list[ForecastItem]] = Field(
        default=None,
        description="Ordered list of hourly or daily forecast items.",
    )

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_timestamp(cls, v: object) -> datetime:
        """Accept ISO-8601 strings and pass through datetime objects."""
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        return v  # type: ignore[return-value]

    model_config = {
        "json_schema_extra": {
            "example": {
                "location": "Warangal",
                "latitude": 17.9689,
                "longitude": 79.5941,
                "timestamp": "2026-09-28T10:00:00Z",
                "temperature": 31.5,
                "humidity": 72.0,
                "rainfall": 12.4,
                "wind_speed": 18.2,
                "wind_direction": 240.0,
                "pressure": 1008.5,
                "visibility": 8.5,
                "forecast": [
                    {
                        "timestamp": "2026-09-28T11:00:00Z",
                        "temperature": 32.0,
                        "rainfall": 0.0,
                        "humidity": 70.0,
                        "wind_speed": 20.0,
                        "weather_condition": "Partly Cloudy",
                    }
                ],
            }
        }
    }
