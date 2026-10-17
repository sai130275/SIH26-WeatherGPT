"""
services/forecast_intelligence.py
---------------------------------
Temporal intelligence engine analyzing multi-day and hourly weather forecasts.

Extracts:
  - Rain onset (earliest occurrence and time delta from observation)
  - Rain duration & accumulated volume
  - Peak rainfall period (start, end, rate, accumulation)
  - Heavy rainfall interval detection
  - Diurnal temperature dynamics & swings
  - Wind trends & gust spikes
  - Rapid atmospheric changes (sharp temperature drops, squalls)
  - Multi-day forecast consistency
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from app.schemas.intelligence import (
    ForecastIntelligence,
    PeakRainPeriod,
    RapidWeatherChange,
    TemperatureDynamics,
)
from app.schemas.unified_weather import ForecastPoint, ForecastWeather
from app.services.weather_trend import WeatherTrendEngine


class ForecastIntelligenceEngine:
    """
    Stateless forecast intelligence analyzer.
    """

    def __init__(self, trend_engine: Optional[WeatherTrendEngine] = None) -> None:
        self.trend_engine = trend_engine or WeatherTrendEngine()

    def analyze(
        self,
        forecast: ForecastWeather,
        base_time: Optional[datetime] = None,
        heavy_rain_threshold: float = 15.0,
    ) -> ForecastIntelligence:
        """
        Analyze a ForecastWeather object and return structured temporal intelligence.
        """
        hourly = forecast.hourly or []
        if not hourly:
            return ForecastIntelligence(
                horizon_hours=0,
                rain_expected=False,
                total_rain_duration_hours=0.0,
                total_precipitation_expected_mm=0.0,
                heavy_rain_intervals_count=0,
                forecast_consistency="no_data",
            )

        ref_time = base_time or hourly[0].timestamp
        if ref_time.tzinfo is None:
            ref_time = ref_time.replace(tzinfo=timezone.utc)

        horizon_hours = len(hourly)

        # 1. Rain Analysis
        rain_points = [p for p in hourly if p.rainfall is not None and p.rainfall >= 0.1]
        rain_expected = len(rain_points) > 0

        rain_onset: Optional[datetime] = None
        rain_onset_hours: Optional[float] = None
        total_duration_hours = float(len(rain_points))
        total_precip_mm = round(sum(p.rainfall for p in hourly if p.rainfall is not None), 1)

        if rain_expected:
            first_rain = rain_points[0]
            rain_onset = first_rain.timestamp
            delta_sec = max(0.0, (rain_onset - ref_time).total_seconds())
            rain_onset_hours = round(delta_sec / 3600.0, 1)

        # 2. Peak Rain Window
        peak_period = self._detect_peak_rain_period(hourly)

        # 3. Heavy Rain Intervals
        heavy_intervals = sum(
            1 for p in hourly if p.rainfall is not None and p.rainfall >= heavy_rain_threshold
        )

        # 4. Temperature Dynamics
        temps = [p.temperature for p in hourly if p.temperature is not None]
        temp_dynamics: Optional[TemperatureDynamics] = None
        if temps:
            min_t = min(temps)
            max_t = max(temps)
            swing = round(max_t - min_t, 1)
            temp_trend_state = "stable"
            if len(temps) >= 4:
                first_half_avg = sum(temps[:len(temps)//2]) / (len(temps)//2)
                second_half_avg = sum(temps[len(temps)//2:]) / (len(temps) - len(temps)//2)
                if second_half_avg - first_half_avg >= 1.5:
                    temp_trend_state = "increasing"
                elif first_half_avg - second_half_avg >= 1.5:
                    temp_trend_state = "decreasing"

            temp_dynamics = TemperatureDynamics(
                min_temp=min_t,
                max_temp=max_t,
                diurnal_swing=swing,
                trend=temp_trend_state,
            )

        # 5. Wind Trends
        wind_trend = self.trend_engine.analyze_trends_from_forecast(hourly, max_hours=24).wind

        # 6. Rapid Weather Changes
        rapid_changes = self._detect_rapid_changes(hourly)

        # 7. Consistency
        consistency = "consistent" if len(hourly) > 0 else "insufficient_data"
        if heavy_intervals > 4 or len(rapid_changes) > 1:
            consistency = "volatile"

        return ForecastIntelligence(
            horizon_hours=horizon_hours,
            rain_expected=rain_expected,
            rain_onset=rain_onset,
            rain_onset_hours_from_now=rain_onset_hours,
            total_rain_duration_hours=total_duration_hours,
            total_precipitation_expected_mm=total_precip_mm,
            peak_rain_period=peak_period,
            heavy_rain_intervals_count=heavy_intervals,
            temperature_dynamics=temp_dynamics,
            wind_trend=wind_trend,
            rapid_changes=rapid_changes,
            forecast_consistency=consistency,
        )

    def _detect_peak_rain_period(
        self, hourly: List[ForecastPoint]
    ) -> Optional[PeakRainPeriod]:
        if not hourly:
            return None

        # Find maximum rainfall point
        max_pt: Optional[ForecastPoint] = None
        max_rate = 0.0
        for pt in hourly:
            if pt.rainfall is not None and pt.rainfall > max_rate:
                max_rate = pt.rainfall
                max_pt = pt

        if max_pt is None or max_rate < 0.2:
            return None

        # Expand window around max point to find contiguous rain
        idx = hourly.index(max_pt)
        start_idx = idx
        while start_idx > 0 and (hourly[start_idx - 1].rainfall or 0.0) >= 0.5:
            start_idx -= 1

        end_idx = idx
        while end_idx < len(hourly) - 1 and (hourly[end_idx + 1].rainfall or 0.0) >= 0.5:
            end_idx += 1

        accum = sum((hourly[i].rainfall or 0.0) for i in range(start_idx, end_idx + 1))

        return PeakRainPeriod(
            start=hourly[start_idx].timestamp,
            end=hourly[end_idx].timestamp,
            peak_rate_mm_h=round(max_rate, 1),
            accumulated_mm=round(accum, 1),
        )

    def _detect_rapid_changes(
        self, hourly: List[ForecastPoint]
    ) -> List[RapidWeatherChange]:
        changes: List[RapidWeatherChange] = []
        if len(hourly) < 4:
            return changes

        # Check sliding 3-hour windows
        for i in range(len(hourly) - 3):
            p1 = hourly[i]
            p3 = hourly[i + 3]

            # Rapid temperature drop (e.g. cold front > 5°C in 3h)
            if p1.temperature is not None and p3.temperature is not None:
                temp_delta = p3.temperature - p1.temperature
                if abs(temp_delta) >= 5.0:
                    verb = "drop" if temp_delta < 0 else "spike"
                    changes.append(
                        RapidWeatherChange(
                            metric="temperature",
                            start_time=p1.timestamp,
                            end_time=p3.timestamp,
                            magnitude=round(temp_delta, 1),
                            description=f"Rapid temperature {verb} of {abs(temp_delta):.1f}°C in 3 hours.",
                        )
                    )

            # Rapid wind surge (> 20 km/h jump)
            if p1.wind_speed is not None and p3.wind_speed is not None:
                wind_delta = p3.wind_speed - p1.wind_speed
                if wind_delta >= 20.0:
                    changes.append(
                        RapidWeatherChange(
                            metric="wind_speed",
                            start_time=p1.timestamp,
                            end_time=p3.timestamp,
                            magnitude=round(wind_delta, 1),
                            description=f"Sudden wind surge of +{wind_delta:.1f} km/h in 3 hours.",
                        )
                    )

        # De-duplicate contiguous windows for the same metric
        unique_changes: List[RapidWeatherChange] = []
        seen_metrics: set[str] = set()
        for ch in changes:
            if ch.metric not in seen_metrics:
                unique_changes.append(ch)
                seen_metrics.add(ch.metric)

        return unique_changes
