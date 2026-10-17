"""
services/weather_analysis.py
----------------------------
Deterministic meteorological analysis of current weather observations.

Computes:
  - Heat Index (Rothfusz equation) & Wind Chill
  - Apparent temperature interpretation and thermal comfort bands
  - Humidity comfort categories and dew point depression
  - Beaufort scale wind classification (0 to 12)
  - Precipitation rate and rain probability categorizations
  - Visibility condition ratings
  - Barometric pressure status
  - Deterministic human-readable condition synthesis
"""

from __future__ import annotations

import math
from typing import Optional, Tuple

from app.schemas.intelligence import (
    BarometricState,
    BeaufortCategory,
    CurrentAnalysis,
    HumidityComfortLevel,
    PrecipitationCategory,
    ThermalComfortLevel,
    VisibilityCondition,
)
from app.schemas.unified_weather import CurrentWeather


# --------------------------------------------------------------------------- #
# Pure Meteorological Calculation Functions                                    #
# --------------------------------------------------------------------------- #

def compute_heat_index(temp_c: float, humidity_pct: float) -> float:
    """
    Calculate Heat Index in °C using the standard Rothfusz regression equation.
    Applicable when temperature >= 26.7°C (80°F) and relative humidity >= 40%.
    """
    if temp_c < 20.0 or humidity_pct < 20.0:
        return temp_c

    # Convert Celsius to Fahrenheit for Rothfusz polynomial
    T = (temp_c * 9.0 / 5.0) + 32.0
    R = max(0.0, min(100.0, humidity_pct))

    # Steadman simple approximation
    hi = 0.5 * (T + 61.0 + ((T - 68.0) * 1.2) + (R * 0.094))

    if hi >= 80.0:
        # Full Rothfusz regression
        c1 = -42.379
        c2 = 2.04901523
        c3 = 10.14333127
        c4 = -0.22475541
        c5 = -0.00683783
        c6 = -0.05481717
        c7 = 0.00122874
        c8 = 0.00085282
        c9 = -0.00000199

        hi = (
            c1
            + (c2 * T)
            + (c3 * R)
            + (c4 * T * R)
            + (c5 * (T**2))
            + (c6 * (R**2))
            + (c7 * (T**2) * R)
            + (c8 * T * (R**2))
            + (c9 * (T**2) * (R**2))
        )

        # Adjustments
        if R < 13.0 and 80.0 <= T <= 112.0:
            adjustment = ((13.0 - R) / 4.0) * math.sqrt((17.0 - abs(T - 95.0)) / 17.0)
            hi -= adjustment
        elif R > 85.0 and 80.0 <= T <= 87.0:
            adjustment = ((R - 85.0) / 10.0) * ((87.0 - T) / 5.0)
            hi += adjustment

    # Convert back to Celsius
    hi_c = (hi - 32.0) * 5.0 / 9.0
    return round(hi_c, 1)


def compute_wind_chill(temp_c: float, wind_kmh: float) -> float:
    """
    Calculate Wind Chill in °C using Environment Canada / NOAA formula.
    Applicable when temperature <= 10.0°C and wind speed >= 4.8 km/h.
    """
    if temp_c > 10.0 or wind_kmh < 4.8:
        return temp_c

    # Formula: 13.12 + 0.6215*T - 11.37*(V^0.16) + 0.3965*T*(V^0.16)
    v_pow = wind_kmh**0.16
    wc = 13.12 + (0.6215 * temp_c) - (11.37 * v_pow) + (0.3965 * temp_c * v_pow)
    return round(wc, 1)


def classify_thermal_comfort(apparent_t: float) -> ThermalComfortLevel:
    """Classify apparent temperature into thermal comfort bands."""
    if apparent_t < 0.0:
        return "freezing"
    if apparent_t < 15.0:
        return "cold"
    if apparent_t <= 26.0:
        return "comfortable"
    if apparent_t <= 32.0:
        return "caution"
    if apparent_t <= 39.0:
        return "extreme_caution"
    if apparent_t <= 51.0:
        return "danger"
    return "extreme_danger"


