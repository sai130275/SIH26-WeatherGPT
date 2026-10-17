"""
tests/test_risk_assessment.py
-----------------------------
Unit tests for ComprehensiveRiskEngine (Module 1.2).
"""

from datetime import datetime, timezone
import pytest

from app.schemas.unified_weather import CurrentWeather, ProviderInfo
from app.services.risk_assessment import ComprehensiveRiskEngine


@pytest.fixture
def provider() -> ProviderInfo:
    return ProviderInfo(name="test_provider")


@pytest.fixture
def engine() -> ComprehensiveRiskEngine:
    return ComprehensiveRiskEngine()


def test_comprehensive_risk_all_hazards(engine: ComprehensiveRiskEngine, provider: ProviderInfo):
    obs = CurrentWeather(
        location="Warangal",
        latitude=17.9689,
        longitude=79.5941,
        timestamp=datetime.now(tz=timezone.utc),
        rainfall=60.0,
        temperature=42.0,
        wind_speed=70.0,
        visibility=1.5,
        cape=1800.0,
        provider=provider,
    )

    assessment = engine.assess(obs)

    assert assessment.classification == "HEURISTIC_RISK"
    assert "disaster warning" in assessment.disclaimer.lower()
    assert assessment.overall_score >= 75
    assert assessment.overall_level in ("HIGH", "SEVERE")

    # Check that individual hazards are present
    hazard_types = {h.hazard for h in assessment.risks}
    assert "rain" in hazard_types
    assert "heat" in hazard_types
    assert "wind" in hazard_types
    assert "storm" in hazard_types
    assert "visibility" in hazard_types
    assert "flood" in hazard_types

    # Check evidence & factors
    rain_risk = next(h for h in assessment.risks if h.hazard == "rain")
    assert rain_risk.score >= 75
    assert len(rain_risk.contributing_factors) >= 1
    assert len(rain_risk.evidence) >= 1
    assert rain_risk.classification == "HEURISTIC_RISK"


def test_storm_risk_lightning_detection(engine: ComprehensiveRiskEngine, provider: ProviderInfo):
    obs = CurrentWeather(
        location="ThunderCity",
        latitude=12.0,
        longitude=80.0,
        timestamp=datetime.now(tz=timezone.utc),
        lightning=True,
        cape=2200.0,
        provider=provider,
    )

    assessment = engine.assess(obs)
    storm_risk = next(h for h in assessment.risks if h.hazard == "storm")
    assert storm_risk.score >= 75
    assert storm_risk.level == "SEVERE"
    assert any("lightning" in f.lower() for f in storm_risk.contributing_factors)


def test_mild_weather_minimal_risks(engine: ComprehensiveRiskEngine, provider: ProviderInfo):
    obs = CurrentWeather(
        location="PleasantVille",
        latitude=12.0,
        longitude=80.0,
        timestamp=datetime.now(tz=timezone.utc),
        temperature=24.0,
        rainfall=0.0,
        wind_speed=10.0,
        visibility=12.0,
        provider=provider,
    )

    assessment = engine.assess(obs)
    assert assessment.overall_score <= 25
    assert assessment.overall_level == "LOW"
