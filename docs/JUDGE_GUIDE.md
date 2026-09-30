# WeatherGPT — Judge & Evaluator Guide

> **Smart India Hackathon 2026** · *Disaster Management, Agriculture, and Community Resilience*

---

## 1. What WeatherGPT Is

WeatherGPT is an early-warning weather intelligence platform designed to translate raw atmospheric observations and numerical forecast models into clear, actionable, and safety-oriented advisories. Rather than merely presenting isolated numerical metrics, WeatherGPT computes algorithmic risk scores across multiple natural hazards and provides a grounded natural-language assistant ("Ask AI") that serves farmers, emergency responders, and everyday citizens.

---

## 2. Problem Being Solved

1. **The Telemetry-to-Action Gap**: Standard weather forecasts report raw figures (e.g. *998 hPa pressure, 45 J/kg CAPE, 82% humidity*). Citizens and smallholder farmers cannot easily evaluate whether these numbers imply flash floods, crop damage, or safe travel conditions.
2. **AI Hallucinations in Critical Public Safety**: Generic conversational AI tools hallucinate weather metrics because they lack access to real-time atmospheric observations. In disaster situations, ungrounded advice can endanger lives.
3. **Single Points of Failure**: Conventional web applications crash when third-party LLM endpoints or databases go down. WeatherGPT implements multi-tier deterministic fallbacks to guarantee continuous operation.

---

## 3. Current MVP vs. Future Platform Vision

### Current MVP (What Can Actually Be Demonstrated Today)
* **Live NWP Telemetry**: Ingestion of real-time atmospheric metrics from Open-Meteo (temperature, feels-like, humidity, rain probability, wind speed, pressure, UV index, visibility, CAPE, and lightning detection).
* **Multi-Hazard Mathematical Risk Engine**: Deterministic scoring (0–100) across flood, extreme heat, high wind, and visibility hazards in Python FastAPI.
* **Grounded "Ask AI" Assistant**: Natural language queries grounded in real-time sensor metrics with intent tags and cited sources, supported by Gemini/OpenAI.
* **Deterministic Fallback Engine (`mode: "fallback"`)**: Automatically activates when LLM keys are absent or timeouts occur, delivering rule-based safety guidance without hallucinating.
* **Browser Voice-to-Text Input**: Hands-free speech recognition via the native Web Speech API.
* **Synchronous Global Unit Preferences**: Real-time conversion (`°C`/`°F`, `km/h`/`mph`, `mm`/`in`, `hPa`/`inHg`) propagated across all dashboard cards and forecast views via `PreferencesContext`.
* **Geofenced Severe Weather Alerts**: Severity-tiered alerts (Red Warning, Orange Watch, Yellow Advisory) with action modals.
* **Sector-Specific Advisory Views**: Structured views for Agriculture, Cyclone Monitoring, Aviation, and Marine conditions.
* **Database & Cache Fault Tolerance**: Seamless operation with in-memory fallbacks when MongoDB or Redis are offline.

### Future Platform Vision (The Expanded SIH Idea Scope)
WeatherGPT is designed to evolve into a comprehensive AI-powered weather and environmental intelligence platform serving general users, farmers, disaster-response teams, aviation coordinators, marine operators, and vulnerable populations with limited smartphone or internet access.

Key planned expansions include:
1. **Toll-Free Voice Access**: A future planned interface for users who cannot reliably access a smartphone or web application. Callers will dial a toll-free number to receive spoken weather forecasts, alerts, and AI-assisted agricultural guidance over basic feature phones. *(Notice: This is a future planned expansion; no live toll-free telephone number exists in the current MVP).*
2. **Advanced RAG**: Semantic vector retrieval across official ICAR crop advisories, district flood SOPs, and government relief manuals.
3. **Multi-Source Data Ingestion**: Additional meteorological radar, satellite, and environmental sensors (IMD AWS radar, ISRO INSAT-3D, Tomorrow.io).
4. **Regional / Hyperlocal Intelligence**: Block- and panchayat-level micro-climate modeling combining elevation contours with local crop calendars.
5. **Expanded Farmer Advisory**: Crop-specific phenology calculators (paddy, cotton, chilli, wheat), soil moisture sensor telemetry, and humidity-correlated pest risk models.
6. **Cyclone Intelligence**: Automated storm track cone visualization, barometric pressure drop velocity alerts, storm surge inundation models, and landfall ETA projections.
7. **Aviation Intelligence**: Automated METAR/TAF telegraphic report decoding and runway crosswind component calculators.
8. **Marine Intelligence**: Real-time hydrodynamic wave models (wave height, swell period, sea surface temperature, and potential fishing zones).
9. **Interactive GIS / Map Intelligence**: Spatial hazard visualization layers built upon the preserved Leaflet foundation in `archive/map/`.
10. **Proactive Multi-Channel Notifications**: Automated early-warning alerts via SMS, WhatsApp, Web Push, and voice broadcasts.
11. **Comprehensive Multilingual Support**: Vernacular UI translations and Indian voice models (Bhashini API) for 12+ regional languages.
12. **Mobile Application & Offline PWA**: Installable PWA with offline Service Worker caching for zero-connectivity field operations.
13. **Scalable Cloud Deployment**: Kubernetes manifests, auto-scaling inference workers, and distributed Redis caching.
14. **Analytics & Performance Monitoring**: Query volume trends, hazard heatmaps, and alert delivery analytics.
15. **Government & Emergency Integration**: Common Alerting Protocol (CAP) ingestion and automated NDMA/SDMA synchronization.
16. **Community Ground-Truth Reports**: Verified crowdsourced field reports supplementing satellite and numerical models.
17. **IoT Sensor Integration**: Real-time telemetry ingestion from local automated weather stations (AWS) and agricultural soil probes.

