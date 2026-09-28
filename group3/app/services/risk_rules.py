"""
services/risk_rules.py
-----------------------
Pure, deterministic scoring functions for each weather hazard.

Design principles
-----------------
* Every function is a pure function: same inputs → same output, no I/O.
* Thresholds and band definitions are module-level constants so they can be
  adjusted without touching calculation logic.
* Missing values are NEVER invented.  When a required input is None the
  function returns (score=0, reasons=[...explaining why no score was computed]).
* Every returned reason string is human-readable and self-contained.
* No machine learning.  No LLM.  No external calls.

Score table (from specification)
---------------------------------
Rain (rainfall mm):
  0–10    → 10
  10–25   → 30
  25–50   → 55
  50–100  → 75
  >100    → 95

Wind (wind_speed km/h):
  0–20    → 10
  20–40   → 30
  40–60   → 55
  60–80   → 75
  >80     → 95

Heat (temperature °C):
  <30     → 10
  30–35   → 30
  35–40   → 55
  40–45   → 75
  >45     → 95

Visibility (km):
  >10     → 10
  5–10    → 30
  2–5     → 55
  1–2     → 75
  <1      → 95

Flood (composite):
  rainfall contribution     60 %
  heavy-rain condition      25 %
  other available signals   15 %
"""

from __future__ import annotations

from typing import Optional

from app.schemas.analysis import DetectedCondition

# --------------------------------------------------------------------------- #
# Scoring band definitions                                                     #
# Each entry: (upper_bound_exclusive, score)                                   #
# The final entry has upper_bound = +inf (represented as None).               #
# --------------------------------------------------------------------------- #

# Rainfall bands (mm) — lower bound is previous entry's upper_bound
_RAIN_BANDS: tuple[tuple[Optional[float], int], ...] = (
    (10.0,  10),
    (25.0,  30),
    (50.0,  55),
    (100.0, 75),
    (None,  95),   # > 100
)

# Wind speed bands (km/h)
_WIND_BANDS: tuple[tuple[Optional[float], int], ...] = (
    (20.0,  10),
    (40.0,  30),
    (60.0,  55),
    (80.0,  75),
    (None,  95),   # > 80
)

# Temperature bands (°C)
_HEAT_BANDS: tuple[tuple[Optional[float], int], ...] = (
    (30.0,  10),
    (35.0,  30),
    (40.0,  55),
    (45.0,  75),
    (None,  95),   # > 45
)

# Visibility bands (km) — REVERSED: smaller value = higher risk
# Each entry: (lower_bound_exclusive, score)
# We iterate from highest risk (smallest visibility) downward.
_VISIBILITY_BANDS: tuple[tuple[Optional[float], int], ...] = (
    (None,  95),   # < 1
    (1.0,   75),   # 1–2
    (2.0,   55),   # 2–5
    (5.0,   30),   # 5–10
    (10.0,  10),   # > 10
)

# Flood composite weights
_FLOOD_RAIN_WEIGHT:      float = 0.60
_FLOOD_CONDITION_WEIGHT: float = 0.25
_FLOOD_SIGNAL_WEIGHT:    float = 0.15

# Maximum achievable score for each flood component (used for normalisation)
_FLOOD_MAX_RAIN_SCORE:   int = 95
_FLOOD_MAX_COND_SCORE:   int = 100   # binary: 0 or 100
_FLOOD_MAX_SIGNAL_SCORE: int = 100   # binary: 0 or 100


# --------------------------------------------------------------------------- #
# Private band-lookup helpers                                                  #
# --------------------------------------------------------------------------- #

def _lookup_ascending(
    value: float,
    bands: tuple[tuple[Optional[float], int], ...],
) -> tuple[int, str]:
    """
    Find the score and band-label string for an ascending-band table.

    Parameters
    ----------
    value:
        The meteorological measurement to score.
    bands:
        Ordered tuple of (upper_bound_exclusive | None, score).
        None in the upper_bound means "no upper limit".

    Returns
    -------
    (score, band_label)
        band_label is a human-readable string such as "50–100 mm".
    """
    prev: Optional[float] = 0.0
    for upper, score in bands:
        if upper is None or value < upper:
            hi = f"{upper}" if upper is not None else "∞"
            lo = f"{prev:.3g}" if prev is not None else "0"
            return score, f"{lo}–{hi}"
        prev = upper
    # Fallback (should never reach here if bands cover all values)
    _, last_score = bands[-1]
    return last_score, ">"


