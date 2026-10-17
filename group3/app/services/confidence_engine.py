"""
services/confidence_engine.py
-----------------------------
Explainable, deterministic confidence calculation engine (Module 1.2).

Computes confidence score based on measurable inputs:
  - Completeness of observations
  - Freshness of data
  - Provider agreement / conflict resolution
  - Forecast horizon decay
  - Critical missing field penalties

No arbitrary or LLM-invented scores. Every point is transparently accounted for.
"""

from __future__ import annotations

from typing import List, Optional

from app.schemas.intelligence import (
    ConfidenceAssessment,
    ConfidenceBreakdown,
    DataQualityReport,
)
from app.schemas.unified_weather import CurrentWeather, ForecastWeather


class ExplainableConfidenceEngine:
    """
    Stateless confidence evaluation service.
    """

    def compute(
        self,
        quality: DataQualityReport,
        weather: CurrentWeather,
        forecast: Optional[ForecastWeather] = None,
        forecast_days: int = 1,
    ) -> ConfidenceAssessment:
        uncertainties: List[str] = []

        # 1. Completeness points (0 to 40)
        completeness_pts = quality.completeness_score
        if completeness_pts < 40:
            missing_core = [
                f for f in ["temperature", "rainfall", "wind_speed", "humidity", "pressure", "visibility"]
                if f in quality.missing_fields
            ]
            if missing_core:
                uncertainties.append(f"Missing core variables: {', '.join(missing_core)}.")

        # 2. Freshness points (0 to 30)
        freshness_pts = quality.freshness_score
        if quality.age_seconds > 7200:
            uncertainties.append(
                f"Observation is stale ({quality.age_seconds / 3600:.1f} hours old)."
            )
        elif quality.age_seconds > 3600:
            uncertainties.append("Observation is between 1 and 2 hours old.")

        # 3. Provider agreement points (0 to 20)
        provider_agreement_pts = 20
        if quality.conflicting_fields:
            penalty = min(20, len(quality.conflicting_fields) * 5)
            provider_agreement_pts -= penalty
            conflict_names = [c.field_name for c in quality.conflicting_fields]
            uncertainties.append(f"Discrepancies observed across providers in: {', '.join(conflict_names)}.")

        # 4. Forecast horizon penalty (0 to 20)
        # Horizon decay: confidence decreases as forecast extends into the future
        horizon_penalty = 0
        if forecast:
            horizon_hours = len(forecast.hourly) if forecast.hourly else forecast_days * 24
            if horizon_hours > 120:     # > 5 days
                horizon_penalty = 12
                uncertainties.append("Long-range forecast (>5 days) introduces meteorological divergence.")
            elif horizon_hours > 72:    # > 3 days
                horizon_penalty = 7
                uncertainties.append("Medium-range forecast (3-5 days) has moderate uncertainty.")
            elif horizon_hours > 24:    # > 1 day
                horizon_penalty = 3

        # 5. Critical missing penalty
        critical_penalty = 0
        if weather.temperature is None:
            critical_penalty += 15
            uncertainties.append("Critical field 'temperature' is absent.")
        if weather.rainfall is None:
            critical_penalty += 10
            uncertainties.append("Critical field 'rainfall' is absent.")

        # Composite score
        total_score = (
            completeness_pts
            + freshness_pts
            + provider_agreement_pts
            - horizon_penalty
            - critical_penalty
        )
        final_score = max(0, min(100, total_score))

        breakdown = ConfidenceBreakdown(
            completeness_points=completeness_pts,
            freshness_points=freshness_pts,
            provider_agreement_points=provider_agreement_pts,
            horizon_penalty=horizon_penalty,
            critical_missing_penalty=critical_penalty,
        )

        return ConfidenceAssessment(
            confidence_score=final_score,
            breakdown=breakdown,
            uncertainties=uncertainties,
        )
