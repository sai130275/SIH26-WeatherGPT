"""
api/routes/advisory.py
-----------------------
POST /advisory — Impact and advisory generation endpoint.

Flow
----
Group 2 (Node.js backend) sends:
  WeatherData  (raw observation)
  RiskAnalysis (from POST /risk)
        ↓
ImpactEngine.assess()   → list[ImpactResult]
        ↓
AdvisoryEngine.generate() → list[Advisory]
        ↓
AdvisoryResponse (impacts + advisories)

No risk re-calculation happens here — RiskAnalysis is trusted as-is.
No LLM, no external calls, no database.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.advisory import AdvisoryRequest, AdvisoryResponse
from app.services.advisory_engine import AdvisoryEngine
from app.services.impact_engine import ImpactEngine

router = APIRouter(tags=["Advisory"])

# Stateless singletons — safe to share across requests.
_impact_engine = ImpactEngine()
_advisory_engine = AdvisoryEngine()


@router.post(
    "/advisory",
    response_model=AdvisoryResponse,
    summary="Generate weather impact assessment and actionable advisories",
    description=(
        "Accepts a WeatherData observation and a pre-calculated RiskAnalysis "
        "(from POST /risk). Returns sector impacts (travel, outdoor, farming, general) "
        "and actionable advisories ordered by priority. "
        "All logic is deterministic and rule-based — no LLM, no ML."
    ),
)
async def advisory(request: AdvisoryRequest) -> AdvisoryResponse:
    """
    Run the full Phase 4 pipeline: Impact → Advisory.

    Parameters
    ----------
    request:
        AdvisoryRequest containing WeatherData and RiskAnalysis.

    Returns
    -------
    AdvisoryResponse:
        Sector impacts + actionable advisories for the weather observation.
    """
    impacts = _impact_engine.assess(request.weather, request.risk)
    advisories = _advisory_engine.generate(impacts)

    return AdvisoryResponse(
        location=request.weather.location,
        overall_risk_level=request.risk.overall_level,
        impacts=impacts,
        advisories=advisories,
    )
