# WeatherGPT — Group 3: AI & Weather Intelligence

> **Python 3.12+ · FastAPI · Pydantic v2 · NumPy · Pandas · Pytest**

This microservice is the AI and mathematical risk intelligence layer of the WeatherGPT platform. It is consumed by the **Group 2** Node.js/Express gateway over HTTP.

---

## Architecture Overview

```text
group3/
├── app/
│   ├── main.py               # FastAPI app factory & router registration
│   ├── api/
│   │   └── routes/
│   │       ├── health.py     # GET /health
│   │       ├── chat.py       # POST /chat
│   │       ├── risk.py       # POST /risk
│   │       └── advisory.py   # POST /advisory
│   ├── schemas/              # Pydantic v2 request/response validation schemas
│   │   ├── weather.py        # WeatherData, Observation, ForecastItem
│   │   ├── risk.py           # RiskResult, RiskAnalysis
│   │   ├── chat.py           # ChatRequest, ChatResponse
│   │   └── advisory.py       # AdvisoryPayload, ImpactAdvisory
│   ├── services/             # Core algorithmic & generative engines
│   │   ├── weather_processor.py # Normalizes observations and detects missing fields
│   │   ├── condition_detector.py# Heuristic feature detection (rain, heat, storm, wind)
│   │   ├── risk_engine.py    # Multi-hazard mathematical scoring (0-100)
│   │   ├── impact_engine.py  # Sector impact assessment
│   │   ├── advisory_engine.py# Actionable advisory generator
│   │   ├── evidence_engine.py# Context grounding & confidence scoring
│   │   └── llm_service.py    # Gemini/OpenAI adapter with deterministic fallback
│   └── core/
│       └── config.py         # Pydantic BaseSettings environment loader
├── tests/                    # 347 automated tests (100% passing)
├── requirements.txt          # Python dependencies
├── .python-version           # Pinned Python version (3.12.4)
└── README.md
```

---

## Quick Start

### 1. Prerequisites
* Python 3.12 or higher
* `pip`

### 2. Create and Activate Virtual Environment
```bash
python3.12 -m venv .venv
source .venv/bin/activate       # macOS / Linux
# .venv\Scripts\activate        # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cp .env.example .env
```
*(If `LLM_API_KEY` is omitted, the service automatically runs in deterministic `fallback` mode).*

### 5. Run the Development Server
```bash
uvicorn app.main:app --port 8000 --reload
```

Interactive documentation is available at:
* Swagger UI: `http://localhost:8000/docs`
* ReDoc: `http://localhost:8000/redoc`
* Liveness: `http://localhost:8000/health`

---

## Automated Test Suite

```bash
pytest tests/ -q
```
*Expected: **347 passed** in ~8.75s covering risk math, extreme condition detection, weather data normalization, prompt synthesis, and fallback provider behavior.*

---

## API Reference

### 1. `GET /health`
Liveness probe returning `{"status": "ok"}`.

### 2. `POST /chat`
Accepts user message, geographic location, and live weather telemetry. Evaluates multi-hazard risk, synthesizes grounded evidence, and returns structured advice:
```json
{
  "conversation_id": "conv-123",
  "answer": "Current overall risk is LOW (score 10). Weather conditions are stable for outdoor activities...",
  "sources": ["weather", "risk"],
  "mode": "llm",
  "intent": "forecast"
}
```

### 3. `POST /risk`
Evaluates multi-hazard heuristic scoring across flood, extreme heat, high wind, and visibility. Returns quantitative scores (0–100) and severity ratings (`LOW`, `MODERATE`, `HIGH`, `SEVERE`).

### 4. `POST /advisory`
Delivers domain-specific impacts and protective advisories for agriculture, health, infrastructure, and transport.

---

## Resilient Fallback Engine

When `LLM_API_KEY` is not provided, or when external AI endpoints experience timeouts or rate-limiting (HTTP 429/500):
* The service automatically engages its `FallbackProvider`.
* Synthesizes deterministic, rule-based safety advisories directly from sensor telemetry and risk engine calculations.
* Sets `"mode": "fallback"` for complete transparency without crashing or hallucinating.
