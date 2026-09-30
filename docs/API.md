# WeatherGPT API Reference

This document provides a factual specification of all currently implemented HTTP endpoints across the WeatherGPT platform.

---

## 1. Group 2 — API Gateway Endpoints (`/api/*`)

All client requests from the frontend enter through the Group 2 Gateway.

---

### `GET /api/health`
* **Owner**: Group 2 Gateway
* **Purpose**: System health probe reporting gateway uptime and database/cache connectivity states.
* **Authentication**: None
* **Sample Response (`200 OK`)**:
  ```json
  {
    "status": "UP",
    "timestamp": "2026-09-30T10:00:00.000Z",
    "uptime": 142.3,
    "services": {
      "database": "CONNECTED",
      "redis": "CONNECTED"
    }
  }
  ```

---

### `POST /api/auth/register`
* **Owner**: Group 2 Gateway
* **Purpose**: Register a new user profile.
* **Request Body**:
  ```json
  {
    "name": "Dr. Rajesh Kumar",
    "email": "rajesh@imd.gov.in",
    "password": "SecurePassword123!",
    "language": "en"
  }
  ```
* **Sample Response (`201 Created`)**:
  ```json
  {
    "success": true,
    "data": {
      "user": {
        "id": "66f7f123...",
        "name": "Dr. Rajesh Kumar",
        "email": "rajesh@imd.gov.in",
        "language": "en"
      },
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
  }
  ```

---

### `POST /api/auth/login`
* **Owner**: Group 2 Gateway
* **Purpose**: Authenticate user credentials and issue a JSON Web Token (JWT).
* **Request Body**:
  ```json
  {
    "email": "rajesh@imd.gov.in",
    "password": "SecurePassword123!"
  }
  ```
* **Sample Response (`200 OK`)**:
  ```json
  {
    "success": true,
    "data": {
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
  }
  ```

---

### `GET /api/weather/current`
* **Owner**: Group 2 Gateway
* **Purpose**: Retrieve current weather observations harmonized from Open-Meteo with caching.
* **Query Parameters**:
  * `lat` (number, required): Latitude (e.g. `17.9689`)
  * `lon` (number, required): Longitude (e.g. `79.5941`)
* **Sample Response (`200 OK`)**:
  ```json
  {
    "success": true,
    "data": {
      "temperature": 28.5,
      "wind_speed": 12.4,
      "humidity": 68,
      "rain_probability": 15,
      "precipitation": 0.0,
      "pressure": 1012.3,
      "uv_index": 5.2,
      "visibility": 10.0,
      "cape": 420.0,
      "lightning": false,
      "weather_code": 1,
      "weather_condition": "Mainly clear"
    }
  }
  ```

---

### `GET /api/weather/forecast`
* **Owner**: Group 2 Gateway
* **Purpose**: Retrieve multi-day and hourly forecast projections.
* **Query Parameters**:
  * `lat` (number, required): Latitude
  * `lon` (number, required): Longitude
  * `days` (number, optional, default: 7): Forecast duration (1–16 days)
* **Sample Response (`200 OK`)**:
  ```json
  {
    "success": true,
    "data": {
      "hourly": [
        {
          "time": "2026-09-30T10:00:00Z",
          "temperature": 28.5,
          "weather_code": 1,
          "rain_probability": 10
        }
      ],
      "daily": [
        {
          "date": "2026-09-30",
          "max_temp": 32.1,
          "min_temp": 24.0,
          "max_rain_prob": 25
        }
      ]
    }
  }
  ```

---

### `GET /api/alerts`
* **Owner**: Group 2 Gateway
* **Purpose**: Retrieve active meteorological alerts and advisories within a geographic boundary.
* **Query Parameters**:
  * `lat` (number, required): Center latitude
  * `lon` (number, required): Center longitude
  * `radius` (number, optional, default: 50): Radius in kilometers
* **Sample Response (`200 OK`)**:
  ```json
  {
    "success": true,
    "data": {
      "alerts": [
        {
          "id": "alert-001",
          "level": "WARNING",
          "title": "Severe Thunderstorm Warning",
          "description": "Intense lightning and convective rainfall anticipated.",
          "sourceType": "IMD Consensus",
          "disclaimer": "Avoid open fields and seek substantial shelter.",
          "createdAt": "2026-09-30T06:00:00Z",
          "expiresAt": "2026-09-30T18:00:00Z"
        }
      ]
    }
  }
  ```

