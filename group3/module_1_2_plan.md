# Module 1.2 Implementation Plan — Weather Intelligence & Data Fusion

## 1. Overview & Objectives

Module 1.1 established the unified weather provider layer (Open-Meteo adapter, Provider Registry, Caching Weather Aggregator, canonical schemas, and weather API endpoints).

**Module 1.2** elevates normalized weather data into a **Weather Intelligence & Data Fusion Layer**.
The engine moves beyond returning raw sensor values; it deterministically interprets observations and forecasts, detects extreme weather events, calculates trends, assesses multi-hazard risks with clear distinction between heuristic risks and official warnings, executes multi-provider data fusion, and delivers an explainable data quality & confidence contract for downstream AI/RAG consumers.

---

## 2. Repository Audit: What Already Exists

| Existing Component | File Path | Current Status & Capabilities |
| :--- | :--- | :--- |
| **Unified Weather Schemas** | `group3/app/schemas/unified_weather.py` | `ProviderInfo`, `CurrentWeather`, `ForecastPoint`, `DailyForecast`, `ForecastWeather`, `HistoricalWeather`, `WeatherResponse`. Full optional-field tracking. |
| **Provider Abstraction** | `group3/app/providers/base.py` | `WeatherProvider` ABC, custom exceptions (`ProviderUnavailableError`, `ProviderRateLimitError`, `ProviderDataError`). |
| **Open-Meteo Provider** | `group3/app/providers/open_meteo.py` | Normalizes current, forecast (hourly + daily), and historical data. |
| **Provider Registry** | `group3/app/providers/registry.py` | Central provider registry with priority-based ordering. |
| **Weather Aggregator** | `group3/app/services/weather_aggregator.py` | In-memory TTL caching and sequential fallback across providers. |
| **Weather Bridge** | `group3/app/services/weather_bridge.py` | Adapter converting `CurrentWeather` + `ForecastWeather` into legacy `WeatherData`. |
| **Legacy Weather Schemas** | `group3/app/schemas/weather.py` | `WeatherData`, `ForecastItem`. |
| **Condition Detector** | `group3/app/services/condition_detector.py` | Pure detector for `heavy_rain`, `high_wind`, `extreme_heat`, `low_visibility`. |
| **Risk Engine & Rules** | `group3/app/services/risk_engine.py`<br>`group3/app/services/risk_rules.py` | Deterministic scoring for rain, wind, heat, visibility, flood, overall (0-100, LOW/MODERATE/HIGH/SEVERE). |
| **Impact & Advisory** | `group3/app/services/impact_engine.py`<br>`group3/app/services/advisory_engine.py` | Sector impacts (travel, outdoor, farming, general) and prioritised advisories. |
| **Evidence & Confidence** | `group3/app/services/evidence_engine.py`<br>`group3/app/schemas/evidence.py` | Deterministic confidence (completeness 40 + freshness 30 + rule certainty 30). |
| **Chat & LLM Service** | `group3/app/services/llm_service.py`<br>`group3/app/api/routes/chat.py` | Tool-grounded chat completion with fallback mode. |
| **Existing Test Suite** | `group3/tests/` | 373 tests covering all legacy and Module 1.1 components. |

---

## 3. What Will Be Reused

1. **Unified Weather Schemas (`unified_weather.py`)**: Foundation for all current and forecast data ingestion.
2. **Provider Registry & Base Provider (`base.py`, `registry.py`)**: Provider registration and discovery interface.
3. **Weather Aggregator (`weather_aggregator.py`)**: Enhanced to incorporate multi-provider fusion alongside fallback.
4. **Existing Risk Rules (`risk_rules.py`)**: Pure deterministic scoring formulas for rain, wind, heat, visibility, and flood.
5. **Existing Severity Band Logic (`condition_detector.py`)**: Existing threshold bands for heavy rain, wind, heat, visibility.
6. **Existing Evidence Engine (`evidence_engine.py`)**: Completeness and freshness metrics reused and generalized into data quality evaluation.
7. **Weather Bridge (`weather_bridge.py`)**: Backward compatibility for routes still consuming `WeatherData`.
8. **All existing endpoints (`/analyze`, `/risk`, `/advisory`, `/chat`, `/weather/*`)**: Maintained with 100% backward compatibility.

---

## 4. What Must Be Added

