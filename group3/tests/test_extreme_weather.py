"""
tests/test_extreme_weather.py
-----------------------------
Comprehensive unit and boundary tests for ExtremeWeatherDetector (Module 1.2).

Validates:
- Correct IMD 24-hour rainfall classification (only valid 24h accumulation)
- Hourly vs 24-hour rainfall handling
- Missing precipitation data handling
- Exact threshold boundaries (below, at, above)
- Isolated moderate heatwave, cold wave, and gale classifications
- Direct tests for detect_forecast_hazards()
- Strict safety semantics (is_official_warning=False, heuristic notices)
"""

from datetime import datetime, timezone
import pytest

from app.schemas.unified_weather import (
    CurrentWeather,
    DailyForecast,
    ForecastPoint,
    ForecastWeather,
    ProviderInfo,
)
from app.services.extreme_weather import (
    ExtremeWeatherDetector,
    ICAO_DENSE_FOG_KM,
    ICAO_LOW_VISIBILITY_KM,
    IMD_CLOUDBURST_HOURLY_MM,
    IMD_COLD_WAVE_TEMP_C,
    IMD_EXTREMELY_HEAVY_RAIN_MM,
    IMD_HEATWAVE_TEMP_C,
    IMD_HEAVY_RAIN_MM,
    IMD_SEVERE_COLD_WAVE_TEMP_C,
    IMD_SEVERE_HEATWAVE_TEMP_C,
    IMD_VERY_HEAVY_RAIN_MM,
    WMO_GALE_WIND_KMH,
    WMO_HIGH_WIND_KMH,
    WMO_STORM_WIND_KMH,
)


@pytest.fixture
def provider() -> ProviderInfo:
    return ProviderInfo(name="test_provider")


@pytest.fixture
def detector() -> ExtremeWeatherDetector:
    return ExtremeWeatherDetector()


# --------------------------------------------------------------------------- #
# 1. IMD 24-Hour Rainfall Classification Tests                                 #
# --------------------------------------------------------------------------- #

def test_imd_extremely_heavy_rain_24h(detector: ExtremeWeatherDetector, provider: ProviderInfo):
    obs = CurrentWeather(
        location="Coastal",
        latitude=15.0,
        longitude=80.0,
        timestamp=datetime.now(tz=timezone.utc),
        rainfall_24h=210.0,
        provider=provider,
    )
    events = detector.detect_all(obs)
    assert len(events) >= 1
    ev = events[0]
    assert ev.event_type == "extremely_heavy_rain"
    assert ev.severity == "extreme"
    assert ev.unit == "mm/24h"
    assert ev.classification_source == "IMD_RAINFALL_STANDARD"
    assert ev.is_official_warning is False
    assert "heuristic" in ev.notice.lower()


def test_imd_very_heavy_rain_24h(detector: ExtremeWeatherDetector, provider: ProviderInfo):
    obs = CurrentWeather(
        location="Monsoon",
        latitude=15.0,
        longitude=80.0,
        timestamp=datetime.now(tz=timezone.utc),
        rainfall_24h=130.0,
        provider=provider,
    )
    events = detector.detect_all(obs)
    assert len(events) >= 1
    ev = events[0]
    assert ev.event_type == "very_heavy_rain"
    assert ev.severity == "high"
    assert ev.unit == "mm/24h"


def test_imd_heavy_rain_24h(detector: ExtremeWeatherDetector, provider: ProviderInfo):
    obs = CurrentWeather(
        location="Deccan",
        latitude=17.0,
        longitude=78.0,
        timestamp=datetime.now(tz=timezone.utc),
        rainfall_24h=70.0,
        provider=provider,
    )
    events = detector.detect_all(obs)
    assert len(events) >= 1
    ev = events[0]
    assert ev.event_type == "heavy_rain"
    assert ev.severity == "moderate"
    assert ev.unit == "mm/24h"


# --------------------------------------------------------------------------- #
# 2. Hourly vs 24-Hour Rainfall Handling                                       #
# --------------------------------------------------------------------------- #

