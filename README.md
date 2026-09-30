# WeatherGPT — Hyperlocal AI Weather Intelligence & Early Warning System

> **Smart India Hackathon 2026** · *Disaster Management, Agriculture, and Community Resilience*

WeatherGPT is an AI-powered weather intelligence and early-warning platform designed to bridge the gap between raw meteorological numerical predictions and actionable, human-centric decisions. It combines real-time numerical weather prediction (NWP) telemetry, multi-hazard algorithmic risk modeling, and grounded Large Language Model (LLM) reasoning into an accessible, responsive web application.

---

## 1. What WeatherGPT Is
WeatherGPT is a 3-tier microservice platform that ingests raw atmospheric sensor and forecast data, computes deterministic multi-hazard risk scores (flooding, extreme heat, severe convective storms, wind shear), and delivers natural-language, evidence-backed advisories in multiple Indian languages (English, Telugu, Hindi).

---

## 2. Problem Being Solved
*   **Data vs. Decision Gap**: Traditional weather apps present isolated numbers (e.g. *78% humidity, 998 hPa, 45 J/kg CAPE*). Ordinary citizens, farmers, and emergency managers struggle to translate raw sensor telemetry into actionable safety decisions.
*   **AI Hallucination in Critical Situations**: Generic LLMs hallucinate weather conditions because they lack grounded, real-time atmospheric observations. WeatherGPT uses retrieval-grounded generation (RAG) strictly coupled to live meteorological telemetry.
*   **Single Points of Failure**: Many modern cloud applications crash when an external API (LLM provider, cache, or cloud database) experiences downtime. WeatherGPT features deterministic fallbacks at every tier.

---

## 3. Key Capabilities
*   **Live Atmospheric Telemetry**: Real-time tracking of temperature, feels-like, humidity, rain probability, wind speed, precipitation, surface pressure, UV index, visibility, CAPE, and lightning discharge flags.
*   **Multi-Hazard Risk Engine**: Algorithmic risk evaluation (scores 0–100 and levels `LOW`, `MODERATE`, `HIGH`, `SEVERE`) covering flood risk, extreme heatwaves, convective storms, and visibility hazards.
*   **Grounded Conversational Intelligence ("Ask AI")**: Context-aware natural-language chat that answers queries grounded in live sensor metrics with cited evidence sources.
*   **Hands-Free Voice Querying**: Web Speech API integration enabling voice-to-text inputs.
*   **Color-Coded Geofenced Alerts**: Active warnings categorized into Red Alerts (Severe Warning), Orange Alerts (Watch), and Yellow Advisories with emergency action recommendations.
*   **Sector-Specific Advisory Modes**: Dedicated advisory views for Agriculture (crop protection & spraying), Cyclone Tracking, Aviation, and Marine operations.
*   **Global Unit Harmonization**: Real-time unit conversions (`°C`/`°F`, `km/h`/`mph`, `mm`/`in`, `hPa`/`inHg`) propagated synchronously across all telemetry cards and forecast projections.
*   **Multilingual Support**: Architectural support for English (`en`), Telugu (`te`), and Hindi (`hi`).

---

## 4. System Architecture

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

For complete architectural details, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 5. Service Responsibilities

| Service | Directory | Responsibilities |
| :--- | :--- | :--- |
| **Group 1 (Frontend)** | [`group1/`](group1/) | Client user interface, location switching, audio speech recognition, global unit conversion via `PreferencesContext`, alert presentation modals, and API communication via Axios. |
| **Group 2 (API Gateway)** | [`group2/`](group2/) | Reverse-proxy security perimeter, JWT user authentication, Open-Meteo data harmonization, Redis distributed caching (with in-memory Map fallback), MongoDB persistence (with in-memory store fallback), and rate-limiting. |
| **Group 3 (AI Service)** | [`group3/`](group3/) | Quantitative multi-hazard risk engine, condition detection (heatwaves, heavy rain, lightning), prompt synthesis, Google Gemini / OpenAI integration, and deterministic rule-based fallback generation. |

---

## 6. End-to-End Data Flow

1. **User Request**: User asks *"Can I travel safely from Warangal today?"* via text or voice in Group 1.
2. **Gateway Ingress**: Group 1 sends `POST /api/chat` to Group 2 with the user query and coordinates (`lat`, `lon`).
3. **Telemetry Fetching**: Group 2 fetches live atmospheric conditions from Open-Meteo and compiles a unified `weather_data` payload.
4. **AI Engine Forwarding**: Group 2 forwards the combined message and telemetry to Group 3 (`POST /chat`).
5. **Risk Analysis & Grounding**: Group 3 computes hazard risk scores (0–100), extracts meteorological signals, and builds a grounded system prompt.
6. **Inference / Fallback**: Group 3 generates an evidence-based answer via Gemini. If API limits are exceeded or keys are absent, it executes deterministic safety rules (`mode: "fallback"`).
7. **Delivery**: Group 2 receives the structured answer and returns it to Group 1 for rendering.