### 4.1. Weather Analysis Engine (`app/services/weather_analysis.py`)
- **Deterministic Meteorological Computations**:
  - **Thermal Analysis**: Heat Index (Steadman / Rothfusz formula), Wind Chill, Apparent Temperature interpretation (Comfortable, Caution, Extreme Caution, Danger, Extreme Danger).
  - **Humidity & Moisture**: Relative humidity categorization (Dry, Comfortable, Humid, Oppressive/Muggy), Dew Point depression.
  - **Wind & Dynamics**: Beaufort scale wind classification (Calm, Light, Moderate, Strong, Gale, Storm), gust factor evaluation.
  - **Precipitation**: Rain rate classification (None, Slight, Moderate, Heavy, Violent), precipitation probability interpretation.
  - **Visibility & Atmosphere**: Atmospheric clarity (Dense Fog, Fog, Mist, Haze, Clear), barometric pressure status (Deep Low, Low Trough, Normal, High Pressure).
  - **Human-Readable Synthesis**: Deterministic summary sentence ("High apparent heat with oppressive humidity and high rain probability; potentially uncomfortable conditions").

### 4.2. Forecast Intelligence Engine (`app/services/forecast_intelligence.py`)
- **Temporal Analysis of Forecast Time Series**:
  - **Rain Dynamics**: Rain onset time, total rain duration (hours), peak rainfall period (window, peak mm/h), heavy rainfall intervals.
  - **Temperature Dynamics**: Min/Max range, diurnal temperature variation, cooling/warming trends.
  - **Wind Dynamics**: Sustained wind trend, peak gust period, wind shift detection.
  - **Rapid Weather Changes**: Temperature drop/spike (>5°C in 3h), pressure plunge (>3 hPa in 3h), sudden squall onset.
  - **Multi-day Trajectory**: Multi-day summary, weather stability index, forecast consistency.

### 4.3. Weather Trend Engine (`app/services/weather_trend.py`)
- **Metrics Evaluated**: Temperature, Rainfall, Wind Speed, Humidity, Atmospheric Pressure.
- **Trend States**: `increasing`, `decreasing`, `stable`, `rapidly_changing`.
- **Calculations**: First-difference velocity ($$\Delta / \Delta t$$), rate of change per hour, acceleration/rapid change detection.

### 4.4. Extreme Weather Detection Engine (`app/services/extreme_weather.py`)
- **Supported Hazards**:
  - Heavy rain & torrential rain (IMD classifications: Heavy 64.5–115.5mm, Very Heavy 115.6–204.4mm, Extremely Heavy >204.4mm/24h or hourly rate equivalents).
  - Extreme heat (>40°C, >45°C) & heatwave conditions.
  - Extreme cold (<5°C, <0°C) & cold wave conditions.
  - High winds / Gale (>50 km/h, >70 km/h, >90 km/h).
  - Thunderstorm conditions (CAPE > 1000 J/kg, lightning indicator, convective rain+gusts).
  - Rapid temperature change (cold front or sudden heat blast).
  - Low visibility hazards (dense fog <1 km, severe fog <200m).
- **Architecture**:
  - Configurable via `Settings`.
  - Authoritative source tagging: explicit distinction between `HEURISTIC` detection vs authoritative thresholds (e.g. `IMD_STANDARD`).
  - Backward compatible: seamlessly wraps and extends `ConditionDetector`.

### 4.5. Structured Risk Assessment Layer (`app/services/risk_assessment.py`)
- **Hazards**: Rain, Heat, Wind, Storm (new explicit), Flood, Overall.
- **Output Schema**:
  - `risk_level`: `LOW`, `MODERATE`, `HIGH`, `SEVERE`.
  - `hazard_type`: Hazard category.
  - `score`: 0–100.
  - `contributing_factors`: Concrete values triggering the risk.
  - `evidence`: Evidentiary justification.
  - `confidence`: Risk assessment confidence.
  - `classification`: Explicitly distinguishes `HEURISTIC_RISK` from `OFFICIAL_WARNING`.
  - Disclaimer banner: "Heuristic meteorological risk calculation. Not an official government disaster warning."

### 4.6. Multi-Provider Data Fusion Engine (`app/services/data_fusion.py`)
- **Fusion Pipeline**:
  ```
  Provider Observations (A, B, C...)
              ↓
      Data Normalization & Alignment
              ↓
      Cross-Provider Comparison (variance, delta, outlier detection)
              ↓
      Quality Assessment & Provider Reliability Weighting
              ↓
      Field-Level Selection / Weighted Fusion
              ↓
      Unified Fused Observation + Conflict Manifest
  ```
- **Capabilities**:
  - Temporal alignment within tolerance window.
  - Missing field imputation from complementary providers.
  - Conflicting value detection (e.g. temperature delta > 3°C, rain delta > 10mm).
  - Pluggable provider weights and reliability scores.

