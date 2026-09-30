# WeatherGPT — Project Overview

> **Smart India Hackathon 2026** · *Disaster Management, Agriculture, and Community Resilience*

---

## 1. Project Objective & Vision

WeatherGPT transforms raw, complex numerical weather predictions into actionable, human-centric guidance. The platform bridges the gap between atmospheric science and community safety by coupling real-time telemetry from global NWP models with an automated multi-hazard risk engine and grounded AI reasoning.

### Latest Project Vision
WeatherGPT is designed to evolve into an AI-powered weather and environmental intelligence platform serving:
* **General Citizens & Commuters**: Plain-language weather guidance, thunderstorm warnings, and travel safety.
* **Farmers & Agricultural Workers**: Crop-specific advisories, optimal spraying/harvesting windows, and drought/heat risk indices.
* **Disaster Response Teams**: Algorithmic multi-hazard risk scoring, early warnings, and emergency protocol alignment.
* **Aviation Coordinators**: Plain-language visibility, runway crosswind vectors, and turbulence risk indices.
* **Marine Operators & Coastal Fishermen**: Sea-state forecasts, high-wind squall alerts, and coastal safety guidance.
* **Vulnerable Populations with Limited Smartphone/Internet Access**: Future planned Toll-Free Voice Access allowing users to call an automated telephone hotline for spoken weather intelligence over basic feature phones.

---

## 2. Target Users & Personas

| Target Persona | Key Challenges | WeatherGPT Solution |
| :--- | :--- | :--- |
| **Farmers & Agricultural Workers** | Crop damage from sudden rainfall or extreme heat; uncertainty regarding pesticide spraying and harvesting windows. | Targeted agricultural advisories evaluating precipitation probability, soil saturation, and temperature thresholds. |
| **Disaster Response Managers** | Inability to quickly synthesize multi-hazard risks (simultaneous flooding and high wind vectors) across districts. | Algorithmic multi-hazard risk scoring (0–100) and severity ratings (`LOW`, `MODERATE`, `HIGH`, `SEVERE`). |
| **Aviation & Logistics Operators** | Micro-climate visibility drops, low-level wind shear, and convective cloud buildup causing route delays. | Dedicated aviation metrics tracking crosswinds, ceiling estimates, and CAPE energy. |
| **Marine & Fishery Workers** | Sudden coastal squalls, rough sea states, and lack of accessible marine warnings before setting sail. | Tailored marine risk assessments evaluating coastal wind speeds and visibility. |
| **General Citizens & Commuters** | Cryptic numerical metrics leading to unsafe travel decisions during severe thunderstorms. | Plain-language conversational assistant ("Ask AI") with hands-free voice input and localized safety tips. |
| **Rural & Non-Smartphone Users** | Lack of reliable smartphones or internet data connections during storms. | Future planned Toll-Free Voice Access and SMS early-warning broadcast infrastructure. |

---

## 3. Core Workflow

```text
[ Citizen / Official ]
         │
         │ 1. Queries weather or views dashboard (Browser / Web Speech Voice)
         ▼
[ Group 1: React Frontend ]
         │
         │ 2. Dispatches REST request with coordinates
         ▼
[ Group 2: API Gateway ]
         │
         ├── 3. Checks Redis cache (TTL: 15 min; in-memory fallback if offline)
         ├── 4. On cache miss: Queries Open-Meteo (IMD/ECMWF/GFS consensus)
         └── 5. Orchestrates weather telemetry
         │
         │ 6. Forwards query + sensor telemetry
         ▼
[ Group 3: AI Intelligence Engine ]
         │
         ├── 7. Computes multi-hazard risk scores (Flood, Heat, Wind, Visibility)
         ├── 8. Grounding engine builds structured context block
         └── 9. Generates response via Gemini/OpenAI (or deterministic fallback)
         │
         │ 10. Delivers structured JSON response { answer, intent, sources }
         ▼
[ Group 1: React Frontend displays actionable advisory ]
```