---

## 7. AI & LLM Integration

*   **Supported Providers**: Google Gemini (via OpenAI-compatible endpoint or native Gemini models like `gemini-1.5-flash` / `gemini-2.0-flash`) and OpenAI (`gpt-4o`, `gpt-4o-mini`).
*   **Prompt Grounding**: The LLM is supplied with structured JSON context containing active risks, temperature, wind vectors, and humidity. It is forbidden from guessing metrics.
*   **Deterministic Safety**: If the external AI provider is unavailable, Group 3 automatically generates safety guidance using deterministic rules, preventing downtime.

---

## 8. Weather Data Source

WeatherGPT relies on **Open-Meteo**, an open-source, non-commercial meteorological API that aggregates consensus data from national weather services:
*   **IMD** (India Meteorological Department)
*   **ECMWF** (European Centre for Medium-Range Weather Forecasts)
*   **GFS / NOAA** (Global Forecast System)
*   *Authentication*: No external API keys required, ensuring high reliability for public utility.

---

## 9. Fallback & Fault Tolerance

WeatherGPT operates on a zero-downtime resilience design:
1.  **MongoDB Offline**: Group 2 automatically falls back to an in-memory data store; alert queries and authentication continue to function.
2.  **Redis Offline**: Group 2 automatically switches to an in-memory Map cache with TTL expiration.
3.  **LLM Service Quota / Outage**: Group 3 returns a rule-based advisory (`mode: "fallback"`) derived from mathematical threshold models.
4.  **Network Drops**: Group 1 unmasks error messages and provides interactive retry buttons without crashing.

---

## 10. Category & Sector Modes

WeatherGPT provides specialized intelligence views accessible from the Dashboard:
*   **Farmer Advisory** (`map-farmer`): Agricultural advisories covering pesticide spraying windows, soil saturation, and crop protection.
*   **Cyclone Tracker** (`map-cyclone`): Atmospheric pressure anomalies and trajectory tracking.
*   **Aviation** (`map-aviation`): Cloud ceiling heights, flight visibility, and crosswind vectors.
*   **Marine** (`map-marine`): Coastal weather, wave conditions, and wind safety.

---

## 11. Alerts System

*   **Geofenced Threat Detection**: Calculates distance-based threat perimeters (`/api/alerts?lat=...&lon=...&radius=50`).
*   **Severity Levels**: Red Alert (`WARNING`), Orange Alert (`WATCH`), and Yellow Advisory (`ADVISORY`).
*   **Detail Inspector**: Clickable alert modal displaying issuing agency, affected coordinates, validity timestamps, and recommended safety actions.

---

## 12. Settings & Dynamic Unit Conversion

Users can customize their measurement system in **Settings**:
*   **Temperature**: Celsius (`°C`) ↔ Fahrenheit (`°F`)
*   **Wind Speed**: Kilometers per hour (`km/h`) ↔ Miles per hour (`mph`)
*   **Precipitation**: Millimeters (`mm`) ↔ Inches (`in`)
*   **Pressure**: Hectopascals (`hPa`) ↔ Inches of Mercury (`inHg`)

Conversions are managed centrally by [`PreferencesContext`](group1/src/context/PreferencesContext.tsx) and computed dynamically using pure conversion functions in [`units.ts`](group1/src/utils/units.ts). Changes reflect immediately across all views.

---

## 13. Current Implemented Features

*   [x] Real-time weather dashboard with live NWP telemetry
*   [x] Hourly 24-hour weather timeline & 7-day model consensus outlook
*   [x] Multi-city location switching (Warangal, Hyderabad, Delhi, Mumbai, Bengaluru)
*   [x] "Ask AI" natural-language conversational assistant
*   [x] Web Speech API hands-free voice input
*   [x] Grounded risk calculation engine with 347 unit tests
*   [x] Deterministic AI fallback mode
*   [x] Active geofenced alerts feed with detailed modal viewer
*   [x] Specialized sector modes (Farmer, Cyclone, Aviation, Marine)
*   [x] Global dynamic unit conversion system
*   [x] Quick demo login with pre-configured role profiles
*   [x] Reverse-proxy rate limiting and CORS configuration

---

## 14. Upcoming Roadmap Features

*   [ ] Full interactive GIS Leaflet map layer integration (code preserved in [`archive/map/`](archive/map/))
*   [ ] SMS / WhatsApp emergency broadcast integration for rural areas
*   [ ] Multi-station IoT radar sensor ingestion (Doppler radar feeds)
*   [ ] Crowdsourced ground truth hazard verification

---

## 15. Repository Structure