### 4.7. Data Quality & Confidence Engine (`app/services/data_quality.py`, `app/services/confidence_engine.py`)
- **Data Quality**:
  - Freshness (seconds since observation, freshness score).
  - Completeness (percentage of core & secondary fields present).
  - Conflict tracking (list of conflicting fields across providers).
  - Overall quality score (0.0 to 1.0 or 0 to 100).
- **Confidence Engine**:
  - Quantifiable inputs: Freshness score, Completeness score, Provider agreement score, Forecast horizon decay factor, Missing critical field penalties.
  - Explainable factors and uncertainty list.

### 4.8. Unified Intelligence Contract & API Endpoints
- **Schemas (`app/schemas/intelligence.py`)**:
  - `CurrentIntelligence`
  - `ForecastIntelligence`
  - `ExtremeWeatherEvent`
  - `WeatherTrendReport`
  - `HazardRiskAssessment`
  - `DataQualityReport`
  - `ConfidenceAssessment`
  - `WeatherIntelligenceResponse`
- **Endpoints (`app/api/routes/weather.py` & `app/api/routes/intelligence.py`)**:
  - `GET /weather/intelligence`: Full end-to-end intelligence for coordinates.
  - `POST /weather/intelligence/analyze`: Run intelligence on client-supplied `CurrentWeather` + `ForecastWeather`.

---

## 5. Proposed Files & Directory Structure

```
group3/app/
├── schemas/
│   ├── unified_weather.py          # Existing (Module 1.1)
│   ├── intelligence.py             # NEW: Intelligence contract schemas
│   └── ...
├── services/
│   ├── weather_analysis.py         # NEW: Deterministic current weather analysis
│   ├── forecast_intelligence.py    # NEW: Rain onset, duration, temporal analysis
│   ├── weather_trend.py            # NEW: Trend calculations (temp, wind, rain, pressure)
│   ├── extreme_weather.py          # NEW: IMD & heuristic extreme event detection
│   ├── risk_assessment.py          # NEW: Comprehensive risk with HEURISTIC_RISK distinction
│   ├── data_quality.py             # NEW: Data quality evaluation & conflict detection
│   ├── confidence_engine.py        # NEW: Explainable multi-factor confidence engine
│   ├── data_fusion.py              # NEW: Multi-provider comparison & fusion engine
│   ├── weather_aggregator.py       # MODIFIED: Integrated with data fusion & multi-provider query
│   └── weather_intelligence.py     # NEW: Orchestrator service combining all components
├── api/routes/
│   ├── weather.py                  # MODIFIED: Added /weather/intelligence endpoints
│   └── intelligence.py             # NEW (or sub-router): Dedicated intelligence endpoints
group3/tests/
├── test_weather_analysis.py        # NEW: Test thermal, moisture, wind, pressure analysis
├── test_forecast_intelligence.py   # NEW: Test rain onset, duration, peak periods, changes
├── test_weather_trend.py           # NEW: Test trend states (increasing, decreasing, etc.)
├── test_extreme_weather.py         # NEW: Test severe events & IMD classifications
├── test_risk_assessment.py         # NEW: Test risk scoring, heuristic vs official warning
├── test_data_quality.py            # NEW: Test completeness, freshness, conflict detection
├── test_confidence_engine.py       # NEW: Test explainable confidence scoring
├── test_data_fusion.py             # NEW: Test multi-provider alignment, fusion, conflicts
├── test_weather_intelligence.py    # NEW: Test full intelligence orchestrator and API routes
```

---

## 6. End-to-End Data Flow

```
1. Request (lat, lon, days)
        │
2. Provider Retrieval (WeatherAggregator)
        ├── Open-Meteo (Real Provider)
        └── [Optional Additional Providers in Registry]
        │
3. Data Fusion Engine (DataFusionEngine)
        ├── Cross-provider comparison
        ├── Conflict detection & resolution
        └── Fused CurrentWeather & ForecastWeather
        │
4. Parallel / Sequential Intelligence Pipelines
        ├── WeatherAnalysisEngine        → Current meteorological analysis & comfort
        ├── WeatherTrendEngine           → Trend rates & trajectories
        ├── ForecastIntelligenceEngine  → Rain onset, duration, peaks, swings
        ├── ExtremeWeatherDetector       → IMD & heuristic hazard detection
        ├── ComprehensiveRiskEngine      → Multi-hazard risk + HEURISTIC_RISK tag
        ├── DataQualityEngine            → Quality score, completeness, freshness
        └── ExplainableConfidenceEngine  → Deterministic confidence score & breakdown
        │
5. Assembly (WeatherIntelligenceService)
        └── WeatherIntelligenceResponse
```

