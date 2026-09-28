"""
tests/test_evidence.py
-----------------------
Comprehensive tests for Phase 6: Evidence + Confidence.

Coverage
--------
EvidenceEngine:
  - complete weather data -> high completeness score
  - missing weather fields -> reduced completeness score + uncertainty
  - fresh data (<30m) -> 30 points freshness
  - stale data (>2h) -> 0 points freshness + uncertainty
  - all hazards assessed -> 30 points rule certainty
  - some hazards missing -> reduced rule certainty + uncertainty
  - evidence generation (weather, risk, impact, advisory sources)
  - threshold filtering (only MODERATE+ risk/advisory gets evidence)
  - multiple hazards / multiple evidence sources
  - determinism

LLM Integration:
  - context block includes '=== Evidence & Confidence ==='
  - LLM fallback mode preserves evidence text in logs / output
  - LLM failure drops to fallback safely
  - Confidence calculation logic works independently
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.schemas.chat import ChatMessage, IntentResult
from app.schemas.evidence import ConfidenceResult, EvidenceItem
from app.schemas.weather import WeatherData
from app.services.evidence_engine import EvidenceEngine
from app.services.llm_service import LLMService

# --------------------------------------------------------------------------- #
# Fixtures & Builders                                                          #
# --------------------------------------------------------------------------- #

@pytest.fixture
def evidence_engine() -> EvidenceEngine:
    return EvidenceEngine()

_NOW = datetime(2026, 9, 28, 10, 0, 0, tzinfo=timezone.utc)

def _weather(**overrides) -> WeatherData:
    base = {
        "location": "Warangal",
        "latitude": 17.9689,
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

def _full_risk_dict() -> dict:
    return {
        "overall_level": "SEVERE",
        "overall_score": 95,
        "risks": [
            {"type": "rain", "level": "SEVERE", "score": 90, "reasons": ["Heavy rain"]},
            {"type": "wind", "level": "SEVERE", "score": 85, "reasons": ["High wind"]},
            {"type": "heat", "level": "MODERATE", "score": 45, "reasons": ["Warm"]},
            {"type": "visibility", "level": "LOW", "score": 10, "reasons": ["Clear"]},
            {"type": "flood", "level": "SEVERE", "score": 95, "reasons": ["Flood risk"]},
        ]
    }

def _full_advisory_dict() -> dict:
    return {
        "impacts": [
            {"type": "travel", "severity": "SEVERE", "reason": "Dangerous roads"},
            {"type": "farming", "severity": "HIGH", "reason": "Crop damage likely"}
        ],
        "advisories": [
            {"category": "travel", "priority": "SEVERE", "message": "Do not travel"},
            {"category": "farming", "priority": "HIGH", "message": "Suspend farming"}
        ]
    }

# =========================================================================== #
# EvidenceEngine Tests                                                         #
# =========================================================================== #

class TestEvidenceEngine:

    def test_complete_data_high_confidence(self, evidence_engine: EvidenceEngine) -> None:
        result = evidence_engine.generate(
            weather=_full_weather(),
            risk=_full_risk_dict(),
            advisory=_full_advisory_dict(),
            reference_time=_NOW
        )
        # Completeness: 7*4 + 6*2 = 40
        # Freshness: <30m = 30
        # Rule certainty: 10 base + 5*4 = 30
        # Total = 100
        assert result.completeness_score == 40
        assert result.freshness_score == 30
        assert result.rule_certainty_score == 30
        assert result.confidence == 100
        assert result.uncertainty == []

    def test_missing_weather_fields_reduced_confidence(self, evidence_engine: EvidenceEngine) -> None:
        w = _weather(temperature=42.0) # only temp
        result = evidence_engine.generate(w, risk=_full_risk_dict(), reference_time=_NOW)
        assert result.completeness_score == 7
        assert any("rainfall" in u.lower() for u in result.uncertainty)
        assert result.confidence < 100

    def test_stale_data_reduced_freshness(self, evidence_engine: EvidenceEngine) -> None:
        stale_time = _NOW - timedelta(hours=3)
        w = _full_weather()
        w = _weather(**w.model_dump(exclude={"timestamp"}))
        w = WeatherData(**{**w.model_dump(), "timestamp": stale_time})

        result = evidence_engine.generate(w, reference_time=_NOW)
        assert result.freshness_score == 0
        assert any("old" in u for u in result.uncertainty)

    def test_partially_stale_data(self, evidence_engine: EvidenceEngine) -> None:
        stale_time = _NOW - timedelta(minutes=45)
        w = _full_weather()
        w = WeatherData(**{**w.model_dump(), "timestamp": stale_time})

        result = evidence_engine.generate(w, reference_time=_NOW)
        assert result.freshness_score == 20

    def test_missing_risk_hazards_reduced_rule_certainty(self, evidence_engine: EvidenceEngine) -> None:
        partial_risk = {
            "overall_level": "MODERATE",
            "overall_score": 40,
            "risks": [
                {"type": "rain", "level": "MODERATE", "score": 40, "reasons": []}
            ]
        }
        result = evidence_engine.generate(_full_weather(), risk=partial_risk, reference_time=_NOW)
        # Base 10 + 5 (rain) = 15
        assert result.rule_certainty_score == 15
        assert any("wind" in u.lower() for u in result.uncertainty)

    def test_no_risk_data(self, evidence_engine: EvidenceEngine) -> None:
        result = evidence_engine.generate(_full_weather(), reference_time=_NOW)
        assert result.rule_certainty_score == 0
        assert any("not available" in u.lower() for u in result.uncertainty)

    def test_evidence_generation_sources(self, evidence_engine: EvidenceEngine) -> None:
        result = evidence_engine.generate(
            weather=_full_weather(),
            risk=_full_risk_dict(),
            advisory=_full_advisory_dict(),
            reference_time=_NOW
        )
        sources = {item.source for item in result.evidence}
        assert "weather" in sources
        assert "risk" in sources
        assert "impact" in sources
        assert "advisory" in sources

    def test_multiple_hazards_evidence(self, evidence_engine: EvidenceEngine) -> None:
        result = evidence_engine.generate(
            weather=_full_weather(),
            risk=_full_risk_dict(),
            reference_time=_NOW
        )
        # Should have evidence for rain, wind, heat (all MODERATE+). Visibility is LOW in fixture.
        risk_evidence = [e for e in result.evidence if e.source == "risk"]
        risk_data = " ".join(e.data for e in risk_evidence)
        assert "rain risk" in risk_data
        assert "wind risk" in risk_data
        assert "heat risk" in risk_data
        assert "visibility risk" not in risk_data

    def test_threshold_filtering(self, evidence_engine: EvidenceEngine) -> None:
        w = _weather(temperature=20.0, rainfall=0.0, wind_speed=5.0, visibility=15.0)
        result = evidence_engine.generate(w, reference_time=_NOW)
        weather_evidence = [e for e in result.evidence if e.source == "weather"]
        # None of these are notable
        assert len(weather_evidence) == 0

    def test_deterministic(self, evidence_engine: EvidenceEngine) -> None:
        r1 = evidence_engine.generate(_full_weather(), _full_risk_dict(), _full_advisory_dict(), _NOW)
        r2 = evidence_engine.generate(_full_weather(), _full_risk_dict(), _full_advisory_dict(), _NOW)
        assert r1.confidence == r2.confidence
        assert len(r1.evidence) == len(r2.evidence)

# =========================================================================== #
# LLM Integration Tests                                                        #
# =========================================================================== #

class TestEvidenceLLMIntegration:

    def _make_mock_provider(self, answer: str) -> MagicMock:
        mock = MagicMock()
        mock.generate = AsyncMock(return_value=answer)
        return mock

    def test_evidence_included_in_context(self) -> None:
        svc = LLMService(api_key="")
        
        # We'll mock the provider to just echo the context back so we can assert on it
        async def mock_generate(user_message, context_block, history):
            return context_block
            
        mock = MagicMock()
        mock.generate = mock_generate
        svc.override_provider(mock, "llm")
        
        intent = IntentResult(intent="risk", requires_weather_data=True)
        answer, sources, mode = asyncio.run(
            svc.respond("What is the risk?", _full_weather(), intent, [])
        )
        
        assert "=== Evidence & Confidence ===" in answer
        assert "Confidence:" in answer
        assert "Breakdown: completeness" in answer

    def test_fallback_mode_still_works(self) -> None:
        svc = LLMService(api_key="") # Force fallback
        intent = IntentResult(intent="risk", requires_weather_data=True)
        answer, sources, mode = asyncio.run(
            svc.respond("What is the risk?", _full_weather(), intent, [])
        )
        assert mode == "fallback"
        assert len(answer) > 0
        assert "risk" in sources

    def test_llm_failure_drops_to_fallback(self) -> None:
        svc = LLMService(api_key="")
        
        async def mock_generate(*args, **kwargs):
            raise RuntimeError("API down")
            
        mock = MagicMock()
        mock.generate = mock_generate
        svc.override_provider(mock, "llm")
        
        intent = IntentResult(intent="risk", requires_weather_data=True)
        answer, sources, mode = asyncio.run(
            svc.respond("What is the risk?", _full_weather(), intent, [])
        )
        
        # Should gracefully fail to fallback
        assert mode == "fallback"
        assert len(answer) > 0

    def test_confidence_independent_of_llm(self) -> None:
        # Check that we can run EvidenceEngine completely outside LLM
        engine = EvidenceEngine()
        result = engine.generate(_full_weather())
        assert isinstance(result, ConfidenceResult)
        assert result.confidence > 0
