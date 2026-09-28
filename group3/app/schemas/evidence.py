"""
schemas/evidence.py
--------------------
Pydantic models for Phase 6: Evidence + Confidence.

These models are produced by EvidenceEngine and consumed by:
  - app/services/llm_service.py  (adds evidence block to LLM context)
  - tests/test_evidence.py

Confidence score (0–100) is always computed deterministically.
The LLM may READ these values as context — it must NOT modify them.

Score breakdown
---------------
  completeness_score  (0–40)  — how many important weather fields are present
  freshness_score     (0–30)  — how recent the observation is
  rule_certainty_score(0–30)  — how many hazard risks were fully assessed

  confidence = completeness_score + freshness_score + rule_certainty_score
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Type aliases                                                                 #
# --------------------------------------------------------------------------- #

EvidenceSource = Literal["weather", "risk", "impact", "advisory"]


# --------------------------------------------------------------------------- #
# EvidenceItem                                                                 #
# --------------------------------------------------------------------------- #

class EvidenceItem(BaseModel):
    """
    A single piece of structured evidence that supports the confidence score
    or explains the assessment.

    Every risk/advisory result that influenced the overall output must have
    at least one EvidenceItem so the assessment is fully traceable.
    """

    source: EvidenceSource = Field(
        ...,
        description="Which data layer produced this evidence.",
        examples=["risk"],
    )
    data: str = Field(
        ...,
        description="The specific data point that constitutes the evidence.",
        examples=["wind_speed = 85 km/h"],
    )
    reason: str = Field(
        ...,
        description="Human-readable explanation of why this data point is significant.",
        examples=["Wind speed exceeds the severe threshold."],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "source": "risk",
                "data": "wind_speed = 85 km/h",
                "reason": "Wind speed exceeds the severe threshold.",
            }
        }
    }


# --------------------------------------------------------------------------- #
# ConfidenceResult                                                             #
# --------------------------------------------------------------------------- #

class ConfidenceResult(BaseModel):
    """
    Deterministic evidence + confidence output from EvidenceEngine.

    The confidence score is broken into three transparent components so
    callers can understand exactly why confidence is high or reduced.

    Uncertainty strings explain specific gaps in the assessment.
    """

    confidence: int = Field(
        ...,
        ge=0,
        le=100,
        description=(
            "Overall confidence score 0–100. "
            "= completeness_score + freshness_score + rule_certainty_score."
        ),
        examples=[88],
    )
    evidence: list[EvidenceItem] = Field(
        default_factory=list,
        description=(
            "Ordered list of evidence items supporting the assessment. "
            "Items are ordered by source: weather → risk → impact → advisory."
        ),
    )
    uncertainty: list[str] = Field(
        default_factory=list,
        description=(
            "Human-readable descriptions of missing data or limitations. "
            "Empty when all inputs are present and fresh."
        ),
        examples=[["Visibility data unavailable"]],
    )
    completeness_score: int = Field(
        ...,
        ge=0,
        le=40,
        description=(
            "Data completeness component (0–40). "
            "7 pts each: temperature, rainfall, wind_speed, visibility. "
            "6 pts each: humidity, pressure."
        ),
        examples=[28],
    )
    freshness_score: int = Field(
        ...,
        ge=0,
        le=30,
        description=(
            "Data freshness component (0–30). "
            "30 → <30 min; 20 → 30–60 min; 10 → 1–2 h; 0 → >2 h."
        ),
        examples=[30],
    )
    rule_certainty_score: int = Field(
        ...,
        ge=0,
        le=30,
        description=(
            "Rule certainty component (0–30). "
            "10 pts for risk analysis present; "
            "5 pts each for rain, wind, heat, visibility hazards assessed."
        ),
        examples=[30],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "confidence": 88,
                "evidence": [
                    {
                        "source": "weather",
                        "data": "rainfall = 72 mm",
                        "reason": "Heavy rainfall detected.",
                    },
                    {
                        "source": "risk",
                        "data": "rain risk = 75",
                        "reason": "Rainfall falls in the severe band.",
                    },
                ],
                "uncertainty": [],
                "completeness_score": 28,
                "freshness_score": 30,
                "rule_certainty_score": 30,
            }
        }
    }