def classify_humidity_comfort(humidity_pct: Optional[float]) -> HumidityComfortLevel:
    """Classify relative humidity into comfort bands."""
    if humidity_pct is None:
        return "comfortable"
    if humidity_pct < 30.0:
        return "dry"
    if humidity_pct <= 60.0:
        return "comfortable"
    if humidity_pct <= 80.0:
        return "humid"
    return "oppressive"


def classify_beaufort_scale(wind_kmh: Optional[float]) -> Tuple[int, BeaufortCategory]:
    """Classify wind speed (km/h) into Beaufort number and category."""
    if wind_kmh is None or wind_kmh < 1.0:
        return 0, "calm"
    if wind_kmh < 6.0:
        return 1, "light_air"
    if wind_kmh < 12.0:
        return 2, "light_breeze"
    if wind_kmh < 20.0:
        return 3, "gentle_breeze"
    if wind_kmh < 29.0:
        return 4, "moderate_breeze"
    if wind_kmh < 39.0:
        return 5, "fresh_breeze"
    if wind_kmh < 50.0:
        return 6, "strong_breeze"
    if wind_kmh < 62.0:
        return 7, "near_gale"
    if wind_kmh < 75.0:
        return 8, "gale"
    if wind_kmh < 89.0:
        return 9, "strong_gale"
    if wind_kmh < 103.0:
        return 10, "storm"
    if wind_kmh < 118.0:
        return 11, "violent_storm"
    return 12, "hurricane"


def classify_precipitation(rainfall_mm: Optional[float]) -> PrecipitationCategory:
    """Classify rainfall rate into standard meteorological intensity categories."""
    if rainfall_mm is None or rainfall_mm <= 0.1:
        return "none"
    if rainfall_mm < 2.5:
        return "slight_rain"
    if rainfall_mm < 7.6:
        return "moderate_rain"
    if rainfall_mm <= 50.0:
        return "heavy_rain"
    return "violent_rain"


def classify_rain_probability(prob_pct: Optional[float]) -> Optional[str]:
    """Classify precipitation probability percentage."""
    if prob_pct is None:
        return None
    if prob_pct < 20.0:
        return "unlikely"
    if prob_pct < 40.0:
        return "slight_chance"
    if prob_pct < 60.0:
        return "possible"
    if prob_pct < 80.0:
        return "likely"
    return "very_likely"


def classify_visibility(vis_km: Optional[float]) -> VisibilityCondition:
    """Classify horizontal visibility into atmospheric clarity bands."""
    if vis_km is None:
        return "clear"
    if vis_km < 0.5:
        return "dense_fog"
    if vis_km < 1.0:
        return "fog"
    if vis_km < 4.0:
        return "mist"
    if vis_km < 10.0:
        return "haze"
    return "clear"


def classify_barometric_state(pressure_hpa: Optional[float]) -> BarometricState:
    """Classify atmospheric pressure status."""
    if pressure_hpa is None:
        return "normal"
    if pressure_hpa < 990.0:
        return "deep_low"
    if pressure_hpa < 1006.0:
        return "low_trough"
    if pressure_hpa <= 1025.0:
        return "normal"
    return "high_pressure"


# --------------------------------------------------------------------------- #
# Weather Analysis Engine Service                                              #
# --------------------------------------------------------------------------- #

