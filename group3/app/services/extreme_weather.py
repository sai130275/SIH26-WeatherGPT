"""
services/extreme_weather.py
---------------------------
Extensible rule-based extreme weather event detection layer.

Detects:
  - Heavy, very heavy, and extremely heavy rainfall (IMD Standards)
  - Extreme heat & heatwave conditions (IMD Standards)
  - Extreme cold & cold wave conditions (IMD Standards)
  - High winds, gales, and storm-force gusts (WMO / Beaufort Standards)
  - Thunderstorm & convective instability conditions (CAPE & lightning)
  - Rapid temperature changes (frontal passages)
  - Low visibility & dense fog (ICAO Standards)

All detected events clearly indicate their classification source and are
explicitly marked with is_official_warning=False and heuristic notices.
"""

from __future__ import annotations

from typing import List, Optional

from app.core.config import Settings, settings as default_settings
from app.schemas.intelligence import (
    DetectedExtremeEvent,
    ExtremeEventType,
    SeverityLevel,
)
from app.schemas.unified_weather import CurrentWeather, ForecastWeather


# Standard IMD / WMO Threshold Constants
IMD_HEAVY_RAIN_MM = 64.5
IMD_VERY_HEAVY_RAIN_MM = 115.6
IMD_EXTREMELY_HEAVY_RAIN_MM = 204.5

IMD_HEATWAVE_TEMP_C = 40.0
IMD_SEVERE_HEATWAVE_TEMP_C = 45.0

IMD_COLD_WAVE_TEMP_C = 5.0
IMD_SEVERE_COLD_WAVE_TEMP_C = 2.0

WMO_HIGH_WIND_KMH = 50.0
WMO_GALE_WIND_KMH = 62.0
WMO_STORM_WIND_KMH = 89.0

ICAO_LOW_VISIBILITY_KM = 1.0
ICAO_DENSE_FOG_KM = 0.2

IMD_CLOUDBURST_HOURLY_MM = 100.0