```text
Weathergpt/
├── README.md               # Master project overview & judge documentation
├── LICENSE                 # MIT License
├── .gitignore              # Multi-tier exclusion for secrets, dependencies, and cache
├── docs/                   # In-depth technical documentation
│   ├── ARCHITECTURE.md     # Architectural blueprints, data pipelines & fallbacks
│   ├── SETUP.md            # Installation, environment setup & startup commands
│   ├── API.md              # Complete specification of all HTTP endpoints
│   ├── DEMO_GUIDE.md       # 12-step practical live evaluation script for judges
│   └── PROJECT_STRUCTURE.md# Detailed file-by-file directory map
├── group1/                 # Frontend (React 18, Vite, TypeScript, Tailwind CSS)
├── group2/                 # API Gateway (Node.js, Express, Socket.IO, Axios)
├── group3/                 # AI Engine (Python 3.12, FastAPI, Pydantic, NumPy)
├── archive/
│   └── map/                # Preserved roadmap Leaflet GIS map implementation
└── demo/                   # UI verification screenshots
```

For full file details, see [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md).

---

## 16. Prerequisites

*   **Node.js**: `v18.0.0` or higher
*   **npm**: `v9.0.0` or higher
*   **Python**: `3.12.0` or higher
*   **pip**: Included with Python 3.12
*   *(Optional)* **MongoDB** (port `27017`) & **Redis** (port `6379`) — Gateway will fall back to in-memory mode if omitted.

---

## 17. Environment Variables Summary

### Group 1 (`group1/.env.local`)
```env
VITE_API_BASE_URL=http://localhost:5001/api
```

### Group 2 (`group2/.env`)
```env
PORT=5001
NODE_ENV=development
JWT_SECRET=dev-secret-123
GROUP3_URL=http://localhost:8000
ALLOWED_ORIGINS=*
```

### Group 3 (`group3/.env`)
```env
PORT=8000
LLM_PROVIDER=google
LLM_API_KEY=your_gemini_api_key_here
LLM_MODEL=gemini-1.5-flash
CORS_ORIGINS=*
```

> **Security Guarantee**: Real API keys and credentials are never committed to version control. All `.env` files are excluded by [`.gitignore`](.gitignore).

---

## 18. Local Setup & Startup Sequence

Start the services in order: **Group 3 ➔ Group 2 ➔ Group 1**.

### 1. Start Group 3 (AI Service — Port 8000)
```bash
cd group3
python3.12 -m venv .venv
source .venv/bin/activate       # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --port 8000 --reload
```

### 2. Start Group 2 (API Gateway — Port 5001)
```bash
cd group2
npm install
cp .env.example .env
npm run dev
```

### 3. Start Group 1 (Frontend — Port 5173)
```bash
cd group1
npm install
cp .env.example .env.local
npm run dev
```

Open `http://localhost:5173` in your browser.

For complete setup instructions, see [docs/SETUP.md](docs/SETUP.md).

---

## 19. Running Tests

### Group 3 (Python Pytest Suite — 347 Tests)
```bash
cd group3
source .venv/bin/activate
pytest tests/ -v
```

### Group 2 (Node.js Jest Integration Suite — 15 Tests)
```bash
cd group2
npm test
```

### Group 1 (TypeScript Verification & Build)
```bash
cd group1
npm run typecheck
npm run build
```

---

## 20. Demo Flow for Judges

Follow this quick 12-step path during live evaluations:
1.  **Open Dashboard** at `http://localhost:5173` and use **Quick Demo Login**.
2.  **Inspect Telemetry**: Point out live NWP sensor readings (CAPE, lightning, humidity).
3.  **Switch Location**: Select Hyderabad or Delhi and observe instant telemetry updates.
4.  **Review Forecast**: Check 24-hour hourly trend and 7-day model consensus curves.
5.  **View Alerts**: Open the **Alerts** tab and inspect the Red/Orange hazard modal.
6.  **Sector Modes**: Open **Farmer Advisory** from the dashboard.
7.  **Ask AI**: Submit a natural-language query (*"Can I spray crops tomorrow?"*).
8.  **Voice Query**: Click the microphone icon and ask a question hands-free.
9.  **Change Units**: Open **Settings** and toggle to `°F` and `mph`.
10. **Global Sync**: Return to the dashboard and confirm all readings converted synchronously.
11. **Demonstrate Fallbacks**: Explain how the deterministic risk engine guarantees uptime even without external LLM keys.
12. **Highlight Architecture**: Point to the clean 3-tier microservice architecture.

For full details, see [docs/DEMO_GUIDE.md](docs/DEMO_GUIDE.md).

---

## 21. Known Limitations

*   **Render Free-Tier Cold Starts**: On free hosting tiers, Group 3 will spin down after 15 minutes of inactivity; initial requests may take 15–30 seconds while the container boots.
*   **Web Speech API Browser Compatibility**: Voice input relies on the native browser Web Speech API, which is supported in Google Chrome, Chromium-based browsers, and Safari, but may have limited support in certain Firefox configurations.
*   **Offline Mode**: Full historical analysis requires active connectivity to Open-Meteo. Cached responses are served during temporary connection drops.

---

## 22. License
This project is open-source and distributed under the [MIT License](LICENSE).
