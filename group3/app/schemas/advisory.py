"""
schemas/advisory.py
--------------------
Pydantic models for Phase 4: Impact + Advisory Engine.

Data flow:
  WeatherData + RiskAnalysis
       ↓
  ImpactEngine   → ImpactAnalysis  (list[ImpactResult])
       ↓
  AdvisoryEngine → AdvisoryAnalysis (list[Advisory])
       ↓
  POST /advisory response: AdvisoryResponse

Consumed by:
  - app/services/impact_engine.py
  - app/services/advisory_engine.py
  - app/api/routes/advisory.py
  - Group 2 Node.js backend
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.risk import RiskAnalysis
from app.schemas.weather import WeatherData


# --------------------------------------------------------------------------- #
# Shared literals                                                              #
# --------------------------------------------------------------------------- #

ImpactCategory = Literal["travel", "outdoor", "farming", "general"]

ImpactSeverity = Literal["LOW", "MODERATE", "HIGH", "SEVERE"]

AdvisoryPriority = Literal["LOW", "MODERATE", "HIGH", "SEVERE"]


# --------------------------------------------------------------------------- #
# Request                                                                      #
# --------------------------------------------------------------------------- #

class AdvisoryRequest(BaseModel):
    """
    Input payload for POST /advisory.

    Group 2 sends the raw weather observation alongside the already-calculated
    RiskAnalysis so the Impact/Advisory engines can use both without
    re-running the risk pipeline.
    """

    weather: WeatherData = Field(
        ...,
        description="Raw weather observation.",
    )
    risk: RiskAnalysis = Field(
        ...,
        description="Pre-calculated risk analysis from POST /risk.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "weather": {
                    "location": "Warangal",
                    "latitude": 17.9689,
                    "longitude": 79.5941,
                    "timestamp": "2026-09-28T10:00:00Z",
                    "temperature": 42.0,
                    "humidity": 90.0,
                    "rainfall": 72.0,
                    "wind_speed": 85.0,
                    "wind_direction": 240.0,
                    "pressure": 995.0,
                    "visibility": 0.5,
                    "forecast": [],
                },
                "risk": {
                    "risks": [
                        {
                            "type": "rain",
                            "score": 75,
                            "level": "SEVERE",
                            "reasons": ["Rainfall is in the 50–100 mm band."],
                        }
                    ],
                    "overall_score": 95,
                    "overall_level": "SEVERE",
                },
            }
        }
    }


# --------------------------------------------------------------------------- #
# ImpactResult                                                                 #
# --------------------------------------------------------------------------- #

class ImpactResult(BaseModel):
    """
    A single sector impact derived from weather + risk data.

    Every impact must carry a reason string so the result is fully
    transparent and auditable.
    """

    type: ImpactCategory = Field(
        ...,
        description="The affected sector.",
        examples=["travel"],
    )
    severity: ImpactSeverity = Field(
        ...,
        description="Impact severity level.",
        examples=["HIGH"],
    )
    reason: str = Field(
        ...,
        description="Human-readable explanation for this impact assessment.",
        examples=["Heavy rain and poor visibility may affect road travel."],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "type": "travel",
                "severity": "HIGH",
                "reason": "Heavy rain and poor visibility may affect road travel.",
            }
        }
    }


# --------------------------------------------------------------------------- #
# ImpactAnalysis                                                               #
# --------------------------------------------------------------------------- #

class ImpactAnalysis(BaseModel):
    """Collection of sector impacts for a weather observation."""

    impacts: list[ImpactResult] = Field(
        default_factory=list,
        description=(
            "Per-category impact results. "
            "Only categories with relevant hazards are included."
        ),
    )


# --------------------------------------------------------------------------- #
# Advisory                                                                     #
# --------------------------------------------------------------------------- #

class Advisory(BaseModel):
    """
    A single actionable advisory for one impact category.

    Advisories are ordered by priority (highest first) in AdvisoryAnalysis.
    """

    category: ImpactCategory = Field(
        ...,
        description="The sector this advisory addresses.",
        examples=["travel"],
    )
    priority: AdvisoryPriority = Field(
        ...,
        description="Advisory priority — mirrors impact severity.",
        examples=["HIGH"],
    )
    message: str = Field(
        ...,
        description="Actionable advisory message addressed to the public.",
        examples=["Avoid unnecessary travel during the heavy-rain period."],
    )
    reason: str = Field(
        ...,
        description="Evidence basis for this advisory.",
        examples=["Heavy rain and visibility below 1 km."],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "category": "travel",
                "priority": "HIGH",
                "message": "Avoid unnecessary travel during the heavy-rain period.",
                "reason": "Heavy rain and visibility below 1 km.",
            }
        }
    }


# --------------------------------------------------------------------------- #
# AdvisoryAnalysis                                                             #
# --------------------------------------------------------------------------- #

class AdvisoryAnalysis(BaseModel):
    """Ordered list of actionable advisories, highest priority first."""

    advisories: list[Advisory] = Field(
        default_factory=list,
        description=(
            "Actionable advisories ordered by priority (SEVERE → HIGH → MODERATE → LOW). "
            "Empty when overall risk is LOW and no significant impacts are detected."
        ),
    )


# --------------------------------------------------------------------------- #
# AdvisoryResponse (API response)                                              #
# --------------------------------------------------------------------------- #

_PRIORITY_ORDER = {"SEVERE": 0, "HIGH": 1, "MODERATE": 2, "LOW": 3}


class AdvisoryResponse(BaseModel):
    """
    Combined response from POST /advisory.

    Contains both the intermediate impact analysis and the final advisories
    so Group 2 can display either level of detail in the app.
    """

    location: str = Field(..., description="Location name from the input WeatherData.")
    overall_risk_level: str = Field(..., description="Overall risk level from the input RiskAnalysis.")
    impacts: list[ImpactResult] = Field(
        default_factory=list,
        description="Sector impacts derived from weather + risk data.",
    )
    advisories: list[Advisory] = Field(
        default_factory=list,
        description="Actionable advisories ordered by priority (SEVERE first).",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "location": "Warangal",
                "overall_risk_level": "SEVERE",
                "impacts": [
                    {
                        "type": "travel",
                        "severity": "HIGH",
                        "reason": "Heavy rain and poor visibility may affect road travel.",
                    }
                ],
                "advisories": [
                    {
                        "category": "travel",
                        "priority": "HIGH",
                        "message": "Avoid unnecessary travel during the heavy-rain period.",
                        "reason": "Heavy rain and visibility below 1 km.",
                    }
                ],
            }
        }
    }