def test_hourly_rain_cannot_be_classified_as_24h_imd(detector: ExtremeWeatherDetector, provider: ProviderInfo):
    """
    An hourly rate of 70 mm/h must NOT be classified as IMD 24h heavy rain.
    It must return an explicit insufficient_rainfall_data event.
    """
    obs = CurrentWeather(
        location="RainyCity",
        latitude=15.0,
        longitude=80.0,
        timestamp=datetime.now(tz=timezone.utc),
        rainfall=70.0,  # mm/h hourly rate
        rainfall_24h=None,
        provider=provider,
    )
    events = detector.detect_all(obs)
    assert len(events) == 1
    ev = events[0]
    assert ev.event_type == "insufficient_rainfall_data"
    assert ev.is_official_warning is False
    assert "hourly precipitation cannot be compared against 24-hour thresholds" in ev.description.lower()


def test_zero_hourly_rainfall_without_24h_returns_no_hazard(detector: ExtremeWeatherDetector, provider: ProviderInfo):
    obs = CurrentWeather(
        location="DryPlains",
        latitude=20.0,
        longitude=75.0,
        timestamp=datetime.now(tz=timezone.utc),
        rainfall=0.0,
        rainfall_24h=None,
        provider=provider,
    )
    events = detector.detect_rainfall_hazards(obs)
    assert len(events) == 0


def test_missing_precipitation_data_handling(detector: ExtremeWeatherDetector, provider: ProviderInfo):
    obs = CurrentWeather(
        location="NoSensorCity",
        latitude=20.0,
        longitude=75.0,
        timestamp=datetime.now(tz=timezone.utc),
        rainfall=None,
        rainfall_24h=None,
        provider=provider,
    )
    events = detector.detect_rainfall_hazards(obs)
    assert len(events) == 1
    assert events[0].event_type == "insufficient_rainfall_data"
    assert "unavailable" in events[0].description.lower()


def test_forecast_daily_accumulation_supplies_24h_data(detector: ExtremeWeatherDetector, provider: ProviderInfo):
    now = datetime.now(tz=timezone.utc)
    obs = CurrentWeather(
        location="ForecastTown",
        latitude=18.0,
        longitude=79.0,
        timestamp=now,
        rainfall=10.0,
        rainfall_24h=None,
        provider=provider,
    )
    forecast = ForecastWeather(
        location="ForecastTown",
        latitude=18.0,
        longitude=79.0,
        hourly=[],
        daily=[DailyForecast(date="2026-10-16", precipitation_sum=125.0)],
        provider=provider,
    )
    events = detector.detect_all(obs, forecast=forecast)
    # The 24h rainfall is resolved from forecast.daily[0].precipitation_sum
    very_heavy = next(e for e in events if e.event_type == "very_heavy_rain")
    assert very_heavy.value == 125.0
    assert very_heavy.severity == "high"


# --------------------------------------------------------------------------- #
# 3. Exact Threshold Boundary Tests (Below, At, Above)                        #
# --------------------------------------------------------------------------- #

# Rainfall Thresholds: 64.5, 115.6, 204.5 mm/24h
def test_rainfall_heavy_boundaries(detector: ExtremeWeatherDetector, provider: ProviderInfo):
    now = datetime.now(tz=timezone.utc)
    # 64.4 mm: Below Heavy Rain
    obs_below = CurrentWeather(location="L", latitude=0, longitude=0, timestamp=now, rainfall_24h=64.4, provider=provider)
    assert len(detector.detect_rainfall_hazards(obs_below)) == 0

    # 64.5 mm: Exactly At Heavy Rain
    obs_at = CurrentWeather(location="L", latitude=0, longitude=0, timestamp=now, rainfall_24h=64.5, provider=provider)
    ev_at = detector.detect_rainfall_hazards(obs_at)
    assert len(ev_at) == 1 and ev_at[0].event_type == "heavy_rain"

    # 64.6 mm: Above Heavy Rain
    obs_above = CurrentWeather(location="L", latitude=0, longitude=0, timestamp=now, rainfall_24h=64.6, provider=provider)
    ev_above = detector.detect_rainfall_hazards(obs_above)
    assert len(ev_above) == 1 and ev_above[0].event_type == "heavy_rain"