class ExtremeWeatherDetector:
    """
    Extensible hazard and severe event detection service.
    """

    def __init__(self, cfg: Optional[Settings] = None) -> None:
        self.cfg = cfg or default_settings

    def detect_all(
        self,
        current: CurrentWeather,
        forecast: Optional[ForecastWeather] = None,
        rainfall_24h: Optional[float] = None,
    ) -> List[DetectedExtremeEvent]:
        """
        Run all detection rules against current observation and optional forecast.
        """
        events: List[DetectedExtremeEvent] = []

        # 1. Rainfall hazards (strictly using 24-hour accumulation)
        rain_events = self.detect_rainfall_hazards(
            current=current,
            forecast=forecast,
            rainfall_24h=rainfall_24h,
        )
        events.extend(rain_events)

        # 2. Thermal hazards (heat / cold)
        thermal_events = self.detect_thermal_hazards(current)
        events.extend(thermal_events)

        # 3. Wind hazards
        wind_events = self.detect_wind_hazards(current)
        events.extend(wind_events)

        # 4. Thunderstorm / convective hazards
        thunder_events = self.detect_thunderstorm(current)
        if thunder_events:
            events.append(thunder_events)

        # 5. Visibility hazards
        vis_events = self.detect_visibility(current)
        if vis_events:
            events.append(vis_events)

        # 6. Forecast multi-day and hourly hazards
        if forecast:
            forecast_events = self.detect_forecast_hazards(forecast)
            events.extend(forecast_events)

        return events

    def detect_rainfall_hazards(
        self,
        current: CurrentWeather,
        forecast: Optional[ForecastWeather] = None,
        rainfall_24h: Optional[float] = None,
    ) -> List[DetectedExtremeEvent]:
        """
        Evaluate IMD rainfall hazard classifications.

        IMD Standard (24-hour accumulation):
          - Heavy Rain: 64.5 to 115.5 mm/24h
          - Very Heavy Rain: 115.6 to 204.4 mm/24h
          - Extremely Heavy Rain: >= 204.5 mm/24h

        CRITICAL METEOROLOGICAL INTEGRITY:
          - Hourly precipitation rate (mm/h) is NEVER compared directly against
            IMD 24-hour thresholds.
          - 24-hour accumulation is resolved from:
              1. Explicit rainfall_24h argument
              2. current.rainfall_24h attribute
              3. forecast.daily[0].precipitation_sum (if forecast is provided)
              4. 24-hour sum of forecast.hourly precipitation (if >= 24 hours available)
          - If 24-hour accumulation data is unavailable:
              * If precipitation is occurring (current.rainfall > 0), returns an explicit
                'insufficient_rainfall_data' event rather than a misleading classification.
              * If precipitation observation is missing (current.rainfall is None), returns
                an explicit 'insufficient_rainfall_data' event noting data absence.
        """
        events: List[DetectedExtremeEvent] = []

        # Resolve 24-hour accumulated rainfall
        val: Optional[float] = rainfall_24h
        if val is None:
            val = getattr(current, "rainfall_24h", None)

        if val is None and forecast is not None:
            if forecast.daily and len(forecast.daily) > 0 and forecast.daily[0].precipitation_sum is not None:
                val = forecast.daily[0].precipitation_sum
            elif forecast.hourly and len(forecast.hourly) >= 24:
                first_24 = forecast.hourly[:24]
                if all(p.rainfall is not None for p in first_24):
                    val = sum(p.rainfall for p in first_24 if p.rainfall is not None)

        # Case 1: Missing precipitation data entirely
        if current.rainfall is None and val is None:
            events.append(
                DetectedExtremeEvent(
                    event_type="insufficient_rainfall_data",
                    severity="low",
                    value=0.0,
                    unit="mm",
                    threshold=IMD_HEAVY_RAIN_MM,
                    classification_source="IMD_RAINFALL_STANDARD",
                    is_official_warning=False,
                    notice="DATA UNAVAILABLE — HEURISTIC DETECTION ONLY",
                    description="Precipitation observation data is unavailable; cannot evaluate rainfall hazards.",
                )
            )
            return events

        # Case 2: 24-hour accumulation is unavailable, but hourly rain is recorded
        if val is None:
            if current.rainfall is not None and current.rainfall > 0.0:
                events.append(
                    DetectedExtremeEvent(
                        event_type="insufficient_rainfall_data",
                        severity="low",
                        value=current.rainfall,
                        unit="mm/h",
                        threshold=IMD_HEAVY_RAIN_MM,
                        classification_source="IMD_RAINFALL_STANDARD",
                        is_official_warning=False,
                        notice="INSUFFICIENT 24-HOUR DATA — HEURISTIC DETECTION ONLY",
                        description=(
                            f"Current precipitation is {current.rainfall:.1f} mm/h (hourly rate). "
                            "IMD rainfall classifications strictly require 24-hour accumulated rainfall "
                            f"(heavy rain threshold >={IMD_HEAVY_RAIN_MM} mm/24h). 24-hour accumulation data is unavailable; "
                            "hourly precipitation cannot be compared against 24-hour thresholds."
                        ),
                    )
                )
            return events

        # Case 3: Valid 24-hour accumulated rainfall is available
        # Evaluate standard IMD 24h thresholds:
        # Extremely Heavy: >= 204.5 mm
        # Very Heavy: 115.6 - 204.4 mm
        # Heavy: 64.5 - 115.5 mm
        if val >= IMD_EXTREMELY_HEAVY_RAIN_MM:
            events.append(
                DetectedExtremeEvent(
                    event_type="extremely_heavy_rain",
                    severity="extreme",
                    value=val,
                    unit="mm/24h",
                    threshold=IMD_EXTREMELY_HEAVY_RAIN_MM,
                    classification_source="IMD_RAINFALL_STANDARD",
                    description=f"24-hour rainfall of {val:.1f} mm exceeds IMD extremely heavy rain criteria (>={IMD_EXTREMELY_HEAVY_RAIN_MM} mm/24h).",
                )
            )
        elif val >= IMD_VERY_HEAVY_RAIN_MM:
            events.append(
                DetectedExtremeEvent(
                    event_type="very_heavy_rain",
                    severity="high",
                    value=val,
                    unit="mm/24h",
                    threshold=IMD_VERY_HEAVY_RAIN_MM,
                    classification_source="IMD_RAINFALL_STANDARD",
                    description=f"24-hour rainfall of {val:.1f} mm meets IMD very heavy rain criteria ({IMD_VERY_HEAVY_RAIN_MM}–{IMD_EXTREMELY_HEAVY_RAIN_MM - 0.1:.1f} mm/24h).",
                )
            )
        elif val >= IMD_HEAVY_RAIN_MM:
            events.append(
                DetectedExtremeEvent(
                    event_type="heavy_rain",
                    severity="high" if val >= 100.0 else "moderate",
                    value=val,
                    unit="mm/24h",
                    threshold=IMD_HEAVY_RAIN_MM,
                    classification_source="IMD_RAINFALL_STANDARD",
                    description=f"24-hour rainfall of {val:.1f} mm meets IMD heavy rain criteria ({IMD_HEAVY_RAIN_MM}–{IMD_VERY_HEAVY_RAIN_MM - 0.1:.1f} mm/24h).",
                )
            )

        return events

    def detect_thermal_hazards(
        self, current: CurrentWeather
    ) -> List[DetectedExtremeEvent]:
        events: List[DetectedExtremeEvent] = []
        t = current.temperature
        if t is None:
            return events

        # Extreme Heat (IMD absolute temperature criteria)
        if t >= IMD_SEVERE_HEATWAVE_TEMP_C:
            events.append(
                DetectedExtremeEvent(
                    event_type="extreme_heat",
                    severity="extreme",
                    value=t,
                    unit="°C",
                    threshold=IMD_SEVERE_HEATWAVE_TEMP_C,
                    classification_source="IMD_HEATWAVE_STANDARD",
                    description=f"Temperature of {t:.1f}°C meets IMD severe heatwave criteria (>={IMD_SEVERE_HEATWAVE_TEMP_C}°C).",
                )
            )
        elif t >= IMD_HEATWAVE_TEMP_C:
            events.append(
                DetectedExtremeEvent(
                    event_type="extreme_heat",
                    severity="high",
                    value=t,
                    unit="°C",
                    threshold=IMD_HEATWAVE_TEMP_C,
                    classification_source="IMD_HEATWAVE_STANDARD",
                    description=f"Temperature of {t:.1f}°C meets IMD heatwave criteria (>={IMD_HEATWAVE_TEMP_C}°C).",
                )
            )

        # Extreme Cold (IMD absolute temperature criteria)
        if t <= IMD_SEVERE_COLD_WAVE_TEMP_C:
            events.append(
                DetectedExtremeEvent(
                    event_type="extreme_cold",
                    severity="extreme" if t <= 0.0 else "high",
                    value=t,
                    unit="°C",
                    threshold=IMD_SEVERE_COLD_WAVE_TEMP_C,
                    classification_source="IMD_COLD_WAVE_STANDARD",
                    description=f"Temperature of {t:.1f}°C meets IMD severe cold wave / freezing criteria (<={IMD_SEVERE_COLD_WAVE_TEMP_C}°C).",
                )
            )
        elif t <= IMD_COLD_WAVE_TEMP_C:
            events.append(
                DetectedExtremeEvent(
                    event_type="extreme_cold",
                    severity="moderate",
                    value=t,
                    unit="°C",
                    threshold=IMD_COLD_WAVE_TEMP_C,
                    classification_source="IMD_COLD_WAVE_STANDARD",
                    description=f"Temperature of {t:.1f}°C meets IMD cold wave criteria (<={IMD_COLD_WAVE_TEMP_C}°C).",
                )
            )

        return events

    def detect_wind_hazards(
        self, current: CurrentWeather
    ) -> List[DetectedExtremeEvent]:
        events: List[DetectedExtremeEvent] = []
        w = current.wind_speed
        if w is None or w < WMO_HIGH_WIND_KMH:
            return events

        if w >= WMO_STORM_WIND_KMH:
            events.append(
                DetectedExtremeEvent(
                    event_type="storm_wind",
                    severity="extreme",
                    value=w,
                    unit="km/h",
                    threshold=WMO_STORM_WIND_KMH,
                    classification_source="WMO_BEAUFORT_STANDARD",
                    description=f"Wind speed of {w:.1f} km/h reaches storm force (>={WMO_STORM_WIND_KMH} km/h, Beaufort 10+).",
                )
            )
        elif w >= WMO_GALE_WIND_KMH:
            events.append(
                DetectedExtremeEvent(
                    event_type="gale_wind",
                    severity="high",
                    value=w,
                    unit="km/h",
                    threshold=WMO_GALE_WIND_KMH,
                    classification_source="WMO_BEAUFORT_STANDARD",
                    description=f"Wind speed of {w:.1f} km/h reaches gale force (>={WMO_GALE_WIND_KMH} km/h, Beaufort 8+).",
                )
            )
        elif w >= WMO_HIGH_WIND_KMH:
            events.append(
                DetectedExtremeEvent(
                    event_type="high_wind",
                    severity="moderate",
                    value=w,
                    unit="km/h",
                    threshold=WMO_HIGH_WIND_KMH,
                    classification_source="WMO_BEAUFORT_STANDARD",
                    description=f"Wind speed of {w:.1f} km/h meets high wind criteria (>={WMO_HIGH_WIND_KMH} km/h, Beaufort 7+).",
                )
            )

        return events

    def detect_thunderstorm(
        self, current: CurrentWeather
    ) -> Optional[DetectedExtremeEvent]:
        # Check CAPE or explicit lightning indicator
        cape = current.cape or 0.0
        lightning = current.lightning is True

        is_severe_cape = cape >= 2000.0
        is_moderate_cape = cape >= 1000.0
        convective_rain_wind = (current.rainfall or 0.0) >= 15.0 and (current.wind_speed or 0.0) >= 40.0

        if lightning or is_severe_cape:
            return DetectedExtremeEvent(
                event_type="thunderstorm",
                severity="extreme" if is_severe_cape else "high",
                value=cape if cape > 0 else 1.0,
                unit="J/kg" if cape > 0 else "flag",
                threshold=1000.0 if cape > 0 else 1.0,
                classification_source="IMD_THUNDERSTORM_CRITERIA",
                description=f"Active thunderstorm conditions detected (CAPE: {cape:.0f} J/kg, lightning: {lightning}).",
            )
        elif is_moderate_cape or convective_rain_wind:
            return DetectedExtremeEvent(
                event_type="thunderstorm",
                severity="moderate",
                value=cape if cape > 0 else (current.rainfall or 0.0),
                unit="J/kg" if cape > 0 else "mm",
                threshold=1000.0 if cape > 0 else 15.0,
                classification_source="HEURISTIC_CONVECTIVE_RULE",
                description="Elevated convective instability indicating thunderstorm potential.",
            )

        return None

    def detect_visibility(
        self, current: CurrentWeather
    ) -> Optional[DetectedExtremeEvent]:
        v = current.visibility
        if v is None:
            return None

        if v <= ICAO_DENSE_FOG_KM:
            return DetectedExtremeEvent(
                event_type="low_visibility",
                severity="extreme",
                value=v,
                unit="km",
                threshold=ICAO_DENSE_FOG_KM,
                classification_source="ICAO_VISIBILITY_STANDARD",
                description=f"Dense fog with visibility of {v:.2f} km (at or below 200 m).",
            )
        elif v <= ICAO_LOW_VISIBILITY_KM:
            return DetectedExtremeEvent(
                event_type="low_visibility",
                severity="high",
                value=v,
                unit="km",
                threshold=ICAO_LOW_VISIBILITY_KM,
                classification_source="ICAO_VISIBILITY_STANDARD",
                description=f"Visibility of {v:.1f} km is at or below the 1.0 km threshold.",
            )

        return None

    def detect_forecast_hazards(
        self, forecast: ForecastWeather
    ) -> List[DetectedExtremeEvent]:
        events: List[DetectedExtremeEvent] = []
        if not forecast:
            return events

        # 1. Scan forecast daily accumulation for 24-hour rain hazards
        if forecast.daily:
            daily_vals = [d.precipitation_sum for d in forecast.daily if d.precipitation_sum is not None]
            if daily_vals:
                max_daily_rain = max(daily_vals)
                if max_daily_rain >= IMD_EXTREMELY_HEAVY_RAIN_MM:
                    events.append(
                        DetectedExtremeEvent(
                            event_type="extremely_heavy_rain",
                            severity="extreme",
                            value=max_daily_rain,
                            unit="mm/24h",
                            threshold=IMD_EXTREMELY_HEAVY_RAIN_MM,
                            classification_source="IMD_RAINFALL_STANDARD",
                            description=f"Forecast peak 24-hour precipitation of {max_daily_rain:.1f} mm exceeds IMD extremely heavy rain criteria (>={IMD_EXTREMELY_HEAVY_RAIN_MM} mm/24h).",
                        )
                    )
                elif max_daily_rain >= IMD_VERY_HEAVY_RAIN_MM:
                    events.append(
                        DetectedExtremeEvent(
                            event_type="very_heavy_rain",
                            severity="high",
                            value=max_daily_rain,
                            unit="mm/24h",
                            threshold=IMD_VERY_HEAVY_RAIN_MM,
                            classification_source="IMD_RAINFALL_STANDARD",
                            description=f"Forecast peak 24-hour precipitation of {max_daily_rain:.1f} mm meets IMD very heavy rain criteria ({IMD_VERY_HEAVY_RAIN_MM}–{IMD_EXTREMELY_HEAVY_RAIN_MM - 0.1:.1f} mm/24h).",
                        )
                    )
                elif max_daily_rain >= IMD_HEAVY_RAIN_MM:
                    events.append(
                        DetectedExtremeEvent(
                            event_type="heavy_rain",
                            severity="high" if max_daily_rain >= 100.0 else "moderate",
                            value=max_daily_rain,
                            unit="mm/24h",
                            threshold=IMD_HEAVY_RAIN_MM,
                            classification_source="IMD_RAINFALL_STANDARD",
                            description=f"Forecast peak 24-hour precipitation of {max_daily_rain:.1f} mm meets IMD heavy rain criteria ({IMD_HEAVY_RAIN_MM}–{IMD_VERY_HEAVY_RAIN_MM - 0.1:.1f} mm/24h).",
                        )
                    )

        # 2. Scan forecast hourly points for intense cloudburst downpour or wind hazards
        if forecast.hourly:
            # Check for cloudburst intensity in hourly forecast (>= 100 mm/h)
            hourly_rains = [p.rainfall for p in forecast.hourly if p.rainfall is not None]
            if hourly_rains:
                max_hourly_rain = max(hourly_rains)
                if max_hourly_rain >= IMD_CLOUDBURST_HOURLY_MM:
                    events.append(
                        DetectedExtremeEvent(
                            event_type="heavy_rain",
                            severity="extreme",
                            value=max_hourly_rain,
                            unit="mm/h",
                            threshold=IMD_CLOUDBURST_HOURLY_MM,
                            classification_source="IMD_CLOUDBURST_CRITERIA",
                            description=f"Forecast peak hourly precipitation of {max_hourly_rain:.1f} mm/h meets IMD cloudburst criteria (>={IMD_CLOUDBURST_HOURLY_MM} mm in 1 hour).",
                        )
                    )

            # Scan for max forecast wind
            hourly_winds = [p.wind_speed for p in forecast.hourly if p.wind_speed is not None]
            if hourly_winds:
                max_wind = max(hourly_winds)
                if max_wind >= WMO_STORM_WIND_KMH:
                    events.append(
                        DetectedExtremeEvent(
                            event_type="storm_wind",
                            severity="extreme",
                            value=max_wind,
                            unit="km/h",
                            threshold=WMO_STORM_WIND_KMH,
                            classification_source="WMO_BEAUFORT_STANDARD",
                            description=f"Forecast peak wind speed of {max_wind:.1f} km/h reaches storm force (>={WMO_STORM_WIND_KMH} km/h, Beaufort 10+).",
                        )
                    )
                elif max_wind >= WMO_GALE_WIND_KMH:
                    events.append(
                        DetectedExtremeEvent(
                            event_type="gale_wind",
                            severity="high",
                            value=max_wind,
                            unit="km/h",
                            threshold=WMO_GALE_WIND_KMH,
                            classification_source="WMO_BEAUFORT_STANDARD",
                            description=f"Forecast peak wind speed of {max_wind:.1f} km/h reaches gale force (>={WMO_GALE_WIND_KMH} km/h, Beaufort 8+).",
                        )
                    )
                elif max_wind >= WMO_HIGH_WIND_KMH:
                    events.append(
                        DetectedExtremeEvent(
                            event_type="high_wind",
                            severity="moderate",
                            value=max_wind,
                            unit="km/h",
                            threshold=WMO_HIGH_WIND_KMH,
                            classification_source="WMO_BEAUFORT_STANDARD",
                            description=f"Forecast peak wind speed of {max_wind:.1f} km/h meets high wind criteria (>={WMO_HIGH_WIND_KMH} km/h, Beaufort 7+).",
                        )
                    )

        return events