class WeatherAnalysisEngine:
    """
    Stateless engine to produce deterministic meteorological analysis
    from a CurrentWeather observation.
    """

    def analyze(
        self,
        weather: CurrentWeather,
        rain_probability: Optional[float] = None,
    ) -> CurrentAnalysis:
        # 1. Determine Apparent Temperature
        apparent_t = weather.feels_like
        if apparent_t is None:
            if weather.temperature is not None:
                if weather.temperature >= 26.7 and weather.humidity is not None:
                    apparent_t = compute_heat_index(weather.temperature, weather.humidity)
                elif weather.temperature <= 10.0 and weather.wind_speed is not None:
                    apparent_t = compute_wind_chill(weather.temperature, weather.wind_speed)
                else:
                    apparent_t = weather.temperature
            else:
                apparent_t = 25.0

        thermal_comfort = classify_thermal_comfort(apparent_t)
        humidity_comfort = classify_humidity_comfort(weather.humidity)
        beaufort_num, beaufort_cat = classify_beaufort_scale(weather.wind_speed)
        precip_cat = classify_precipitation(weather.rainfall)
        precip_prob_rating = classify_rain_probability(rain_probability)
        vis_condition = classify_visibility(weather.visibility)
        baro_state = classify_barometric_state(weather.pressure)

        # Dew point depression
        dew_point_dep: Optional[float] = None
        if weather.temperature is not None and weather.dew_point is not None:
            dew_point_dep = round(weather.temperature - weather.dew_point, 1)

        # Synthesize deterministic descriptive summary
        summary = self._generate_summary(
            temp_c=weather.temperature,
            apparent_t=apparent_t,
            thermal_comfort=thermal_comfort,
            humidity_comfort=humidity_comfort,
            precip_cat=precip_cat,
            rain_prob_rating=precip_prob_rating,
            beaufort_cat=beaufort_cat,
            vis_condition=vis_condition,
            baro_state=baro_state,
        )

        return CurrentAnalysis(
            apparent_temperature=apparent_t,
            thermal_comfort=thermal_comfort,
            humidity_comfort=humidity_comfort,
            wind_beaufort_scale=beaufort_num,
            wind_classification=beaufort_cat,
            precipitation_category=precip_cat,
            precipitation_probability_rating=precip_prob_rating,
            visibility_condition=vis_condition,
            barometric_state=baro_state,
            dew_point_depression=dew_point_dep,
            summary=summary,
        )

    def _generate_summary(
        self,
        temp_c: Optional[float],
        apparent_t: float,
        thermal_comfort: ThermalComfortLevel,
        humidity_comfort: HumidityComfortLevel,
        precip_cat: PrecipitationCategory,
        rain_prob_rating: Optional[str],
        beaufort_cat: BeaufortCategory,
        vis_condition: VisibilityCondition,
        baro_state: BarometricState,
    ) -> str:
        parts: list[str] = []

        # Temperature / Thermal note
        if thermal_comfort in ("extreme_danger", "danger"):
            parts.append(f"Dangerous heat conditions (feels like {apparent_t}°C)")
        elif thermal_comfort == "extreme_caution":
            parts.append(f"High apparent heat ({apparent_t}°C) requiring caution")
        elif thermal_comfort == "caution":
            parts.append(f"Warm apparent temperature ({apparent_t}°C)")
        elif thermal_comfort in ("freezing", "cold"):
            parts.append(f"Cold conditions (feels like {apparent_t}°C)")
        else:
            parts.append(f"Comfortable thermal conditions ({apparent_t}°C)")

        # Humidity note
        if humidity_comfort == "oppressive":
            parts.append("oppressive humidity")
        elif humidity_comfort == "humid":
            parts.append("elevated humidity")
        elif humidity_comfort == "dry":
            parts.append("dry air")

        # Precipitation note
        if precip_cat == "violent_rain":
            parts.append("torrential rainfall underway")
        elif precip_cat == "heavy_rain":
            parts.append("heavy rain observed")
        elif precip_cat == "moderate_rain":
            parts.append("moderate rainfall")
        elif precip_cat == "slight_rain":
            parts.append("light rain observed")
        elif rain_prob_rating in ("likely", "very_likely"):
            parts.append("high probability of rain")

        # Wind note
        if beaufort_cat in ("storm", "violent_storm", "hurricane"):
            parts.append("destructive storm-force winds")
        elif beaufort_cat in ("gale", "strong_gale"):
            parts.append("gale-force winds")
        elif beaufort_cat in ("strong_breeze", "near_gale"):
            parts.append("gusty strong winds")

        # Visibility note
        if vis_condition in ("dense_fog", "fog"):
            parts.append("severely reduced visibility in fog")
        elif vis_condition == "mist":
            parts.append("misty conditions")

        # Barometric note
        if baro_state == "deep_low":
            parts.append("deep low-pressure system")
        elif baro_state == "low_trough":
            parts.append("unstable low-pressure trough")

        # Form sentence
        if not parts:
            return "Stable atmospheric conditions."
        return "; ".join(parts[0:1] + [p for p in parts[1:]]) + "."
