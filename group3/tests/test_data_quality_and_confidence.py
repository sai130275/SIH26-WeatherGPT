"""
tests/test_data_quality_and_confidence.py
-----------------------------------------
Unit tests for DataQualityEngine and ExplainableConfidenceEngine (Module 1.2).
"""

from datetime import datetime, timedelta, timezone
import pytest

from app.schemas.intelligence import ConflictingField
from app.schemas.unified_weather import CurrentWeather, ForecastPoint, ForecastWeather, ProviderInfo
from app.services.confidence_engine import ExplainableConfidenceEngine
from app.services.data_quality import DataQualityEngine


@pytest.fixture
def provider() -> ProviderInfo:
    return ProviderInfo(name="test_provider")


@pytest.fixture
def quality_engine() -> DataQualityEngine:
    return DataQualityEngine()


@pytest.fixture
def confidence_engine() -> ExplainableConfidenceEngine:
    return ExplainableConfidenceEngine()


def test_data_quality_fresh_and_complete(quality_engine: DataQualityEngine, provider: ProviderInfo):
    now = datetime.now(tz=timezone.utc)
    obs = CurrentWeather(
        location="Warangal",
        latitude=17.9689,
        longitude=79.5941,
        timestamp=now - timedelta(minutes=10),
        temperature=32.0,
        rainfall=0.0,
        wind_speed=15.0,
        visibility=10.0,
        humidity=65.0,
        pressure=1010.0,
        provider=provider,
    )

    report = quality_engine.evaluate(obs, reference_time=now)
    assert report.freshness_score == 30
    assert report.completeness_score == 40
    assert report.quality_score >= 0.95
    assert len(report.missing_fields) < 12


def test_data_quality_stale_and_partial(quality_engine: DataQualityEngine, provider: ProviderInfo):
    now = datetime.now(tz=timezone.utc)
    obs = CurrentWeather(
        location="OldStation",
        latitude=17.9,
        longitude=79.5,
        timestamp=now - timedelta(hours=3),  # 3 hours old
        temperature=30.0,  # only temperature present
        provider=provider,
    )

    report = quality_engine.evaluate(obs, reference_time=now)
    assert report.freshness_score == 0
    assert report.completeness_score == 7
    assert report.quality_score <= 0.25
    assert "rainfall" in report.missing_fields
    assert "wind_speed" in report.missing_fields


def test_explainable_confidence_fresh_complete(
    quality_engine: DataQualityEngine,
    confidence_engine: ExplainableConfidenceEngine,
    provider: ProviderInfo,
):
    now = datetime.now(tz=timezone.utc)
    obs = CurrentWeather(
        location="Warangal",
        latitude=17.9689,
        longitude=79.5941,
        timestamp=now - timedelta(minutes=5),
        temperature=32.0,
        rainfall=0.0,
        wind_speed=15.0,
        visibility=10.0,
        humidity=65.0,
        pressure=1010.0,
        provider=provider,
    )

    quality = quality_engine.evaluate(obs, reference_time=now)
    confidence = confidence_engine.compute(quality, obs, forecast_days=1)

    assert confidence.confidence_score >= 85
    assert confidence.breakdown.completeness_points == 40
    assert confidence.breakdown.freshness_points == 30
    assert confidence.breakdown.provider_agreement_points == 20
    assert len(confidence.uncertainties) == 0


def test_confidence_penalties_for_missing_and_horizon(
    quality_engine: DataQualityEngine,
    confidence_engine: ExplainableConfidenceEngine,
    provider: ProviderInfo,
):
    now = datetime.now(tz=timezone.utc)
    # Missing temperature & rainfall, 7-day forecast
    obs = CurrentWeather(
        location="Gaps",
        latitude=17.9,
        longitude=79.5,
        timestamp=now - timedelta(hours=2, minutes=30),
        wind_speed=20.0,
        provider=provider,
    )

    # 7-day forecast mock
    points = [ForecastPoint(timestamp=now + timedelta(hours=i), temperature=25.0) for i in range(168)]
    fw = ForecastWeather(location="Gaps", latitude=17.9, longitude=79.5, hourly=points, provider=provider)

    conflicts = [
        ConflictingField(
            field_name="wind_speed",
            provider_values={"p1": 20.0, "p2": 45.0},
            discrepancy=25.0,
            resolution="weighted_average",
        )
    ]

    quality = quality_engine.evaluate(obs, conflicting_fields=conflicts, reference_time=now)
    confidence = confidence_engine.compute(quality, obs, forecast=fw, forecast_days=7)

    assert confidence.confidence_score < 40
    assert confidence.breakdown.horizon_penalty > 0
    assert confidence.breakdown.critical_missing_penalty > 0
    assert len(confidence.uncertainties) >= 3
    assert any("critical" in u.lower() for u in confidence.uncertainties)
