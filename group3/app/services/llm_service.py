"""
services/llm_service.py
------------------------
LLM provider abstraction, tool registry, and chat orchestration for Phase 5.

Architecture
------------

  LLMProvider (ABC)
      ├── OpenAIProvider   — real OpenAI chat completions
      └── FallbackProvider — deterministic template responses (no API key)

  ChatTools — wraps existing Group 3 services as callable tool functions
      ├── analyse_conditions(WeatherData)
      ├── get_risk_analysis(WeatherData)
      └── get_full_advisory(WeatherData)

  LLMService — orchestrator
      ├── Selects provider based on LLM_API_KEY presence
      ├── Runs tools based on intent
      ├── Feeds structured results into the provider
      └── Returns (answer: str, sources: list[str], mode: ChatMode)

Key constraints
---------------
* The LLM receives structured data — it CANNOT invent weather values.
* Tool functions call existing Phase 1–4 services — no duplication of logic.
* If the API key is missing OR any LLM API call fails, the service
  switches to FallbackProvider and returns mode="fallback".
* Never silently pretend the LLM is working.

Adding a new LLM provider
--------------------------
1. Subclass LLMProvider and implement generate().
2. Set LLM_PROVIDER env var and add a branch in LLMService.__init__().
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

from app.schemas.advisory import AdvisoryRequest
from app.schemas.chat import ChatMessage, ChatMode, IntentResult
from app.schemas.risk import RiskAnalysis
from app.schemas.weather import WeatherData
from app.services.advisory_engine import AdvisoryEngine
from app.services.condition_detector import ConditionDetector
from app.services.evidence_engine import EvidenceEngine
from app.services.impact_engine import ImpactEngine
from app.services.risk_engine import RiskEngine
from app.services.weather_processor import WeatherProcessor

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Optional openai import — gracefully degrade if package is not installed     #
# --------------------------------------------------------------------------- #

try:
    import openai as _openai  # type: ignore[import]
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    _openai = None  # type: ignore[assignment]


# --------------------------------------------------------------------------- #
# System prompt                                                                #
# --------------------------------------------------------------------------- #

_SYSTEM_PROMPT_TEMPLATE = """\
You are WeatherGPT, an AI weather assistant for the WeatherGPT platform.

Your job is to answer the user's weather question using ONLY the structured \
data provided below. Do NOT invent weather values, risk scores, or forecasts. \
If specific information is not in the context, say clearly that it is \
unavailable rather than guessing.

Keep answers concise, factual, and actionable (2–4 sentences).

