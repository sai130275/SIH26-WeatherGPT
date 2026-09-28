"""
tests/test_risk_engine.py
--------------------------
Comprehensive tests for Phase 3: risk rules, risk engine, and POST /risk.

Coverage
--------
* score_to_level — all band boundaries (24, 25, 49, 50, 74, 75, 0, 100)
* rain_risk     — zero, low, moderate, high, severe, missing
* wind_risk     — zero, low, moderate, high, severe, missing
* heat_risk     — zero, low, moderate, high, severe, missing
* visibility_risk — all bands, missing
* flood_risk    — all combinations of available/missing inputs
* overall_risk  — single hazard, multi-hazard escalation, cap at 100, empty
* RiskEngine.analyse — normal, severe, missing fields, determinism
* POST /risk    — HTTP contract, full response shape, example request
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.analysis import DetectedCondition
from app.schemas.risk import RiskAnalysis, RiskResult, score_to_level
from app.schemas.weather import WeatherData
from app.services.risk_engine import RiskEngine
from app.services.risk_rules import (
    flood_risk,
    heat_risk,
    overall_risk,
    rain_risk,
    visibility_risk,
    wind_risk,
)


# --------------------------------------------------------------------------- #
# Shared fixtures                                                              #
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(scope="module")
def engine() -> RiskEngine:
    return RiskEngine()


_NOW = datetime(2026, 9, 28, 10, 0, 0, tzinfo=timezone.utc)


def _weather(**overrides) -> WeatherData:
    base: dict = {
        "location": "Warangal",
        "latitude": 17.9689,
        "longitude": 79.5941,
        "timestamp": _NOW,
    }
    base.update(overrides)
    return WeatherData(**base)


def _heavy_rain_condition() -> DetectedCondition:
    return DetectedCondition(
        type="heavy_rain",
        severity="high",
        value=72.0,
        unit="mm",
        threshold=50.0,
        reason="Rainfall of 72.0 mm exceeds threshold.",
    )


# =========================================================================== #
# score_to_level — boundary tests                                              #
# =========================================================================== #

class TestScoreToLevel:
    def test_score_0_is_low(self) -> None:
        assert score_to_level(0) == "LOW"

    def test_score_24_is_low(self) -> None:
        assert score_to_level(24) == "LOW"

    def test_score_25_is_moderate(self) -> None:
        assert score_to_level(25) == "MODERATE"

    def test_score_49_is_moderate(self) -> None:
        assert score_to_level(49) == "MODERATE"

    def test_score_50_is_high(self) -> None:
        assert score_to_level(50) == "HIGH"

    def test_score_74_is_high(self) -> None:
        assert score_to_level(74) == "HIGH"

    def test_score_75_is_severe(self) -> None:
        assert score_to_level(75) == "SEVERE"

    def test_score_100_is_severe(self) -> None:
        assert score_to_level(100) == "SEVERE"

    def test_score_clamps_below_zero(self) -> None:
        assert score_to_level(-10) == "LOW"

    def test_score_clamps_above_100(self) -> None:
        assert score_to_level(110) == "SEVERE"


# =========================================================================== #
# rain_risk                                                                    #
# =========================================================================== #

class TestRainRisk:
    def test_missing_returns_zero(self) -> None:
        score, reasons = rain_risk(None)
        assert score == 0
        assert len(reasons) >= 1
        assert "unavailable" in reasons[0].lower()

    def test_zero_rainfall(self) -> None:
        score, _ = rain_risk(0.0)
        assert score == 10

    def test_low_rainfall_band(self) -> None:
        # 5 mm → 0–10 band → score 10 (LOW)
        score, _ = rain_risk(5.0)
        assert score == 10
        assert score_to_level(score) == "LOW"

    def test_moderate_band(self) -> None:
        # 15 mm → 10–25 band → score 30 (MODERATE)
        score, _ = rain_risk(15.0)
        assert score == 30
        assert score_to_level(score) == "MODERATE"

    def test_high_band(self) -> None:
        # 35 mm → 25–50 band → score 55 (HIGH)
        score, _ = rain_risk(35.0)
        assert score == 55
        assert score_to_level(score) == "HIGH"

    def test_severe_lower_band(self) -> None:
        # 72 mm → 50–100 band → score 75 (SEVERE)
        score, _ = rain_risk(72.0)
        assert score == 75
        assert score_to_level(score) == "SEVERE"

    def test_extreme_rainfall(self) -> None:
        # 150 mm → >100 band → score 95 (SEVERE)
        score, _ = rain_risk(150.0)
        assert score == 95
        assert score_to_level(score) == "SEVERE"

    def test_exactly_at_band_boundary_10(self) -> None:
        # Exactly 10 mm → still in 10–25 band (lower bound exclusive)
        score, _ = rain_risk(10.0)
        assert score == 30

    def test_exactly_at_band_boundary_25(self) -> None:
        score, _ = rain_risk(25.0)
        assert score == 55

    def test_exactly_at_band_boundary_50(self) -> None:
        score, _ = rain_risk(50.0)
        assert score == 75

    def test_exactly_at_band_boundary_100(self) -> None:
        score, _ = rain_risk(100.0)
        assert score == 95

    def test_reason_is_non_empty(self) -> None:
        _, reasons = rain_risk(30.0)
        assert len(reasons) >= 1
        assert reasons[0] != ""

    def test_deterministic(self) -> None:
        assert rain_risk(42.0) == rain_risk(42.0)


# =========================================================================== #
# wind_risk                                                                    #
# =========================================================================== #

class TestWindRisk:
    def test_missing_returns_zero(self) -> None:
        score, reasons = wind_risk(None)
        assert score == 0
        assert "unavailable" in reasons[0].lower()

    def test_calm_wind(self) -> None:
        score, _ = wind_risk(5.0)
        assert score == 10
        assert score_to_level(score) == "LOW"

    def test_moderate_wind(self) -> None:
        score, _ = wind_risk(30.0)
        assert score == 30
        assert score_to_level(score) == "MODERATE"

    def test_strong_wind(self) -> None:
        score, _ = wind_risk(50.0)
        assert score == 55
        assert score_to_level(score) == "HIGH"

    def test_high_wind(self) -> None:
        score, _ = wind_risk(70.0)
        assert score == 75
        assert score_to_level(score) == "SEVERE"

    def test_extreme_wind(self) -> None:
        score, _ = wind_risk(100.0)
        assert score == 95
        assert score_to_level(score) == "SEVERE"

    def test_boundary_20(self) -> None:
        score, _ = wind_risk(20.0)
        assert score == 30

    def test_boundary_40(self) -> None:
        score, _ = wind_risk(40.0)
        assert score == 55

    def test_boundary_60(self) -> None:
        score, _ = wind_risk(60.0)
        assert score == 75

    def test_boundary_80(self) -> None:
        score, _ = wind_risk(80.0)
        assert score == 95

    def test_deterministic(self) -> None:
        assert wind_risk(65.0) == wind_risk(65.0)


# =========================================================================== #
# heat_risk                                                                    #
# =========================================================================== #

class TestHeatRisk:
    def test_missing_returns_zero(self) -> None:
        score, reasons = heat_risk(None)
        assert score == 0
        assert "unavailable" in reasons[0].lower()

    def test_cool_temperature(self) -> None:
        score, _ = heat_risk(20.0)
        assert score == 10
        assert score_to_level(score) == "LOW"

    def test_warm_temperature(self) -> None:
        score, _ = heat_risk(32.0)
        assert score == 30
        assert score_to_level(score) == "MODERATE"

    def test_hot_temperature(self) -> None:
        score, _ = heat_risk(37.0)
        assert score == 55
        assert score_to_level(score) == "HIGH"

    def test_very_hot_temperature(self) -> None:
        score, _ = heat_risk(42.0)
        assert score == 75
        assert score_to_level(score) == "SEVERE"

    def test_extreme_temperature(self) -> None:
        score, _ = heat_risk(48.0)
        assert score == 95
        assert score_to_level(score) == "SEVERE"

    def test_boundary_30(self) -> None:
        score, _ = heat_risk(30.0)
        assert score == 30

    def test_boundary_35(self) -> None:
        score, _ = heat_risk(35.0)
        assert score == 55

    def test_boundary_40(self) -> None:
        score, _ = heat_risk(40.0)
        assert score == 75

    def test_boundary_45(self) -> None:
        score, _ = heat_risk(45.0)
        assert score == 95

    def test_deterministic(self) -> None:
        assert heat_risk(38.0) == heat_risk(38.0)


# =========================================================================== #
# visibility_risk                                                               #
# =========================================================================== #

class TestVisibilityRisk:
    def test_missing_returns_zero(self) -> None:
        score, reasons = visibility_risk(None)
        assert score == 0
        assert "unavailable" in reasons[0].lower()

    def test_clear_visibility(self) -> None:
        score, _ = visibility_risk(15.0)
        assert score == 10
        assert score_to_level(score) == "LOW"

    def test_good_visibility(self) -> None:
        # 7 km → 5–10 band → score 30
        score, _ = visibility_risk(7.0)
        assert score == 30
        assert score_to_level(score) == "MODERATE"

    def test_moderate_visibility(self) -> None:
        # 3 km → 2–5 band → score 55
        score, _ = visibility_risk(3.0)
        assert score == 55
        assert score_to_level(score) == "HIGH"

    def test_poor_visibility(self) -> None:
        # 1.5 km → 1–2 band → score 75
        score, _ = visibility_risk(1.5)
        assert score == 75
        assert score_to_level(score) == "SEVERE"

    def test_very_poor_visibility(self) -> None:
        # 0.3 km → <1 band → score 95
        score, _ = visibility_risk(0.3)
        assert score == 95
        assert score_to_level(score) == "SEVERE"

    def test_boundary_exactly_1km(self) -> None:
        # 1.0 km → 1–2 band → score 75
        score, _ = visibility_risk(1.0)
        assert score == 75

    def test_boundary_exactly_2km(self) -> None:
        # 2.0 km → 2–5 band → score 55
        score, _ = visibility_risk(2.0)
        assert score == 55

    def test_boundary_exactly_5km(self) -> None:
        # 5.0 km → 5–10 band → score 30
        score, _ = visibility_risk(5.0)
        assert score == 30

    def test_boundary_exactly_10km(self) -> None:
        # 10.0 km → >10 band → score 10
        score, _ = visibility_risk(10.0)
        assert score == 10

    def test_deterministic(self) -> None:
        assert visibility_risk(0.8) == visibility_risk(0.8)


# =========================================================================== #
# flood_risk                                                                   #
# =========================================================================== #

class TestFloodRisk:
    def test_no_data_returns_zero(self) -> None:
        score, reasons = flood_risk(None, [], None, None)
        assert score == 0

    def test_rainfall_only_no_conditions(self) -> None:
        score, reasons = flood_risk(72.0, [], None, None)
        assert score > 0
        assert any("72" in r for r in reasons)

    def test_heavy_rain_condition_increases_score(self) -> None:
        score_no_cond, _ = flood_risk(72.0, [], None, None)
        score_with_cond, _ = flood_risk(72.0, [_heavy_rain_condition()], None, None)
        assert score_with_cond >= score_no_cond

    def test_humidity_signal_in_valid_range(self) -> None:
        """Adding a humidity signal must produce a valid score (0–100)."""
        score, _ = flood_risk(72.0, [], 90.0, None)  # humidity ≥ 85%
        assert 0 <= score <= 100

    def test_low_pressure_signal_in_valid_range(self) -> None:
        """Adding a low-pressure signal must produce a valid score (0–100)."""
        score, _ = flood_risk(72.0, [], None, 995.0)  # pressure < 1000 hPa
        assert 0 <= score <= 100

    def test_full_data_highest_score(self) -> None:
        score_full, _ = flood_risk(72.0, [_heavy_rain_condition()], 90.0, 995.0)
        score_minimal, _ = flood_risk(72.0, [], None, None)
        assert score_full >= score_minimal

    def test_score_within_range(self) -> None:
        score, _ = flood_risk(150.0, [_heavy_rain_condition()], 92.0, 990.0)
        assert 0 <= score <= 100

    def test_reasons_always_non_empty(self) -> None:
        _, reasons = flood_risk(30.0, [], 70.0, 1005.0)
        assert len(reasons) >= 1

    def test_missing_rainfall_excludes_rain_component(self) -> None:
        """Without rainfall the rainfall component reason must mention exclusion."""
        _, reasons = flood_risk(None, [_heavy_rain_condition()], 90.0, 990.0)
        assert any("excluded" in r.lower() or "unavailable" in r.lower() for r in reasons)

    def test_no_data_at_all_returns_zero(self) -> None:
        """No rainfall, no conditions, no signals → score 0."""
        score, _ = flood_risk(None, [], None, None)
        assert score == 0

    def test_deterministic(self) -> None:
        args = (72.0, [_heavy_rain_condition()], 90.0, 990.0)
        assert flood_risk(*args) == flood_risk(*args)


# =========================================================================== #
# overall_risk                                                                 #
# =========================================================================== #

class TestOverallRisk:
    def test_empty_list_returns_zero(self) -> None:
        score, reasons = overall_risk([])
        assert score == 0

    def test_single_hazard(self) -> None:
        score, _ = overall_risk([75])
        assert score == 75

    def test_max_of_hazards(self) -> None:
        score, _ = overall_risk([30, 10, 55])
        # No multi-hazard escalation (only one ≥ 50)
        assert score == 55

    def test_multi_hazard_escalation(self) -> None:
        # Two hazards ≥ 50 → +10
        score, reasons = overall_risk([55, 75])
        assert score == 85
        assert any("escalation" in r.lower() for r in reasons)

    def test_multi_hazard_escalation_three_hazards(self) -> None:
        score, _ = overall_risk([50, 55, 75])
        assert score == 85

    def test_cap_at_100(self) -> None:
        score, _ = overall_risk([95, 95, 95])
        assert score == 100

    def test_no_escalation_when_only_one_high(self) -> None:
        score, _ = overall_risk([75, 30, 10])
        # Only one hazard ≥ 50 → no escalation
        assert score == 75

    def test_score_boundary_24(self) -> None:
        score, _ = overall_risk([24])
        assert score_to_level(score) == "LOW"

    def test_score_boundary_25(self) -> None:
        score, _ = overall_risk([25])
        assert score_to_level(score) == "MODERATE"

    def test_score_boundary_49(self) -> None:
        score, _ = overall_risk([49])
        assert score_to_level(score) == "MODERATE"

    def test_score_boundary_50(self) -> None:
        score, _ = overall_risk([50])
        assert score_to_level(score) == "HIGH"

    def test_score_boundary_74(self) -> None:
        score, _ = overall_risk([74])
        assert score_to_level(score) == "HIGH"

    def test_score_boundary_75(self) -> None:
        score, _ = overall_risk([75])
        assert score_to_level(score) == "SEVERE"

    def test_deterministic(self) -> None:
        assert overall_risk([55, 75, 30]) == overall_risk([55, 75, 30])


# =========================================================================== #
# RiskEngine.analyse                                                           #
# =========================================================================== #

class TestRiskEngine:
    def test_normal_weather_low_risk(self, engine: RiskEngine) -> None:
        data = _weather(temperature=25.0, rainfall=3.0, wind_speed=10.0, visibility=15.0)
        analysis = engine.analyse(data, [])
        assert analysis.overall_level in ("LOW", "MODERATE")

    def test_severe_weather_high_overall(self, engine: RiskEngine) -> None:
        data = _weather(rainfall=120.0, wind_speed=100.0, temperature=48.0, visibility=0.2)
        conditions = [_heavy_rain_condition()]
        analysis = engine.analyse(data, conditions)
        assert analysis.overall_score >= 75
        assert analysis.overall_level == "SEVERE"

    def test_returns_risk_analysis_type(self, engine: RiskEngine) -> None:
        data = _weather(rainfall=10.0)
        analysis = engine.analyse(data, [])
        assert isinstance(analysis, RiskAnalysis)

    def test_each_risk_is_risk_result(self, engine: RiskEngine) -> None:
        data = _weather(rainfall=10.0, wind_speed=15.0, temperature=28.0)
        analysis = engine.analyse(data, [])
        assert all(isinstance(r, RiskResult) for r in analysis.risks)

    def test_level_consistent_with_score(self, engine: RiskEngine) -> None:
        data = _weather(rainfall=72.0, wind_speed=85.0)
        analysis = engine.analyse(data, [_heavy_rain_condition()])
        for risk_result in analysis.risks:
            assert risk_result.level == score_to_level(risk_result.score)
        assert analysis.overall_level == score_to_level(analysis.overall_score)

    def test_missing_rainfall_skips_rain_risk(self, engine: RiskEngine) -> None:
        data = _weather(temperature=30.0, wind_speed=20.0)
        analysis = engine.analyse(data, [])
        types = [r.type for r in analysis.risks]
        assert "rain" not in types

    def test_missing_wind_skips_wind_risk(self, engine: RiskEngine) -> None:
        data = _weather(rainfall=10.0, temperature=30.0)
        analysis = engine.analyse(data, [])
        types = [r.type for r in analysis.risks]
        assert "wind" not in types

    def test_missing_temperature_skips_heat_risk(self, engine: RiskEngine) -> None:
        data = _weather(rainfall=10.0, wind_speed=20.0)
        analysis = engine.analyse(data, [])
        types = [r.type for r in analysis.risks]
        assert "heat" not in types

    def test_missing_visibility_skips_visibility_risk(self, engine: RiskEngine) -> None:
        data = _weather(rainfall=10.0)
        analysis = engine.analyse(data, [])
        types = [r.type for r in analysis.risks]
        assert "visibility" not in types

    def test_flood_always_present(self, engine: RiskEngine) -> None:
        """Flood result is always included (it manages its own missing-data logic)."""
        data = _weather(rainfall=10.0)
        analysis = engine.analyse(data, [])
        types = [r.type for r in analysis.risks]
        assert "flood" in types

    def test_all_reasons_non_empty(self, engine: RiskEngine) -> None:
        data = _weather(rainfall=72.0, wind_speed=85.0, temperature=43.0, visibility=0.5)
        analysis = engine.analyse(data, [_heavy_rain_condition()])
        for risk_result in analysis.risks:
            assert len(risk_result.reasons) >= 1
            for reason in risk_result.reasons:
                assert reason.strip() != ""

    def test_overall_score_in_range(self, engine: RiskEngine) -> None:
        data = _weather(rainfall=200.0, wind_speed=200.0, temperature=60.0, visibility=0.0)
        analysis = engine.analyse(data, [_heavy_rain_condition()])
        assert 0 <= analysis.overall_score <= 100

    def test_deterministic_results(self, engine: RiskEngine) -> None:
        data = _weather(rainfall=72.0, wind_speed=55.0, temperature=38.0)
        conditions = [_heavy_rain_condition()]
        result1 = engine.analyse(data, conditions)
        result2 = engine.analyse(data, conditions)
        assert result1.overall_score == result2.overall_score
        assert result1.overall_level == result2.overall_level

    def test_no_optional_fields(self, engine: RiskEngine) -> None:
        """Engine must not crash when all optional met fields are missing."""
        data = _weather()
        analysis = engine.analyse(data, [])
        assert isinstance(analysis, RiskAnalysis)
        assert analysis.overall_score >= 0


# =========================================================================== #
# POST /risk — HTTP contract                                                   #
# =========================================================================== #

class TestRiskEndpoint:
    def test_returns_200(self, client: TestClient) -> None:
        payload = {
            "location": "Warangal",
            "latitude": 17.9689,
            "longitude": 79.5941,
            "timestamp": "2026-09-28T10:00:00Z",
            "temperature": 31.5,
            "humidity": 72.0,
            "rainfall": 72.0,
            "wind_speed": 18.2,
            "wind_direction": 240.0,
            "pressure": 1008.5,
            "visibility": 8.5,
        }
        response = client.post("/risk", json=payload)
        assert response.status_code == 200

    def test_response_has_risks_key(self, client: TestClient) -> None:
        payload = {
            "location": "Warangal",
            "latitude": 17.9689,
            "longitude": 79.5941,
            "timestamp": "2026-09-28T10:00:00Z",
            "rainfall": 72.0,
        }
        response = client.post("/risk", json=payload)
        data = response.json()
        assert "risks" in data

    def test_response_has_overall_score(self, client: TestClient) -> None:
        payload = {
            "location": "Warangal",
            "latitude": 17.9689,
            "longitude": 79.5941,
            "timestamp": "2026-09-28T10:00:00Z",
            "rainfall": 72.0,
        }
        response = client.post("/risk", json=payload)
        data = response.json()
        assert "overall_score" in data
        assert "overall_level" in data

    def test_overall_score_is_integer_in_range(self, client: TestClient) -> None:
        payload = {
            "location": "Warangal",
            "latitude": 17.9689,
            "longitude": 79.5941,
            "timestamp": "2026-09-28T10:00:00Z",
            "rainfall": 50.0,
            "wind_speed": 65.0,
            "temperature": 42.0,
            "visibility": 0.5,
        }
        response = client.post("/risk", json=payload)
        data = response.json()
        assert 0 <= data["overall_score"] <= 100

    def test_each_risk_has_required_fields(self, client: TestClient) -> None:
        payload = {
            "location": "Warangal",
            "latitude": 17.9689,
            "longitude": 79.5941,
            "timestamp": "2026-09-28T10:00:00Z",
            "rainfall": 72.0,
            "wind_speed": 85.0,
        }
        response = client.post("/risk", json=payload)
        data = response.json()
        for risk_result in data["risks"]:
            assert "type" in risk_result
            assert "score" in risk_result
            assert "level" in risk_result
            assert "reasons" in risk_result
            assert isinstance(risk_result["reasons"], list)
            assert len(risk_result["reasons"]) >= 1

    def test_minimal_payload_does_not_crash(self, client: TestClient) -> None:
        """Only required identity fields — all optional met fields absent."""
        payload = {
            "location": "Warangal",
            "latitude": 17.9689,
            "longitude": 79.5941,
            "timestamp": "2026-09-28T10:00:00Z",
        }
        response = client.post("/risk", json=payload)
        assert response.status_code == 200

    def test_severe_rainfall_gives_severe_rain_risk(self, client: TestClient) -> None:
        payload = {
            "location": "Warangal",
            "latitude": 17.9689,
            "longitude": 79.5941,
            "timestamp": "2026-09-28T10:00:00Z",
            "rainfall": 120.0,   # >100 mm → score 95 → SEVERE
        }
        response = client.post("/risk", json=payload)
        data = response.json()
        rain_risk_result = next(r for r in data["risks"] if r["type"] == "rain")
        assert rain_risk_result["level"] == "SEVERE"
        assert rain_risk_result["score"] == 95
