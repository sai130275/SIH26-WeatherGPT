"""
schemas/risk.py
---------------
Pydantic models for the Phase 3 risk engine output.

Consumed by:
  - app/services/risk_engine.py  (produces these models)
  - app/api/routes/risk.py       (returns RiskAnalysis in HTTP response)
  - Group 2 Node.js backend      (consumes RiskAnalysis via JSON)

Score range: 0–100  (int, clamped at boundaries)
Level mapping:
  0–24    → LOW
  25–49   → MODERATE
  50–74   → HIGH
  75–100  → SEVERE
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


# --------------------------------------------------------------------------- #
# Type aliases                                                                 #
# --------------------------------------------------------------------------- #

RiskLevel = Literal["LOW", "MODERATE", "HIGH", "SEVERE"]

RiskType = Literal["rain", "flood", "heat", "wind", "visibility", "overall"]


# --------------------------------------------------------------------------- #
# Pure helper: score → level                                                   #
# --------------------------------------------------------------------------- #

def score_to_level(score: int) -> RiskLevel:
    """
    Convert a 0–100 integer risk score to its corresponding level label.

    Bands
    -----
    0–24    → LOW
    25–49   → MODERATE
    50–74   → HIGH
    75–100  → SEVERE

    Parameters
    ----------
    score:
        Integer in [0, 100]. Values outside this range are clamped silently.
    """
    clamped = max(0, min(100, score))
    if clamped <= 24:
        return "LOW"
    if clamped <= 49:
        return "MODERATE"
    if clamped <= 74:
        return "HIGH"
    return "SEVERE"


# --------------------------------------------------------------------------- #
# RiskResult                                                                   #
# --------------------------------------------------------------------------- #

class RiskResult(BaseModel):
    """
    Risk assessment for a single hazard type.

    Every score is backed by at least one reason so the result is fully
    transparent and auditable without access to source code.
    """

    type: RiskType = Field(
        ...,
        description="Hazard category.",
        examples=["rain"],
    )
    score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Risk score 0–100.",
        examples=[75],
    )
    level: RiskLevel = Field(
        ...,
        description="Risk level derived from the score.",
        examples=["SEVERE"],
    )
    reasons: list[str] = Field(
        ...,
        min_length=1,
        description=(
            "Ordered list of human-readable explanations for the score. "
            "Always contains at least one entry."
        ),
        examples=[["Rainfall of 72 mm falls in the 50–100 mm band (score 75)."]],
    )

    @field_validator("score")
    @classmethod
    def score_matches_level(cls, v: int) -> int:
        """score is stored as-is; level must be set consistently by the engine."""
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "type": "rain",
                "score": 75,
                "level": "SEVERE",
                "reasons": ["Rainfall of 72 mm falls in the 50–100 mm band (score 75)."],
            }
        }
    }


# --------------------------------------------------------------------------- #
# RiskAnalysis                                                                 #
# --------------------------------------------------------------------------- #

class RiskAnalysis(BaseModel):
    """
    Complete risk analysis for a weather observation.

    Returned by POST /risk.  Contains per-hazard results and the
    aggregate overall score.
    """

    risks: list[RiskResult] = Field(
        ...,
        description="Per-hazard risk results. Only hazards with available data are included.",
    )
    overall_score: int = Field(
        ...,
        ge=0,
        le=100,
        description=(
            "Overall risk score (0–100). "
            "Equal to max(hazard scores) + 10 if 2+ hazards are HIGH or above, capped at 100."
        ),
        examples=[75],
    )
    overall_level: RiskLevel = Field(
        ...,
        description="Risk level derived from overall_score.",
        examples=["SEVERE"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "risks": [
                    {
                        "type": "rain",
                        "score": 75,
                        "level": "SEVERE",
                        "reasons": ["Rainfall of 72 mm falls in the 50–100 mm band (score 75)."],
                    }
                ],
                "overall_score": 75,
                "overall_level": "SEVERE",
            }
        }
    }
