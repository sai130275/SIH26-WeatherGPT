"""
services/risk_assessment.py
---------------------------
Structured risk assessment layer (Module 1.2).

Produces:
  - rain risk
  - heat risk
  - wind risk
  - storm risk (convective & gale composite)
  - flood-related risk
  - visibility risk
  - overall composite risk

Design rules:
  - Explicitly tags output as 'HEURISTIC_RISK'
  - Transparently shows contributing factors and evidence
  - Includes a clear disclaimer distinguishing it from official disaster warnings
  - Deterministic calculations based on risk_rules
"""

from __future__ import annotations

from typing import List, Optional

from app.schemas.analysis import DetectedCondition
from app.schemas.intelligence import (
    HazardRisk,
    HazardType,
    RiskAssessment,
    RiskLevel,
)
from app.schemas.unified_weather import CurrentWeather
from app.services import risk_rules


def _score_to_level(score: int) -> RiskLevel:
    clamped = max(0, min(100, score))
    if clamped <= 24:
        return "LOW"
    if clamped <= 49:
        return "MODERATE"
    if clamped <= 74:
        return "HIGH"
    return "SEVERE"


class ComprehensiveRiskEngine:
    """
    Stateless risk assessment engine.
    """

    def assess(
        self,
        weather: CurrentWeather,
        detected_conditions: Optional[List[DetectedCondition]] = None,
    ) -> RiskAssessment:
        conditions = detected_conditions or []
        hazard_risks: List[HazardRisk] = []
        scores_for_overall: List[int] = []

        # 1. Rain Risk
        if weather.rainfall is not None:
            r_score, r_reasons = risk_rules.rain_risk(weather.rainfall)
            hazard_risks.append(
                HazardRisk(
                    hazard="rain",
                    score=r_score,
                    level=_score_to_level(r_score),
                    classification="HEURISTIC_RISK",
                    contributing_factors=[f"Rainfall: {weather.rainfall} mm"],
                    evidence=r_reasons,
                    confidence=95,
                )
            )
            scores_for_overall.append(r_score)

        # 2. Wind Risk
        if weather.wind_speed is not None:
            w_score, w_reasons = risk_rules.wind_risk(weather.wind_speed)
            factors = [f"Wind speed: {weather.wind_speed} km/h"]
            if weather.wind_gusts is not None:
                factors.append(f"Wind gusts: {weather.wind_gusts} km/h")
            hazard_risks.append(
                HazardRisk(
                    hazard="wind",
                    score=w_score,
                    level=_score_to_level(w_score),
                    classification="HEURISTIC_RISK",
                    contributing_factors=factors,
                    evidence=w_reasons,
                    confidence=90,
                )
            )
            scores_for_overall.append(w_score)

        # 3. Heat Risk
        if weather.temperature is not None:
            h_score, h_reasons = risk_rules.heat_risk(weather.temperature)
            factors = [f"Temperature: {weather.temperature} °C"]
            if weather.feels_like is not None:
                factors.append(f"Apparent temperature: {weather.feels_like} °C")
            hazard_risks.append(
                HazardRisk(
                    hazard="heat",
                    score=h_score,
                    level=_score_to_level(h_score),
                    classification="HEURISTIC_RISK",
                    contributing_factors=factors,
                    evidence=h_reasons,
                    confidence=92,
                )
            )
            scores_for_overall.append(h_score)

        # 4. Storm Risk (Convective & Thunderstorm potential)
        storm_score, storm_reasons, storm_factors = self._compute_storm_risk(weather)
        if storm_score is not None:
            hazard_risks.append(
                HazardRisk(
                    hazard="storm",
                    score=storm_score,
                    level=_score_to_level(storm_score),
                    classification="HEURISTIC_RISK",
                    contributing_factors=storm_factors,
                    evidence=storm_reasons,
                    confidence=85 if weather.cape is not None else 75,
                )
            )
            scores_for_overall.append(storm_score)

        # 5. Visibility Risk
        if weather.visibility is not None:
            v_score, v_reasons = risk_rules.visibility_risk(weather.visibility)
            hazard_risks.append(
                HazardRisk(
                    hazard="visibility",
                    score=v_score,
                    level=_score_to_level(v_score),
                    classification="HEURISTIC_RISK",
                    contributing_factors=[f"Visibility: {weather.visibility} km"],
                    evidence=v_reasons,
                    confidence=88,
                )
            )
            scores_for_overall.append(v_score)

        # 6. Flood Risk
        flood_score, flood_reasons = risk_rules.flood_risk(
            rainfall=weather.rainfall,
            conditions=conditions,
            humidity=weather.humidity,
            pressure=weather.pressure,
        )
        hazard_risks.append(
            HazardRisk(
                hazard="flood",
                score=flood_score,
                level=_score_to_level(flood_score),
                classification="HEURISTIC_RISK",
                contributing_factors=[
                    f"Rainfall: {weather.rainfall or 0.0} mm",
                    f"Humidity: {weather.humidity or 0.0} %",
                ],
                evidence=flood_reasons,
                confidence=85,
            )
        )
        if weather.rainfall is not None:
            scores_for_overall.append(flood_score)

        # 7. Overall Risk Calculation
        overall_score, overall_reasons = risk_rules.overall_risk(scores_for_overall)
        overall_level = _score_to_level(overall_score)

        return RiskAssessment(
            risks=hazard_risks,
            overall_score=overall_score,
            overall_level=overall_level,
            classification="HEURISTIC_RISK",
            disclaimer=(
                "Automated heuristic meteorological risk assessment. "
                "This is not an official disaster warning issued by government meteorological agencies (such as IMD)."
            ),
        )

    def _compute_storm_risk(
        self, weather: CurrentWeather
    ) -> tuple[Optional[int], list[str], list[str]]:
        factors: list[str] = []
        reasons: list[str] = []
        score = 10  # baseline minimal

        cape = weather.cape
        lightning = weather.lightning
        wind = weather.wind_speed or 0.0
        rain = weather.rainfall or 0.0

        if lightning is True:
            score = max(score, 75)
            factors.append("Active lightning detected")
            reasons.append("Lightning detected directly elevates storm risk to severe band.")

        if cape is not None:
            factors.append(f"CAPE: {cape} J/kg")
            if cape >= 2500:
                score = max(score, 90)
                reasons.append(f"Extreme convective energy (CAPE {cape} J/kg) indicates severe storm capability.")
            elif cape >= 1500:
                score = max(score, 70)
                reasons.append(f"High convective energy (CAPE {cape} J/kg) supports thunderstorm development.")
            elif cape >= 800:
                score = max(score, 45)
                reasons.append(f"Moderate instability (CAPE {cape} J/kg).")

        # Convective rain & wind synergy
        if rain >= 20.0 and wind >= 40.0:
            score = max(score, 65)
            factors.append(f"Heavy rain ({rain} mm) combined with strong wind ({wind} km/h)")
            reasons.append("High rainfall and wind combination creates squall-line hazard.")

        if not factors:
            factors.append("No convective signals or lightning present")
            reasons.append("Normal atmospheric stability; minimal storm hazard.")

        return score, reasons, factors
