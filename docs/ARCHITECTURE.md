# WeatherGPT System Architecture

This document describes the high-level architecture, service boundaries, data pipelines, failure resilience mechanisms, and communication protocols across the WeatherGPT platform.

---

## 1. High-Level System Architecture

```text
                    ┌───────────────────────────────────┐
                    │              Group 1              │
                    │   React 18 + Vite Frontend UI     │
                    │   Tailwind CSS · Context API      │
                    └─────────────────┬─────────────────┘
                                      │
                                      │ HTTP REST (JSON)
                                      │ Socket.IO (Realtime alerts)
                                      ▼
                    ┌───────────────────────────────────┐
                    │              Group 2              │
                    │   Node.js / Express API Gateway   │
                    │   Auth · Cache · Provider Adapter │
                    └─────────┬───────────────┬─────────┘
                              │               │
                 Weather Data │               │ Orchestrated Payload
                 (Open-Meteo) │               │ (/chat, /risk, /advisory)
                              ▼               ▼
                 ┌──────────────────┐  ┌───────────────────────────────────┐
                 │    Open-Meteo    │  │              Group 3              │
                 │   Public API     │  │    FastAPI AI & Intelligence      │
                 │ (NWP GFS/ECMWF)  │  │    Pydantic · Risk Engine · RAG   │
                 └──────────────────┘  └─────────────────┬─────────────────┘
                                                         │
                                                         │ LLM Prompt / Grounding
                                                         ▼
                                                ┌──────────────────┐
                                                │  Google Gemini / │
                                                │      OpenAI      │
                                                └──────────────────┘
```

---

## 2. Microservice Boundaries & Responsibilities

| Service | Primary Stack | Core Responsibilities |
| :--- | :--- | :--- |
| **Group 1** (Frontend) | React 18, Vite, TypeScript, Tailwind CSS, Lucide / Material Symbols | User interface, responsive mobile-first views, unit preferences (`°C`/`°F`, `km/h`/`mph`, `mm`/`in`, `hPa`/`inHg`), location selector, voice-to-text input, alert presentation, Ask AI conversational interface. |
| **Group 2** (API Gateway) | Node.js, Express, Socket.IO, Axios, JWT, Rate Limiter | Single point of ingress for clients (`/api/*`), user authentication & JWT verification, Open-Meteo weather telemetry fetching and harmonization, MongoDB persistence (with auto in-memory fallback), Redis response caching (with auto in-memory Map fallback), rate limiting, request forwarding to Group 3. |
| **Group 3** (AI & Intelligence) | Python 3.12, FastAPI, Pydantic v2, NumPy, Pandas | Multi-hazard heuristic risk engine (flood, heat, storm, wind, lightning), evidence & confidence scoring engine, prompt assembly & grounded LLM generation via Gemini/OpenAI, deterministic rule-based fallback generation. |

---

## 3. End-to-End Request & Data Flow

### A. Ask AI Pipeline (`POST /api/chat`)

1. **User Input (Group 1)**:
   - The user enters a question (e.g., *"Can I spray pesticides in Warangal tomorrow morning?"*) or uses the Web Speech API voice input.
   - Group 1 sends `POST /api/chat` to Group 2 with the payload:
     ```json
     {
       "message": "Can I spray pesticides in Warangal tomorrow morning?",
       "latitude": 17.9689,
       "longitude": 79.5941,
       "language": "en"
     }
     ```

2. **Weather Enrichment & Orchestration (Group 2)**:
   - Group 2's `chatController` intercepts the request.
   - Group 2 calls `OpenMeteoProvider.getCurrentWeather(lat, lon)` to retrieve real-time surface observations (temperature, humidity, precipitation probability, wind speed, CAPE, surface pressure, visibility).
   - Group 2 packages the enriched weather telemetry alongside the user query and generates/preserves a `conversation_id`.
   - Group 2 calls Group 3: `POST ${GROUP3_URL}/chat`.

3. **Risk Scoring & Evidence Grounding (Group 3)**:
   - Group 3 validates the payload against Pydantic schemas (`ChatRequest`).
   - Group 3 passes the telemetry through `RiskEngine` to compute quantitative scores (0–100) and severity levels (`LOW`, `MODERATE`, `HIGH`, `SEVERE`) across multiple hazards.
   - Group 3 synthesizes an evidence context block containing observed thresholds, active risks, and location metadata.

