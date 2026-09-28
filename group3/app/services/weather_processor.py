"""
services/weather_processor.py
------------------------------
Accepts a raw WeatherData payload, validates it semantically, and produces
a ProcessedWeather snapshot ready for condition detection.

Design rules
------------
* Required identity fields (location, lat, lon, timestamp) are always present
  — enforced by the WeatherData schema; no extra checks needed.
* Optional meteorological fields may be None.  They are passed through as-is.
* Missing values are NEVER invented or interpolated.
* Missing fields are tracked in `missing_fields` so downstream detectors can
  skip them explicitly instead of silently ignoring None.
* Units are already normalised by the WeatherData Pydantic schema; this layer
  verifies the contract and documents it, not re-converts values.
* The processor is stateless — safe to reuse across requests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.schemas.weather import ForecastItem, WeatherData


# --------------------------------------------------------------------------- #
# Canonical list of optional meteorological field names                        #
# (order is preserved in available_fields / missing_fields output)             #
# --------------------------------------------------------------------------- #
_OPTIONAL_MET_FIELDS: tuple[str, ...] = (
    "temperature",
    "humidity",
    "rainfall",
    "wind_speed",
    "wind_direction",
    "pressure",
    "visibility",
    "forecast",
)


# --------------------------------------------------------------------------- #
# ProcessedWeather                                                             #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class ProcessedWeather:
    """
    Validated, normalised weather snapshot used internally between services.

    All values use canonical units:
      temperature    → °C
      humidity       → % (0–100)
      rainfall       → mm  (≥ 0)
      wind_speed     → km/h (≥ 0)
      wind_direction → degrees (0–359)
      pressure       → hPa  (> 0)
      visibility     → km   (≥ 0)

    `available_fields` and `missing_fields` together cover every field in
    _OPTIONAL_MET_FIELDS.  Their union is always exactly that tuple.
    """

    # -- Identity (always present) ------------------------------------------ #
    location: str
    latitude: float
    longitude: float
    timestamp: datetime                 # always timezone-aware (UTC)

    # -- Meteorological (may be None if source did not provide) -------------- #
    temperature: Optional[float]        # °C
    humidity: Optional[float]           # %
    rainfall: Optional[float]           # mm
    wind_speed: Optional[float]         # km/h
    wind_direction: Optional[float]     # degrees
    pressure: Optional[float]           # hPa
    visibility: Optional[float]         # km
    forecast: Optional[list[ForecastItem]]

    # -- Availability metadata ----------------------------------------------- #
    available_fields: tuple[str, ...] = field(default_factory=tuple)
    missing_fields: tuple[str, ...] = field(default_factory=tuple)


# --------------------------------------------------------------------------- #
# WeatherProcessor                                                             #
# --------------------------------------------------------------------------- #

class WeatherProcessor:
    """
    Stateless weather data processor.

    Example
    -------
    >>> processor = WeatherProcessor()
    >>> result = processor.process(weather_data)
    >>> print(result.missing_fields)
    ('wind_direction', 'forecast')
    """

    def process(self, data: WeatherData) -> ProcessedWeather:
        """
        Validate and normalise a WeatherData payload.

        Parameters
        ----------
        data:
            A fully Pydantic-validated WeatherData instance from the API layer.

        Returns
        -------
        ProcessedWeather:
            Immutable snapshot with all values in canonical units and
            explicit tracking of which optional fields were present.

        Notes
        -----
        - Timestamp is normalised to UTC (timezone-aware) if naive.
        - No values are invented for missing optional fields.
        """
        available: list[str] = []
        missing: list[str] = []

        for field_name in _OPTIONAL_MET_FIELDS:
            value = getattr(data, field_name)
            if value is None:
                missing.append(field_name)
            else:
                available.append(field_name)

        # Ensure timestamp is always timezone-aware (UTC).
        ts = data.timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)

        return ProcessedWeather(
            location=data.location,
            latitude=data.latitude,
            longitude=data.longitude,
            timestamp=ts,
            temperature=data.temperature,
            humidity=data.humidity,
            rainfall=data.rainfall,
            wind_speed=data.wind_speed,
            wind_direction=data.wind_direction,
            pressure=data.pressure,
            visibility=data.visibility,
            forecast=data.forecast,
            available_fields=tuple(available),
            missing_fields=tuple(missing),
        )