---

## 7. API and Schema Contract

### Schema Sample: `WeatherIntelligenceResponse`
```json
{
  "location": "Warangal",
  "latitude": 17.9689,
  "longitude": 79.5941,
  "timestamp": "2026-10-08T04:15:00Z",
  "current_analysis": {
    "apparent_temperature_level": "extreme_caution",
    "humidity_comfort": "oppressive",
    "wind_classification": "moderate_breeze",
    "precipitation_category": "moderate_rain",
    "visibility_condition": "clear",
    "barometric_trend": "low_pressure_trough",
    "summary": "High apparent heat (38.2°C) with oppressive humidity (82%) and moderate rainfall; potentially uncomfortable conditions."
  },
  "forecast_intelligence": {
    "rain_expected": true,
    "rain_onset": "2026-10-08T06:00:00Z",
    "rain_duration_hours": 4.0,
    "peak_rain_period": {
      "start": "2026-10-08T07:00:00Z",
      "end": "2026-10-08T09:00:00Z",
      "max_rate_mm_h": 18.5
    },
    "temperature_range": {"min": 24.0, "max": 34.0, "diurnal_swing": 10.0},
    "rapid_changes_detected": []
  },
  "trends": {
    "temperature": {"state": "decreasing", "rate_per_hour": -0.8},
    "rainfall": {"state": "increasing", "rate_per_hour": 3.2},
    "wind": {"state": "stable", "rate_per_hour": 0.1},
    "pressure": {"state": "decreasing", "rate_per_hour": -0.5}
  },
  "extreme_events": [
    {
      "event_type": "heavy_rain",
      "severity": "high",
      "classification_source": "IMD_HEAVY_RAIN_STANDARD",
      "is_official_warning": false,
      "notice": "HEURISTIC METEOROLOGICAL DETECTION ONLY"
    }
  ],
  "risks": {
    "rain": {"score": 75, "level": "HIGH", "classification": "HEURISTIC_RISK"},
    "storm": {"score": 60, "level": "HIGH", "classification": "HEURISTIC_RISK"},
    "heat": {"score": 30, "level": "MODERATE", "classification": "HEURISTIC_RISK"},
    "overall": {"score": 85, "level": "SEVERE", "classification": "HEURISTIC_RISK"},
    "disclaimer": "Heuristic risk assessment, not an official government disaster warning."
  },
  "data_quality": {
    "quality_score": 0.92,
    "completeness_score": 38,
    "freshness_score": 30,
    "conflicting_fields": []
  },
  "confidence": {
    "overall_score": 86,
    "breakdown": {
      "completeness": 38,
      "freshness": 30,
      "provider_agreement": 20,
      "forecast_horizon_penalty": 2
    },
    "uncertainties": []
  }
}
```

---

## 8. Test Strategy & Backward Compatibility

1. **Baseline Invariance**: All 373 existing tests must pass without modification.
2. **Unit Tests per Service**:
   - `test_weather_analysis.py`: Thermal indices, humidity comfort bands, wind Beaufort scale, deterministic text generation.
   - `test_forecast_intelligence.py`: Onset calculation, duration aggregation, peak rain finding, rapid swing detection.
   - `test_weather_trend.py`: Trend categorization (increasing, decreasing, stable, rapid change).
   - `test_extreme_weather.py`: IMD thresholds, extreme cold, heatwave, wind gusts, thunderstorm conditions.
   - `test_risk_assessment.py`: Multi-hazard risks, storm risk addition, heuristic vs official warning label enforcement.
   - `test_data_fusion.py`: Multi-provider merging, missing field backfill, conflict detection, provider weighting.
   - `test_data_quality_and_confidence.py`: Freshness degradation, completeness scores, horizon penalties.
3. **Integration & API Tests**:
   - `test_weather_intelligence.py`: Testing `GET /weather/intelligence` and `POST /weather/intelligence/analyze`.
4. **Target Suite**: ~450+ passing tests (373 baseline + ~80+ new tests).

---

## 9. Architectural Safeguards

- **No LLM in Numerical Computations**: All index calculations, trends, onsets, and risk scores are 100% deterministic Python functions.
- **Explainability**: Every confidence score and risk level is accompanied by its underlying numerical breakdown.
- **Stateless & Composable**: Every new intelligence service is stateless and injectable with settings for test isolation.
- **Non-Breaking Extension**: Legacy schemas and routes remain intact.
