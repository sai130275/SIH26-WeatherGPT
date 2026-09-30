# WeatherGPT — Group 2: API Gateway & Orchestrator

> **Smart India Hackathon 2026** · *Node.js 18+ · Express · Socket.IO · Axios*

Group 2 is the central API Gateway and orchestration perimeter for the WeatherGPT platform. It receives HTTP requests from the React frontend (Group 1), manages authentication, caches weather data, enriches user queries with live NWP observations from Open-Meteo, and forwards structured intelligence payloads to the Python AI service (Group 3).

---

## Architecture Overview

```text
[Group 1: React 18 Frontend] (Port 5173)
              │
              │ HTTP REST / Web Speech Voice
              ▼
┌─────────────────────────────────────────────────────────────┐
│                 Group 2 Express API Gateway                 │
│                        (Port 5001)                          │
│   Rate Limiting · Helmet · JWT Auth · Open-Meteo Adapter    │
└──────┬────────────────────┬────────────────────┬────────────┘
       │                    │                    │
       ▼                    ▼                    ▼
 ┌───────────┐        ┌───────────┐    ┌──────────────────┐
 │  MongoDB  │        │   Redis   │    │ Weather Provider │
 │(In-Memory │        │(In-Memory │    │   (Open-Meteo)   │
 │ Fallback) │        │ Fallback) │    │  IMD/ECMWF/GFS   │
 └───────────┘        └───────────┘    └──────────────────┘
       │
       ▼ (Forward Enriched Query + Telemetry)
 ┌───────────────────────────────────────────────────────────┐
 │        Group 3 Python FastAPI AI & Risk Engine            │
 │                        (Port 8000)                        │
 └───────────────────────────────────────────────────────────┘
```

---

## Quick Start (Local Run)

### 1. Install Node.js Dependencies
```bash
npm install
```

### 2. Configure Environment Variables
```bash
cp .env.example .env
```
Default port is `5001` (to prevent conflicts with macOS AirPlay receiver).

### 3. Start Development Server
```bash
npm run dev
```

The gateway is now live at `http://localhost:5001`.
* Health check: `GET http://localhost:5001/api/health`

---

## Key Endpoints

### 1. Conversational AI (`POST /api/chat`)
* Receives user message and geographic coordinates.
* Enriches the query with real-time Open-Meteo telemetry.
* Proxies the request to Group 3's `/chat` endpoint.

### 2. Weather Ingestion
* `GET /api/weather/current?lat=17.9689&lon=79.5941`
* `GET /api/weather/forecast?lat=17.9689&lon=79.5941&days=7`
* Cached via Redis with automated in-memory Map fallback.

### 3. Authentication & User Profiles
* `POST /api/auth/register` (Name, email, password, language)
* `POST /api/auth/login` (Email, password) -> returns signed JWT

### 4. Active Alerts
* `GET /api/alerts?lat=17.9689&lon=79.5941&radius=50`
* Geofenced radius filtering and severity categorization.

---

## Testing

```bash
npm test
```
*Expected: 15 integration tests passing covering auth, weather normalization, alert queries, and Group 3 proxying.*

---

## Resilient Architecture & Fallbacks

* **MongoDB In-Memory Fallback**: If MongoDB is not reachable, `src/config/db.js` automatically activates an in-memory data store.
* **Redis In-Memory Fallback**: If Redis is not reachable, `src/config/redis.js` automatically activates an internal Map cache with TTL expiration.
