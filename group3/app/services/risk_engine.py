"""
services/risk_engine.py
------------------------
Orchestrates the Phase 3 risk scoring pipeline.

Responsibilities
----------------
1. Accept WeatherData and a list of DetectedCondition (from Phase 2).
2. Calculate each applicable hazard risk via risk_rules functions.
3. Skip calculations when the required meteorological field is None
   (no value invention).
4. Build RiskResult objects with score, level, and reasons.
5. Calculate the overall risk score.
6. Return a RiskAnalysis.

The engine is stateless — safe to share across requests.
"""

from __future__ import annotations

from typing import Optional

from app.schemas.analysis import DetectedCondition
from app.schemas.risk import RiskAnalysis, RiskResult, RiskType, score_to_level
from app.schemas.weather import WeatherData
from app.services import risk_rules


# --------------------------------------------------------------------------- #
# Internal helpers                                                             #
# --------------------------------------------------------------------------- #

def _build_result(
    risk_type: RiskType,
    score: int,
    reasons: list[str],
) -> RiskResult:
    """Construct a RiskResult, deriving the level from the score."""
    return RiskResult(
        type=risk_type,
        score=score,
        level=score_to_level(score),
        reasons=reasons,
    )


# --------------------------------------------------------------------------- #
# RiskEngine                                                                   #
# --------------------------------------------------------------------------- #

class RiskEngine:
    """
    Stateless risk engine.

    Usage
    -----
    >>> engine = RiskEngine()
    >>> analysis = engine.analyse(weather_data, detected_conditions)

    Adding a new hazard
    -------------------
    1. Add a pure scoring function to risk_rules.py.
    2. Call it inside analyse() and append to `results`.
    3. Include the hazard score in `hazard_scores` for overall calculation.
    """

    def analyse(
        self,
        data: WeatherData,
        conditions: list[DetectedCondition],
    ) -> RiskAnalysis:
        """
        Run the full risk-scoring pipeline.

        Parameters
        ----------
        data:
            Validated WeatherData from the API layer.
        conditions:
            Detected weather conditions from Phase 2 ConditionDetector.

        Returns
        -------
        RiskAnalysis:
            Per-hazard risks and overall risk with full score explanations.
        """
        results: list[RiskResult] = []
        hazard_scores: list[int] = []

        # ------------------------------------------------------------------ #
        # Rain risk                                                            #
        # ------------------------------------------------------------------ #
        if data.rainfall is not None:
            score, reasons = risk_rules.rain_risk(data.rainfall)
            results.append(_build_result("rain", score, reasons))
            hazard_scores.append(score)

        # ------------------------------------------------------------------ #
        # Wind risk                                                            #
        # ------------------------------------------------------------------ #
        if data.wind_speed is not None:
            score, reasons = risk_rules.wind_risk(data.wind_speed)
            results.append(_build_result("wind", score, reasons))
            hazard_scores.append(score)

        # ------------------------------------------------------------------ #
        # Heat risk                                                            #
        # ------------------------------------------------------------------ #
        if data.temperature is not None:
            score, reasons = risk_rules.heat_risk(data.temperature)
            results.append(_build_result("heat", score, reasons))
            hazard_scores.append(score)

        # ------------------------------------------------------------------ #
        # Visibility risk                                                      #
        # ------------------------------------------------------------------ #
        if data.visibility is not None:
            score, reasons = risk_rules.visibility_risk(data.visibility)
            results.append(_build_result("visibility", score, reasons))
            hazard_scores.append(score)

        # ------------------------------------------------------------------ #
        # Flood risk (always calculated — uses available subset of inputs)    #
        # ------------------------------------------------------------------ #
        flood_score, flood_reasons = risk_rules.flood_risk(
            rainfall=data.rainfall,
            conditions=conditions,
            humidity=data.humidity,
            pressure=data.pressure,
        )
        results.append(_build_result("flood", flood_score, flood_reasons))
        # Only include flood in overall score when rainfall data is explicitly observed;
        # otherwise, indirect humidity/pressure indicators would artificially bias overall hazard score.
        if data.rainfall is not None:
            hazard_scores.append(flood_score)

        # ------------------------------------------------------------------ #
        # Overall risk                                                         #
        # ------------------------------------------------------------------ #
        overall_score, overall_reasons = risk_rules.overall_risk(hazard_scores)
        overall_level = score_to_level(overall_score)

        return RiskAnalysis(
            risks=results,
            overall_score=overall_score,
            overall_level=overall_level,
        )