def _lookup_visibility(visibility: float) -> tuple[int, str]:
    """
    Find the score for visibility using the reversed (descending) table.

    Lower visibility = higher score.
    """
    if visibility < 1.0:
        return 95, "<1 km"
    if visibility < 2.0:
        return 75, "1–2 km"
    if visibility < 5.0:
        return 55, "2–5 km"
    if visibility < 10.0:
        return 30, "5–10 km"
    return 10, ">10 km"


# --------------------------------------------------------------------------- #
# Public scoring functions                                                     #
# --------------------------------------------------------------------------- #

def rain_risk(
    rainfall: Optional[float],
) -> tuple[int, list[str]]:
    """
    Calculate rain risk score from rainfall (mm).

    Returns
    -------
    (score, reasons)
        score: 0 when rainfall is None (not invented).
        reasons: always contains ≥ 1 entry explaining the score.
    """
    if rainfall is None:
        return 0, ["Rainfall data unavailable — rain risk score not calculated."]

    score, band = _lookup_ascending(rainfall, _RAIN_BANDS)
    return score, [
        f"Rainfall of {rainfall:.4g} mm falls in the {band} mm band (score {score})."
    ]


def wind_risk(
    wind_speed: Optional[float],
) -> tuple[int, list[str]]:
    """
    Calculate wind risk score from wind_speed (km/h).

    Returns
    -------
    (score, reasons)
        score: 0 when wind_speed is None (not invented).
    """
    if wind_speed is None:
        return 0, ["Wind speed data unavailable — wind risk score not calculated."]

    score, band = _lookup_ascending(wind_speed, _WIND_BANDS)
    return score, [
        f"Wind speed of {wind_speed:.4g} km/h falls in the {band} km/h band (score {score})."
    ]


def heat_risk(
    temperature: Optional[float],
) -> tuple[int, list[str]]:
    """
    Calculate heat risk score from temperature (°C).

    Returns
    -------
    (score, reasons)
        score: 0 when temperature is None (not invented).
    """
    if temperature is None:
        return 0, ["Temperature data unavailable — heat risk score not calculated."]

    score, band = _lookup_ascending(temperature, _HEAT_BANDS)
    return score, [
        f"Temperature of {temperature:.4g} °C falls in the {band} °C band (score {score})."
    ]


def visibility_risk(
    visibility: Optional[float],
) -> tuple[int, list[str]]:
    """
    Calculate visibility risk score from visibility (km).

    Lower visibility = higher risk.

    Returns
    -------
    (score, reasons)
        score: 0 when visibility is None (not invented).
    """
    if visibility is None:
        return 0, ["Visibility data unavailable — visibility risk score not calculated."]

    score, band = _lookup_visibility(visibility)
    return score, [
        f"Visibility of {visibility:.4g} km falls in the {band} band (score {score})."
    ]