def test_rainfall_very_heavy_boundaries(detector: ExtremeWeatherDetector, provider: ProviderInfo):
    now = datetime.now(tz=timezone.utc)
    # 115.5 mm: Below Very Heavy Rain (is heavy rain)
    obs_below = CurrentWeather(location="L", latitude=0, longitude=0, timestamp=now, rainfall_24h=115.5, provider=provider)
    ev_below = detector.detect_rainfall_hazards(obs_below)
    assert len(ev_below) == 1 and ev_below[0].event_type == "heavy_rain"

    # 115.6 mm: Exactly At Very Heavy Rain
    obs_at = CurrentWeather(location="L", latitude=0, longitude=0, timestamp=now, rainfall_24h=115.6, provider=provider)
    ev_at = detector.detect_rainfall_hazards(obs_at)
    assert len(ev_at) == 1 and ev_at[0].event_type == "very_heavy_rain"

    # 115.7 mm: Above Very Heavy Rain
    obs_above = CurrentWeather(location="L", latitude=0, longitude=0, timestamp=now, rainfall_24h=115.7, provider=provider)
    ev_above = detector.detect_rainfall_hazards(obs_above)
    assert len(ev_above) == 1 and ev_above[0].event_type == "very_heavy_rain"


def test_rainfall_extremely_heavy_boundaries(detector: ExtremeWeatherDetector, provider: ProviderInfo):
    now = datetime.now(tz=timezone.utc)
    # 204.4 mm: Below Extremely Heavy Rain (is very heavy)
    obs_below = CurrentWeather(location="L", latitude=0, longitude=0, timestamp=now, rainfall_24h=204.4, provider=provider)
    ev_below = detector.detect_rainfall_hazards(obs_below)
    assert len(ev_below) == 1 and ev_below[0].event_type == "very_heavy_rain"

    # 204.5 mm: Exactly At Extremely Heavy Rain
    obs_at = CurrentWeather(location="L", latitude=0, longitude=0, timestamp=now, rainfall_24h=204.5, provider=provider)
    ev_at = detector.detect_rainfall_hazards(obs_at)
    assert len(ev_at) == 1 and ev_at[0].event_type == "extremely_heavy_rain"

    # 204.6 mm: Above Extremely Heavy Rain
    obs_above = CurrentWeather(location="L", latitude=0, longitude=0, timestamp=now, rainfall_24h=204.6, provider=provider)
    ev_above = detector.detect_rainfall_hazards(obs_above)
    assert len(ev_above) == 1 and ev_above[0].event_type == "extremely_heavy_rain"


# Thermal Thresholds: Heat (40.0°C, 45.0°C) and Cold (5.0°C, 2.0°C)
def test_heatwave_moderate_boundaries(detector: ExtremeWeatherDetector, provider: ProviderInfo):
    now = datetime.now(tz=timezone.utc)
    # 39.9°C: Below Heatwave
    assert len(detector.detect_thermal_hazards(CurrentWeather(location="L", latitude=0, longitude=0, timestamp=now, temperature=39.9, provider=provider))) == 0

    # 40.0°C: Exactly At Moderate Heatwave
    ev_at = detector.detect_thermal_hazards(CurrentWeather(location="L", latitude=0, longitude=0, timestamp=now, temperature=40.0, provider=provider))
    assert len(ev_at) == 1 and ev_at[0].event_type == "extreme_heat" and ev_at[0].severity == "high"

    # 40.1°C: Above
    ev_above = detector.detect_thermal_hazards(CurrentWeather(location="L", latitude=0, longitude=0, timestamp=now, temperature=40.1, provider=provider))
    assert len(ev_above) == 1 and ev_above[0].event_type == "extreme_heat" and ev_above[0].severity == "high"


