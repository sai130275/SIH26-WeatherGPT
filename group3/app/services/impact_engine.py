"""
services/impact_engine.py
--------------------------
Converts WeatherData + RiskAnalysis into sector-level impact assessments.

Design principles
-----------------
* Pure, deterministic rules — same inputs always produce same output.
* No missing values are invented; if a required field is None the
  corresponding impact check is skipped or downgraded.
* Impact rules are kept separate from advisory generation (advisory_engine.py).
* One impact rule function per category, each returning Optional[ImpactResult].
* All rules are independently testable.

Impact categories
-----------------
  travel   — road / public transport hazards
  outdoor  — outdoor activity safety
  farming  — agricultural concerns
  general  — public safety / shelter advice

Severity mapping from risk level
---------------------------------
  LOW      → LOW
  MODERATE → MODERATE
  HIGH     → HIGH
  SEVERE   → SEVERE

(Impact severity mirrors the driving risk level for that category.)

Adding a new category
---------------------
1. Write a `_<category>_impact()` function.
2. Append a call to it inside `ImpactEngine.assess()`.
"""

from __future__ import annotations

from typing import Optional

from app.schemas.advisory import ImpactCategory, ImpactResult, ImpactSeverity
from app.schemas.risk import RiskAnalysis, RiskLevel
from app.schemas.weather import WeatherData


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #

_RISK_TO_IMPACT: dict[RiskLevel, ImpactSeverity] = {
    "LOW":      "LOW",
    "MODERATE": "MODERATE",
    "HIGH":     "HIGH",
    "SEVERE":   "SEVERE",
}

# Minimum risk level that triggers an impact for each category.
# Categories are only included in the output when risk reaches their threshold.
_TRIGGER_THRESHOLD: dict[ImpactCategory, set[str]] = {
    "travel":  {"MODERATE", "HIGH", "SEVERE"},
    "outdoor": {"MODERATE", "HIGH", "SEVERE"},
    "farming": {"MODERATE", "HIGH", "SEVERE"},
    "general": {"HIGH", "SEVERE"},
}

_SEVERITY_RANK: dict[str, int] = {
    "LOW": 0, "MODERATE": 1, "HIGH": 2, "SEVERE": 3,
}


def _max_level(*levels: Optional[str]) -> Optional[str]:
    """Return the highest risk level from a variable-length argument list."""
    valid = [lv for lv in levels if lv is not None]
    if not valid:
        return None
    return max(valid, key=lambda lv: _SEVERITY_RANK.get(lv, -1))


def _risk_level_for(risk_type: str, risk: RiskAnalysis) -> Optional[RiskLevel]:
    """Look up the level for a specific risk type in a RiskAnalysis."""
    for r in risk.risks:
        if r.type == risk_type:
            return r.level
    return None


def _above_threshold(level: Optional[str], category: ImpactCategory) -> bool:
    """Return True if level meets the trigger threshold for a category."""
    if level is None:
        return False
    return level in _TRIGGER_THRESHOLD[category]


# --------------------------------------------------------------------------- #
# Per-category impact rule functions                                           #
# --------------------------------------------------------------------------- #

def _travel_impact(
    weather: WeatherData,
    risk: RiskAnalysis,
) -> Optional[ImpactResult]:
    """
    Travel impact — driven by rain, wind, visibility, and overall risk.

    Triggers when any of rain / wind / visibility risk is MODERATE or above.
    """
    rain_level  = _risk_level_for("rain", risk)
    wind_level  = _risk_level_for("wind", risk)
    vis_level   = _risk_level_for("visibility", risk)

    driving_level = _max_level(rain_level, wind_level, vis_level)

    if not _above_threshold(driving_level, "travel"):
        return None

    severity: ImpactSeverity = _RISK_TO_IMPACT[driving_level]  # type: ignore[index]

    # Build a concise, factual reason
    parts: list[str] = []
    if rain_level in {"HIGH", "SEVERE"}:
        rain_val = f"{weather.rainfall:.4g} mm" if weather.rainfall is not None else "heavy rain"
        parts.append(f"rainfall ({rain_val})")
    if wind_level in {"HIGH", "SEVERE"}:
        wind_val = f"{weather.wind_speed:.4g} km/h" if weather.wind_speed is not None else "high wind"
        parts.append(f"wind speed ({wind_val})")
    if vis_level in {"HIGH", "SEVERE"}:
        vis_val = f"{weather.visibility:.4g} km" if weather.visibility is not None else "poor visibility"
        parts.append(f"visibility ({vis_val})")
    if not parts:
        parts.append("adverse weather conditions")

    reason = (
        f"Road travel is affected by {', '.join(parts)}. "
        f"Travel risk is {driving_level}."
    )

    return ImpactResult(type="travel", severity=severity, reason=reason)


