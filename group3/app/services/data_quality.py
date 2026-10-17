"""
services/data_quality.py
------------------------
Structured data quality evaluation engine (Module 1.2).

Assesses:
  - Observation freshness (age in seconds, degradation over time)
  - Data completeness (presence of essential meteorological variables)
  - Missing fields tracking (without silent masking)
  - Conflicting fields manifest (from multi-provider comparison)
  - Composite normalized quality score (0.0 to 1.0)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from app.schemas.intelligence import ConflictingField, DataQualityReport
from app.schemas.unified_weather import CURRENT_WEATHER_OPTIONAL_FIELDS, CurrentWeather


# Weight table for completeness (sums to 40)
_FIELD_WEIGHTS = {
    "temperature": 7,
    "rainfall": 7,
    "wind_speed": 7,
    "visibility": 7,
    "humidity": 6,
    "pressure": 6,
}


class DataQualityEngine:
    """
    Stateless data quality evaluation service.
    """

    def evaluate(
        self,
        weather: CurrentWeather,
        conflicting_fields: Optional[List[ConflictingField]] = None,
        reference_time: Optional[datetime] = None,
    ) -> DataQualityReport:
        conflicts = conflicting_fields or []
        now = reference_time or datetime.now(tz=timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        obs_time = weather.timestamp
        if obs_time.tzinfo is None:
            obs_time = obs_time.replace(tzinfo=timezone.utc)

        age_seconds = max(0.0, (now - obs_time).total_seconds())

        # 1. Freshness score (0 to 30)
        freshness_score = 0
        if age_seconds <= 1800:       # < 30 min
            freshness_score = 30
        elif age_seconds <= 3600:     # < 1 hour
            freshness_score = 20
        elif age_seconds <= 7200:     # < 2 hours
            freshness_score = 10
        else:
            freshness_score = 0

        # 2. Completeness score (0 to 40)
        completeness_score = 0
        for field_name, pts in _FIELD_WEIGHTS.items():
            if getattr(weather, field_name, None) is not None:
                completeness_score += pts

        # Track missing fields
        missing: List[str] = []
        for f in CURRENT_WEATHER_OPTIONAL_FIELDS:
            if getattr(weather, f, None) is None:
                missing.append(f)

        avail_count = len(CURRENT_WEATHER_OPTIONAL_FIELDS) - len(missing)

        # 3. Overall composite quality score (0.0 to 1.0)
        # Completeness contributes 55%, Freshness 45%
        raw_score = (completeness_score / 40.0 * 0.55) + (freshness_score / 30.0 * 0.45)
        # Deduct 0.05 per conflict detected
        raw_score -= len(conflicts) * 0.05
        quality_score = round(max(0.0, min(1.0, raw_score)), 2)

        return DataQualityReport(
            quality_score=quality_score,
            completeness_score=completeness_score,
            freshness_score=freshness_score,
            age_seconds=round(age_seconds, 1),
            available_fields_count=avail_count,
            missing_fields=missing,
            conflicting_fields=conflicts,
            providers=[weather.provider],
        )
