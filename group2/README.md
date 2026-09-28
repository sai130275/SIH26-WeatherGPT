# WeatherGPT Backend (Smart India Hackathon 2026)

WeatherGPT is a decision-support backend built around the core concept:
**Weather → Context → Risk → Decision → Action**

It combines an Express.js orchestration server, a Python FastAPI deterministic risk engine, Open-Meteo forecast providers, and generative LLM providers (Gemini / OpenAI / Mock).

---

## Architecture Overview

```
Flutter Mobile App (Dart)
       │
       ▼  HTTP / REST & WebSockets
┌─────────────────────────────────────────────────────────────┐
│                 Main Express.js Orchestrator                │
│                        (Port 5000)                          │
└──────┬────────────────────┬────────────────────┬────────────┘
       │                    │                    │
       ▼                    ▼                    ▼
 ┌───────────┐        ┌───────────┐    ┌──────────────────┐
 │  MongoDB  │        │   Redis   │    │ Weather Provider │
 │ (Port 27017)       │ (Port 6379)    │   (Open-Meteo)   │
 └───────────┘        └───────────┘    └──────────────────┘
       │
       ▼
 ┌───────────────────────────────────────────────────────────┐
 │               Python FastAPI Risk Engine                  │
 │                       (Port 8000)                         │
 └────────────────────────────┬──────────────────────────────┘
                              │
                              ▼
                       Flutter Frontend
```

---

## Quick Start (Local Run)

### 1. Install Node.js Dependencies
```bash
cd backend
cmd /c npm install
```

### 2. Start Node.js Orchestrator
```bash
cmd /c npm run dev
```

### 3. Start Python FastAPI Risk Engine
```bash
cd risk-engine
pip install -r requirements.txt
python main.py
```

### 4. Docker Compose (Full Stack)
```bash
docker-compose up --build
```

---

## Flutter Integration Guide & API Endpoints

### 1. WeatherGPT Chat Endpoint
* **Method**: `POST`
* **Endpoint**: `/api/chat`
* **Request Body**:
```json
{
  "message": "I have to travel tomorrow from 7 AM to 11 AM. What time is better?",
  "latitude": 17.9689,
  "longitude": 79.5941,
  "language": "en"
}
```
* **Sample Flutter (Dart) HTTP Request**:
```dart
import 'dart:convert';
import 'http/http.dart' as http;

Future<Map<String, dynamic>> sendWeatherGptQuery(String message, double lat, double lon, String lang) async {
  final url = Uri.parse('http://10.0.2.2:5000/api/chat');
  final response = await http.post(
    url,
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'message': message,
      'latitude': lat,
      'longitude': lon,
      'language': lang,
    }),
  );
  return jsonDecode(response.body);
}
```

---

### 2. Authentication Endpoints
* `POST /api/auth/register` (Name, email, password, language)
* `POST /api/auth/login` (Email, password) -> returns JWT token
* `GET /api/auth/me` -> Headers: `Authorization: Bearer <token>`

---

### 3. Weather Endpoints
* `GET /api/weather/current?lat=17.9689&lon=79.5941`
* `GET /api/weather/forecast?lat=17.9689&lon=79.5941&days=7`
* `GET /api/weather/history?lat=17.9689&lon=79.5941&start_date=2026-09-01&end_date=2026-09-25`

---

### 4. GeoJSON Risk Map (Mapbox Integration)
* `GET /api/risk/map?lat=17.9689&lon=79.5941`
* Returns GeoJSON `FeatureCollection` ready for direct loading into Mapbox Flutter vector layers.

---

### 5. Geofenced Alerts Endpoint
* `GET /api/alerts?lat=17.9689&lon=79.5941&radius=50`
* `POST /api/alerts/check`

---

## Disclaimers & Safety Rules

> [!IMPORTANT]
> WeatherGPT risk scores are deterministic prototype assessments designed for decision support. They are **never** described as 100% "safe" (using *"lower weather-risk profile"*) and are strictly separated from official IMD warnings.