---

### `POST /api/chat`
* **Owner**: Group 2 Gateway (Proxied to Group 3)
* **Purpose**: Natural-language conversational interface. Enriches query with current weather telemetry and calls Group 3's intelligence pipeline.
* **Request Body**:
  ```json
  {
    "message": "Is it safe to travel from Warangal to Hyderabad today?",
    "latitude": 17.9689,
    "longitude": 79.5941,
    "language": "en",
    "conversation_id": "conv-12345"
  }
  ```
* **Sample Response (`200 OK`)**:
  ```json
  {
    "success": true,
    "data": {
      "conversation_id": "conv-12345",
      "answer": "Current conditions are favorable for travel. Weather is mainly clear with a low rain probability (15%) and moderate winds (12 km/h). No severe hazard alerts are currently active.",
      "intent": "travel",
      "sources": ["weather", "risk"],
      "mode": "llm"
    },
    "message": null
  }
  ```

---

## 2. Group 3 — AI & Weather Intelligence Endpoints

Group 3 handles scientific evaluation, heuristic calculations, and LLM inference.

---

### `GET /health`
* **Owner**: Group 3 AI Engine
* **Purpose**: Liveness probe.
* **Sample Response (`200 OK`)**:
  ```json
  {
    "status": "ok"
  }
  ```

---

### `POST /chat`
* **Owner**: Group 3 AI Engine
* **Purpose**: Grounded conversational reasoning engine. Combines weather telemetry with heuristic risk scores to generate natural-language guidance via Gemini or deterministic fallback rules.
* **Request Body**:
  ```json
  {
    "message": "Will rainfall disrupt outdoor crop harvesting?",
    "location": {
      "latitude": 17.9689,
      "longitude": 79.5941
    },
    "conversation_id": "conv-test",
    "weather_data": {
      "location": "Warangal",
      "latitude": 17.9689,
      "longitude": 79.5941,
      "timestamp": "2026-09-30T10:00:00Z",
      "temperature": 29.0,
      "humidity": 70,
      "rainfall": 0.0,
      "wind_speed": 10.0,
      "visibility": 10.0,
      "pressure": 1012.0
    }
  }
  ```
* **Sample Response (`200 OK`)**:
  ```json
  {
    "conversation_id": "conv-test",
    "answer": "Current overall risk is LOW (score 10). Dry weather is projected for the next 12 hours, making it suitable for harvesting operations.",
    "sources": ["weather", "risk"],
    "mode": "llm",
    "intent": "agriculture"
  }
  ```

---

### `POST /risk`
* **Owner**: Group 3 AI Engine
* **Purpose**: Multi-hazard risk assessment calculating component scores and overall danger level.
* **Request Body**:
  ```json
  {
    "location": "Warangal",
    "latitude": 17.9689,
    "longitude": 79.5941,
    "timestamp": "2026-09-30T10:00:00Z",
    "temperature": 41.5,
    "humidity": 30,
    "rainfall": 0.0,
    "wind_speed": 15.0
  }
  ```
* **Sample Response (`200 OK`)**:
  ```json
  {
    "location": "Warangal",
    "overall_score": 65,
    "overall_level": "HIGH",
    "risks": [
      {
        "hazard_type": "heat",
        "score": 75,
        "level": "SEVERE",
        "reasons": ["Extreme temperature: 41.5°C exceeds heatwave safety thresholds."]
      },
      {
        "hazard_type": "flood",
        "score": 0,
        "level": "LOW",
        "reasons": ["Negligible rainfall accumulation."]
      }
    ]
  }
  ```

---

### `POST /advisory`
* **Owner**: Group 3 AI Engine
* **Purpose**: Generates targeted sector impacts and protective advisories (agriculture, health, infrastructure, transport).
* **Sample Response (`200 OK`)**:
  ```json
  {
    "overall_risk_level": "HIGH",
    "impacts": [
      "High probability of heat exhaustion during afternoon peak hours (12 PM - 4 PM)."
    ],
    "advisories": [
      "Avoid direct solar exposure; consume adequate electrolytes and schedule outdoor labor during early morning."
    ]
  }
  ```