---

## 4. Technology Stack Summary

### Frontend (Group 1)
* **Framework**: React 18, Vite, TypeScript
* **Styling**: Tailwind CSS, Mobile-First Design Tokens
* **Icons**: Material Symbols (`@material-symbols/svg-react`) & Lucide React
* **State Management**: React Context (`PreferencesContext` for global units)
* **HTTP Client**: Axios with interceptors and base URL auto-normalization
* **Voice Recognition**: Web Speech API (`webkitSpeechRecognition` / `SpeechRecognition`)

### API Gateway (Group 2)
* **Runtime**: Node.js v18+, Express 4
* **Security & Ingress**: Helmet, CORS origin resolution, Express Rate Limiter, Trust Proxy
* **Authentication**: JSON Web Tokens (`jsonwebtoken`), bcryptjs
* **Persistence & Caching**: Mongoose (MongoDB) with in-memory fallback; ioredis with in-memory Map fallback
* **Real-time Protocol**: Socket.IO for server-side alert emission
* **External Provider**: Open-Meteo REST API adapter

### AI & Risk Engine (Group 3)
* **Runtime**: Python 3.12, FastAPI, Uvicorn
* **Data Validation**: Pydantic v2 BaseModels and Settings
* **Computation**: NumPy, Pandas for numerical normalization
* **AI Orchestration**: Grounded RAG prompt synthesis, OpenAI SDK (compatible with Google Gemini)
* **Reliability**: Deterministic Fallback Engine for zero-downtime operation
* **Test Suite**: Pytest, Pytest-AsyncIO (347 automated tests)

---

## 5. Implementation Status

### Currently Implemented (Current MVP)
* **Core Weather Telemetry**: **Complete** (Live ingestion from Open-Meteo covering temperature, humidity, wind speed, pressure, UV index, CAPE, and lightning).
* **Multi-Hazard Risk Engine**: **Complete** (Deterministic mathematical models for heatwaves, heavy rainfall, high wind, and visibility with full test coverage).
* **Conversational AI ("Ask AI")**: **Complete** (Grounded retrieval coupled with Gemini/OpenAI and deterministic fallback mode).
* **Voice Querying**: **Complete** (Client-side speech recognition enabled via Web Speech API).
* **Dynamic Unit Conversion**: **Complete** (Synchronous global propagation across all dashboard cards and forecast views via `PreferencesContext`).
* **Active Alerts & Detail Modal**: **Complete** (Geofenced query endpoint with severity indicators and action modal).
* **Sector-Specific Modes**: **Complete** (Structured cards for Agriculture, Cyclone, Aviation, and Marine).

### Future Expansions (Planned / Not Currently Implemented)
* **Toll-Free Voice Access**: Future planned telephony interface for non-smartphone users *(Status: FUTURE / NOT CURRENTLY IMPLEMENTED)*.
* **Advanced RAG**: Vector database integration searching official ICAR crop advisories and government flood SOPs *(Status: FUTURE)*.
* **Interactive GIS Map**: Re-integration of interactive spatial GIS map layers (preserved foundation in `archive/map/`) *(Status: FUTURE)*.
* **Additional Weather Providers**: Ingestion adapters for Tomorrow.io, MeteoBlue, IMD radar feeds, and ISRO satellite data *(Status: FUTURE)*.
* **Automated Notifications**: Multi-channel alert dispatch via SMS, WhatsApp, Web Push, and voice broadcasts *(Status: FUTURE)*.
* **Multilingual Translation**: Vernacular UI dictionaries and Bhashini voice pipelines for 12+ Indian languages *(Status: FUTURE)*.
* **PWA & Mobile**: Offline Service Worker caching and installable app package *(Status: FUTURE)*.
* **IoT Sensor Integration**: Ingestion protocols for automated weather stations and agricultural soil probes *(Status: FUTURE)*.
