"""
tests/test_chat.py
-------------------
Comprehensive tests for Phase 5: LLM / AI Query Engine.

Coverage
--------
IntentService
  - weather intent
  - forecast intent
  - risk intent
  - advisory intent
  - activity intent (travel, farming, outdoor)
  - general intent (default / no match)
  - activity extraction
  - time reference extraction
  - requires_weather_data flag
  - determinism

ContextService
  - add and retrieve messages
  - conversation isolation
  - sliding-window max messages
  - clear conversation
  - list_ids / message_count
  - empty conversation returns empty list

ChatTools
  - analyse_conditions returns list of dicts
  - get_risk_analysis returns dict with known keys
  - get_full_advisory returns impacts + advisories
  - get_weather_summary returns flat dict

LLMService (fallback mode — no API key)
  - mode is "fallback" when no key
  - returns (answer, sources, mode) tuple
  - answer is non-empty string
  - sources populated when weather_data provided
  - mode is "fallback" with missing API key
  - override_provider enables mock injection

FallbackProvider
  - returns answer when context is available
  - returns "unavailable" message when no context

POST /chat — HTTP contract
  - returns 200
  - response has required fields: conversation_id, answer, sources, mode, intent
  - mode is "fallback" without API key (test env)
  - answer is non-empty
  - conversation_id echoed when provided
  - conversation_id generated when absent
  - intent field reflects detected intent
  - weather question with weather_data → sources include "weather"
  - risk question with weather_data → sources include "risk"
  - advisory question with weather_data → sources include "advisory"
  - missing weather_data → sources empty, answer explains unavailability
  - invalid request (empty message) → 422
  - multi-turn: second request echoes same conversation_id
  - deterministic across identical requests

LLM failure → fallback
  - mock provider that raises exception → mode becomes "fallback"
  - service still returns a valid ChatResponse
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.routes import chat as chat_route
from app.main import app
from app.schemas.chat import ChatMessage, ChatRequest, IntentResult
from app.schemas.weather import WeatherData
from app.services.context_service import ContextService
from app.services.intent_service import IntentService
from app.services.llm_service import (
    ChatTools,
    FallbackProvider,
    LLMService,
    OpenAIProvider,
)


# --------------------------------------------------------------------------- #
# Fixtures                                                                     #
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def intent_svc() -> IntentService:
    return IntentService()


@pytest.fixture
def context_svc() -> ContextService:
    return ContextService()


@pytest.fixture
def tools() -> ChatTools:
    return ChatTools()


_NOW = datetime(2026, 9, 28, 10, 0, 0, tzinfo=timezone.utc)


def _weather(**overrides) -> WeatherData:
    base: dict = {
        "location":  "Warangal",
        "latitude":  17.9689,
        "longitude": 79.5941,
        "timestamp": _NOW,
    }
    base.update(overrides)
    return WeatherData(**base)


def _full_weather() -> WeatherData:
    return _weather(
        temperature=42.0,
        rainfall=72.0,
        wind_speed=85.0,
        humidity=90.0,
        visibility=0.5,
        pressure=995.0,
    )


# --------------------------------------------------------------------------- #
# Chat payload helpers                                                         #
# --------------------------------------------------------------------------- #

_BASE_WEATHER_DICT = {
    "location":    "Warangal",
    "latitude":    17.9689,
    "longitude":   79.5941,
    "timestamp":   "2026-09-28T10:00:00Z",
    "temperature": 42.0,
    "rainfall":    72.0,
    "wind_speed":  85.0,
    "humidity":    90.0,
    "visibility":  0.5,
    "pressure":    995.0,
}


def _payload(message: str, include_weather: bool = True, **extra) -> dict:
    p: dict = {
        "message":         message,
        "location":        {"latitude": 17.9689, "longitude": 79.5941},
        "conversation_id": "test-conv-001",
    }
    if include_weather:
        p["weather_data"] = _BASE_WEATHER_DICT
    p.update(extra)
    return p


# =========================================================================== #
# IntentService                                                                #
# =========================================================================== #

class TestIntentService:

    def test_weather_intent(self, intent_svc: IntentService) -> None:
        result = intent_svc.extract("What is the current temperature?")
        assert result.intent == "weather"

    def test_weather_intent_rain(self, intent_svc: IntentService) -> None:
        result = intent_svc.extract("How much rainfall is expected?")
        assert result.intent in {"weather", "forecast"}

    def test_forecast_intent_tomorrow(self, intent_svc: IntentService) -> None:
        result = intent_svc.extract("Will it rain tomorrow?")
        assert result.intent == "forecast"

    def test_forecast_intent_tonight(self, intent_svc: IntentService) -> None:
        result = intent_svc.extract("What is the weather tonight?")
        assert result.intent == "forecast"

    def test_risk_intent(self, intent_svc: IntentService) -> None:
        result = intent_svc.extract("Is there any danger from the storm?")
        assert result.intent == "risk"

    def test_risk_intent_safe(self, intent_svc: IntentService) -> None:
        result = intent_svc.extract("Is it safe to go outside?")
        assert result.intent in {"risk", "advisory", "activity"}

    def test_advisory_intent(self, intent_svc: IntentService) -> None:
        result = intent_svc.extract("What should I do during the flood warning?")
        assert result.intent == "advisory"

    def test_advisory_intent_recommend(self, intent_svc: IntentService) -> None:
        result = intent_svc.extract("Do you recommend travelling today?")
        assert result.intent in {"advisory", "activity"}

    def test_activity_intent_travel(self, intent_svc: IntentService) -> None:
        result = intent_svc.extract("Can I travel tomorrow evening?")
        assert result.intent in {"activity", "forecast"}

    def test_activity_intent_farm(self, intent_svc: IntentService) -> None:
        result = intent_svc.extract("Is it okay to start farming today?")
        assert result.intent == "activity"

    def test_activity_intent_outdoor(self, intent_svc: IntentService) -> None:
        result = intent_svc.extract("Can I exercise outside right now?")
        assert result.intent == "activity"

    def test_general_intent_default(self, intent_svc: IntentService) -> None:
        result = intent_svc.extract("Hello there!")
        assert result.intent == "general"

    def test_general_intent_unrelated(self, intent_svc: IntentService) -> None:
        result = intent_svc.extract("What is the capital of France?")
        assert result.intent == "general"

    # Activity extraction
    def test_activity_travel_extracted(self, intent_svc: IntentService) -> None:
        result = intent_svc.extract("Can I travel to Hyderabad?")
        assert result.activity == "travel"

    def test_activity_farming_extracted(self, intent_svc: IntentService) -> None:
        result = intent_svc.extract("Is it safe to harvest the crops?")
        assert result.activity == "farming"

    def test_activity_outdoor_extracted(self, intent_svc: IntentService) -> None:
        result = intent_svc.extract("Should I go for a walk?")
        assert result.activity == "outdoor"

    def test_no_activity_when_absent(self, intent_svc: IntentService) -> None:
        result = intent_svc.extract("What is the wind speed?")
        assert result.activity is None

    # Time reference extraction
    def test_time_tomorrow_extracted(self, intent_svc: IntentService) -> None:
        result = intent_svc.extract("Will it rain tomorrow?")
        assert result.time_reference == "tomorrow"

    def test_time_tonight_extracted(self, intent_svc: IntentService) -> None:
        result = intent_svc.extract("How cold will it be tonight?")
        assert result.time_reference == "tonight"

    def test_no_time_when_absent(self, intent_svc: IntentService) -> None:
        result = intent_svc.extract("What is the current temperature?")
        assert result.time_reference is None

    # requires_weather_data
    def test_general_intent_no_weather_needed(self, intent_svc: IntentService) -> None:
        result = intent_svc.extract("Hello!")
        assert result.requires_weather_data is False

    def test_weather_intent_needs_data(self, intent_svc: IntentService) -> None:
        result = intent_svc.extract("What is the temperature?")
        assert result.requires_weather_data is True

    # Determinism
    def test_deterministic(self, intent_svc: IntentService) -> None:
        msg = "Can I travel to the market today safely?"
        r1 = intent_svc.extract(msg)
        r2 = intent_svc.extract(msg)
        assert r1.intent == r2.intent
        assert r1.activity == r2.activity

    def test_returns_intent_result_type(self, intent_svc: IntentService) -> None:
        result = intent_svc.extract("Any weather alerts?")
        assert isinstance(result, IntentResult)

    def test_confidence_between_0_and_1(self, intent_svc: IntentService) -> None:
        result = intent_svc.extract("Is it going to rain?")
        assert 0.0 <= result.confidence <= 1.0


# =========================================================================== #
# ContextService                                                               #
# =========================================================================== #

class TestContextService:

    def test_empty_conversation_returns_empty(self, context_svc: ContextService) -> None:
        assert context_svc.get_history("nonexistent-id") == []

    def test_add_and_retrieve(self, context_svc: ContextService) -> None:
        cid = "ctx-test-001"
        msg = ChatMessage(role="user", content="Hello")
        context_svc.add_message(cid, msg)
        history = context_svc.get_history(cid)
        assert len(history) == 1
        assert history[0].content == "Hello"

    def test_conversation_isolation(self, context_svc: ContextService) -> None:
        cid_a = "ctx-a"
        cid_b = "ctx-b"
        context_svc.add_message(cid_a, ChatMessage(role="user", content="A"))
        context_svc.add_message(cid_b, ChatMessage(role="user", content="B"))
        assert context_svc.get_history(cid_a)[0].content == "A"
        assert context_svc.get_history(cid_b)[0].content == "B"

    def test_sliding_window(self) -> None:
        svc = ContextService(max_messages=3)
        cid = "ctx-window"
        for i in range(5):
            svc.add_message(cid, ChatMessage(role="user", content=f"msg{i}"))
        history = svc.get_history(cid)
        assert len(history) == 3
        assert history[0].content == "msg2"
        assert history[-1].content == "msg4"

    def test_clear_removes_conversation(self, context_svc: ContextService) -> None:
        cid = "ctx-clear"
        context_svc.add_message(cid, ChatMessage(role="user", content="Hi"))
        context_svc.clear(cid)
        assert context_svc.get_history(cid) == []

    def test_clear_nonexistent_does_not_crash(self, context_svc: ContextService) -> None:
        context_svc.clear("never-existed")   # must not raise

    def test_list_ids_includes_added(self, context_svc: ContextService) -> None:
        cid = "ctx-list-test"
        context_svc.add_message(cid, ChatMessage(role="user", content="X"))
        assert cid in context_svc.list_ids()

    def test_message_count(self, context_svc: ContextService) -> None:
        cid = "ctx-count"
        context_svc.add_message(cid, ChatMessage(role="user", content="1"))
        context_svc.add_message(cid, ChatMessage(role="assistant", content="2"))
        assert context_svc.message_count(cid) == 2

    def test_history_is_copy(self, context_svc: ContextService) -> None:
        """Mutating the returned list must not affect internal state."""
        cid = "ctx-copy"
        context_svc.add_message(cid, ChatMessage(role="user", content="orig"))
        history = context_svc.get_history(cid)
        history.clear()
        assert context_svc.message_count(cid) == 1


# =========================================================================== #
# ChatTools                                                                    #
# =========================================================================== #

class TestChatTools:

    def test_analyse_conditions_returns_list(self, tools: ChatTools) -> None:
        result = tools.analyse_conditions(_full_weather())
        assert isinstance(result, list)

    def test_analyse_conditions_item_has_type(self, tools: ChatTools) -> None:
        result = tools.analyse_conditions(_full_weather())
        if result:
            assert "type" in result[0]
            assert "severity" in result[0]

    def test_get_risk_analysis_returns_dict(self, tools: ChatTools) -> None:
        result = tools.get_risk_analysis(_full_weather())
        assert isinstance(result, dict)

    def test_get_risk_analysis_has_overall_score(self, tools: ChatTools) -> None:
        result = tools.get_risk_analysis(_full_weather())
        assert "overall_score" in result
        assert "overall_level" in result
        assert "risks" in result

    def test_get_full_advisory_returns_dict(self, tools: ChatTools) -> None:
        result = tools.get_full_advisory(_full_weather())
        assert isinstance(result, dict)

    def test_get_full_advisory_has_advisories(self, tools: ChatTools) -> None:
        result = tools.get_full_advisory(_full_weather())
        assert "advisories" in result
        assert "impacts" in result

    def test_get_weather_summary_flat_dict(self, tools: ChatTools) -> None:
        result = tools.get_weather_summary(_full_weather())
        assert isinstance(result, dict)
        assert "location" in result
        assert "timestamp" in result
        assert "rainfall" in result

    def test_tools_deterministic(self, tools: ChatTools) -> None:
        w = _full_weather()
        r1 = tools.get_risk_analysis(w)
        r2 = tools.get_risk_analysis(w)
        assert r1["overall_score"] == r2["overall_score"]

    def test_missing_weather_data_no_fabrication(self, tools: ChatTools) -> None:
        """Tools with minimal WeatherData must not crash or invent values."""
        minimal = _weather()  # no optional met fields
        result = tools.get_risk_analysis(minimal)
        assert isinstance(result, dict)


# =========================================================================== #
# FallbackProvider                                                             #
# =========================================================================== #

class TestFallbackProvider:

    def test_returns_string(self) -> None:
        provider = FallbackProvider()
        answer = asyncio.run(
            provider.generate("What is the risk?", "=== Risk Analysis ===\nOverall: HIGH (score 65)\n", [])
        )
        assert isinstance(answer, str)
        assert len(answer) > 0

    def test_no_context_returns_unavailable(self) -> None:
        provider = FallbackProvider()
        answer = asyncio.run(
            provider.generate("What is the weather?", "", [])
        )
        assert "unavailable" in answer.lower() or "cannot" in answer.lower()

    def test_context_with_advisory_uses_it(self) -> None:
        provider = FallbackProvider()
        context = (
            "=== Risk Analysis ===\nOverall: SEVERE (score 95)\n"
            "=== Advisories ===\n[SEVERE] Travel: Do not travel.\n"
        )
        answer = asyncio.run(
            provider.generate("Should I drive?", context, [])
        )
        assert isinstance(answer, str)
        assert len(answer) > 0

    def test_deterministic(self) -> None:
        provider = FallbackProvider()
        context = "=== Risk Analysis ===\nOverall: HIGH (score 65)\n"
        a1 = asyncio.run(
            provider.generate("Is it safe?", context, [])
        )
        a2 = asyncio.run(
            provider.generate("Is it safe?", context, [])
        )
        assert a1 == a2


# =========================================================================== #
# LLMService — fallback mode (no API key in test env)                         #
# =========================================================================== #

class TestLLMServiceFallback:

    def test_mode_is_fallback_without_key(self) -> None:
        svc = LLMService(api_key="", model="gpt-4o")
        assert svc.mode == "fallback"

    def test_respond_returns_tuple(self) -> None:
        svc = LLMService(api_key="")
        intent = IntentResult(intent="risk", requires_weather_data=True)
        answer, sources, mode = asyncio.run(
            svc.respond(
                user_message="What is the risk?",
                weather_data=_full_weather(),
                intent=intent,
                history=[],
            )
        )
        assert isinstance(answer, str)
        assert isinstance(sources, list)
        assert mode == "fallback"

    def test_sources_include_weather_when_data_provided(self) -> None:
        svc = LLMService(api_key="")
        intent = IntentResult(intent="weather", requires_weather_data=True)
        _, sources, _ = asyncio.run(
            svc.respond("Current weather?", _full_weather(), intent, [])
        )
        assert "weather" in sources

    def test_sources_include_risk_for_risk_intent(self) -> None:
        svc = LLMService(api_key="")
        intent = IntentResult(intent="risk", requires_weather_data=True)
        _, sources, _ = asyncio.run(
            svc.respond("What is the risk?", _full_weather(), intent, [])
        )
        assert "risk" in sources

    def test_sources_include_advisory_for_advisory_intent(self) -> None:
        svc = LLMService(api_key="")
        intent = IntentResult(intent="advisory", requires_weather_data=True)
        _, sources, _ = asyncio.run(
            svc.respond("What should I do?", _full_weather(), intent, [])
        )
        assert "advisory" in sources

    def test_no_sources_when_no_weather_data(self) -> None:
        svc = LLMService(api_key="")
        intent = IntentResult(intent="risk", requires_weather_data=True)
        _, sources, _ = asyncio.run(
            svc.respond("What is the risk?", None, intent, [])
        )
        assert sources == []

    def test_answer_non_empty(self) -> None:
        svc = LLMService(api_key="")
        intent = IntentResult(intent="advisory", requires_weather_data=True)
        answer, _, _ = asyncio.run(
            svc.respond("Should I travel?", _full_weather(), intent, [])
        )
        assert answer.strip() != ""

    def test_general_intent_no_weather_needed(self) -> None:
        svc = LLMService(api_key="")
        intent = IntentResult(intent="general", requires_weather_data=False)
        _, sources, _ = asyncio.run(
            svc.respond("Hello!", None, intent, [])
        )
        # general intent does not require weather data → no sources
        assert sources == []

    def test_deterministic_results(self) -> None:
        svc = LLMService(api_key="")
        intent = IntentResult(intent="risk", requires_weather_data=True)
        w = _full_weather()
        a1, s1, m1 = asyncio.run(
            svc.respond("What is the risk?", w, intent, [])
        )
        a2, s2, m2 = asyncio.run(
            svc.respond("What is the risk?", w, intent, [])
        )
        assert s1 == s2
        assert m1 == m2


# =========================================================================== #
# LLMService — mock provider injection                                         #
# =========================================================================== #

class TestLLMServiceMockProvider:

    def _make_mock_provider(self, answer: str) -> MagicMock:
        mock = MagicMock()
        mock.generate = AsyncMock(return_value=answer)
        return mock

    def test_override_provider_used(self) -> None:
        svc = LLMService(api_key="")
        mock = self._make_mock_provider("Mocked answer from LLM.")
        svc.override_provider(mock, "llm")
        assert svc.mode == "llm"

    def test_mock_provider_answer_returned(self) -> None:
        svc = LLMService(api_key="")
        mock = self._make_mock_provider("Heavy rain expected. Avoid travel.")
        svc.override_provider(mock, "llm")
        intent = IntentResult(intent="advisory", requires_weather_data=True)
        answer, _, mode = asyncio.run(
            svc.respond("Should I travel?", _full_weather(), intent, [])
        )
        assert answer == "Heavy rain expected. Avoid travel."
        assert mode == "llm"

    def test_failing_provider_returns_fallback_mode(self) -> None:
        """If the injected provider raises, respond() must return mode='fallback'."""
        svc = LLMService(api_key="")

        async def _raise(*args, **kwargs):  # noqa: ANN002
            raise RuntimeError("LLM API timeout")

        mock = MagicMock()
        mock.generate = _raise
        svc.override_provider(mock, "llm")

        intent = IntentResult(intent="risk", requires_weather_data=True)
        answer, sources, mode = asyncio.run(
            svc.respond("Is it risky?", _full_weather(), intent, [])
        )
        assert mode == "fallback"
        assert isinstance(answer, str)
        assert len(answer) > 0

    def test_mock_provider_generate_called_once(self) -> None:
        svc = LLMService(api_key="")
        mock = self._make_mock_provider("Answer.")
        svc.override_provider(mock, "llm")
        intent = IntentResult(intent="weather", requires_weather_data=True)
        asyncio.run(
            svc.respond("Temperature?", _full_weather(), intent, [])
        )
        assert mock.generate.call_count == 1


# =========================================================================== #
# POST /chat — HTTP contract                                                   #
# =========================================================================== #

class TestChatEndpoint:

    def test_returns_200(self, client: TestClient) -> None:
        response = client.post("/chat", json=_payload("What is the weather?"))
        assert response.status_code == 200

    def test_response_has_required_fields(self, client: TestClient) -> None:
        response = client.post("/chat", json=_payload("What is the risk?"))
        data = response.json()
        assert "conversation_id" in data
        assert "answer" in data
        assert "sources" in data
        assert "mode" in data
        assert "intent" in data

    def test_mode_is_fallback_without_api_key(self, client: TestClient) -> None:
        """In the test environment LLM_API_KEY is empty — must be fallback."""
        response = client.post("/chat", json=_payload("Should I travel?"))
        assert response.json()["mode"] == "fallback"

    def test_answer_is_non_empty(self, client: TestClient) -> None:
        response = client.post("/chat", json=_payload("What are the risks?"))
        assert response.json()["answer"].strip() != ""

    def test_conversation_id_echoed(self, client: TestClient) -> None:
        payload = _payload("Hello", conversation_id="my-session-42")
        response = client.post("/chat", json=payload)
        assert response.json()["conversation_id"] == "my-session-42"

    def test_conversation_id_generated_when_absent(self, client: TestClient) -> None:
        payload = {"message": "What is the temperature?", "weather_data": _BASE_WEATHER_DICT}
        response = client.post("/chat", json=payload)
        assert len(response.json()["conversation_id"]) > 0

    def test_intent_field_present(self, client: TestClient) -> None:
        response = client.post("/chat", json=_payload("Will it rain tomorrow?"))
        assert response.json()["intent"] is not None

    def test_weather_question_sources_include_weather(
        self, client: TestClient
    ) -> None:
        payload = _payload("What is the current temperature?", include_weather=True)
        response = client.post("/chat", json=payload)
        assert "weather" in response.json()["sources"]

    def test_risk_question_sources_include_risk(self, client: TestClient) -> None:
        payload = _payload("Is there any danger?", include_weather=True)
        response = client.post("/chat", json=payload)
        assert "risk" in response.json()["sources"]

    def test_advisory_question_sources_include_advisory(
        self, client: TestClient
    ) -> None:
        payload = _payload("What should I do about the storm?", include_weather=True)
        response = client.post("/chat", json=payload)
        assert "advisory" in response.json()["sources"]

    def test_missing_weather_data_returns_empty_sources(
        self, client: TestClient
    ) -> None:
        payload = {
            "message":         "What is the current risk?",
            "conversation_id": "no-weather-test",
        }
        response = client.post("/chat", json=payload)
        data = response.json()
        assert response.status_code == 200
        assert data["sources"] == []

    def test_missing_weather_data_answer_explains(
        self, client: TestClient
    ) -> None:
        payload = {
            "message": "What is the temperature right now?",
        }
        response = client.post("/chat", json=payload)
        answer = response.json()["answer"].lower()
        assert any(word in answer for word in ["unavailable", "cannot", "provide", "data", "without"])

    def test_invalid_empty_message_returns_422(self, client: TestClient) -> None:
        payload = {"message": "", "conversation_id": "x"}
        response = client.post("/chat", json=payload)
        assert response.status_code == 422

    def test_missing_message_returns_422(self, client: TestClient) -> None:
        payload = {"conversation_id": "x"}
        response = client.post("/chat", json=payload)
        assert response.status_code == 422

    def test_multi_turn_same_conversation(self, client: TestClient) -> None:
        """Two sequential requests with the same conversation_id must both succeed."""
        cid = "multi-turn-test-999"
        r1 = client.post("/chat", json=_payload("What is the risk?", conversation_id=cid))
        r2 = client.post("/chat", json=_payload("And the advisories?", conversation_id=cid))
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r2.json()["conversation_id"] == cid

    def test_deterministic_sources(self, client: TestClient) -> None:
        """Same request → same sources list."""
        payload = _payload("What is the risk?")
        r1 = client.post("/chat", json=payload).json()
        r2 = client.post("/chat", json=payload).json()
        assert sorted(r1["sources"]) == sorted(r2["sources"])

    def test_content_type_is_json(self, client: TestClient) -> None:
        response = client.post("/chat", json=_payload("Weather?"))
        assert "application/json" in response.headers.get("content-type", "")

    def test_activity_travel_intent_recognised(self, client: TestClient) -> None:
        payload = _payload("Can I travel safely today?", include_weather=True)
        response = client.post("/chat", json=payload)
        assert response.json()["intent"] in {"activity", "advisory", "risk"}

    def test_forecast_intent_recognised(self, client: TestClient) -> None:
        payload = _payload("Will it rain tomorrow?", include_weather=True)
        response = client.post("/chat", json=payload)
        assert response.json()["intent"] in {"forecast", "weather"}

    def test_minimal_weather_no_crash(self, client: TestClient) -> None:
        """Minimal WeatherData (no optional met fields) must not crash."""
        payload = {
            "message": "What are the risks?",
            "weather_data": {
                "location":  "Warangal",
                "latitude":  17.9689,
                "longitude": 79.5941,
                "timestamp": "2026-09-28T10:00:00Z",
            },
        }
        response = client.post("/chat", json=payload)
        assert response.status_code == 200

    def test_llm_failure_falls_back(self, client: TestClient) -> None:
        """
        Inject a failing provider into the route singleton.
        The endpoint must still return 200 with mode='fallback'.
        """
        async def _raise(*args, **kwargs):
            raise RuntimeError("Simulated LLM failure")

        mock = MagicMock()
        mock.generate = _raise

        original_mode = chat_route._llm_service.mode
        original_provider = chat_route._llm_service._provider

        try:
            chat_route._llm_service.override_provider(mock, "llm")
            response = client.post("/chat", json=_payload("What is the risk?"))
            assert response.status_code == 200
            assert response.json()["mode"] == "fallback"
        finally:
            # Restore original state so other tests are not affected
            chat_route._llm_service.override_provider(original_provider, original_mode)

    def test_sources_is_list(self, client: TestClient) -> None:
        response = client.post("/chat", json=_payload("Hello!"))
        assert isinstance(response.json()["sources"], list)
