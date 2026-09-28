"""
services/advisory_engine.py
-----------------------------
Converts ImpactResult[] into actionable, human-readable advisories.

Design principles
-----------------
* One advisory per impact category present in the input.
* Advisory messages are deterministic — keyed on (category, severity).
* Priority mirrors impact severity exactly.
* Messages are concise, action-oriented sentences addressed to the public.
* The reason field passes through the impact reason for full traceability.
* No LLM, no external calls, no missing value invention.

Message table
-------------
Each (category, severity) pair maps to a fixed advisory message.
This keeps messages consistent and testable.  Messages can be updated
without touching logic by editing the MESSAGE_TABLE dict below.

Adding a new category or severity
----------------------------------
1. Add entries to _MESSAGE_TABLE[(category, severity)].
2. No other changes needed.
"""

from __future__ import annotations

from app.schemas.advisory import (
    Advisory,
    AdvisoryPriority,
    ImpactCategory,
    ImpactResult,
    ImpactSeverity,
)


# --------------------------------------------------------------------------- #
# Advisory message table                                                       #
# (category, severity) → message                                              #
# --------------------------------------------------------------------------- #

_MESSAGE_TABLE: dict[tuple[ImpactCategory, ImpactSeverity], str] = {
    # Travel
    ("travel", "LOW"):      "Monitor weather updates before travelling.",
    ("travel", "MODERATE"): "Exercise caution while travelling; allow extra journey time.",
    ("travel", "HIGH"):     "Avoid non-essential travel; road conditions may be hazardous.",
    ("travel", "SEVERE"):   "Do not travel. Conditions pose serious risk to road safety.",

    # Outdoor
    ("outdoor", "LOW"):      "Outdoor activities are generally safe; stay informed.",
    ("outdoor", "MODERATE"): "Limit strenuous outdoor activities; seek shade and hydrate.",
    ("outdoor", "HIGH"):     "Avoid prolonged outdoor exposure; conditions are dangerous.",
    ("outdoor", "SEVERE"):   "Stay indoors. Outdoor conditions are life-threatening.",

    # Farming
    ("farming", "LOW"):      "Standard farm operations can continue; monitor weather.",
    ("farming", "MODERATE"): "Delay field operations; protect standing crops from weather.",
    ("farming", "HIGH"):     "Halt farming activities; secure equipment and protect crops.",
    ("farming", "SEVERE"):   "All farming must stop. Severe damage to crops and equipment is likely.",

    # General
    ("general", "LOW"):      "Stay informed about weather developments in your area.",
    ("general", "MODERATE"): "Take precautions; be prepared for changing weather conditions.",
    ("general", "HIGH"):     "Take immediate precautions; follow official emergency guidance.",
    ("general", "SEVERE"):   "This is a severe weather event. Follow emergency services guidance immediately.",
}

# Fallback message when a (category, severity) pair is missing from the table
_FALLBACK_MESSAGE = "Take appropriate precautions for current weather conditions."


# --------------------------------------------------------------------------- #
# AdvisoryEngine                                                               #
# --------------------------------------------------------------------------- #

class AdvisoryEngine:
    """
    Stateless advisory generation engine.

    Usage
    -----
    >>> engine = AdvisoryEngine()
    >>> advisories = engine.generate(impact_results)

    The engine converts each ImpactResult into one Advisory using the
    pre-defined message table.  Priority mirrors impact severity.
    """

    def generate(
        self,
        impacts: list[ImpactResult],
    ) -> list[Advisory]:
        """
        Convert a list of ImpactResult objects into actionable advisories.

        Parameters
        ----------
        impacts:
            Output from ImpactEngine.assess(), already sorted by severity.

        Returns
        -------
        list[Advisory]:
            One advisory per impact, ordered by priority (SEVERE → LOW).
            The reason field carries through the impact reason verbatim.
        """
        advisories: list[Advisory] = []

        for impact in impacts:
            key = (impact.type, impact.severity)
            message = _MESSAGE_TABLE.get(key, _FALLBACK_MESSAGE)
            priority: AdvisoryPriority = impact.severity  # mirrors severity exactly

            advisories.append(
                Advisory(
                    category=impact.type,
                    priority=priority,
                    message=message,
                    reason=impact.reason,
                )
            )

        return advisories
