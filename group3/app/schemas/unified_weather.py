"""
schemas/unified_weather.py
---------------------------
Canonical weather data schemas for the Weather + AI Intelligence Engine.

Every weather provider adapter normalises its raw API response into these
schemas.  Downstream services (condition detection, risk scoring, advisory
generation, LLM orchestration) consume ONLY these types — never raw
provider payloads.

Design rules
------------
* All meteorological fields are Optional — different providers expose
  different subsets.  Downstream consumers must handle None gracefully.
* ProviderInfo is attached to every response for full source attribution.
* available_fields / missing_fields track data completeness explicitly.
* Units are canonical and documented inline — no ambiguity.

Units
-----
temperature    → °C
humidity       → % (0–100)
rainfall       → mm (≥ 0)
wind_speed     → km/h (≥ 0)
wind_gusts     → km/h (≥ 0)
wind_direction → degrees (0–359, meteorological)
pressure       → hPa (> 0)
visibility     → km (≥ 0)
uv_index       → dimensionless (0–11+)
cloud_cover    → % (0–100)
dew_point      → °C
feels_like     → °C
cape           → J/kg (≥ 0)
precipitation_probability → % (0–100)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# --------------------------------------------------------------------------- #
# Provider metadata                                                            #
# --------------------------------------------------------------------------- #

class ProviderInfo(BaseModel):
    """
    Metadata identifying the weather data source.

    Attached to every weather response for full source attribution and
    traceability.  Callers can inspect which provider supplied the data,
    what NWP model backs it, and when the fetch occurred.
    """

    name: str = Field(
        ...,
        description="Machine-readable provider identifier.",
        examples=["open_meteo"],
    )
    display_name: Optional[str] = Field(
        default=None,
        description="Human-readable provider name for UI display.",
        examples=["Open-Meteo"],
    )

    @field_validator("display_name", mode="before")
    @classmethod
    def populate_display_name(cls, v, info):
        if not v and "name" in info.data:
            return info.data["name"].replace("_", " ").title()
        return v

    model: Optional[str] = Field(
        default=None,
        description=(
            "Underlying NWP model, if known "
            "(e.g. 'GFS', 'ECMWF IFS', 'ICON')."
        ),
        examples=["GFS"],
    )
    fetched_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        description="UTC timestamp when data was retrieved from the provider.",
    )
    api_version: Optional[str] = Field(
        default=None,
        description="Provider API version string, if available.",
        examples=["v1"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "open_meteo",
                "display_name": "Open-Meteo",
                "model": "GFS",
                "fetched_at": "2026-10-06T10:00:00Z",
                "api_version": "v1",
            }
        }
    }


# --------------------------------------------------------------------------- #
# Optional-field tracking                                                      #
# --------------------------------------------------------------------------- #

# Canonical list of optional meteorological field names on CurrentWeather.
# Order is preserved in available_fields / missing_fields output.
CURRENT_WEATHER_OPTIONAL_FIELDS: tuple[str, ...] = (
    "temperature",
    "humidity",
    "rainfall",
    "wind_speed",
    "wind_direction",
    "wind_gusts",
    "pressure",
    "visibility",
    "uv_index",
    "cloud_cover",
    "dew_point",
    "feels_like",
    "weather_code",
    "weather_condition",
    "lightning",
    "cape",
)


def _compute_field_availability(
    obj: object,
    field_names: tuple[str, ...],
) -> tuple[list[str], list[str]]:
    """
    Partition field_names into available and missing based on whether the
    attribute value is None on the given object.

    Returns (available, missing).
    """
    available: list[str] = []
    missing: list[str] = []
    for name in field_names:
        if getattr(obj, name, None) is not None:
            available.append(name)
        else:
            missing.append(name)
    return available, missing


# --------------------------------------------------------------------------- #
# Current weather observation                                                  #
# --------------------------------------------------------------------------- #

class CurrentWeather(BaseModel):
    """
    A single weather observation for a specific location and time.

    All meteorological fields are Optional so that providers with partial
    coverage are accepted without validation errors.  Downstream services
    must handle None values (and should use available_fields / missing_fields
    to understand what is present).
    """

    # -- Identity ----------------------------------------------------------- #
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
        examples=["2026-10-06T10:00:00Z"],
    )

    # -- Core meteorological fields (all Optional) -------------------------- #
    temperature: Optional[float] = Field(
        default=None, description="Observed temperature in °C.", examples=[31.5],
    )
    humidity: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Relative humidity in % (0–100).", examples=[72.0],
    )
    rainfall: Optional[float] = Field(
        default=None, ge=0,
        description="Precipitation in mm. Must be ≥ 0.", examples=[12.4],
    )
    wind_speed: Optional[float] = Field(
        default=None, ge=0,
        description="Wind speed in km/h. Must be ≥ 0.", examples=[18.2],
    )
    wind_direction: Optional[float] = Field(
        default=None, ge=0, lt=360,
        description="Wind direction in degrees (0–359, meteorological).",
        examples=[240.0],
    )
    wind_gusts: Optional[float] = Field(
        default=None, ge=0,
        description="Wind gust speed in km/h. Must be ≥ 0.", examples=[35.0],
    )
    pressure: Optional[float] = Field(
        default=None, gt=0,
        description="Atmospheric pressure in hPa.", examples=[1008.5],
    )
    visibility: Optional[float] = Field(
        default=None, ge=0,
        description="Horizontal visibility in km. Must be ≥ 0.", examples=[8.5],
    )
    uv_index: Optional[float] = Field(
        default=None, ge=0,
        description="UV index (0–11+).", examples=[6.2],
    )
    cloud_cover: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Cloud cover in % (0–100).", examples=[45.0],
    )
    dew_point: Optional[float] = Field(
        default=None,
        description="Dew point temperature in °C.", examples=[22.3],
    )
    feels_like: Optional[float] = Field(
        default=None,
        description="Apparent (feels-like) temperature in °C.", examples=[34.0],
    )
    weather_code: Optional[int] = Field(
        default=None,
        description="WMO weather interpretation code.", examples=[61],
    )
    weather_condition: Optional[str] = Field(
        default=None,
        description="Human-readable weather condition label.",
        examples=["Slight rain"],
    )
    lightning: Optional[bool] = Field(
        default=None,
        description="Whether thunderstorm/lightning is detected.",
        examples=[False],
    )
    cape: Optional[float] = Field(
        default=None, ge=0,
        description=(
            "Convective Available Potential Energy in J/kg. "
            "Higher values indicate greater storm potential."
        ),
        examples=[250.0],
    )

    # -- Provider metadata -------------------------------------------------- #
    provider: ProviderInfo = Field(
        ..., description="Source provider metadata.",
    )

    # -- Data quality ------------------------------------------------------- #
    available_fields: list[str] = Field(
        default_factory=list,
        description="Meteorological fields present (non-null) in this observation.",
    )
    missing_fields: list[str] = Field(
        default_factory=list,
        description="Meteorological fields absent (null) in this observation.",
    )

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_timestamp(cls, v: object) -> datetime:
        """Accept ISO-8601 strings and pass through datetime objects."""
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        return v  # type: ignore[return-value]

    def model_post_init(self, __context: object) -> None:
        """Auto-compute available_fields and missing_fields after init."""
        if not self.available_fields and not self.missing_fields:
            available, missing = _compute_field_availability(
                self, CURRENT_WEATHER_OPTIONAL_FIELDS,
            )
            # Pydantic frozen=False by default, so direct assignment is fine.
            object.__setattr__(self, "available_fields", available)
            object.__setattr__(self, "missing_fields", missing)

    model_config = {
        "json_schema_extra": {
            "example": {
                "location": "Warangal",
                "latitude": 17.9689,
                "longitude": 79.5941,
                "timestamp": "2026-10-06T10:00:00Z",
                "temperature": 31.5,
                "humidity": 72.0,
                "rainfall": 12.4,
                "wind_speed": 18.2,
                "pressure": 1008.5,
                "visibility": 8.5,
                "provider": {
                    "name": "open_meteo",
                    "display_name": "Open-Meteo",
                    "fetched_at": "2026-10-06T10:00:05Z",
                },
                "available_fields": [
                    "temperature", "humidity", "rainfall",
                    "wind_speed", "pressure", "visibility",
                ],
                "missing_fields": [
                    "wind_direction", "wind_gusts", "uv_index",
                    "cloud_cover", "dew_point", "feels_like",
                    "weather_code", "weather_condition", "lightning", "cape",
                ],
            }
        }
    }


# --------------------------------------------------------------------------- #
# Forecast data point (hourly)                                                 #
# --------------------------------------------------------------------------- #

class ForecastPoint(BaseModel):
    """A single hourly forecast data-point."""

    timestamp: datetime = Field(
        ...,
        description="UTC timestamp for this forecast interval (ISO-8601).",
        examples=["2026-10-06T11:00:00Z"],
    )
    temperature: Optional[float] = Field(
        default=None, description="Forecast temperature in °C.", examples=[30.1],
    )
    rainfall: Optional[float] = Field(
        default=None, ge=0,
        description="Forecast precipitation in mm.", examples=[5.2],
    )
    humidity: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Forecast relative humidity in %.", examples=[75.0],
    )
    wind_speed: Optional[float] = Field(
        default=None, ge=0,
        description="Forecast wind speed in km/h.", examples=[20.0],
    )
    wind_gusts: Optional[float] = Field(
        default=None, ge=0,
        description="Forecast wind gust speed in km/h.", examples=[35.0],
    )
    weather_code: Optional[int] = Field(
        default=None,
        description="WMO weather interpretation code.", examples=[61],
    )
    weather_condition: Optional[str] = Field(
        default=None,
        description="Human-readable weather condition label.",
        examples=["Slight rain"],
    )
    precipitation_probability: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Probability of precipitation in % (0–100).", examples=[65.0],
    )
    cloud_cover: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Cloud cover in % (0–100).", examples=[80.0],
    )

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_timestamp(cls, v: object) -> datetime:
        """Accept ISO-8601 strings and pass through datetime objects."""
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        return v  # type: ignore[return-value]


# --------------------------------------------------------------------------- #
# Daily forecast summary                                                       #
# --------------------------------------------------------------------------- #

class DailyForecast(BaseModel):
    """Aggregated daily forecast summary."""

    date: str = Field(
        ...,
        description="Date in YYYY-MM-DD format.",
        examples=["2026-10-07"],
    )
    temperature_max: Optional[float] = Field(
        default=None, description="Maximum temperature in °C.", examples=[34.0],
    )
    temperature_min: Optional[float] = Field(
        default=None, description="Minimum temperature in °C.", examples=[24.0],
    )
    precipitation_sum: Optional[float] = Field(
        default=None, ge=0,
        description="Total precipitation in mm.", examples=[15.0],
    )
    precipitation_probability_max: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Maximum precipitation probability in %.", examples=[85.0],
    )
    wind_speed_max: Optional[float] = Field(
        default=None, ge=0,
        description="Maximum wind speed in km/h.", examples=[25.0],
    )
    weather_code: Optional[int] = Field(
        default=None,
        description="Dominant WMO weather code for the day.", examples=[63],
    )
    weather_condition: Optional[str] = Field(
        default=None,
        description="Human-readable dominant condition.",
        examples=["Moderate rain"],
    )
    sunrise: Optional[str] = Field(
        default=None,
        description="Sunrise time (ISO-8601 or local HH:MM).",
        examples=["06:12"],
    )
    sunset: Optional[str] = Field(
        default=None,
        description="Sunset time (ISO-8601 or local HH:MM).",
        examples=["18:05"],
    )
    uv_index_max: Optional[float] = Field(
        default=None, ge=0,
        description="Maximum UV index for the day.", examples=[8.0],
    )


# --------------------------------------------------------------------------- #
# Full forecast response                                                       #
# --------------------------------------------------------------------------- #

class ForecastWeather(BaseModel):
    """
    Complete forecast response containing hourly and daily forecasts.

    Returned by WeatherProvider.get_forecast().
    """

    location: str = Field(
        ..., min_length=1, description="Human-readable place name.",
    )
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    hourly: list[ForecastPoint] = Field(
        default_factory=list,
        description="Hourly forecast data-points.",
    )
    daily: list[DailyForecast] = Field(
        default_factory=list,
        description="Daily forecast summaries.",
    )
    provider: ProviderInfo = Field(
        ..., description="Source provider metadata.",
    )


# --------------------------------------------------------------------------- #
# Historical weather response                                                  #
# --------------------------------------------------------------------------- #

class HistoricalWeather(BaseModel):
    """
    Historical weather data for a date range.

    Returned by WeatherProvider.get_historical().
    Reuses ForecastPoint for hourly data since the schema is identical.
    """

    location: str = Field(
        ..., min_length=1, description="Human-readable place name.",
    )
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    start_date: str = Field(
        ..., description="Start date (YYYY-MM-DD).", examples=["2026-09-01"],
    )
    end_date: str = Field(
        ..., description="End date (YYYY-MM-DD).", examples=["2026-09-25"],
    )
    hourly: list[ForecastPoint] = Field(
        default_factory=list,
        description="Hourly historical observations.",
    )
    provider: ProviderInfo = Field(
        ..., description="Source provider metadata.",
    )


# --------------------------------------------------------------------------- #
# Unified weather response wrapper                                             #
# --------------------------------------------------------------------------- #

class WeatherResponse(BaseModel):
    """
    Top-level response wrapper for weather endpoints.

    Can contain any combination of current, forecast, and historical data
    depending on what was requested.  providers_used lists all providers
    that contributed to this response (for multi-provider consensus).
    """

    current: Optional[CurrentWeather] = Field(
        default=None,
        description="Current weather observation, if requested.",
    )
    forecast: Optional[ForecastWeather] = Field(
        default=None,
        description="Weather forecast, if requested.",
    )
    historical: Optional[HistoricalWeather] = Field(
        default=None,
        description="Historical weather data, if requested.",
    )
    providers_used: list[ProviderInfo] = Field(
        default_factory=list,
        description=(
            "All providers that contributed data to this response. "
            "For single-provider queries, this is a list of one."
        ),
    )
    fetched_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        description="UTC timestamp when this response was assembled.",
    )