{context_block}
"""


def _build_context_block(tool_results: dict[str, Any]) -> str:
    """Render structured tool results as a readable context block for the LLM."""
    if not tool_results:
        return "No weather data is available for this query."

    lines: list[str] = []

    if "weather" in tool_results:
        w = tool_results["weather"]
        lines.append("=== Current Weather ===")
        lines.append(f"Location : {w.get('location', 'Unknown')}")
        lines.append(f"Timestamp: {w.get('timestamp', 'N/A')}")
        for field in ("temperature", "rainfall", "wind_speed", "humidity",
                       "visibility", "pressure"):
            if w.get(field) is not None:
                lines.append(f"{field.replace('_', ' ').title()}: {w[field]}")
        lines.append("")

    if "risk" in tool_results:
        r = tool_results["risk"]
        lines.append("=== Risk Analysis ===")
        lines.append(f"Overall: {r.get('overall_level')} (score {r.get('overall_score')})")
        for risk_item in r.get("risks", []):
            lines.append(
                f"  {risk_item['type'].title()}: {risk_item['level']} "
                f"(score {risk_item['score']})"
            )
        lines.append("")

    if "advisory" in tool_results:
        a = tool_results["advisory"]
        lines.append("=== Advisories ===")
        for adv in a.get("advisories", []):
            lines.append(
                f"  [{adv['priority']}] {adv['category'].title()}: {adv['message']}"
            )
        lines.append("")

    if "conditions" in tool_results:
        conds = tool_results["conditions"]
        if conds:
            lines.append("=== Detected Conditions ===")
            for c in conds:
                lines.append(f"  {c.get('type')}: {c.get('severity')} — {c.get('reason', '')}")
            lines.append("")

    if "evidence" in tool_results:
        ev = tool_results["evidence"]
        lines.append("=== Evidence & Confidence ===")
        lines.append(f"Confidence: {ev.get('confidence', 'N/A')}/100")
        comp = ev.get('completeness_score', 0)
        fresh = ev.get('freshness_score', 0)
        cert = ev.get('rule_certainty_score', 0)
        lines.append(
            f"  Breakdown: completeness {comp}/40, "
            f"freshness {fresh}/30, rule certainty {cert}/30"
        )
        uncertainties = ev.get('uncertainty', [])
        if uncertainties:
            lines.append(f"  Uncertainties: {'; '.join(uncertainties[:3])}")
        for item in ev.get('evidence', [])[:6]:   # top 6 evidence items
            lines.append(
                f"  [{item['source'].upper()}] {item['data']} — {item['reason']}"
            )
        lines.append("")

    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# ChatTools — wraps existing Group 3 services                                 #
# --------------------------------------------------------------------------- #

class ChatTools:
    """
    Exposes existing Group 3 engines as structured tool functions.

    All tool functions call the SAME service instances used by the
    /analyze, /risk, and /advisory endpoints — no logic is duplicated.
    """

    def __init__(self) -> None:
        self._processor   = WeatherProcessor()
        self._detector    = ConditionDetector()
        self._risk_engine = RiskEngine()
        self._impact      = ImpactEngine()
        self._advisory    = AdvisoryEngine()

    def analyse_conditions(self, weather: WeatherData) -> list[dict]:
        """Run Phase 2 condition detection; return a list of condition dicts."""
        processed = self._processor.process(weather)
        conditions = self._detector.detect_all(processed)
        return [c.model_dump() for c in conditions]

    def get_risk_analysis(self, weather: WeatherData) -> dict:
        """Run Phase 3 risk engine; return a RiskAnalysis dict."""
        processed   = self._processor.process(weather)
        conditions  = self._detector.detect_all(processed)
        risk: RiskAnalysis = self._risk_engine.analyse(weather, conditions)
        return risk.model_dump()

    def get_full_advisory(self, weather: WeatherData) -> dict:
        """Run Phase 3 + Phase 4 pipeline; return impacts + advisories dict."""
        processed    = self._processor.process(weather)
        conditions   = self._detector.detect_all(processed)
        risk: RiskAnalysis = self._risk_engine.analyse(weather, conditions)
        impacts      = self._impact.assess(weather, risk)
        advisories   = self._advisory.generate(impacts)
        return {
            "impacts":   [i.model_dump() for i in impacts],
            "advisories": [a.model_dump() for a in advisories],
        }

    def get_weather_summary(self, weather: WeatherData) -> dict:
        """Return a flat summary of observed weather values."""
        return {
            "location":       weather.location,
            "timestamp":      weather.timestamp.isoformat(),
            "temperature":    weather.temperature,
            "rainfall":       weather.rainfall,
            "wind_speed":     weather.wind_speed,
            "humidity":       weather.humidity,
            "visibility":     weather.visibility,
            "pressure":       weather.pressure,
            "wind_direction": weather.wind_direction,
        }


# --------------------------------------------------------------------------- #
# Abstract provider                                                            #
# --------------------------------------------------------------------------- #

class LLMProvider(ABC):
    """Abstract base for LLM response generators."""

    @abstractmethod
    async def generate(
        self,
        user_message: str,
        context_block: str,
        history: list[ChatMessage],
    ) -> str:
        """
        Generate a grounded response.

        Parameters
        ----------
        user_message:
            The latest user message.
        context_block:
            Pre-rendered structured data (weather, risk, advisories).
        history:
            Previous turns in the conversation (oldest first).

        Returns
        -------
        str:
            Natural-language answer. Must be grounded in context_block.
        """


# --------------------------------------------------------------------------- #
# OpenAI provider                                                              #
# --------------------------------------------------------------------------- #

class OpenAIProvider(LLMProvider):
    """
    OpenAI chat completions provider.

    Uses AsyncOpenAI for non-blocking requests.
    The LLM receives structured context — it cannot invent weather values.
    """

    def __init__(self, api_key: str, model: str) -> None:
        if not OPENAI_AVAILABLE:
            raise RuntimeError(
                "openai package is not installed. "
                "Run: pip install 'openai>=1.0.0'"
            )
        self._client = _openai.AsyncOpenAI(api_key=api_key)
        self._model  = model

    async def generate(
        self,
        user_message: str,
        context_block: str,
        history: list[ChatMessage],
    ) -> str:
        system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(
            context_block=context_block
        )

        messages: list[dict] = [{"role": "system", "content": system_prompt}]

        # Append recent conversation history (up to last 6 turns)
        for msg in history[-6:]:
            if msg.role in {"user", "assistant"}:
                messages.append({"role": msg.role, "content": msg.content})

        # Append the current user message
        messages.append({"role": "user", "content": user_message})

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=0.3,        # low temperature = more factual
            max_tokens=400,
        )

        return (response.choices[0].message.content or "").strip()


# --------------------------------------------------------------------------- #
# Fallback provider                                                            #
# --------------------------------------------------------------------------- #

class FallbackProvider(LLMProvider):
    """
    Deterministic template-based provider used when:
      - LLM_API_KEY is not set.
      - The LLM API call fails for any reason.

    Generates structured, readable responses from the context_block without
    any LLM call.  Mode is always "fallback".
    """

    async def generate(
        self,
        user_message: str,
        context_block: str,
        history: list[ChatMessage],
    ) -> str:
        if not context_block or context_block.startswith("No weather data"):
            return (
                "I cannot answer that question without current weather data. "
                "Please provide a weather observation alongside your query."
            )

        # Extract the most actionable line from the advisory block
        advisory_line = ""
        risk_line = ""
        for line in context_block.splitlines():
            line = line.strip()
            if line.startswith("[") and ":" in line and not advisory_line:
                advisory_line = line.split(":", 1)[1].strip()
            if line.startswith("Overall:") and not risk_line:
                risk_line = line.replace("Overall:", "").strip()

        parts: list[str] = []
        if risk_line:
            parts.append(f"Current overall risk is {risk_line}.")
        if advisory_line:
            parts.append(advisory_line)
        if not parts:
            parts.append(
                "Weather data has been processed. "
                "Please enable the AI service for a detailed natural-language answer."
            )

        return " ".join(parts)


# --------------------------------------------------------------------------- #
# LLMService                                                                  #
# --------------------------------------------------------------------------- #

class LLMService:
    """
    Orchestrates intent → tools → LLM response.

    Responsibilities
    ----------------
    1. Select provider on startup (OpenAI if key present, else Fallback).
    2. Run appropriate ChatTools based on intent.
    3. Build the context block from tool results.
    4. Call the selected provider to generate a grounded answer.
    5. Return (answer, sources, mode).

    The mode is always set truthfully — never silently pretend LLM is active.
    """

    def __init__(
        self,
        api_key: str = "",
        model: str = "gpt-4o",
        provider: str = "openai",
    ) -> None:
        self._tools           = ChatTools()
        self._evidence_engine = EvidenceEngine()
        self._mode: ChatMode

        if api_key and OPENAI_AVAILABLE:
            try:
                self._provider: LLMProvider = OpenAIProvider(api_key, model)
                self._mode = "llm"
                logger.info("LLMService: OpenAI provider active (model=%s).", model)
            except Exception as exc:
                logger.warning(
                    "LLMService: Failed to initialise OpenAI provider (%s). "
                    "Falling back to template mode.",
                    exc,
                )
                self._provider = FallbackProvider()
                self._mode = "fallback"
        else:
            self._provider = FallbackProvider()
            self._mode = "fallback"
            if not api_key:
                logger.info("LLMService: No API key — running in fallback mode.")

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    @property
    def mode(self) -> ChatMode:
        """Current operating mode: 'llm' or 'fallback'."""
        return self._mode

    def override_provider(self, provider: LLMProvider, mode: ChatMode) -> None:
        """
        Replace the active provider at runtime.

        Intended for use in tests only — inject a mock provider without
        reconstructing the service.
        """
        self._provider = provider
        self._mode = mode

    async def respond(
        self,
        user_message: str,
        weather_data: Optional[WeatherData],
        intent: IntentResult,
        history: list[ChatMessage],
    ) -> tuple[str, list[str], ChatMode]:
        """
        Run the full tool → context → LLM pipeline.

        Parameters
        ----------
        user_message:
            The user's latest question.
        weather_data:
            Optional WeatherData from the request. None → no tool calls.
        intent:
            Extracted intent from IntentService.
        history:
            Conversation history from ContextService.

        Returns
        -------
        (answer, sources, mode)
        """
        tool_results: dict[str, Any] = {}
        sources: list[str] = []

        # ------------------------------------------------------------- #
        # Tool execution — driven by intent + data availability          #
        # ------------------------------------------------------------- #
        if weather_data is not None and intent.requires_weather_data:
            # Weather summary is always included when data is present
            tool_results["weather"] = self._tools.get_weather_summary(weather_data)
            sources.append("weather")

            if intent.intent in {"risk", "advisory", "activity", "general", "weather"}:
                tool_results["risk"] = self._tools.get_risk_analysis(weather_data)
                sources.append("risk")

            if intent.intent in {"advisory", "activity", "general"}:
                adv = self._tools.get_full_advisory(weather_data)
                tool_results["advisory"] = adv
                sources.append("advisory")

            if intent.intent in {"weather", "forecast"}:
                conds = self._tools.analyse_conditions(weather_data)
                if conds:
                    tool_results["conditions"] = conds

        # ------------------------------------------------------------- #
        # Evidence + confidence (always runs when weather_data present)  #
        # ------------------------------------------------------------- #
        if weather_data is not None:
            evidence_result = self._evidence_engine.generate(
                weather  = weather_data,
                risk     = tool_results.get("risk"),
                advisory = tool_results.get("advisory"),
            )
            tool_results["evidence"] = evidence_result.model_dump()

        # ------------------------------------------------------------- #
        # Build context block                                             #
        # ------------------------------------------------------------- #
        context_block = _build_context_block(tool_results)

        # ------------------------------------------------------------- #
        # Generate answer via provider                                   #
        # ------------------------------------------------------------- #
        try:
            answer = await self._provider.generate(
                user_message=user_message,
                context_block=context_block,
                history=history,
            )
        except Exception as exc:
            logger.error(
                "LLM provider failed (%s). Switching to fallback for this request.",
                exc,
            )
            # Per-request fallback guarantees that a single transient network timeout or rate-limit
            # does not permanently downgrade the server instance for subsequent queries,
            # while ensuring the current user still receives an immediate rule-based advisory.
            fallback = FallbackProvider()
            answer = await fallback.generate(user_message, context_block, history)
            return answer, sources, "fallback"

        return answer, sources, self._mode