def test_heatwave_severe_boundaries(detector: ExtremeWeatherDetector, provider: ProviderInfo):
    now = datetime.now(tz=timezone.utc)
    # 44.9°C: Below Severe Heatwave (is high heat)
    ev_below = detector.detect_thermal_hazards(CurrentWeather(location="L", latitude=0, longitude=0, timestamp=now, temperature=44.9, provider=provider))
    assert len(ev_below) == 1 and ev_below[0].severity == "high"

    # 45.0°C: Exactly At Severe Heatwave
    ev_at = detector.detect_thermal_hazards(CurrentWeather(location="L", latitude=0, longitude=0, timestamp=now, temperature=45.0, provider=provider))
    assert len(ev_at) == 1 and ev_at[0].severity == "extreme"

    # 45.1°C: Above Severe Heatwave
    ev_above = detector.detect_thermal_hazards(CurrentWeather(location="L", latitude=0, longitude=0, timestamp=now, temperature=45.1, provider=provider))
    assert len(ev_above) == 1 and ev_above[0].severity == "extreme"


def test_cold_wave_moderate_boundaries(detector: ExtremeWeatherDetector, provider: ProviderInfo):
    now = datetime.now(tz=timezone.utc)
    # 5.1°C: Above Cold Wave threshold (not triggered)
    assert len(detector.detect_thermal_hazards(CurrentWeather(location="L", latitude=0, longitude=0, timestamp=now, temperature=5.1, provider=provider))) == 0

    # 5.0°C: Exactly At Cold Wave
    ev_at = detector.detect_thermal_hazards(CurrentWeather(location="L", latitude=0, longitude=0, timestamp=now, temperature=5.0, provider=provider))
    assert len(ev_at) == 1 and ev_at[0].event_type == "extreme_cold" and ev_at[0].severity == "moderate"

    # 4.9°C: Below Cold Wave threshold
    ev_below = detector.detect_thermal_hazards(CurrentWeather(location="L", latitude=0, longitude=0, timestamp=now, temperature=4.9, provider=provider))
    assert len(ev_below) == 1 and ev_below[0].event_type == "extreme_cold" and ev_below[0].severity == "moderate"


def test_cold_wave_severe_boundaries(detector: ExtremeWeatherDetector, provider: ProviderInfo):
    now = datetime.now(tz=timezone.utc)
    # 2.1°C: Moderate cold wave
    ev_above = detector.detect_thermal_hazards(CurrentWeather(location="L", latitude=0, longitude=0, timestamp=now, temperature=2.1, provider=provider))
    assert len(ev_above) == 1 and ev_above[0].severity == "moderate"

    # 2.0°C: Exactly At Severe Cold Wave
    ev_at = detector.detect_thermal_hazards(CurrentWeather(location="L", latitude=0, longitude=0, timestamp=now, temperature=2.0, provider=provider))
    assert len(ev_at) == 1 and ev_at[0].severity == "high"

    # 1.9°C: Below
    ev_below = detector.detect_thermal_hazards(CurrentWeather(location="L", latitude=0, longitude=0, timestamp=now, temperature=1.9, provider=provider))
    assert len(ev_below) == 1 and ev_below[0].severity == "high"


# Wind Thresholds: 50.0 (high), 62.0 (gale), 89.0 (storm) km/h
def test_wind_high_boundaries(detector: ExtremeWeatherDetector, provider: ProviderInfo):
    now = datetime.now(tz=timezone.utc)
    assert len(detector.detect_wind_hazards(CurrentWeather(location="L", latitude=0, longitude=0, timestamp=now, wind_speed=49.9, provider=provider))) == 0

    ev_at = detector.detect_wind_hazards(CurrentWeather(location="L", latitude=0, longitude=0, timestamp=now, wind_speed=50.0, provider=provider))
    assert len(ev_at) == 1 and ev_at[0].event_type == "high_wind" and ev_at[0].severity == "moderate"

    ev_above = detector.detect_wind_hazards(CurrentWeather(location="L", latitude=0, longitude=0, timestamp=now, wind_speed=50.1, provider=provider))
    assert len(ev_above) == 1 and ev_above[0].event_type == "high_wind" and ev_above[0].severity == "moderate"


