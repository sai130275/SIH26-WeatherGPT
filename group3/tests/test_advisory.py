"""
tests/test_advisory.py
-----------------------
Comprehensive tests for Phase 4: Impact Engine, Advisory Engine, POST /advisory.

Coverage
--------
* ImpactEngine
  - normal / low-risk weather → no impacts
  - high rain risk → travel + outdoor + farming impacts
  - high wind risk → travel + outdoor + farming impacts
  - high heat risk → outdoor + farming impacts
  - poor visibility → travel + outdoor impacts
  - multiple simultaneous hazards → all categories triggered
  - general impact requires HIGH or SEVERE overall risk
  - each impact category independently
  - missing optional weather values (no crash, no fabrication)
  - deterministic output

* AdvisoryEngine
  - one advisory per impact
  - advisory priority mirrors impact severity
  - message is non-empty and non-generic fallback for known pairs
  - reason carries through from impact
  - empty impacts → empty advisories
  - deterministic output

* POST /advisory
  - HTTP 200 for valid payload
  - response shape: location, overall_risk_level, impacts, advisories
  - each advisory has category, priority, message, reason
  - severe scenario → advisory list non-empty
  - minimal payload (no optional fields) → no crash
  - deterministic across identical requests
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.advisory import (
    Advisory,
    AdvisoryRequest,
    AdvisoryResponse,
    ImpactResult,
)
from app.schemas.risk import RiskAnalysis, RiskResult
from app.schemas.weather import WeatherData
from app.services.advisory_engine import AdvisoryEngine, _MESSAGE_TABLE
from app.services.impact_engine import ImpactEngine


# --------------------------------------------------------------------------- #
# Fixtures & shared builders                                                   #
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(scope="module")
def impact_engine() -> ImpactEngine:
    return ImpactEngine()


@pytest.fixture(scope="module")
def advisory_engine() -> AdvisoryEngine:
    return AdvisoryEngine()


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


def _risk_result(
    rtype: str,
    score: int,
    level: str,
    reasons: list[str] | None = None,
) -> RiskResult:
    return RiskResult(
        type=rtype,  # type: ignore[arg-type]
        score=score,
        level=level,  # type: ignore[arg-type]
        reasons=reasons or [f"{rtype} risk reason."],
    )


def _risk(
    results: list[RiskResult],
    overall_score: int,
    overall_level: str,
) -> RiskAnalysis:
    return RiskAnalysis(
        risks=results,
        overall_score=overall_score,
        overall_level=overall_level,  # type: ignore[arg-type]
    )


def _low_risk() -> RiskAnalysis:
    """A safe, low-risk scenario — no impacts should trigger."""
    return _risk(
        results=[
            _risk_result("rain",  10, "LOW"),
            _risk_result("wind",  10, "LOW"),
            _risk_result("heat",  10, "LOW"),
            _risk_result("flood", 10, "LOW"),
        ],
        overall_score=10,
        overall_level="LOW",
    )


def _high_rain_risk() -> RiskAnalysis:
    return _risk(
        results=[
            _risk_result("rain",  75, "SEVERE"),
            _risk_result("flood", 70, "HIGH"),
            _risk_result("wind",  10, "LOW"),
            _risk_result("heat",  10, "LOW"),
        ],
        overall_score=75,
        overall_level="SEVERE",
    )


def _high_wind_risk() -> RiskAnalysis:
    return _risk(
        results=[
            _risk_result("wind", 75, "SEVERE"),
            _risk_result("rain", 10, "LOW"),
            _risk_result("heat", 10, "LOW"),
        ],
        overall_score=75,
        overall_level="SEVERE",
    )


def _high_heat_risk() -> RiskAnalysis:
    return _risk(
        results=[
            _risk_result("heat", 75, "SEVERE"),
            _risk_result("rain", 10, "LOW"),
            _risk_result("wind", 10, "LOW"),
        ],
        overall_score=75,
        overall_level="SEVERE",
    )


def _poor_visibility_risk() -> RiskAnalysis:
    return _risk(
        results=[
            _risk_result("visibility", 95, "SEVERE"),
            _risk_result("rain",       30, "MODERATE"),
            _risk_result("wind",       10, "LOW"),
        ],
        overall_score=95,
        overall_level="SEVERE",
    )


def _all_hazards_risk() -> RiskAnalysis:
    return _risk(
        results=[
            _risk_result("rain",       75, "SEVERE"),
            _risk_result("wind",       75, "SEVERE"),
            _risk_result("heat",       75, "SEVERE"),
            _risk_result("visibility", 95, "SEVERE"),
            _risk_result("flood",      89, "SEVERE"),
        ],
        overall_score=100,
        overall_level="SEVERE",
    )


# =========================================================================== #
# ImpactEngine                                                                 #
# =========================================================================== #

class TestImpactEngine:

    # ------------------------------------------------------------------ #
    # Normal / low risk                                                    #
    # ------------------------------------------------------------------ #

    def test_low_risk_no_impacts(self, impact_engine: ImpactEngine) -> None:
        weather = _weather(rainfall=2.0, wind_speed=5.0, temperature=25.0, visibility=15.0)
        impacts = impact_engine.assess(weather, _low_risk())
        assert impacts == []

    def test_returns_list(self, impact_engine: ImpactEngine) -> None:
        weather = _weather()
        impacts = impact_engine.assess(weather, _low_risk())
        assert isinstance(impacts, list)

    # ------------------------------------------------------------------ #
    # High rain risk                                                       #
    # ------------------------------------------------------------------ #

    def test_high_rain_triggers_travel(self, impact_engine: ImpactEngine) -> None:
        weather = _weather(rainfall=72.0)
        impacts = impact_engine.assess(weather, _high_rain_risk())
        types = [i.type for i in impacts]
        assert "travel" in types

    def test_high_rain_triggers_outdoor(self, impact_engine: ImpactEngine) -> None:
        weather = _weather(rainfall=72.0)
        impacts = impact_engine.assess(weather, _high_rain_risk())
        types = [i.type for i in impacts]
        assert "outdoor" in types

    def test_high_rain_triggers_farming(self, impact_engine: ImpactEngine) -> None:
        weather = _weather(rainfall=72.0)
        impacts = impact_engine.assess(weather, _high_rain_risk())
        types = [i.type for i in impacts]
        assert "farming" in types

    def test_high_rain_triggers_general(self, impact_engine: ImpactEngine) -> None:
        """Overall SEVERE should trigger general impact."""
        weather = _weather(rainfall=72.0)
        impacts = impact_engine.assess(weather, _high_rain_risk())
        types = [i.type for i in impacts]
        assert "general" in types

    # ------------------------------------------------------------------ #
    # High wind risk                                                       #
    # ------------------------------------------------------------------ #

    def test_high_wind_triggers_travel(self, impact_engine: ImpactEngine) -> None:
        weather = _weather(wind_speed=85.0)
        impacts = impact_engine.assess(weather, _high_wind_risk())
        types = [i.type for i in impacts]
        assert "travel" in types

    def test_high_wind_triggers_outdoor(self, impact_engine: ImpactEngine) -> None:
        weather = _weather(wind_speed=85.0)
        impacts = impact_engine.assess(weather, _high_wind_risk())
        types = [i.type for i in impacts]
        assert "outdoor" in types

    def test_high_wind_triggers_farming(self, impact_engine: ImpactEngine) -> None:
        weather = _weather(wind_speed=85.0)
        impacts = impact_engine.assess(weather, _high_wind_risk())
        types = [i.type for i in impacts]
        assert "farming" in types

    # ------------------------------------------------------------------ #
    # High heat risk                                                       #
    # ------------------------------------------------------------------ #

    def test_high_heat_triggers_outdoor(self, impact_engine: ImpactEngine) -> None:
        weather = _weather(temperature=42.0)
        impacts = impact_engine.assess(weather, _high_heat_risk())
        types = [i.type for i in impacts]
        assert "outdoor" in types

    def test_high_heat_triggers_farming(self, impact_engine: ImpactEngine) -> None:
        weather = _weather(temperature=42.0)
        impacts = impact_engine.assess(weather, _high_heat_risk())
        types = [i.type for i in impacts]
        assert "farming" in types

    def test_high_heat_does_not_trigger_travel_alone(
        self, impact_engine: ImpactEngine
    ) -> None:
        """Heat alone (no rain/wind/vis) should not trigger travel impact."""
        weather = _weather(temperature=42.0)
        heat_only_risk = _risk(
            results=[
                _risk_result("heat", 75, "SEVERE"),
                _risk_result("rain", 10, "LOW"),
                _risk_result("wind", 10, "LOW"),
                _risk_result("visibility", 10, "LOW"),
            ],
            overall_score=75,
            overall_level="SEVERE",
        )
        impacts = impact_engine.assess(weather, heat_only_risk)
        types = [i.type for i in impacts]
        assert "travel" not in types

    # ------------------------------------------------------------------ #
    # Poor visibility                                                      #
    # ------------------------------------------------------------------ #

    def test_poor_visibility_triggers_travel(self, impact_engine: ImpactEngine) -> None:
        weather = _weather(visibility=0.3)
        impacts = impact_engine.assess(weather, _poor_visibility_risk())
        types = [i.type for i in impacts]
        assert "travel" in types

    def test_poor_visibility_triggers_outdoor(self, impact_engine: ImpactEngine) -> None:
        weather = _weather(visibility=0.3)
        impacts = impact_engine.assess(weather, _poor_visibility_risk())
        types = [i.type for i in impacts]
        assert "outdoor" in types

    # ------------------------------------------------------------------ #
    # All hazards simultaneously                                           #
    # ------------------------------------------------------------------ #

    def test_all_hazards_trigger_all_categories(
        self, impact_engine: ImpactEngine
    ) -> None:
        weather = _weather(
            rainfall=72.0, wind_speed=85.0, temperature=42.0, visibility=0.3
        )
        impacts = impact_engine.assess(weather, _all_hazards_risk())
        types = {i.type for i in impacts}
        assert {"travel", "outdoor", "farming", "general"} == types

    # ------------------------------------------------------------------ #
    # General impact threshold                                             #
    # ------------------------------------------------------------------ #

    def test_general_not_triggered_at_moderate_overall(
        self, impact_engine: ImpactEngine
    ) -> None:
        weather = _weather(rainfall=15.0)
        moderate_risk = _risk(
            results=[_risk_result("rain", 30, "MODERATE")],
            overall_score=30,
            overall_level="MODERATE",
        )
        impacts = impact_engine.assess(weather, moderate_risk)
        types = [i.type for i in impacts]
        assert "general" not in types

    def test_general_triggered_at_high_overall(
        self, impact_engine: ImpactEngine
    ) -> None:
        weather = _weather(rainfall=72.0)
        high_risk = _risk(
            results=[_risk_result("rain", 55, "HIGH")],
            overall_score=55,
            overall_level="HIGH",
        )
        impacts = impact_engine.assess(weather, high_risk)
        types = [i.type for i in impacts]
        assert "general" in types

    # ------------------------------------------------------------------ #
    # Impact fields                                                        #
    # ------------------------------------------------------------------ #

    def test_impact_is_impact_result_type(self, impact_engine: ImpactEngine) -> None:
        weather = _weather(rainfall=72.0)
        impacts = impact_engine.assess(weather, _high_rain_risk())
        for impact in impacts:
            assert isinstance(impact, ImpactResult)

    def test_impact_reason_is_non_empty(self, impact_engine: ImpactEngine) -> None:
        weather = _weather(rainfall=72.0)
        impacts = impact_engine.assess(weather, _high_rain_risk())
        for impact in impacts:
            assert impact.reason.strip() != ""

    def test_impacts_sorted_by_severity(self, impact_engine: ImpactEngine) -> None:
        """Highest severity impacts must appear first."""
        weather = _weather(
            rainfall=72.0, wind_speed=85.0, temperature=42.0, visibility=0.3
        )
        impacts = impact_engine.assess(weather, _all_hazards_risk())
        severity_rank = {"LOW": 0, "MODERATE": 1, "HIGH": 2, "SEVERE": 3}
        scores = [severity_rank[i.severity] for i in impacts]
        assert scores == sorted(scores, reverse=True)

    # ------------------------------------------------------------------ #
    # Missing optional weather values                                      #
    # ------------------------------------------------------------------ #

    def test_missing_all_met_fields_no_crash(
        self, impact_engine: ImpactEngine
    ) -> None:
        weather = _weather()  # no optional fields
        impacts = impact_engine.assess(weather, _low_risk())
        assert isinstance(impacts, list)

    def test_missing_rainfall_no_rain_value_in_reason(
        self, impact_engine: ImpactEngine
    ) -> None:
        weather = _weather()  # rainfall=None
        impacts = impact_engine.assess(weather, _high_rain_risk())
        for impact in impacts:
            # Reason should not contain fabricated values
            assert "None" not in impact.reason

    # ------------------------------------------------------------------ #
    # Determinism                                                          #
    # ------------------------------------------------------------------ #

    def test_deterministic(self, impact_engine: ImpactEngine) -> None:
        weather = _weather(rainfall=72.0, wind_speed=85.0, temperature=42.0)
        risk = _all_hazards_risk()
        result1 = impact_engine.assess(weather, risk)
        result2 = impact_engine.assess(weather, risk)
        assert [(r.type, r.severity) for r in result1] == [(r.type, r.severity) for r in result2]


# =========================================================================== #
# AdvisoryEngine                                                               #
# =========================================================================== #

class TestAdvisoryEngine:

    def test_empty_impacts_returns_empty(self, advisory_engine: AdvisoryEngine) -> None:
        assert advisory_engine.generate([]) == []

    def test_one_advisory_per_impact(self, advisory_engine: AdvisoryEngine) -> None:
        impacts = [
            ImpactResult(type="travel", severity="HIGH", reason="Heavy rain."),
            ImpactResult(type="outdoor", severity="SEVERE", reason="Extreme heat."),
        ]
        advisories = advisory_engine.generate(impacts)
        assert len(advisories) == 2

    def test_advisory_is_advisory_type(self, advisory_engine: AdvisoryEngine) -> None:
        impacts = [ImpactResult(type="travel", severity="HIGH", reason="Rain.")]
        advisories = advisory_engine.generate(impacts)
        assert isinstance(advisories[0], Advisory)

    def test_priority_mirrors_severity(self, advisory_engine: AdvisoryEngine) -> None:
        for severity in ("LOW", "MODERATE", "HIGH", "SEVERE"):
            impacts = [
                ImpactResult(
                    type="travel",
                    severity=severity,  # type: ignore[arg-type]
                    reason="test",
                )
            ]
            advisories = advisory_engine.generate(impacts)
            assert advisories[0].priority == severity

    def test_category_preserved(self, advisory_engine: AdvisoryEngine) -> None:
        for category in ("travel", "outdoor", "farming", "general"):
            impacts = [
                ImpactResult(
                    type=category,  # type: ignore[arg-type]
                    severity="HIGH",
                    reason="test",
                )
            ]
            advisories = advisory_engine.generate(impacts)
            assert advisories[0].category == category

    def test_reason_passthrough(self, advisory_engine: AdvisoryEngine) -> None:
        original_reason = "Heavy rain of 72 mm and wind speed 85 km/h."
        impacts = [ImpactResult(type="travel", severity="HIGH", reason=original_reason)]
        advisories = advisory_engine.generate(impacts)
        assert advisories[0].reason == original_reason

    def test_message_non_empty(self, advisory_engine: AdvisoryEngine) -> None:
        impacts = [ImpactResult(type="farming", severity="SEVERE", reason="test")]
        advisories = advisory_engine.generate(impacts)
        assert advisories[0].message.strip() != ""

    def test_all_category_severity_pairs_in_table(
        self, advisory_engine: AdvisoryEngine
    ) -> None:
        """Every known (category, severity) combination must have a message."""
        for category in ("travel", "outdoor", "farming", "general"):
            for severity in ("LOW", "MODERATE", "HIGH", "SEVERE"):
                assert (category, severity) in _MESSAGE_TABLE, (
                    f"Missing message for ({category!r}, {severity!r})"
                )

    def test_known_pair_not_fallback(self, advisory_engine: AdvisoryEngine) -> None:
        impacts = [ImpactResult(type="travel", severity="SEVERE", reason="test")]
        advisories = advisory_engine.generate(impacts)
        assert advisories[0].message != "Take appropriate precautions for current weather conditions."

    def test_deterministic(self, advisory_engine: AdvisoryEngine) -> None:
        impacts = [
            ImpactResult(type="travel", severity="HIGH", reason="Rain."),
            ImpactResult(type="outdoor", severity="SEVERE", reason="Heat."),
        ]
        result1 = advisory_engine.generate(impacts)
        result2 = advisory_engine.generate(impacts)
        assert [(a.category, a.priority) for a in result1] == [
            (a.category, a.priority) for a in result2
        ]


# =========================================================================== #
# POST /advisory                                                               #
# =========================================================================== #

# Shared payload for HTTP tests
_SEVERE_PAYLOAD = {
    "weather": {
        "location": "Warangal",
        "latitude": 17.9689,
        "longitude": 79.5941,
        "timestamp": "2026-09-28T10:00:00Z",
        "temperature": 42.0,
        "humidity": 90.0,
        "rainfall": 72.0,
        "wind_speed": 85.0,
        "wind_direction": 240.0,
        "pressure": 995.0,
        "visibility": 0.5,
    },
    "risk": {
        "risks": [
            {"type": "rain",       "score": 75, "level": "SEVERE", "reasons": ["Rain band 50–100 mm."]},
            {"type": "wind",       "score": 95, "level": "SEVERE", "reasons": ["Wind >80 km/h."]},
            {"type": "heat",       "score": 75, "level": "SEVERE", "reasons": ["Temp 40–45 °C."]},
            {"type": "visibility", "score": 95, "level": "SEVERE", "reasons": ["Vis <1 km."]},
            {"type": "flood",      "score": 89, "level": "SEVERE", "reasons": ["Composite flood."]},
        ],
        "overall_score": 100,
        "overall_level": "SEVERE",
    },
}

_MINIMAL_PAYLOAD = {
    "weather": {
        "location": "Warangal",
        "latitude": 17.9689,
        "longitude": 79.5941,
        "timestamp": "2026-09-28T10:00:00Z",
    },
    "risk": {
        "risks": [],
        "overall_score": 0,
        "overall_level": "LOW",
    },
}


class TestAdvisoryEndpoint:

    def test_returns_200(self, client: TestClient) -> None:
        response = client.post("/advisory", json=_SEVERE_PAYLOAD)
        assert response.status_code == 200

    def test_response_has_location(self, client: TestClient) -> None:
        response = client.post("/advisory", json=_SEVERE_PAYLOAD)
        assert response.json()["location"] == "Warangal"

    def test_response_has_overall_risk_level(self, client: TestClient) -> None:
        response = client.post("/advisory", json=_SEVERE_PAYLOAD)
        assert "overall_risk_level" in response.json()

    def test_response_has_impacts(self, client: TestClient) -> None:
        response = client.post("/advisory", json=_SEVERE_PAYLOAD)
        assert "impacts" in response.json()
        assert isinstance(response.json()["impacts"], list)

    def test_response_has_advisories(self, client: TestClient) -> None:
        response = client.post("/advisory", json=_SEVERE_PAYLOAD)
        assert "advisories" in response.json()
        assert isinstance(response.json()["advisories"], list)

    def test_severe_scenario_non_empty_advisories(self, client: TestClient) -> None:
        response = client.post("/advisory", json=_SEVERE_PAYLOAD)
        assert len(response.json()["advisories"]) > 0

    def test_each_advisory_has_required_fields(self, client: TestClient) -> None:
        response = client.post("/advisory", json=_SEVERE_PAYLOAD)
        for advisory_item in response.json()["advisories"]:
            assert "category" in advisory_item
            assert "priority" in advisory_item
            assert "message" in advisory_item
            assert "reason" in advisory_item
            assert advisory_item["message"].strip() != ""

    def test_each_impact_has_required_fields(self, client: TestClient) -> None:
        response = client.post("/advisory", json=_SEVERE_PAYLOAD)
        for impact in response.json()["impacts"]:
            assert "type" in impact
            assert "severity" in impact
            assert "reason" in impact
            assert impact["reason"].strip() != ""

    def test_minimal_payload_returns_200(self, client: TestClient) -> None:
        response = client.post("/advisory", json=_MINIMAL_PAYLOAD)
        assert response.status_code == 200

    def test_minimal_payload_empty_advisories(self, client: TestClient) -> None:
        response = client.post("/advisory", json=_MINIMAL_PAYLOAD)
        assert response.json()["advisories"] == []

    def test_all_four_categories_in_severe(self, client: TestClient) -> None:
        response = client.post("/advisory", json=_SEVERE_PAYLOAD)
        impact_types = {i["type"] for i in response.json()["impacts"]}
        assert {"travel", "outdoor", "farming", "general"}.issubset(impact_types)

    def test_deterministic_across_requests(self, client: TestClient) -> None:
        r1 = client.post("/advisory", json=_SEVERE_PAYLOAD).json()
        r2 = client.post("/advisory", json=_SEVERE_PAYLOAD).json()
        assert r1["overall_risk_level"] == r2["overall_risk_level"]
        assert len(r1["advisories"]) == len(r2["advisories"])
        for a1, a2 in zip(r1["advisories"], r2["advisories"]):
            assert a1["category"] == a2["category"]
            assert a1["priority"] == a2["priority"]

    def test_content_type_is_json(self, client: TestClient) -> None:
        response = client.post("/advisory", json=_SEVERE_PAYLOAD)
        assert "application/json" in response.headers.get("content-type", "")
