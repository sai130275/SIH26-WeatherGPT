"""
tests/test_weather_processor.py
--------------------------------
Unit tests for WeatherProcessor and ProcessedWeather.

Tests cover:
  - Full payload (all optional fields present)
  - Partial payload (some fields missing)
  - All optional fields missing
  - Timezone-naive timestamp gets UTC attached
  - available_fields / missing_fields correctness
  - Immutability of ProcessedWeather (frozen dataclass)
  - Identity fields are always preserved
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.schemas.weather import ForecastItem, WeatherData
from app.services.weather_processor import (
    ProcessedWeather,
    WeatherProcessor,
    _OPTIONAL_MET_FIELDS,
)

# --------------------------------------------------------------------------- #
# Fixtures                                                                     #
# --------------------------------------------------------------------------- #

@pytest.fixture
def processor() -> WeatherProcessor:
    return WeatherProcessor()


def _base_identity() -> dict:
    """Minimum required fields for WeatherData."""
    return {
        "location": "Warangal",
        "latitude": 17.9689,
        "longitude": 79.5941,
        "timestamp": "2026-09-28T10:00:00Z",
    }


def _full_met_fields() -> dict:
    """All optional meteorological fields with valid values."""
    return {
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


# --------------------------------------------------------------------------- #
# Identity field preservation                                                  #
# --------------------------------------------------------------------------- #

class TestIdentityFields:
    def test_location_preserved(self, processor: WeatherProcessor) -> None:
        data = WeatherData(**_base_identity())
        result = processor.process(data)
        assert result.location == "Warangal"

    def test_latitude_preserved(self, processor: WeatherProcessor) -> None:
        data = WeatherData(**_base_identity())
        result = processor.process(data)
        assert result.latitude == pytest.approx(17.9689)

    def test_longitude_preserved(self, processor: WeatherProcessor) -> None:
        data = WeatherData(**_base_identity())
        result = processor.process(data)
        assert result.longitude == pytest.approx(79.5941)


# --------------------------------------------------------------------------- #
# Full payload (all optional fields present)                                   #
# --------------------------------------------------------------------------- #

class TestFullPayload:
    def test_all_fields_available(self, processor: WeatherProcessor) -> None:
        data = WeatherData(**_base_identity(), **_full_met_fields())
        result = processor.process(data)
        assert set(result.available_fields) == set(_OPTIONAL_MET_FIELDS)
        assert result.missing_fields == ()

    def test_temperature_passed_through(self, processor: WeatherProcessor) -> None:
        data = WeatherData(**_base_identity(), **_full_met_fields())
        result = processor.process(data)
        assert result.temperature == pytest.approx(31.5)

    def test_rainfall_passed_through(self, processor: WeatherProcessor) -> None:
        data = WeatherData(**_base_identity(), **_full_met_fields())
        result = processor.process(data)
        assert result.rainfall == pytest.approx(12.4)

    def test_wind_speed_passed_through(self, processor: WeatherProcessor) -> None:
        data = WeatherData(**_base_identity(), **_full_met_fields())
        result = processor.process(data)
        assert result.wind_speed == pytest.approx(18.2)

    def test_visibility_passed_through(self, processor: WeatherProcessor) -> None:
        data = WeatherData(**_base_identity(), **_full_met_fields())
        result = processor.process(data)
        assert result.visibility == pytest.approx(8.5)

    def test_forecast_passed_through(self, processor: WeatherProcessor) -> None:
        data = WeatherData(**_base_identity(), **_full_met_fields())
        result = processor.process(data)
        assert result.forecast is not None
        assert len(result.forecast) == 1
        assert result.forecast[0].weather_condition == "Partly Cloudy"


# --------------------------------------------------------------------------- #
# Partial payload (some optional fields missing)                               #
# --------------------------------------------------------------------------- #

class TestPartialPayload:
    def test_missing_rainfall_tracked(self, processor: WeatherProcessor) -> None:
        data = WeatherData(**_base_identity(), temperature=30.0, wind_speed=20.0)
        result = processor.process(data)
        assert "rainfall" in result.missing_fields
        assert result.rainfall is None

    def test_missing_wind_speed_tracked(self, processor: WeatherProcessor) -> None:
        data = WeatherData(**_base_identity(), temperature=30.0, rainfall=5.0)
        result = processor.process(data)
        assert "wind_speed" in result.missing_fields
        assert result.wind_speed is None

    def test_missing_temperature_tracked(self, processor: WeatherProcessor) -> None:
        data = WeatherData(**_base_identity(), rainfall=10.0)
        result = processor.process(data)
        assert "temperature" in result.missing_fields
        assert result.temperature is None

    def test_missing_visibility_tracked(self, processor: WeatherProcessor) -> None:
        data = WeatherData(**_base_identity(), temperature=30.0)
        result = processor.process(data)
        assert "visibility" in result.missing_fields
        assert result.visibility is None

    def test_available_and_missing_are_complete(
        self, processor: WeatherProcessor
    ) -> None:
        """available_fields ∪ missing_fields == all optional met fields."""
        data = WeatherData(**_base_identity(), temperature=30.0, rainfall=10.0)
        result = processor.process(data)
        all_fields = set(result.available_fields) | set(result.missing_fields)
        assert all_fields == set(_OPTIONAL_MET_FIELDS)

    def test_no_overlap_between_available_and_missing(
        self, processor: WeatherProcessor
    ) -> None:
        data = WeatherData(**_base_identity(), **_full_met_fields())
        result = processor.process(data)
        overlap = set(result.available_fields) & set(result.missing_fields)
        assert overlap == set()


# --------------------------------------------------------------------------- #
# All optional fields missing                                                  #
# --------------------------------------------------------------------------- #

class TestNoOptionalFields:
    def test_all_fields_missing(self, processor: WeatherProcessor) -> None:
        data = WeatherData(**_base_identity())
        result = processor.process(data)
        assert set(result.missing_fields) == set(_OPTIONAL_MET_FIELDS)
        assert result.available_fields == ()

    def test_no_values_invented(self, processor: WeatherProcessor) -> None:
        data = WeatherData(**_base_identity())
        result = processor.process(data)
        for field_name in _OPTIONAL_MET_FIELDS:
            assert getattr(result, field_name) is None, (
                f"Expected {field_name} to be None, got {getattr(result, field_name)}"
            )


# --------------------------------------------------------------------------- #
# Timestamp normalisation                                                      #
# --------------------------------------------------------------------------- #

class TestTimestampNormalisation:
    def test_timezone_aware_timestamp_preserved(
        self, processor: WeatherProcessor
    ) -> None:
        data = WeatherData(**_base_identity())
        result = processor.process(data)
        assert result.timestamp.tzinfo is not None

    def test_naive_timestamp_gets_utc(self, processor: WeatherProcessor) -> None:
        """A naive datetime (no tzinfo) must be tagged as UTC."""
        naive_ts = datetime(2026, 9, 28, 10, 0, 0)  # no tzinfo
        data = WeatherData(
            location="Warangal",
            latitude=17.9689,
            longitude=79.5941,
            timestamp=naive_ts,
        )
        result = processor.process(data)
        assert result.timestamp.tzinfo == timezone.utc

    def test_utc_offset_preserved(self, processor: WeatherProcessor) -> None:
        data = WeatherData(**_base_identity())
        result = processor.process(data)
        # "2026-09-28T10:00:00Z" → utcoffset == 0
        assert result.timestamp.utcoffset().total_seconds() == 0  # type: ignore[union-attr]


# --------------------------------------------------------------------------- #
# Immutability                                                                 #
# --------------------------------------------------------------------------- #

class TestImmutability:
    def test_processed_weather_is_frozen(self, processor: WeatherProcessor) -> None:
        """ProcessedWeather is a frozen dataclass — mutation must raise."""
        data = WeatherData(**_base_identity(), temperature=30.0)
        result = processor.process(data)
        with pytest.raises((AttributeError, TypeError)):
            result.temperature = 99.0  # type: ignore[misc]
