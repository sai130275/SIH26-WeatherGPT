"""
api/routes/risk.py
-------------------
POST /risk — Risk analysis endpoint.

Flow
----
1. Receive WeatherData payload.
2. Run Phase 2 condition detection (WeatherProcessor + ConditionDetector).
3. Pass WeatherData + detected conditions to Phase 3 RiskEngine.
4. Return RiskAnalysis.

The endpoint encapsulates the entire Phase 2 → Phase 3 pipeline so
Group 2 (Node.js backend) only needs to POST raw WeatherData and
receives a fully scored risk assessment in one call.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.risk import RiskAnalysis
from app.schemas.weather import WeatherData
from app.services.condition_detector import ConditionDetector
from app.services.risk_engine import RiskEngine
from app.services.weather_processor import WeatherProcessor

router = APIRouter(tags=["Risk"])

# Stateless singletons — safe to share across requests.
_processor = WeatherProcessor()
_detector = ConditionDetector()
_engine = RiskEngine()


@router.post(
    "/risk",
    response_model=RiskAnalysis,
    summary="Calculate weather risk scores",
    description=(
        "Accepts a WeatherData payload and returns a RiskAnalysis containing "
        "per-hazard risk scores (rain, wind, heat, visibility, flood) and an "
        "overall score, each with human-readable reasons. "
        "All scoring is deterministic and rule-based — no ML, no LLM. "
        "Missing optional fields are skipped rather than invented."
    ),
)
async def risk_analysis(data: WeatherData) -> RiskAnalysis:
    """
    Run the full Phase 2 → Phase 3 pipeline on a weather observation.

    Parameters
    ----------
    data:
        WeatherData payload from Group 2 (Node.js backend) or any caller.

    Returns
    -------
    RiskAnalysis:
        Per-hazard and overall risk scores with explanations.
    """
    # Phase 2: process + detect conditions
    processed = _processor.process(data)
    conditions = _detector.detect_all(processed)

    # Phase 3: score risks
    return _engine.analyse(data, conditions)