def test_wind_gale_boundaries(detector: ExtremeWeatherDetector, provider: ProviderInfo):
    now = datetime.now(tz=timezone.utc)
    # 61.9 km/h: high wind
    ev_below = detector.detect_wind_hazards(CurrentWeather(location="L", latitude=0, longitude=0, timestamp=now, wind_speed=61.9, provider=provider))
    assert len(ev_below) == 1 and ev_below[0].event_type == "high_wind"

    # 62.0 km/h: gale wind
    ev_at = detector.detect_wind_hazards(CurrentWeather(location="L", latitude=0, longitude=0, timestamp=now, wind_speed=62.0, provider=provider))
    assert len(ev_at) == 1 and ev_at[0].event_type == "gale_wind" and ev_at[0].severity == "high"

    # 62.1 km/h: gale wind
    ev_above = detector.detect_wind_hazards(CurrentWeather(location="L", latitude=0, longitude=0, timestamp=now, wind_speed=62.1, provider=provider))
    assert len(ev_above) == 1 and ev_above[0].event_type == "gale_wind" and ev_above[0].severity == "high"


def test_wind_storm_boundaries(detector: ExtremeWeatherDetector, provider: ProviderInfo):
    now = datetime.now(tz=timezone.utc)
    # 88.9 km/h: gale wind
    ev_below = detector.detect_wind_hazards(CurrentWeather(location="L", latitude=0, longitude=0, timestamp=now, wind_speed=88.9, provider=provider))
    assert len(ev_below) == 1 and ev_below[0].event_type == "gale_wind"

    # 89.0 km/h: storm wind
    ev_at = detector.detect_wind_hazards(CurrentWeather(location="L", latitude=0, longitude=0, timestamp=now, wind_speed=89.0, provider=provider))
    assert len(ev_at) == 1 and ev_at[0].event_type == "storm_wind" and ev_at[0].severity == "extreme"

    # 89.1 km/h: storm wind
    ev_above = detector.detect_wind_hazards(CurrentWeather(location="L", latitude=0, longitude=0, timestamp=now, wind_speed=89.1, provider=provider))
    assert len(ev_above) == 1 and ev_above[0].event_type == "storm_wind" and ev_above[0].severity == "extreme"


# Visibility Thresholds: 1.0 km (low visibility), 0.2 km (dense fog)
def test_visibility_boundaries(detector: ExtremeWeatherDetector, provider: ProviderInfo):
    now = datetime.now(tz=timezone.utc)
    # 1.01 km: no hazard
    assert detector.detect_visibility(CurrentWeather(location="L", latitude=0, longitude=0, timestamp=now, visibility=1.01, provider=provider)) is None

    # 1.0 km: low visibility (high)
    ev_1_0 = detector.detect_visibility(CurrentWeather(location="L", latitude=0, longitude=0, timestamp=now, visibility=1.0, provider=provider))
    assert ev_1_0 is not None and ev_1_0.event_type == "low_visibility" and ev_1_0.severity == "high"

    # 0.21 km: low visibility (high)
    ev_0_21 = detector.detect_visibility(CurrentWeather(location="L", latitude=0, longitude=0, timestamp=now, visibility=0.21, provider=provider))
    assert ev_0_21 is not None and ev_0_21.severity == "high"

    # 0.20 km: dense fog (extreme)
    ev_0_20 = detector.detect_visibility(CurrentWeather(location="L", latitude=0, longitude=0, timestamp=now, visibility=0.20, provider=provider))
    assert ev_0_20 is not None and ev_0_20.severity == "extreme"


# --------------------------------------------------------------------------- #
# 4. Direct Tests for detect_forecast_hazards()                               #
# --------------------------------------------------------------------------- #

