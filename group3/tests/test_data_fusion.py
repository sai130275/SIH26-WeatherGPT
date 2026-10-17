"""
tests/test_data_fusion.py
-------------------------
Unit tests for DataFusionEngine (Module 1.2).
"""

from datetime import datetime, timezone
import pytest

from app.schemas.unified_weather import CurrentWeather, ProviderInfo
from app.services.data_fusion import DataFusionEngine


@pytest.fixture
def fusion_engine() -> DataFusionEngine:
    return DataFusionEngine()


def test_single_provider_fusion(fusion_engine: DataFusionEngine):
    p = ProviderInfo(name="open_meteo")
    obs = CurrentWeather(
        location="Warangal",
        latitude=17.9689,
        longitude=79.5941,
        timestamp=datetime.now(tz=timezone.utc),
        temperature=30.0,
        provider=p,
    )

    fused, conflicts, summary = fusion_engine.fuse_current([obs])
    assert fused.temperature == 30.0
    assert len(conflicts) == 0
    assert summary.strategy == "single_provider"


def test_missing_field_imputation(fusion_engine: DataFusionEngine):
    # Provider 1 has temp, rain, but NO uv_index or pressure
    p1 = ProviderInfo(name="provider_a")
    obs1 = CurrentWeather(
        location="Warangal",
        latitude=17.9689,
        longitude=79.5941,
        timestamp=datetime.now(tz=timezone.utc),
        temperature=32.0,
        rainfall=5.0,
        provider=p1,
    )

    # Provider 2 has pressure and uv_index
    p2 = ProviderInfo(name="provider_b")
    obs2 = CurrentWeather(
        location="Warangal",
        latitude=17.9689,
        longitude=79.5941,
        timestamp=datetime.now(tz=timezone.utc),
        temperature=32.5,
        pressure=1008.0,
        uv_index=7.5,
        provider=p2,
    )

    fused, conflicts, summary = fusion_engine.fuse_current([obs1, obs2])
    assert fused.temperature is not None
    assert fused.rainfall == 5.0
    assert fused.pressure == 1008.0  # Imputed from provider_b!
    assert fused.uv_index == 7.5     # Imputed from provider_b!
    assert "pressure" in summary.fields_imputed
    assert "uv_index" in summary.fields_imputed


def test_conflicting_values_detection(fusion_engine: DataFusionEngine):
    # Provider 1 says temp is 28°C
    p1 = ProviderInfo(name="open_meteo")
    obs1 = CurrentWeather(
        location="DisputedZone",
        latitude=18.0,
        longitude=79.0,
        timestamp=datetime.now(tz=timezone.utc),
        temperature=28.0,
        wind_speed=20.0,
        provider=p1,
    )

    # Provider 2 says temp is 35°C (delta = 7°C > 2.5°C threshold)
    p2 = ProviderInfo(name="mock_secondary")
    obs2 = CurrentWeather(
        location="DisputedZone",
        latitude=18.0,
        longitude=79.0,
        timestamp=datetime.now(tz=timezone.utc),
        temperature=35.0,
        wind_speed=22.0,
        provider=p2,
    )

    fused, conflicts, summary = fusion_engine.fuse_current([obs1, obs2], strategy="weighted_consensus")
    assert len(conflicts) >= 1
    t_conflict = next(c for c in conflicts if c.field_name == "temperature")
    assert t_conflict.discrepancy == 7.0
    assert summary.conflicts_detected >= 1
    # Check weighted average: open_meteo weight=1.0, mock_secondary weight=0.8
    # (28*1.0 + 35*0.8) / 1.8 = (28 + 28) / 1.8 = 56 / 1.8 ≈ 31.11°C
    assert fused.temperature is not None
    assert 30.5 <= fused.temperature <= 31.5


def test_three_providers_consensus(fusion_engine: DataFusionEngine):
    p1 = ProviderInfo(name="open_meteo")
    p2 = ProviderInfo(name="imd")
    p3 = ProviderInfo(name="tomorrow_io")

    now = datetime.now(tz=timezone.utc)
    obs1 = CurrentWeather(location="Hyd", latitude=17.38, longitude=78.48, timestamp=now, temperature=30.0, rainfall=10.0, provider=p1)
    obs2 = CurrentWeather(location="Hyd", latitude=17.38, longitude=78.48, timestamp=now, temperature=31.0, rainfall=12.0, provider=p2)
    obs3 = CurrentWeather(location="Hyd", latitude=17.38, longitude=78.48, timestamp=now, temperature=29.0, rainfall=8.0, provider=p3)

    fused, conflicts, summary = fusion_engine.fuse_current([obs1, obs2, obs3])
    assert fused.location == "Hyd"
    assert len(summary.providers_evaluated) == 3
    # All values are close, no conflicts
    assert len(conflicts) == 0
    assert fused.temperature is not None
    assert 29.5 <= fused.temperature <= 30.5


def test_empty_observations_raises_value_error(fusion_engine: DataFusionEngine):
    with pytest.raises(ValueError, match="Cannot fuse empty"):
        fusion_engine.fuse_current([])