def flood_risk(
    rainfall: Optional[float],
    conditions: list[DetectedCondition],
    humidity: Optional[float],
    pressure: Optional[float],
) -> tuple[int, list[str]]:
    """
    Calculate flood proxy risk from rainfall, detected conditions, and context.

    Note: this is an engineering proxy, not an official flood-prediction model.

    Composition
    -----------
    60 % rainfall sub-score  (0–95 mapped proportionally to 0–100)
    25 % heavy-rain condition detected (0 or 100)
    15 % other available signals (humidity ≥ 85 % or pressure < 1000 hPa)

    Missing components reduce the effective weight rather than being invented.

    Returns
    -------
    (score, reasons)
    """
    reasons: list[str] = []

    # ------------------------------------------------------------------ #
    # Component 1: Rainfall (60 %)                                        #
    # ------------------------------------------------------------------ #
    if rainfall is not None:
        rain_score, _ = rain_risk(rainfall)
        # Normalise rain_score (max 95) to 0–100 for weighting
        rain_component = (rain_score / _FLOOD_MAX_RAIN_SCORE) * 100.0
        rain_weight = _FLOOD_RAIN_WEIGHT
        reasons.append(
            f"Rainfall of {rainfall:.4g} mm contributes {rain_component:.1f}/100 "
            f"(weight {_FLOOD_RAIN_WEIGHT:.0%}) to flood proxy."
        )
    else:
        rain_component = 0.0
        rain_weight = 0.0
        reasons.append(
            "Rainfall data unavailable — rainfall component excluded from flood score."
        )

    # ------------------------------------------------------------------ #
    # Component 2: Heavy-rain condition detected (25 %)                   #
    # ------------------------------------------------------------------ #
    heavy_rain_detected = any(c.type == "heavy_rain" for c in conditions)
    if heavy_rain_detected:
        cond_component = 100.0
        cond_weight = _FLOOD_CONDITION_WEIGHT
        reasons.append(
            f"Heavy-rain condition detected — condition component is 100/100 "
            f"(weight {_FLOOD_CONDITION_WEIGHT:.0%})."
        )
    else:
        cond_component = 0.0
        cond_weight = _FLOOD_CONDITION_WEIGHT
        reasons.append(
            f"No heavy-rain condition detected — condition component is 0/100 "
            f"(weight {_FLOOD_CONDITION_WEIGHT:.0%})."
        )

    # ------------------------------------------------------------------ #
    # Component 3: Other available signals (15 %)                         #
    # ------------------------------------------------------------------ #
    signal_component = 0.0
    signal_weight = _FLOOD_SIGNAL_WEIGHT
    signal_parts: list[str] = []

    if humidity is not None and humidity >= 85.0:
        signal_component += 50.0
        signal_parts.append(f"humidity {humidity:.4g}% ≥ 85%")
    if pressure is not None and pressure < 1000.0:
        signal_component += 50.0
        signal_parts.append(f"pressure {pressure:.4g} hPa < 1000 hPa")

    if humidity is None and pressure is None:
        signal_weight = 0.0
        reasons.append(
            "Humidity and pressure both unavailable — signal component excluded from flood score."
        )
    else:
        if signal_parts:
            reasons.append(
                f"Additional signals present ({', '.join(signal_parts)}) — "
                f"signal component is {signal_component:.0f}/100 "
                f"(weight {_FLOOD_SIGNAL_WEIGHT:.0%})."
            )
        else:
            reasons.append(
                f"No additional flood signals — signal component is 0/100 "
                f"(weight {_FLOOD_SIGNAL_WEIGHT:.0%})."
            )

    # ------------------------------------------------------------------ #
    # Composite score (normalise weights if any component was excluded)   #
    # ------------------------------------------------------------------ #
    total_weight = rain_weight + cond_weight + signal_weight
    if total_weight == 0.0:
        return 0, ["Insufficient data to compute flood risk."]

    raw = (
        rain_component * rain_weight
        + cond_component * cond_weight
        + signal_component * signal_weight
    ) / total_weight

    score = max(0, min(100, round(raw)))
    reasons.append(f"Weighted flood proxy score: {score}/100.")
    return score, reasons


def overall_risk(hazard_scores: list[int]) -> tuple[int, list[str]]:
    """
    Calculate the overall risk score from a list of per-hazard scores.

    Algorithm
    ---------
    1. overall = max(hazard_scores)
    2. If 2+ hazards score ≥ 50 (HIGH): overall += 10
    3. Cap at 100.

    Returns
    -------
    (score, reasons)
        score: 0 when hazard_scores is empty.
    """
    if not hazard_scores:
        return 0, ["No individual hazard scores available — overall score is 0."]

    reasons: list[str] = []
    base = max(hazard_scores)
    reasons.append(f"Base overall score = max of individual hazard scores = {base}.")

    high_count = sum(1 for s in hazard_scores if s >= 50)
    escalation = 0
    if high_count >= 2:
        escalation = 10
        reasons.append(
            f"{high_count} hazards are HIGH or above (score ≥ 50) — "
            f"multi-hazard escalation +{escalation}."
        )

    score = max(0, min(100, base + escalation))
    if escalation:
        reasons.append(f"Overall score after escalation and cap: {score}.")
    return score, reasons