---

## 4. How the Three Microservices Work Together

```text
[Group 1: React 18 UI] 
        │ (POST /api/chat { message, lat, lon })
        ▼
[Group 2: Node.js Gateway] ──(HTTP GET)──> [Open-Meteo NWP API]
        │ Enriches query with live weather telemetry
        │ (POST /chat { message, location, weather_data })
        ▼
[Group 3: FastAPI AI Engine] 
        ├── Evaluates RiskEngine (0-100 hazard scores)
        ├── Formulates grounded system prompt
        ├── Calls Gemini / OpenAI (or triggers FallbackProvider)
        ▼
[Group 2: Node.js Gateway]
        │ Formats standard JSON envelope { success: true, data: { answer, intent, sources } }
        ▼
[Group 1: React UI renders assistant response bubble]
```

---

## 5. Real Data Sources

WeatherGPT uses **Open-Meteo**, an open meteorological API aggregating consensus data from:
* **IMD** (India Meteorological Department)
* **ECMWF** (European Centre for Medium-Range Weather Forecasts)
* **GFS / NOAA** (Global Forecast System)
* *Authentication*: Public utility API requiring no external API keys, ensuring high reliability for public emergency response.

---

## 6. AI, Grounding (RAG), and Fallback Reliability

### Grounded Context Injection
When a user asks a question, Group 3 does NOT allow the LLM to guess atmospheric conditions. Instead:
1. Numerical metrics (`temperature`, `humidity`, `precipitation`, `wind_speed`, `pressure`, `cape`) are extracted from Open-Meteo.
2. Group 3's `RiskEngine` calculates risk scores (e.g. *Heat Risk: 75/100, Flood Risk: 0/100*).
3. The prompt explicitly instructs the model: *"You are an operational meteorological assistant. You MUST base your answer solely on the provided evidence block."*

### Deterministic Fallback Mode (`mode: "fallback"`)
If `LLM_API_KEY` is not provided, or if the external LLM provider experiences timeouts or rate-limiting (HTTP 429/500):
* Group 3 automatically activates its `FallbackProvider`.
* It evaluates deterministic meteorological rules to formulate a concise safety advisory directly from the calculated risk levels and sensor thresholds.
* The response sets `"mode": "fallback"` to maintain transparency.

---

## 7. 3–5 Minute Judge Demonstration Flow

Follow this sequence during live evaluation:
1. **0:00 – Launch & Login**: Open `http://localhost:5173` and click **Quick Demo Login** (*Dr. Rajesh Kumar*).
2. **0:45 – Live Telemetry**: Inspect live atmospheric metrics (CAPE, lightning status, pressure, humidity).
3. **1:30 – Location Switch**: Select **Hyderabad** or **Delhi** from the header dropdown; observe instantaneous telemetry updates.
4. **2:15 – Alerts Feed**: Navigate to **Alerts** to show active severity warnings and click a card to open the action modal.
5. **2:45 – Ask AI Query**: Go to **Ask AI** and ask: *"Is it safe to spray pesticides on paddy crops in Warangal tomorrow?"*
6. **3:30 – Voice Input**: Click the microphone icon to demonstrate speech-to-text.
7. **4:00 – Unit Conversion**: Go to **Settings**, toggle to **Fahrenheit (`°F`)** and **Miles per hour (`mph`)**, return to Dashboard, and observe synchronous global conversion.
8. **4:30 – Explain Reliability & Future Vision**: Explain how the deterministic risk engine guarantees uptime even if cloud AI limits are exceeded, and highlight the roadmap for Toll-Free voice access and Advanced RAG.

---

## 8. How to Run the Project Locally

```bash
# 1. Start Group 3 (AI Service — Port 8000)
cd group3
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --port 8000 --reload

# 2. Start Group 2 (API Gateway — Port 5001)
cd ../group2
npm install && cp .env.example .env
npm run dev

# 3. Start Group 1 (Frontend — Port 5173)
cd ../group1
npm install && cp .env.example .env.local
npm run dev
```

---

## 9. What Judges Should Specifically Test

1. **Ask AI Resilience**: Test Ask AI with and without an active `LLM_API_KEY`. Notice how it delivers a structured advisory in both states without crashing.
2. **Unit Conversion Integrity**: Toggle temperature and wind units in Settings and confirm they reflect instantly on the Dashboard, Hourly Timeline, and Sector cards.
3. **Database & Cache Fallbacks**: Stop MongoDB or Redis if running locally; notice the gateway gracefully continues running using in-memory fallbacks.
4. **Automated Test Coverage**:
   * Run `pytest tests/ -q` in `group3` to verify **347 automated tests** covering multi-hazard risk math and prompt assembly.
   * Run `npm test` in `group2` to verify **15 end-to-end integration tests**.
   * Run `npm run typecheck` in `group1` to verify TypeScript compile-time safety.

---

## 10. Current Limitations & Clarifications

* **Toll-Free Voice Access**: A future planned interface for non-smartphone/rural users; there is **no** active telephony carrier integration or working phone number in the current MVP. Voice in the MVP is provided via browser Web Speech API.
* **Render Free-Tier Cold Starts**: On free cloud hosting tiers, the backend may sleep after 15 minutes of inactivity; initial wakeup requests may take 15–30 seconds.
* **Web Speech API Browser Compatibility**: Native browser voice recognition relies on Web Speech API support (Google Chrome, Chromium, Edge, and Safari).
* **GIS Map Layer Status**: The full interactive Leaflet map tile overlay has been preserved in `archive/map/` for future roadmap deployment; active sector views currently render structured cards.