4. **Natural Language Generation (Group 3 -> LLM)**:
   - If `LLM_API_KEY` is configured and active, Group 3 formats a strictly grounded prompt instructing Gemini/OpenAI to answer purely based on the meteorological telemetry and risk scores.
   - If the LLM provider fails, times out, or keys are omitted, Group 3 engages its **Deterministic Fallback Engine** (`mode: "fallback"`), outputting a rule-based advisory synthesized from the risk score and weather conditions.

5. **Response Delivery**:
   - Group 3 returns a structured response to Group 2:
     ```json
     {
       "conversation_id": "conv-1790676725226",
       "answer": "Current overall risk is LOW (score 10). Weather conditions are stable for outdoor activities...",
       "sources": ["weather", "risk"],
       "mode": "llm",
       "intent": "forecast"
     }
     ```
   - Group 2 formats the output with `sendSuccess(res, response.data)` and returns `HTTP 200 OK` to Group 1.
   - Group 1 renders the assistant response bubble with intent badges and sources.

---

### B. Telemetry & Forecast Pipeline (`GET /api/weather/*`)

1. Group 1 requests current conditions (`/api/weather/current?lat=...&lon=...`) and 7-day outlook (`/api/weather/forecast?lat=...&lon=...&days=7`).
2. Group 2 checks Redis for a cached key (`weather:current:<lat>:<lon>`).
   - **Cache Hit**: Serves directly within < 5 ms.
   - **Cache Miss**: Calls Open-Meteo NWP APIs, normalizes hourly and daily matrices, stores in cache with a 5-minute TTL, and returns to Group 1.
3. Group 1 receives raw metric values (metric system standard) and dynamically runs them through `PreferencesContext` (`formatTemp`, `formatWind`, `formatPrecip`, `formatPressure`) according to user configuration.

---

## 4. Failure Modes & Graceful Fallbacks

| Failure Scenario | Resilient Architecture Behavior | User Impact |
| :--- | :--- | :--- |
| **MongoDB Unreachable / Down** | Group 2 intercepts connection errors in `src/config/db.js` and activates an **in-memory data store**. Alerts and user sessions continue functioning. | Zero user downtime; alerts return local fallbacks. |
| **Redis Unreachable / Down** | Group 2 catches connection timeouts in `src/config/redis.js` and automatically switches to an internal **in-memory Map cache** with TTL expiration. | Zero user downtime; caching continues in RAM. |
| **LLM Key Missing / Quota Exceeded** | Group 3 detects unconfigured `LLM_API_KEY` or catches upstream API errors (HTTP 429/500 from Google/OpenAI). Group 3 returns `mode: "fallback"` with rule-based meteorological insights. | User receives factual, numerical weather advice without hallucination. |
| **Group 3 Service Unreachable** | Group 2 logs an upstream timeout / error and returns an HTTP 503 structured envelope. Group 1 unmasks `error.message` and prompts the user cleanly. | User is alerted to upstream AI downtime without app crash. |
| **Open-Meteo Weather API Outage** | Group 2 checks cached data; if empty, it catches the network exception and returns a structured validation error to Group 1. | Graceful error banner in UI; no white screen of death. |
| **Client Disconnects / Network Drops** | Group 1 intercepts Axios errors in `api.ts` and updates page state with actionable retry buttons. | Clear retry prompt for the user. |

---

## 5. Security & Reverse Proxy Architecture

- **CORS Handling**: Group 2 validates the incoming `Origin` against `ALLOWED_ORIGINS`, stripping trailing slashes and supporting comma-separated whitelists as well as wildcard development mode.
- **Trust Proxy**: Group 2 explicitly configures `app.set('trust proxy', 1)` to correctly inspect client IPs behind Cloudflare and Render reverse proxies for accurate rate-limiting.
- **Header Sanitization**: Group 2 applies `helmet()` middleware for secure HTTP headers (XSS filtering, frameguard, noSniff).
- **Environment Isolation**: All credentials (`JWT_SECRET`, `LLM_API_KEY`, `MONGODB_URI`, `REDIS_URL`) are read purely from environment variables and strictly gitignored.
