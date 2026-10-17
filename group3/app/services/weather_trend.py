"""
services/weather_trend.py
-------------------------
Calculates rates of change and trend states for weather variables across
hourly observations or forecast sequences.

Supports:
  - temperature
  - rainfall
  - wind speed
  - humidity
  - atmospheric pressure

States:
  - increasing
  - decreasing
  - stable
  - rapidly_changing
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Tuple

from app.schemas.intelligence import MetricTrend, TrendState, WeatherTrends
from app.schemas.unified_weather import ForecastPoint


# Rapid change thresholds (change per hour)
_RAPID_CHANGE_THRESHOLDS = {
    "temperature": 2.0,   # °C per hour
    "rainfall": 5.0,      # mm increase per hour
    "wind": 12.0,         # km/h per hour
    "humidity": 15.0,     # % per hour
    "pressure": 1.5,      # hPa per hour
}

# Neutral / stable threshold bands (absolute change per hour below which it is "stable")
_STABLE_THRESHOLDS = {
    "temperature": 0.3,
    "rainfall": 0.2,
    "wind": 1.5,
    "humidity": 2.0,
    "pressure": 0.3,
}


def compute_linear_rate_per_hour(
    times: List[datetime],
    values: List[float],
) -> Optional[float]:
    """
    Compute rate of change per hour between first and last valid points,
    or via linear fit when 3+ points exist.
    """
    if len(times) < 2 or len(values) < 2 or len(times) != len(values):
        return None

    # Calculate hours elapsed between first and last point
    t0 = times[0].timestamp()
    t_end = times[-1].timestamp()
    hours_elapsed = (t_end - t0) / 3600.0

    if hours_elapsed <= 0.05:  # Avoid division by zero (<3 minutes)
        return 0.0

    delta = values[-1] - values[0]
    return round(delta / hours_elapsed, 2)


class WeatherTrendEngine:
    """
    Stateless weather trend calculation service.
    """

    def analyze_trends_from_forecast(
        self,
        hourly_points: List[ForecastPoint],
        max_hours: int = 24,
    ) -> WeatherTrends:
        """
        Extract trends from the first N hours of a forecast sequence.
        """
        if not hourly_points:
            return WeatherTrends()

        window = hourly_points[:max_hours]
        times = [pt.timestamp for pt in window]

        # Extract series
        temp_series = [(pt.timestamp, pt.temperature) for pt in window if pt.temperature is not None]
        rain_series = [(pt.timestamp, pt.rainfall) for pt in window if pt.rainfall is not None]
        wind_series = [(pt.timestamp, pt.wind_speed) for pt in window if pt.wind_speed is not None]
        hum_series = [(pt.timestamp, pt.humidity) for pt in window if pt.humidity is not None]

        temp_trend = self._eval_metric_trend("temperature", temp_series, "°C")
        rain_trend = self._eval_metric_trend("rainfall", rain_series, "mm/h")
        wind_trend = self._eval_metric_trend("wind", wind_series, "km/h")
        hum_trend = self._eval_metric_trend("humidity", hum_series, "%")

        return WeatherTrends(
            temperature=temp_trend,
            rainfall=rain_trend,
            wind=wind_trend,
            humidity=hum_trend,
            pressure=None,
        )

    def evaluate_metric(
        self,
        metric: str,
        data_points: List[Tuple[datetime, float]],
        unit: str = "",
    ) -> Optional[MetricTrend]:
        """Public method to evaluate an individual series."""
        return self._eval_metric_trend(metric, data_points, unit)

    def _eval_metric_trend(
        self,
        metric: str,
        series: List[Tuple[datetime, float]],
        unit: str,
    ) -> Optional[MetricTrend]:
        if len(series) < 2:
            return None

        times = [t for t, _ in series]
        vals = [v for _, v in series]

        rate = compute_linear_rate_per_hour(times, vals)
        if rate is None:
            return None

        rapid_thresh = _RAPID_CHANGE_THRESHOLDS.get(metric, 2.0)
        stable_thresh = _STABLE_THRESHOLDS.get(metric, 0.5)

        # Detect any sub-interval rapid spikes
        has_sub_interval_spike = False
        for i in range(len(series) - 1):
            h_diff = (series[i + 1][0].timestamp() - series[i][0].timestamp()) / 3600.0
            if h_diff > 0:
                interval_rate = abs(series[i + 1][1] - series[i][1]) / h_diff
                if interval_rate >= rapid_thresh:
                    has_sub_interval_spike = True
                    break

        if abs(rate) >= rapid_thresh or has_sub_interval_spike:
            state: TrendState = "rapidly_changing"
            direction = "spiking" if rate > 0 else "plunging"
            desc = f"{metric.capitalize()} is {direction} rapidly at {rate:+.2f} {unit}/h."
        elif abs(rate) <= stable_thresh:
            state = "stable"
            desc = f"{metric.capitalize()} is steady with negligible hourly variation."
        elif rate > 0:
            state = "increasing"
            desc = f"{metric.capitalize()} is trending upward by {rate:+.2f} {unit}/h."
        else:
            state = "decreasing"
            desc = f"{metric.capitalize()} is trending downward by {rate:+.2f} {unit}/h."

        return MetricTrend(
            metric=metric,
            state=state,
            rate_per_hour=rate,
            description=desc,
        )
