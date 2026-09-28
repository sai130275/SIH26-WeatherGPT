# WeatherGPT — Group 3: AI & Weather Intelligence

> **Python 3.12+ · FastAPI · Pydantic · NumPy · Pandas**

This micro-service is the AI and weather intelligence layer of the WeatherGPT platform. It is consumed by the **Group 2** Node.js/Express backend via HTTP.

---

## Architecture Overview

```
group3/
├── app/
│   ├── main.py               # FastAPI app factory
│   ├── api/
│   │   └── routes/
│   │       └── health.py     # GET /health
│   ├── schemas/
│   │   └── weather.py        # WeatherData + ForecastItem Pydantic models
│   ├── services/             # Phase 2+: processing, risk, LLM engines
│   └── core/
│       └── config.py         # Env-based configuration (pydantic-settings)
├── tests/
│   └── test_health.py        # pytest suite
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Quick Start

### 1. Prerequisites

- Python 3.12 or higher
- `pip` or a virtual-environment tool of your choice

### 2. Create and activate a virtual environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate       # macOS / Linux
# .venv\Scripts\activate        # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
# Open .env and fill in real values (especially LLM_API_KEY for Phase 2+)
```

### 5. Run the development server

```bash
uvicorn app.main:app --reload
```

The API is now live at **http://localhost:8000**.

| URL | Description |
|-----|-------------|
| `http://localhost:8000/health` | Liveness probe |
| `http://localhost:8000/docs` | Swagger / OpenAPI UI |
| `http://localhost:8000/redoc` | ReDoc UI |

---

## Running Tests

```bash
pytest tests/ -v
```

Expected output:

```
tests/test_health.py::TestHealthEndpoint::test_health_returns_200      PASSED
tests/test_health.py::TestHealthEndpoint::test_health_returns_json     PASSED
tests/test_health.py::TestHealthEndpoint::test_health_status_ok        PASSED
tests/test_health.py::TestHealthEndpoint::test_health_content_type     PASSED
tests/test_health.py::TestHealthEndpoint::test_health_no_extra_keys    PASSED
```

---

## API Reference (Phase 1)

### `GET /health`

Liveness probe. Returns `200 OK` when the service process is alive.

**Response**

```json
{
  "status": "ok"
}
```

---

## Data Schemas

### `WeatherData`

| Field | Type | Unit | Required |
|---|---|---|---|
| `location` | `str` | — | ✅ |
| `latitude` | `float` | degrees (−90 to +90) | ✅ |
| `longitude` | `float` | degrees (−180 to +180) | ✅ |
| `timestamp` | `datetime` | UTC ISO-8601 | ✅ |
| `temperature` | `float` | °C | Optional |
| `humidity` | `float` | % (0–100) | Optional |
| `rainfall` | `float` | mm | Optional |
| `wind_speed` | `float` | km/h | Optional |
| `wind_direction` | `float` | degrees (0–359) | Optional |
| `pressure` | `float` | hPa | Optional |
| `visibility` | `float` | km | Optional |
| `forecast` | `list[ForecastItem]` | — | Optional |

### `ForecastItem`

| Field | Type | Unit |
|---|---|---|
| `timestamp` | `datetime` | UTC ISO-8601 |
| `temperature` | `float` | °C |
| `rainfall` | `float` | mm |
| `humidity` | `float` | % (0–100) |
| `wind_speed` | `float` | km/h |
| `weather_condition` | `str` | — |

---

## Roadmap

| Phase | Feature |
|---|---|
| ✅ Phase 1 | Project setup, `/health`, Pydantic schemas |
| 🔜 Phase 2 | Weather data processing & condition detection |
| 🔜 Phase 3 | Risk engine & impact engine |
| 🔜 Phase 4 | Advisory engine |
| 🔜 Phase 5 | LLM integration & evidence/confidence generation |

---

## Integration with Group 2

Group 2 (Node.js/Express) calls this service over HTTP. Base URL is configured in their environment:

```
WEATHER_AI_SERVICE_URL=http://group3-service:8000
```

All endpoints follow REST conventions and return JSON.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `APP_NAME` | `WeatherGPT – AI & Weather Intelligence (Group 3)` | Service display name |
| `APP_VERSION` | `0.1.0` | Semver |
| `DEBUG` | `false` | Enable debug mode |
| `HOST` | `0.0.0.0` | Bind host |
| `PORT` | `8000` | Bind port |
| `LLM_PROVIDER` | `openai` | LLM backend (Phase 2+) |
| `LLM_API_KEY` | *(required in Phase 2+)* | API key — never commit |
| `LLM_MODEL` | `gpt-4o` | Model name |