def test_detect_forecast_hazards_daily_rain(detector: ExtremeWeatherDetector, provider: ProviderInfo):
    forecast = ForecastWeather(
        location="Station",
        latitude=10.0,
        longitude=75.0,
        hourly=[],
        daily=[
            DailyForecast(date="2026-10-17", precipitation_sum=120.0),
            DailyForecast(date="2026-10-18", precipitation_sum=210.0),
        ],
        provider=provider,
    )
    events = detector.detect_forecast_hazards(forecast)
    assert len(events) >= 1
    ext = next(e for e in events if e.event_type == "extremely_heavy_rain")
    assert ext.value == 210.0
    assert ext.severity == "extreme"


def test_detect_forecast_hazards_hourly_cloudburst(detector: ExtremeWeatherDetector, provider: ProviderInfo):
    now = datetime.now(tz=timezone.utc)
    forecast = ForecastWeather(
        location="CloudburstZone",
        latitude=30.0,
        longitude=78.0,
        hourly=[
            ForecastPoint(timestamp=now, rainfall=105.0),
        ],
        daily=[],
        provider=provider,
    )
    events = detector.detect_forecast_hazards(forecast)
    cb = next(e for e in events if e.classification_source == "IMD_CLOUDBURST_CRITERIA")
    assert cb.value == 105.0
    assert cb.severity == "extreme"


def test_detect_forecast_hazards_hourly_gale_and_storm(detector: ExtremeWeatherDetector, provider: ProviderInfo):
    now = datetime.now(tz=timezone.utc)
    forecast_gale = ForecastWeather(
        location="Coast",
        latitude=12.0,
        longitude=80.0,
        hourly=[ForecastPoint(timestamp=now, wind_speed=65.0)],
        daily=[],
        provider=provider,
    )
    events_gale = detector.detect_forecast_hazards(forecast_gale)
    assert any(e.event_type == "gale_wind" and e.severity == "high" for e in events_gale)

    forecast_storm = ForecastWeather(
        location="Coast",
        latitude=12.0,
        longitude=80.0,
        hourly=[ForecastPoint(timestamp=now, wind_speed=95.0)],
        daily=[],
        provider=provider,
    )
    events_storm = detector.detect_forecast_hazards(forecast_storm)
    assert any(e.event_type == "storm_wind" and e.severity == "extreme" for e in events_storm)


def test_detect_forecast_hazards_empty(detector: ExtremeWeatherDetector, provider: ProviderInfo):
    empty_forecast = ForecastWeather(
        location="Empty",
        latitude=0,
        longitude=0,
        hourly=[],
        daily=[],
        provider=provider,
    )
    assert len(detector.detect_forecast_hazards(empty_forecast)) == 0


# --------------------------------------------------------------------------- #
# 5. Thunderstorm & Visibility Tests                                           #
# --------------------------------------------------------------------------- #

def test_thunderstorm_cape_detection(detector: ExtremeWeatherDetector, provider: ProviderInfo):
    obs = CurrentWeather(
        location="StormZone",
        latitude=22.0,
        longitude=88.0,
        timestamp=datetime.now(tz=timezone.utc),
        cape=2400.0,
        lightning=True,
        provider=provider,
    )
    events = detector.detect_all(obs)
    storm_ev = next(e for e in events if e.event_type == "thunderstorm")
    assert storm_ev.severity == "extreme"


def test_low_visibility_dense_fog(detector: ExtremeWeatherDetector, provider: ProviderInfo):
    obs = CurrentWeather(
        location="DelhiAirport",
        latitude=28.5,
        longitude=77.1,
        timestamp=datetime.now(tz=timezone.utc),
        visibility=0.15,  # 150 meters
        provider=provider,
    )
    events = detector.detect_all(obs)
    vis_ev = next(e for e in events if e.event_type == "low_visibility")
    assert vis_ev.severity == "extreme"
    assert vis_ev.classification_source == "ICAO_VISIBILITY_STANDARD"
