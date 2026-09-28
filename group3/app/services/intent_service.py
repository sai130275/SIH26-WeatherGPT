"""
services/intent_service.py
---------------------------
Deterministic, keyword-based intent extraction.

Design principles
-----------------
* Pure function — no I/O, no LLM calls, no side effects.
* Same message → same IntentResult, always.
* Intent classification uses weighted keyword scoring.
* Activity and time-reference extraction via keyword lists.
* "general" intent is the safe fallback when no keywords match.

Adding a new intent
-------------------
1. Add keywords to the corresponding entry in _INTENT_KEYWORDS.
2. Add time-phrase keywords to _TIME_KEYWORDS if needed.
3. Add activity keywords to _ACTIVITY_KEYWORDS if needed.
"""

from __future__ import annotations

from app.schemas.chat import IntentResult, IntentType


# --------------------------------------------------------------------------- #
# Keyword tables                                                               #
# --------------------------------------------------------------------------- #

# Each intent maps to a tuple of lowercase keywords/phrases.
# Longer phrases must appear before short words to match greedily.
_INTENT_KEYWORDS: dict[IntentType, tuple[str, ...]] = {
    "forecast": (
        "tomorrow", "tonight", "this evening", "later today", "next week",
        "forecast", "will it rain", "will it be", "will there be",
        "next few days", "coming days", "expected",
    ),
    "risk": (
        "risk", "danger", "dangerous", "hazard", "hazardous", "safe", "safety",
        "warning", "alert", "severe", "threat", "concern",
    ),
    "advisory": (
        "should i", "what should", "recommend", "advice", "advise",
        "advisory", "suggestion", "suggest", "what to do", "precaution",
    ),
    "activity": (
        "travel", "drive", "driving", "commute", "road",
        "farm", "farming", "harvest", "crop", "irrigation", "agriculture",
        "outdoor", "outside", "play", "sport", "exercise", "walk", "run",
        "go out", "outing", "picnic", "construction",
    ),
    "weather": (
        "weather", "temperature", "rain", "rainfall", "wind", "humidity",
        "pressure", "visibility", "cloud", "cloudy", "sunny", "storm",
        "thunder", "lightning", "flood", "heat", "hot", "cold",
        "current weather", "conditions",
    ),
}

# Time phrases that indicate a forecast question
_TIME_KEYWORDS: tuple[str, ...] = (
    "tomorrow", "tonight", "this evening", "later today",
    "next week", "next few days", "coming days", "this afternoon",
    "this morning", "next hour", "next 24 hours", "next 48 hours",
)

# Activity-specific keywords mapped to their canonical label
_ACTIVITY_MAP: dict[str, str] = {
    "travel": "travel",
    "drive": "travel",
    "driving": "travel",
    "commute": "travel",
    "road": "travel",
    "farm": "farming",
    "farming": "farming",
    "harvest": "farming",
    "crop": "farming",
    "irrigation": "farming",
    "agriculture": "farming",
    "outdoor": "outdoor",
    "outside": "outdoor",
    "play": "outdoor",
    "sport": "outdoor",
    "exercise": "outdoor",
    "walk": "outdoor",
    "run": "outdoor",
    "go out": "outdoor",
    "outing": "outdoor",
    "picnic": "outdoor",
    "construction": "outdoor",
}

# Intents that DO NOT need weather data to answer
_NO_WEATHER_DATA_INTENTS: frozenset[IntentType] = frozenset({"general"})

# Evaluation order — higher priority intents are evaluated first
_PRIORITY_ORDER: tuple[IntentType, ...] = (
    "advisory",
    "activity",
    "forecast",
    "risk",
    "weather",
    "general",
)


# --------------------------------------------------------------------------- #
# IntentService                                                                #
# --------------------------------------------------------------------------- #

class IntentService:
    """
    Stateless, deterministic intent extractor.

    Usage
    -----
    >>> service = IntentService()
    >>> result = service.extract("Can I travel tomorrow?")
    >>> result.intent
    'activity'
    >>> result.activity
    'travel'
    >>> result.time_reference
    'tomorrow'
    """

    def extract(self, message: str) -> IntentResult:
        """
        Extract structured intent from a natural-language message.

        Parameters
        ----------
        message:
            The user's raw chat message.

        Returns
        -------
        IntentResult:
            Classified intent with optional activity and time_reference.
        """
        lower = message.lower()

        # ------------------------------------------------------------- #
        # Score each intent by keyword matches                            #
        # ------------------------------------------------------------- #
        scores: dict[IntentType, int] = {k: 0 for k in _INTENT_KEYWORDS}
        for intent, keywords in _INTENT_KEYWORDS.items():
            for kw in keywords:
                if kw in lower:
                    # Longer phrase matches score more
                    scores[intent] += len(kw.split())

        # ------------------------------------------------------------- #
        # Resolve winning intent in priority order                        #
        # ------------------------------------------------------------- #
        winning_intent: IntentType = "general"
        winning_score = 0
        for intent in _PRIORITY_ORDER:
            if scores.get(intent, 0) > winning_score:
                winning_score = scores[intent]
                winning_intent = intent

        # ------------------------------------------------------------- #
        # Extract activity                                                #
        # ------------------------------------------------------------- #
        activity: str | None = None
        for kw, label in sorted(
            _ACTIVITY_MAP.items(), key=lambda x: -len(x[0])
        ):
            if kw in lower:
                activity = label
                break

        # ------------------------------------------------------------- #
        # Extract time reference                                          #
        # ------------------------------------------------------------- #
        time_reference: str | None = None
        for phrase in sorted(_TIME_KEYWORDS, key=lambda x: -len(x)):
            if phrase in lower:
                time_reference = phrase
                break

        requires_weather_data = winning_intent not in _NO_WEATHER_DATA_INTENTS

        # Confidence: ratio of matched score to max possible (heuristic)
        max_possible = max(scores.values()) if max(scores.values()) > 0 else 1
        confidence = min(1.0, winning_score / max_possible) if winning_score > 0 else 0.5

        return IntentResult(
            intent=winning_intent,
            activity=activity,
            time_reference=time_reference,
            requires_weather_data=requires_weather_data,
            confidence=round(confidence, 2),
        )
