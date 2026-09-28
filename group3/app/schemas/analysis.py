"""
schemas/analysis.py
-------------------
Pydantic models for weather condition detection and analysis results.

These models are used by:
  - app/services/condition_detector.py  (produces DetectedCondition)
  - app/api/routes/analyze.py           (returns WeatherAnalysis)
  - Group 2 backend                     (consumes WeatherAnalysis via JSON)
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Severity and condition-type literals                                         #
# --------------------------------------------------------------------------- #

SeverityLevel = Literal["low", "moderate", "high", "extreme"]

ConditionType = Literal[
    "heavy_rain",
    "high_wind",
    "extreme_heat",
    "low_visibility",
]


# --------------------------------------------------------------------------- #
# DetectedCondition                                                            #
# --------------------------------------------------------------------------- #

class DetectedCondition(BaseModel):
    """
    A single weather hazard detected by the condition detector.

    Severity bands (general guidance — each detector may calibrate differently):
      low      → slightly above / below threshold
      moderate → noticeably above / below threshold
      high     → significantly above / below threshold
      extreme  → dangerously above / below threshold
    """

    type: ConditionType = Field(
        ...,
        description="Machine-readable condition identifier.",
        examples=["heavy_rain"],
    )
    severity: SeverityLevel = Field(
        ...,
        description="Severity level of the detected condition.",
        examples=["high"],
    )
    value: float = Field(
        ...,
        description="Observed meteorological value that triggered the condition.",
        examples=[72.0],
    )
    unit: str = Field(
        ...,
        description="Unit of the observed value.",
        examples=["mm"],
    )
    threshold: float = Field(
        ...,
        description="Configured threshold that was breached.",
        examples=[50.0],
    )
    reason: str = Field(
        ...,
        description="Human-readable explanation of why the condition was triggered.",
        examples=["Rainfall of 72.0 mm exceeds the configured heavy-rain threshold of 50.0 mm."],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "type": "heavy_rain",
                "severity": "high",
                "value": 72.0,
                "unit": "mm",
                "threshold": 50.0,
                "reason": "Rainfall of 72.0 mm exceeds the configured heavy-rain threshold of 50.0 mm.",
            }
        }
    }


# --------------------------------------------------------------------------- #
# WeatherAnalysis                                                              #
# --------------------------------------------------------------------------- #

class WeatherAnalysis(BaseModel):
    """
    Complete analysis result returned by POST /analyze.

    Contains all detected conditions plus metadata about which fields were
    present in the input payload (useful for Group 2 to audit data quality).
    """

    location: str = Field(
        ...,
        description="Location name from the input WeatherData.",
        examples=["Warangal"],
    )
    latitude: float = Field(..., examples=[17.9689])
    longitude: float = Field(..., examples=[79.5941])
    timestamp: datetime = Field(
        ...,
        description="Observation timestamp from the input WeatherData (UTC).",
    )
    processed_at: datetime = Field(
        ...,
        description="UTC timestamp when this analysis was produced.",
    )
    conditions: list[DetectedCondition] = Field(
        default_factory=list,
        description=(
            "List of detected weather hazard conditions. "
            "Empty list means no conditions were triggered."
        ),
    )
    available_fields: list[str] = Field(
        default_factory=list,
        description="Meteorological fields that were present (non-null) in the input.",
    )
    missing_fields: list[str] = Field(
        default_factory=list,
        description=(
            "Meteorological fields that were absent (null) in the input. "
            "Detectors for missing fields are skipped — no values are invented."
        ),
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "location": "Warangal",
                "latitude": 17.9689,
                "longitude": 79.5941,
                "timestamp": "2026-09-28T10:00:00Z",
                "processed_at": "2026-09-28T10:00:05Z",
                "conditions": [
                    {
                        "type": "heavy_rain",
                        "severity": "high",
                        "value": 72.0,
                        "unit": "mm",
                        "threshold": 50.0,
                        "reason": "Rainfall of 72.0 mm exceeds the configured heavy-rain threshold of 50.0 mm.",
                    }
                ],
                "available_fields": ["temperature", "rainfall", "wind_speed"],
                "missing_fields": ["humidity", "pressure", "visibility", "wind_direction", "forecast"],
            }
        }
    }
