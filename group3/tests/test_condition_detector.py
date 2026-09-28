"""
tests/test_condition_detector.py
----------------------------------
Unit tests for ConditionDetector and the pure severity helper functions.

Tests cover:
  - Normal weather → no conditions triggered
  - Heavy rain detection (above, at, below threshold)
  - High wind detection (above, at, below threshold)
  - Extreme heat detection (above, at, below threshold)
  - Low visibility detection (below, at, above threshold)
  - Missing field → detector returns None
  - detect_all returns multiple simultaneous conditions
  - Severity levels at defined band boundaries
  - Custom threshold injection (Settings override)
  - DetectedCondition fields are correct (type, unit, threshold, value)
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.core.config import Settings
from app.schemas.analysis import DetectedCondition
from app.services.condition_detector import (
    ConditionDetector,
    _heat_severity,
    _rain_severity,
    _visibility_severity,
    _wind_severity,
)
from app.services.weather_processor import ProcessedWeather


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #

_NOW = datetime(2026, 9, 28, 10, 0, 0, tzinfo=timezone.utc)


def _make_weather(**overrides) -> ProcessedWeather:
    """
    Build a ProcessedWeather with safe normal defaults.
    Override any field for targeted tests.
    """
    defaults: dict = {
        "location": "Warangal",
        "latitude": 17.9689,
        "longitude": 79.5941,
        "timestamp": _NOW,
        # Normal values — below every default threshold
        "temperature": 28.0,      # below 40°C heat threshold
        "humidity": 65.0,
        "rainfall": 5.0,          # below 50mm rain threshold
        "wind_speed": 20.0,       # below 60 km/h wind threshold
        "wind_direction": 180.0,
        "pressure": 1010.0,
        "visibility": 10.0,       # above 1km visibility threshold
        "forecast": None,
        "available_fields": (
            "temperature", "humidity", "rainfall",
            "wind_speed", "wind_direction", "pressure", "visibility",
        ),
        "missing_fields": ("forecast",),
    }
    defaults.update(overrides)
    return ProcessedWeather(**defaults)


def _custom_cfg(**overrides) -> Settings:
    """Build a Settings instance with overridden threshold values."""
    defaults = {
        "HEAVY_RAIN_THRESHOLD_MM": 50.0,
        "HIGH_WIND_THRESHOLD_KMH": 60.0,
        "EXTREME_HEAT_THRESHOLD_C": 40.0,
        "LOW_VISIBILITY_THRESHOLD_KM": 1.0,
    }
    defaults.update(overrides)
    # Prevent pydantic-settings from reading actual .env during tests
    return Settings(**defaults, _env_file=None)  # type: ignore[call-arg]


# --------------------------------------------------------------------------- #
# Severity pure-function tests                                                 #
# --------------------------------------------------------------------------- #

class TestSeverityFunctions:
    """Verify severity band boundaries for each helper function."""

    # -- Rain ---------------------------------------------------------------- #
    def test_rain_severity_low(self) -> None:
        assert _rain_severity(60.0, 50.0) == "low"        # excess = 10

    def test_rain_severity_moderate(self) -> None:
        assert _rain_severity(80.0, 50.0) == "moderate"   # excess = 30

    def test_rain_severity_high(self) -> None:
        assert _rain_severity(110.0, 50.0) == "high"      # excess = 60

    def test_rain_severity_extreme(self) -> None:
        assert _rain_severity(200.0, 50.0) == "extreme"   # excess = 150

    def test_rain_severity_boundary_moderate(self) -> None:
        assert _rain_severity(75.0, 50.0) == "moderate"   # excess = exactly 25

    def test_rain_severity_boundary_high(self) -> None:
        assert _rain_severity(100.0, 50.0) == "high"      # excess = exactly 50

    def test_rain_severity_boundary_extreme(self) -> None:
        assert _rain_severity(150.0, 50.0) == "extreme"   # excess = exactly 100

    # -- Wind ---------------------------------------------------------------- #
    def test_wind_severity_low(self) -> None:
        assert _wind_severity(70.0, 60.0) == "low"        # excess = 10

    def test_wind_severity_moderate(self) -> None:
        assert _wind_severity(80.0, 60.0) == "moderate"   # excess = 20

    def test_wind_severity_high(self) -> None:
        assert _wind_severity(100.0, 60.0) == "high"      # excess = 40

    def test_wind_severity_extreme(self) -> None:
        assert _wind_severity(130.0, 60.0) == "extreme"   # excess = 70

    def test_wind_severity_boundary_moderate(self) -> None:
        assert _wind_severity(75.0, 60.0) == "moderate"   # excess = exactly 15

    def test_wind_severity_boundary_high(self) -> None:
        assert _wind_severity(90.0, 60.0) == "high"       # excess = exactly 30

    def test_wind_severity_boundary_extreme(self) -> None:
        assert _wind_severity(120.0, 60.0) == "extreme"   # excess = exactly 60

    # -- Heat ---------------------------------------------------------------- #
    def test_heat_severity_low(self) -> None:
        assert _heat_severity(41.0, 40.0) == "low"        # excess = 1

    def test_heat_severity_moderate(self) -> None:
        assert _heat_severity(43.0, 40.0) == "moderate"   # excess = 3

    def test_heat_severity_high(self) -> None:
        assert _heat_severity(46.0, 40.0) == "high"       # excess = 6

    def test_heat_severity_extreme(self) -> None:
        assert _heat_severity(52.0, 40.0) == "extreme"    # excess = 12

    def test_heat_severity_boundary_moderate(self) -> None:
        assert _heat_severity(42.0, 40.0) == "moderate"   # excess = exactly 2

    def test_heat_severity_boundary_high(self) -> None:
        assert _heat_severity(45.0, 40.0) == "high"       # excess = exactly 5

    def test_heat_severity_boundary_extreme(self) -> None:
        assert _heat_severity(50.0, 40.0) == "extreme"    # excess = exactly 10

    # -- Visibility ---------------------------------------------------------- #
    def test_visibility_severity_low(self) -> None:
        # ratio = 0.8 > 0.75 → low
        assert _visibility_severity(0.8, 1.0) == "low"

    def test_visibility_severity_moderate(self) -> None:
        # ratio = 0.6 → moderate (0.5 < r ≤ 0.75)
        assert _visibility_severity(0.6, 1.0) == "moderate"

    def test_visibility_severity_high(self) -> None:
        # ratio = 0.4 → high (0.25 < r ≤ 0.5)
        assert _visibility_severity(0.4, 1.0) == "high"

    def test_visibility_severity_extreme(self) -> None:
        # ratio = 0.1 → extreme (≤ 0.25)
        assert _visibility_severity(0.1, 1.0) == "extreme"

    def test_visibility_severity_boundary_moderate(self) -> None:
        # ratio = exactly 0.75 → moderate
        assert _visibility_severity(0.75, 1.0) == "moderate"

    def test_visibility_severity_boundary_high(self) -> None:
        # ratio = exactly 0.5 → high
        assert _visibility_severity(0.5, 1.0) == "high"

    def test_visibility_severity_boundary_extreme(self) -> None:
        # ratio = exactly 0.25 → extreme
        assert _visibility_severity(0.25, 1.0) == "extreme"

    def test_visibility_severity_degenerate_threshold(self) -> None:
        """Zero threshold must not cause division by zero."""
        assert _visibility_severity(0.0, 0.0) == "low"


# --------------------------------------------------------------------------- #
# Normal weather — no conditions triggered                                     #
# --------------------------------------------------------------------------- #

class TestNormalWeather:
    def test_no_conditions_for_normal_values(self) -> None:
        detector = ConditionDetector()
        weather = _make_weather()
        conditions = detector.detect_all(weather)
        assert conditions == []

    def test_each_detector_returns_none_for_normal_values(self) -> None:
        detector = ConditionDetector()
        weather = _make_weather()
        assert detector.detect_heavy_rain(weather) is None
        assert detector.detect_high_wind(weather) is None
        assert detector.detect_extreme_heat(weather) is None
        assert detector.detect_low_visibility(weather) is None


# --------------------------------------------------------------------------- #
# Heavy rain                                                                   #
# --------------------------------------------------------------------------- #

class TestHeavyRain:
    def test_triggers_above_threshold(self) -> None:
        detector = ConditionDetector()
        weather = _make_weather(rainfall=72.0)
        result = detector.detect_heavy_rain(weather)
        assert result is not None
        assert result.type == "heavy_rain"

    def test_does_not_trigger_at_threshold(self) -> None:
        """Condition triggers only when rainfall > threshold, not at exactly."""
        detector = ConditionDetector()
        weather = _make_weather(rainfall=50.0)    # exactly at default threshold
        assert detector.detect_heavy_rain(weather) is None

    def test_does_not_trigger_below_threshold(self) -> None:
        detector = ConditionDetector()
        weather = _make_weather(rainfall=49.9)
        assert detector.detect_heavy_rain(weather) is None

    def test_correct_value_returned(self) -> None:
        detector = ConditionDetector()
        weather = _make_weather(rainfall=72.0)
        result = detector.detect_heavy_rain(weather)
        assert result is not None
        assert result.value == pytest.approx(72.0)

    def test_correct_unit_returned(self) -> None:
        detector = ConditionDetector()
        weather = _make_weather(rainfall=72.0)
        result = detector.detect_heavy_rain(weather)
        assert result is not None
        assert result.unit == "mm"

    def test_correct_threshold_in_response(self) -> None:
        detector = ConditionDetector()
        weather = _make_weather(rainfall=72.0)
        result = detector.detect_heavy_rain(weather)
        assert result is not None
        assert result.threshold == pytest.approx(50.0)

    def test_returns_none_when_rainfall_missing(self) -> None:
        detector = ConditionDetector()
        weather = _make_weather(rainfall=None)
        assert detector.detect_heavy_rain(weather) is None

    def test_custom_threshold_respected(self) -> None:
        cfg = _custom_cfg(HEAVY_RAIN_THRESHOLD_MM=20.0)
        detector = ConditionDetector(cfg=cfg)
        weather = _make_weather(rainfall=25.0)   # above 20 but below default 50
        result = detector.detect_heavy_rain(weather)
        assert result is not None
        assert result.threshold == pytest.approx(20.0)


# --------------------------------------------------------------------------- #
# High wind                                                                    #
# --------------------------------------------------------------------------- #

class TestHighWind:
    def test_triggers_above_threshold(self) -> None:
        detector = ConditionDetector()
        weather = _make_weather(wind_speed=85.0)
        result = detector.detect_high_wind(weather)
        assert result is not None
        assert result.type == "high_wind"

    def test_does_not_trigger_at_threshold(self) -> None:
        detector = ConditionDetector()
        weather = _make_weather(wind_speed=60.0)   # exactly at default threshold
        assert detector.detect_high_wind(weather) is None

    def test_does_not_trigger_below_threshold(self) -> None:
        detector = ConditionDetector()
        weather = _make_weather(wind_speed=59.9)
        assert detector.detect_high_wind(weather) is None

    def test_correct_unit_returned(self) -> None:
        detector = ConditionDetector()
        weather = _make_weather(wind_speed=85.0)
        result = detector.detect_high_wind(weather)
        assert result is not None
        assert result.unit == "km/h"

    def test_returns_none_when_wind_missing(self) -> None:
        detector = ConditionDetector()
        weather = _make_weather(wind_speed=None)
        assert detector.detect_high_wind(weather) is None

    def test_custom_threshold_respected(self) -> None:
        cfg = _custom_cfg(HIGH_WIND_THRESHOLD_KMH=30.0)
        detector = ConditionDetector(cfg=cfg)
        weather = _make_weather(wind_speed=35.0)   # above 30 but below default 60
        result = detector.detect_high_wind(weather)
        assert result is not None


# --------------------------------------------------------------------------- #
# Extreme heat                                                                 #
# --------------------------------------------------------------------------- #

class TestExtremeHeat:
    def test_triggers_above_threshold(self) -> None:
        detector = ConditionDetector()
        weather = _make_weather(temperature=43.0)
        result = detector.detect_extreme_heat(weather)
        assert result is not None
        assert result.type == "extreme_heat"

    def test_does_not_trigger_at_threshold(self) -> None:
        detector = ConditionDetector()
        weather = _make_weather(temperature=40.0)  # exactly at default threshold
        assert detector.detect_extreme_heat(weather) is None

    def test_does_not_trigger_below_threshold(self) -> None:
        detector = ConditionDetector()
        weather = _make_weather(temperature=39.9)
        assert detector.detect_extreme_heat(weather) is None

    def test_correct_unit_returned(self) -> None:
        detector = ConditionDetector()
        weather = _make_weather(temperature=43.0)
        result = detector.detect_extreme_heat(weather)
        assert result is not None
        assert result.unit == "°C"

    def test_returns_none_when_temperature_missing(self) -> None:
        detector = ConditionDetector()
        weather = _make_weather(temperature=None)
        assert detector.detect_extreme_heat(weather) is None

    def test_custom_threshold_respected(self) -> None:
        cfg = _custom_cfg(EXTREME_HEAT_THRESHOLD_C=35.0)
        detector = ConditionDetector(cfg=cfg)
        weather = _make_weather(temperature=37.0)  # above 35 but below default 40
        result = detector.detect_extreme_heat(weather)
        assert result is not None


# --------------------------------------------------------------------------- #
# Low visibility                                                               #
# --------------------------------------------------------------------------- #

class TestLowVisibility:
    def test_triggers_below_threshold(self) -> None:
        detector = ConditionDetector()
        weather = _make_weather(visibility=0.5)
        result = detector.detect_low_visibility(weather)
        assert result is not None
        assert result.type == "low_visibility"

    def test_does_not_trigger_at_threshold(self) -> None:
        detector = ConditionDetector()
        weather = _make_weather(visibility=1.0)    # exactly at default threshold
        assert detector.detect_low_visibility(weather) is None

    def test_does_not_trigger_above_threshold(self) -> None:
        detector = ConditionDetector()
        weather = _make_weather(visibility=1.1)
        assert detector.detect_low_visibility(weather) is None

    def test_correct_unit_returned(self) -> None:
        detector = ConditionDetector()
        weather = _make_weather(visibility=0.5)
        result = detector.detect_low_visibility(weather)
        assert result is not None
        assert result.unit == "km"

    def test_returns_none_when_visibility_missing(self) -> None:
        detector = ConditionDetector()
        weather = _make_weather(visibility=None)
        assert detector.detect_low_visibility(weather) is None

    def test_custom_threshold_respected(self) -> None:
        cfg = _custom_cfg(LOW_VISIBILITY_THRESHOLD_KM=5.0)
        detector = ConditionDetector(cfg=cfg)
        weather = _make_weather(visibility=3.0)    # below 5km but above default 1km
        result = detector.detect_low_visibility(weather)
        assert result is not None


# --------------------------------------------------------------------------- #
# detect_all — multiple simultaneous conditions                                #
# --------------------------------------------------------------------------- #

class TestDetectAll:
    def test_returns_all_triggered_conditions(self) -> None:
        detector = ConditionDetector()
        weather = _make_weather(
            rainfall=80.0,      # heavy rain
            wind_speed=90.0,    # high wind
            temperature=45.0,   # extreme heat
            visibility=0.3,     # low visibility
        )
        conditions = detector.detect_all(weather)
        types = {c.type for c in conditions}
        assert types == {"heavy_rain", "high_wind", "extreme_heat", "low_visibility"}

    def test_returns_only_triggered_conditions(self) -> None:
        detector = ConditionDetector()
        # Only heavy rain should trigger
        weather = _make_weather(rainfall=80.0)
        conditions = detector.detect_all(weather)
        assert len(conditions) == 1
        assert conditions[0].type == "heavy_rain"

    def test_empty_list_for_all_normal(self) -> None:
        detector = ConditionDetector()
        weather = _make_weather()
        assert detector.detect_all(weather) == []

    def test_empty_list_for_all_fields_missing(self) -> None:
        detector = ConditionDetector()
        weather = _make_weather(
            temperature=None,
            rainfall=None,
            wind_speed=None,
            visibility=None,
        )
        assert detector.detect_all(weather) == []

    def test_returns_list_of_detected_condition_type(self) -> None:
        detector = ConditionDetector()
        weather = _make_weather(rainfall=80.0)
        conditions = detector.detect_all(weather)
        assert all(isinstance(c, DetectedCondition) for c in conditions)

    def test_two_conditions_simultaneously(self) -> None:
        detector = ConditionDetector()
        weather = _make_weather(rainfall=80.0, wind_speed=90.0)
        conditions = detector.detect_all(weather)
        assert len(conditions) == 2

    def test_reason_is_non_empty_string(self) -> None:
        detector = ConditionDetector()
        weather = _make_weather(rainfall=80.0)
        result = detector.detect_all(weather)
        assert result[0].reason != ""
