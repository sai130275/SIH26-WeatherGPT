"""
services/evidence_engine.py
-----------------------------
Converts existing Weather/Risk/Impact/Advisory results into structured
evidence items and a deterministic confidence score.

Design principles
-----------------
* The EvidenceEngine does NOT recalculate risk, impact, or advisories.
  It consumes existing outputs only.
* Confidence is always computed deterministically — never by an LLM.
* Missing data reduces confidence; missing values are never invented.
* Every reduction in confidence corresponds to an entry in `uncertainty`.
* All thresholds and weights are module-level constants for easy tuning.

Confidence calculation
----------------------

  completeness_score  (max 40)
  ─────────────────────────────
  temperature  : 7 points (if present)
  rainfall     : 7 points (if present)
  wind_speed   : 7 points (if present)
  visibility   : 7 points (if present)
  humidity     : 6 points (if present)
  pressure     : 6 points (if present)

  freshness_score  (max 30)
  ──────────────────────────
  age <  30 min  : 30
  age   30–60 min: 20
  age   1– 2 h   : 10
  age > 2 h      :  0

  rule_certainty_score  (max 30)
  ────────────────────────────────
  risk analysis present     : 10
  rain  hazard assessed     :  5
  wind  hazard assessed     :  5
  heat  hazard assessed     :  5
  visibility hazard assessed:  5
  Total when all assessed   : 30

  confidence = completeness + freshness + rule_certainty  (capped 0–100)

Adding a new weather field
--------------------------
1. Add a (field_name, points) entry to _COMPLETENESS_FIELDS.
2. Adjust points so the total still sums to 40.

Adding a new risk hazard
------------------------
1. Add the hazard type string to _RULE_HAZARDS.
2. Adjust per-hazard points so the total is still 20 (10 base + 20 hazards = 30).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from app.schemas.evidence import ConfidenceResult, EvidenceItem
from app.schemas.weather import WeatherData


# --------------------------------------------------------------------------- #
# Configuration constants                                                      #
# --------------------------------------------------------------------------- #

# (field_name, points) — must sum to 40
_COMPLETENESS_FIELDS: tuple[tuple[str, int], ...] = (
    ("temperature",  7),
    ("rainfall",     7),
    ("wind_speed",   7),
    ("visibility",   7),
    ("humidity",     6),
    ("pressure",     6),
)

# Freshness bands: (max_age_seconds, score)  — evaluated in order
_FRESHNESS_BANDS: tuple[tuple[int, int], ...] = (
    (1_800,  30),   # < 30 minutes
    (3_600,  20),   # 30 – 60 minutes
    (7_200,  10),   # 1 – 2 hours
)
# Any age beyond the last band scores 0

# Base points for having any risk analysis at all
_RULE_CERTAINTY_BASE: int = 10

# Per-hazard points (all four assessed = 4 × 5 = 20)
_RULE_HAZARDS: tuple[str, ...] = ("rain", "wind", "heat", "visibility")
_RULE_HAZARD_POINTS: int = 5

# Evidence generation — only include risk/impact items at or above this level
_EVIDENCE_MIN_RISK_LEVEL:   str = "MODERATE"
_EVIDENCE_MIN_IMPACT_LEVEL: str = "MODERATE"
_EVIDENCE_MIN_ADVISORY_PRI: str = "MODERATE"

_LEVEL_RANK: dict[str, int] = {
    "LOW": 0, "MODERATE": 1, "HIGH": 2, "SEVERE": 3
}

# Notable weather thresholds — only generate weather evidence above these
_NOTABLE_THRESHOLDS: dict[str, float] = {
    "rainfall":    10.0,   # mm
    "wind_speed":  20.0,   # km/h
    "temperature": 30.0,   # °C
    "humidity":    70.0,   # %
    "pressure":    0.0,    # always notable (any value is useful)
    "visibility":  10.0,   # km  → notable when BELOW this (handled specially)
}


# --------------------------------------------------------------------------- #
# Private helpers                                                              #
# --------------------------------------------------------------------------- #

def _level_meets_threshold(level: str, threshold: str) -> bool:
    return _LEVEL_RANK.get(level, 0) >= _LEVEL_RANK.get(threshold, 0)


def _age_seconds(timestamp: datetime, reference: datetime) -> float:
    """Seconds between observation timestamp and reference time."""
    # Normalise both to UTC-aware
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)
    delta = reference - timestamp
    return max(0.0, delta.total_seconds())


# --------------------------------------------------------------------------- #
# EvidenceEngine                                                               #
# --------------------------------------------------------------------------- #

class EvidenceEngine:
    """
    Stateless evidence and confidence engine.

    Consumes existing Weather/Risk/Impact/Advisory results and produces a
    ConfidenceResult containing:
      - evidence items (source, data, reason)
      - confidence score (0–100, deterministic)
      - uncertainty strings (for missing or stale data)

    Usage
    -----
    >>> engine = EvidenceEngine()
    >>> result = engine.generate(
    ...     weather=weather_data,
    ...     risk=risk_dict,          # from ChatTools.get_risk_analysis()
    ...     advisory=advisory_dict,  # from ChatTools.get_full_advisory()
    ... )
    >>> result.confidence
    88

    Parameters are typed as Optional[dict] so the engine can be called
    with whatever subset of outputs is currently available.
    """

    def generate(
        self,
        weather: WeatherData,
        risk: Optional[dict] = None,
        advisory: Optional[dict] = None,
        reference_time: Optional[datetime] = None,
    ) -> ConfidenceResult:
        """
        Generate evidence + confidence for an existing set of results.

        Parameters
        ----------
        weather:
            The source WeatherData observation.
        risk:
            Dict from ChatTools.get_risk_analysis() or RiskEngine.analyse().
            None if risk was not computed.
        advisory:
            Dict from ChatTools.get_full_advisory() containing
            'impacts' and 'advisories' lists.
            None if advisory was not computed.
        reference_time:
            The "current" time used for freshness calculation.
            Defaults to datetime.now(UTC). Injectable for testing.

        Returns
        -------
        ConfidenceResult
        """
        reference = reference_time or datetime.now(tz=timezone.utc)
        evidence: list[EvidenceItem] = []
        uncertainty: list[str] = []

        # ------------------------------------------------------------- #
        # Component 1: completeness                                       #
        # ------------------------------------------------------------- #
        completeness_score, c_uncertainty = self._completeness(weather)
        uncertainty.extend(c_uncertainty)

        # ------------------------------------------------------------- #
        # Component 2: freshness                                          #
        # ------------------------------------------------------------- #
        freshness_score, f_uncertainty = self._freshness(weather, reference)
        uncertainty.extend(f_uncertainty)

        # ------------------------------------------------------------- #
        # Component 3: rule certainty                                     #
        # ------------------------------------------------------------- #
        rule_certainty_score, r_uncertainty = self._rule_certainty(risk)
        uncertainty.extend(r_uncertainty)

        # ------------------------------------------------------------- #
        # Evidence from weather observation                               #
        # ------------------------------------------------------------- #
        evidence.extend(self._weather_evidence(weather))

        # ------------------------------------------------------------- #
        # Evidence from risk analysis                                     #
        # ------------------------------------------------------------- #
        if risk:
            evidence.extend(self._risk_evidence(risk))

        # ------------------------------------------------------------- #
        # Evidence from impacts                                           #
        # ------------------------------------------------------------- #
        if advisory:
            evidence.extend(self._impact_evidence(advisory))
            evidence.extend(self._advisory_evidence(advisory))

        # ------------------------------------------------------------- #
        # Overall confidence                                              #
        # ------------------------------------------------------------- #
        raw = completeness_score + freshness_score + rule_certainty_score
        confidence = max(0, min(100, raw))

        return ConfidenceResult(
            confidence=confidence,
            evidence=evidence,
            uncertainty=uncertainty,
            completeness_score=completeness_score,
            freshness_score=freshness_score,
            rule_certainty_score=rule_certainty_score,
        )

    # ------------------------------------------------------------------ #
    # Confidence component calculators                                    #
    # ------------------------------------------------------------------ #

    def _completeness(
        self, weather: WeatherData
    ) -> tuple[int, list[str]]:
        """
        Calculate the data-completeness score and corresponding uncertainty notes.

        Returns (score, uncertainty_strings).
        """
        score = 0
        uncertainty: list[str] = []

        for field, points in _COMPLETENESS_FIELDS:
            value = getattr(weather, field, None)
            if value is not None:
                score += points
            else:
                label = field.replace("_", " ").title()
                uncertainty.append(
                    f"{label} data unavailable — related risk may be underestimated."
                )

        return score, uncertainty

    def _freshness(
        self, weather: WeatherData, reference: datetime
    ) -> tuple[int, list[str]]:
        """
        Calculate the data-freshness score.

        Returns (score, uncertainty_strings).
        """
        age = _age_seconds(weather.timestamp, reference)
        uncertainty: list[str] = []

        for max_age, score in _FRESHNESS_BANDS:
            if age < max_age:
                return score, uncertainty

        # Beyond all bands → 0 points
        age_minutes = int(age / 60)
        uncertainty.append(
            f"Weather data is {age_minutes} minutes old — "
            "conditions may have changed since the observation."
        )
        return 0, uncertainty

    def _rule_certainty(
        self, risk: Optional[dict]
    ) -> tuple[int, list[str]]:
        """
        Calculate rule-certainty score based on which hazards were assessed.

        Returns (score, uncertainty_strings).
        """
        if risk is None:
            return 0, ["Risk analysis not available — assessment confidence is limited."]

        score = _RULE_CERTAINTY_BASE
        uncertainty: list[str] = []
        assessed_types = {r.get("type") for r in risk.get("risks", [])}

        for hazard in _RULE_HAZARDS:
            if hazard in assessed_types:
                score += _RULE_HAZARD_POINTS
            else:
                uncertainty.append(
                    f"{hazard.title()} risk not assessed — "
                    f"required data was unavailable."
                )

        return score, uncertainty

    # ------------------------------------------------------------------ #
    # Evidence generators                                                 #
    # ------------------------------------------------------------------ #

    def _weather_evidence(self, weather: WeatherData) -> list[EvidenceItem]:
        """Generate weather-source evidence for notable field values."""
        items: list[EvidenceItem] = []

        # Rainfall
        if weather.rainfall is not None and weather.rainfall >= _NOTABLE_THRESHOLDS["rainfall"]:
            items.append(EvidenceItem(
                source="weather",
                data=f"rainfall = {weather.rainfall:.4g} mm",
                reason=(
                    "Heavy rainfall detected."
                    if weather.rainfall >= 50
                    else "Moderate rainfall detected."
                ),
            ))

        # Wind speed
        if weather.wind_speed is not None and weather.wind_speed >= _NOTABLE_THRESHOLDS["wind_speed"]:
            items.append(EvidenceItem(
                source="weather",
                data=f"wind_speed = {weather.wind_speed:.4g} km/h",
                reason=(
                    "High wind speed detected."
                    if weather.wind_speed >= 60
                    else "Elevated wind speed detected."
                ),
            ))

        # Temperature
        if weather.temperature is not None and weather.temperature >= _NOTABLE_THRESHOLDS["temperature"]:
            items.append(EvidenceItem(
                source="weather",
                data=f"temperature = {weather.temperature:.4g} °C",
                reason=(
                    "Extreme heat detected."
                    if weather.temperature >= 40
                    else "High temperature detected."
                ),
            ))

        # Visibility — notable when LOW
        if weather.visibility is not None and weather.visibility < _NOTABLE_THRESHOLDS["visibility"]:
            items.append(EvidenceItem(
                source="weather",
                data=f"visibility = {weather.visibility:.4g} km",
                reason=(
                    "Very poor visibility detected."
                    if weather.visibility < 2
                    else "Reduced visibility detected."
                ),
            ))

        # Humidity
        if weather.humidity is not None and weather.humidity >= _NOTABLE_THRESHOLDS["humidity"]:
            items.append(EvidenceItem(
                source="weather",
                data=f"humidity = {weather.humidity:.4g}%",
                reason="High humidity may amplify heat and flood risk.",
            ))

        return items

    def _risk_evidence(self, risk: dict) -> list[EvidenceItem]:
        """Generate risk-source evidence for hazards at MODERATE level or above."""
        items: list[EvidenceItem] = []

        for risk_item in risk.get("risks", []):
            level = risk_item.get("level", "LOW")
            if not _level_meets_threshold(level, _EVIDENCE_MIN_RISK_LEVEL):
                continue
            rtype = risk_item.get("type", "unknown")
            score = risk_item.get("score", 0)
            reasons = risk_item.get("reasons", [])
            short_reason = reasons[0] if reasons else f"{rtype} risk is {level}."
            items.append(EvidenceItem(
                source="risk",
                data=f"{rtype} risk = {score} ({level})",
                reason=short_reason,
            ))

        # Overall risk
        overall_level = risk.get("overall_level", "LOW")
        if _level_meets_threshold(overall_level, _EVIDENCE_MIN_RISK_LEVEL):
            items.append(EvidenceItem(
                source="risk",
                data=f"overall risk = {risk.get('overall_score', 0)} ({overall_level})",
                reason=(
                    "Multiple hazards combine to produce an elevated overall risk score."
                ),
            ))

        return items

    def _impact_evidence(self, advisory: dict) -> list[EvidenceItem]:
        """Generate impact-source evidence for sectors at MODERATE or above."""
        items: list[EvidenceItem] = []

        for impact in advisory.get("impacts", []):
            severity = impact.get("severity", "LOW")
            if not _level_meets_threshold(severity, _EVIDENCE_MIN_IMPACT_LEVEL):
                continue
            items.append(EvidenceItem(
                source="impact",
                data=f"{impact.get('type', 'unknown')} impact = {severity}",
                reason=impact.get("reason", f"{impact.get('type')} sector is affected."),
            ))

        return items

    def _advisory_evidence(self, advisory: dict) -> list[EvidenceItem]:
        """Generate advisory-source evidence for advisories at MODERATE or above."""
        items: list[EvidenceItem] = []

        for adv in advisory.get("advisories", []):
            priority = adv.get("priority", "LOW")
            if not _level_meets_threshold(priority, _EVIDENCE_MIN_ADVISORY_PRI):
                continue
            items.append(EvidenceItem(
                source="advisory",
                data=f"{adv.get('category', 'unknown')} advisory: priority {priority}",
                reason=adv.get("message", "Advisory issued."),
            ))

        return items
