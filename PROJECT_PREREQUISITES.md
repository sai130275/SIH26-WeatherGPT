# WeatherGPT Project Prerequisites & Audit

## 1. Software Required

*   **Node.js (v18+)**: REQUIRED (For Group 1 React Frontend and Group 2 Express Backend)
*   **npm**: REQUIRED (Package manager)
*   **Python 3.12+**: REQUIRED (For Group 3 FastAPI Engine)
*   **pip**: REQUIRED (Python package manager)
*   **Virtual Environment (venv)**: REQUIRED (For Group 3 dependencies)
*   **MongoDB**: OPTIONAL (Group 2 has a robust in-memory mock mode if MongoDB is unreachable)
*   **Redis**: OPTIONAL (Group 2 gracefully falls back to an in-memory Map if Redis is unreachable)

## 2. API Keys Required

*   **`GEMINI_API_KEY` / `OPENAI_API_KEY`** (Group 2): 
    *   **Provider**: Google / OpenAI
    *   **Required for MVP?**: No. The orchestrator has a fallback mode.
    *   **What breaks?**: Rich natural language generation will be replaced by deterministic fallback text.
    *   **Configuration**: `group2/.env`
*   **`LLM_API_KEY`** (Group 3): 
    *   **Provider**: OpenAI / Anthropic / Google
    *   **Required for MVP?**: No. The intelligence engine handles missing keys gracefully.
    *   **What breaks?**: Evidence-based natural language insights (returns raw JSON analysis instead).
    *   **Configuration**: `group3/.env`
*   **`VITE_SUPABASE_ANON_KEY`** (Group 1): 
    *   **Provider**: Supabase
    *   **Required for MVP?**: No.
    *   **What breaks?**: Cloud sync of user preferences and chat history (fails silently, app still works).
    *   **Configuration**: `group1/.env.local`

*(Note: Weather data uses Open-Meteo, which is a public API requiring NO authentication keys).*

## 3. Environment Variables

| Variable | Group | Required | Purpose | Example |
| -------- | ----- | -------- | ------- | ------- |
| `VITE_API_BASE_URL` | Group 1 | **Yes** | Directs frontend to Group 2 gateway | `http://localhost:5001/api` |
| `VITE_SUPABASE_URL` | Group 1 | No | Cloud DB URL for preferences | `https://xyz.supabase.co` |
| `VITE_SUPABASE_ANON_KEY` | Group 1 | No | Cloud DB public auth key | `ey...` |
| `PORT` | Group 2 | **Yes** | Local port for the Node gateway | `5001` |
| `JWT_SECRET` | Group 2 | **Yes** | Signs auth tokens | `dev-secret-123` |
| `GROUP3_URL` | Group 2 | **Yes** | Directs gateway to the AI engine | `http://localhost:8000` |
| `MONGODB_URI` | Group 2 | No | MongoDB connection string | `mongodb://localhost:27017/weathergpt` |
| `REDIS_URL` | Group 2 | No | Redis connection string | `redis://localhost:6379` |
| `OPEN_METEO_BASE_URL`| Group 2 | No | Public weather data provider | `https://api.open-meteo.com/v1` |
| `GEMINI_API_KEY` | Group 2 | No | LLM Integration | `AIzaSy...` |
| `PORT` | Group 3 | No | Port for FastAPI (defaults 8000) | `8000` |
| `LLM_PROVIDER` | Group 3 | No | Selects the active LLM | `openai` |
| `LLM_API_KEY` | Group 3 | No | Secret for the active LLM | `sk-proj...` |

## 4. Ports & Networking

*   **Group 1 (Frontend)**: `5173`
*   **Group 2 (Gateway)**: `5001`
*   **Group 3 (Engine)**: `8000`
*   **MongoDB**: `27017` (Optional)
*   **Redis**: `6379` (Optional)

*No port conflicts exist in the current setup. Group 2 intentionally moved to 5001 to avoid macOS AirPlay/AirTunes conflicts on 5000.*

## 5. External Services

*   **Weather APIs (Open-Meteo)**: REQUIRED (Free, open source, no keys).
*   **LLM APIs (OpenAI/Gemini)**: OPTIONAL (Mock/fallback modes active).
*   **Database (MongoDB)**: OPTIONAL (In-memory mock active).
*   **Cache (Redis)**: OPTIONAL (In-memory mock active).
*   **User Profiles (Supabase)**: OPTIONAL (Wrapped in try/catch).

## 6. Startup Order

Start the ecosystem in this exact order to ensure gateways resolve correctly:

**1. Group 3 (Intelligence Engine)**
```bash
cd group3
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --port 8000
```

**2. Group 2 (API Gateway)**
```bash
cd group2
npm install
npm run dev
```

**3. Group 1 (Frontend UI)**
```bash
cd group1
npm install
npm run dev
```

## 7. MVP Readiness

*   🟢 **Weather API (Open-Meteo)**: Ready (No configuration needed)
*   🟢 **Frontend Gateway integration**: Ready (Phase 1 & 2 complete)
*   🟢 **Database & Cache**: Ready (In-memory fallbacks prevent blocking)
*   🟡 **LLM Integrations**: Needs configuration (Currently operating in fallback mode until keys are provided in `.env`)