def _outdoor_impact(
    weather: WeatherData,
    risk: RiskAnalysis,
) -> Optional[ImpactResult]:
    """
    Outdoor impact — driven by heat, wind, rain, and visibility risk.

    Triggers when any of heat / wind / rain / visibility risk is MODERATE or above.
    """
    heat_level  = _risk_level_for("heat", risk)
    wind_level  = _risk_level_for("wind", risk)
    rain_level  = _risk_level_for("rain", risk)
    vis_level   = _risk_level_for("visibility", risk)

    driving_level = _max_level(heat_level, wind_level, rain_level, vis_level)

    if not _above_threshold(driving_level, "outdoor"):
        return None

    severity: ImpactSeverity = _RISK_TO_IMPACT[driving_level]  # type: ignore[index]

    parts: list[str] = []
    if heat_level in {"HIGH", "SEVERE"}:
        temp_val = f"{weather.temperature:.4g} °C" if weather.temperature is not None else "extreme heat"
        parts.append(f"extreme heat ({temp_val})")
    if wind_level in {"HIGH", "SEVERE"}:
        wind_val = f"{weather.wind_speed:.4g} km/h" if weather.wind_speed is not None else "high wind"
        parts.append(f"high wind ({wind_val})")
    if rain_level in {"HIGH", "SEVERE"}:
        rain_val = f"{weather.rainfall:.4g} mm" if weather.rainfall is not None else "heavy rain"
        parts.append(f"heavy rain ({rain_val})")
    if vis_level in {"HIGH", "SEVERE"}:
        parts.append("poor visibility")
    if not parts:
        parts.append("adverse weather conditions")

    reason = (
        f"Outdoor activities are unsafe due to {', '.join(parts)}. "
        f"Outdoor risk is {driving_level}."
    )

    return ImpactResult(type="outdoor", severity=severity, reason=reason)


def _farming_impact(
    weather: WeatherData,
    risk: RiskAnalysis,
) -> Optional[ImpactResult]:
    """
    Farming impact — driven by rain, flood, heat, and wind risk.

    Triggers when any of rain / flood / heat / wind risk is MODERATE or above.
    """
    rain_level  = _risk_level_for("rain", risk)
    flood_level = _risk_level_for("flood", risk)
    heat_level  = _risk_level_for("heat", risk)
    wind_level  = _risk_level_for("wind", risk)

    driving_level = _max_level(rain_level, flood_level, heat_level, wind_level)

    if not _above_threshold(driving_level, "farming"):
        return None

    severity: ImpactSeverity = _RISK_TO_IMPACT[driving_level]  # type: ignore[index]

    parts: list[str] = []
    if flood_level in {"HIGH", "SEVERE"}:
        parts.append("high flood risk (crop and soil damage possible)")
    elif rain_level in {"HIGH", "SEVERE"}:
        rain_val = f"{weather.rainfall:.4g} mm" if weather.rainfall is not None else "heavy rain"
        parts.append(f"heavy rain ({rain_val}), waterlogging risk")
    if heat_level in {"HIGH", "SEVERE"}:
        temp_val = f"{weather.temperature:.4g} °C" if weather.temperature is not None else "extreme heat"
        parts.append(f"extreme heat ({temp_val}), crop stress risk")
    if wind_level in {"HIGH", "SEVERE"}:
        wind_val = f"{weather.wind_speed:.4g} km/h" if weather.wind_speed is not None else "high wind"
        parts.append(f"high wind ({wind_val}), lodging risk")
    if not parts:
        parts.append("adverse weather conditions")

    reason = (
        f"Farming operations are affected by {', '.join(parts)}. "
        f"Agricultural risk is {driving_level}."
    )

    return ImpactResult(type="farming", severity=severity, reason=reason)


def _general_impact(
    weather: WeatherData,
    risk: RiskAnalysis,
) -> Optional[ImpactResult]:
    """
    General public safety impact — driven by overall risk level.

    Only triggers when overall risk is HIGH or SEVERE (higher bar than other categories).
    """
    overall_level = risk.overall_level

    if not _above_threshold(overall_level, "general"):
        return None

    severity: ImpactSeverity = _RISK_TO_IMPACT[overall_level]  # type: ignore[index]

    active_hazards: list[str] = []
    for r in risk.risks:
        if r.level in {"HIGH", "SEVERE"}:
            active_hazards.append(f"{r.type} ({r.level})")

    hazard_str = (
        ", ".join(active_hazards)
        if active_hazards
        else "multiple weather hazards"
    )

    reason = (
        f"Overall risk is {overall_level} based on {hazard_str}. "
        "Public safety measures are advised."
    )

    return ImpactResult(type="general", severity=severity, reason=reason)


# --------------------------------------------------------------------------- #
# ImpactEngine                                                                 #
# --------------------------------------------------------------------------- #

class ImpactEngine:
    """
    Stateless impact assessment engine.

    Usage
    -----
    >>> engine = ImpactEngine()
    >>> analysis = engine.assess(weather_data, risk_analysis)

    Adding a new category
    ---------------------
    1. Add a `_<category>_impact(weather, risk)` function above.
    2. Append a call to it in `assess()` below.
    3. Add the category to `ImpactCategory` in advisory.py.
    4. Set its threshold in `_TRIGGER_THRESHOLD`.
    """

    def assess(
        self,
        weather: WeatherData,
        risk: RiskAnalysis,
    ) -> list[ImpactResult]:
        """
        Run all impact rule functions and return triggered impacts.

        Parameters
        ----------
        weather:
            Raw WeatherData from the API request.
        risk:
            Pre-calculated RiskAnalysis (from POST /risk or RiskEngine).

        Returns
        -------
        list[ImpactResult]:
            Impacts for all triggered categories, ordered by severity
            (SEVERE → HIGH → MODERATE → LOW).
        """
        candidates = [
            _travel_impact(weather, risk),
            _outdoor_impact(weather, risk),
            _farming_impact(weather, risk),
            _general_impact(weather, risk),
        ]

        results = [r for r in candidates if r is not None]

        # Sort by severity descending so highest-priority impacts come first
        results.sort(key=lambda r: _SEVERITY_RANK.get(r.severity, 0), reverse=True)

        return results
