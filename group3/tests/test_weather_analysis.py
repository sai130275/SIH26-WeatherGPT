"""
tests/test_weather_analysis.py
------------------------------
Unit tests for deterministic WeatherAnalysisEngine and meteorological calculation functions.
"""

from datetime import datetime, timezone
import pytest

from app.schemas.unified_weather import CurrentWeather, ProviderInfo
from app.services.weather_analysis import (
    WeatherAnalysisEngine,
    classify_beaufort_scale,
    classify_humidity_comfort,
    classify_precipitation,
    classify_rain_probability,
    classify_thermal_comfort,
    classify_visibility,
    compute_heat_index,
    compute_wind_chill,
)


@pytest.fixture
def provider() -> ProviderInfo:
    return ProviderInfo(name="test_provider", display_name="Test Provider")


@pytest.fixture
def engine() -> WeatherAnalysisEngine:
    return WeatherAnalysisEngine()


# --------------------------------------------------------------------------- #
# Thermal & Comfort Functions                                                  #
# --------------------------------------------------------------------------- #

def test_compute_heat_index_hot_humid():
    # 35°C and 80% humidity should result in high Heat Index (>45°C)
    hi = compute_heat_index(35.0, 80.0)
    assert hi > 45.0


def test_compute_heat_index_cool_bypasses():
    # Heat index only applies when >= 20°C
    hi = compute_heat_index(18.0, 90.0)
    assert hi == 18.0


def test_compute_wind_chill_cold_windy():
    # 2°C with 40 km/h wind should feel sub-zero
    wc = compute_wind_chill(2.0, 40.0)
    assert wc < 0.0


def test_compute_wind_chill_warm_bypasses():
    # Wind chill only applies when temp <= 10°C
    wc = compute_wind_chill(15.0, 50.0)
    assert wc == 15.0


def test_classify_thermal_comfort_bands():
    assert classify_thermal_comfort(-5.0) == "freezing"
    assert classify_thermal_comfort(10.0) == "cold"
    assert classify_thermal_comfort(22.0) == "comfortable"
    assert classify_thermal_comfort(30.0) == "caution"
    assert classify_thermal_comfort(36.0) == "extreme_caution"
    assert classify_thermal_comfort(45.0) == "danger"
    assert classify_thermal_comfort(55.0) == "extreme_danger"


def test_classify_humidity_comfort():
    assert classify_humidity_comfort(20.0) == "dry"
    assert classify_humidity_comfort(50.0) == "comfortable"
    assert classify_humidity_comfort(70.0) == "humid"
    assert classify_humidity_comfort(85.0) == "oppressive"
    assert classify_humidity_comfort(None) == "comfortable"


# --------------------------------------------------------------------------- #
# Dynamic Categorization                                                       #
# --------------------------------------------------------------------------- #

def test_classify_beaufort_scale():
    num, cat = classify_beaufort_scale(0.5)
    assert num == 0 and cat == "calm"

    num, cat = classify_beaufort_scale(15.0)
    assert num == 3 and cat == "gentle_breeze"

    num, cat = classify_beaufort_scale(55.0)
    assert num == 7 and cat == "near_gale"

    num, cat = classify_beaufort_scale(95.0)
    assert num == 10 and cat == "storm"

    num, cat = classify_beaufort_scale(125.0)
    assert num == 12 and cat == "hurricane"


def test_classify_precipitation():
    assert classify_precipitation(0.0) == "none"
    assert classify_precipitation(1.5) == "slight_rain"
    assert classify_precipitation(5.0) == "moderate_rain"
    assert classify_precipitation(25.0) == "heavy_rain"
    assert classify_precipitation(60.0) == "violent_rain"


def test_classify_rain_probability():
    assert classify_rain_probability(10.0) == "unlikely"
    assert classify_rain_probability(30.0) == "slight_chance"
    assert classify_rain_probability(50.0) == "possible"
    assert classify_rain_probability(70.0) == "likely"
    assert classify_rain_probability(90.0) == "very_likely"
    assert classify_rain_probability(None) is None


def test_classify_visibility():
    assert classify_visibility(0.3) == "dense_fog"
    assert classify_visibility(0.8) == "fog"
    assert classify_visibility(2.5) == "mist"
    assert classify_visibility(7.0) == "haze"
    assert classify_visibility(15.0) == "clear"


# --------------------------------------------------------------------------- #
# Full Analysis Engine Execution                                              #
# --------------------------------------------------------------------------- #

def test_analysis_engine_full_observation(engine: WeatherAnalysisEngine, provider: ProviderInfo):
    obs = CurrentWeather(
        location="Warangal",
        latitude=17.9689,
        longitude=79.5941,
        timestamp=datetime.now(tz=timezone.utc),
        temperature=34.0,
        humidity=82.0,
        rainfall=12.0,
        wind_speed=25.0,
        pressure=1002.0,
        visibility=6.0,
        dew_point=28.0,
        provider=provider,
    )

    analysis = engine.analyze(obs, rain_probability=85.0)

    assert analysis.apparent_temperature is not None
    assert analysis.apparent_temperature > 34.0  # Heat index increases perceived temp
    assert analysis.thermal_comfort in ("extreme_caution", "danger", "extreme_danger")
    assert analysis.humidity_comfort == "oppressive"
    assert analysis.wind_beaufort_scale == 4
    assert analysis.wind_classification == "moderate_breeze"
    assert analysis.precipitation_category == "heavy_rain"
    assert analysis.precipitation_probability_rating == "very_likely"
    assert analysis.visibility_condition == "haze"
    assert analysis.barometric_state == "low_trough"
    assert analysis.dew_point_depression == 6.0
    assert "heat" in analysis.summary.lower()
    assert "oppressive humidity" in analysis.summary.lower()


def test_analysis_engine_handles_missing_fields(engine: WeatherAnalysisEngine, provider: ProviderInfo):
    obs = CurrentWeather(
        location="Minimal",
        latitude=0.0,
        longitude=0.0,
        timestamp=datetime.now(tz=timezone.utc),
        provider=provider,
    )

    analysis = engine.analyze(obs)

    assert analysis.apparent_temperature == 25.0
    assert analysis.thermal_comfort == "comfortable"
    assert analysis.humidity_comfort == "comfortable"
    assert analysis.precipitation_category == "none"
    assert analysis.dew_point_depression is None
    assert isinstance(analysis.summary, str)
