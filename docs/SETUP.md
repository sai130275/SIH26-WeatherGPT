# WeatherGPT Setup & Deployment Guide

This guide covers local environment setup, dependency installation, service startup sequence, and production deployment configuration for WeatherGPT.

---

## 1. Prerequisites

Before running the project, ensure your workstation has the following installed:

*   **Node.js**: v18.0.0 or higher
*   **npm**: v9.0.0 or higher
*   **Python**: v3.12.0 or higher
*   **pip**: Included with Python 3.12
*   **Git**: For version control
*   *(Optional)* **MongoDB**: Local instance on port `27017` (Group 2 includes an automatic in-memory fallback if absent)
*   *(Optional)* **Redis**: Local instance on port `6379` (Group 2 includes an automatic in-memory cache if absent)

---

## 2. Port Allocation Summary

| Service | Port | Description |
| :--- | :--- | :--- |
| **Group 3 (FastAPI AI Engine)** | `8000` | Machine learning & risk evaluation service |
| **Group 2 (Node.js API Gateway)** | `5001` | API Gateway, authentication, and weather adapter *(5001 avoids macOS AirPlay conflicts)* |
| **Group 1 (React Frontend)** | `5173` | Vite development web server |

---

## 3. Local Development Setup

To ensure gateways resolve dependencies properly, start services in the following order:

```text
Step 1: Start Group 3 (AI Engine on 8000)
Step 2: Start Group 2 (Gateway on 5001)
Step 3: Start Group 1 (Frontend on 5173)
```

---

### Step 1: Group 3 (Python / FastAPI AI Service)

1. Navigate to the `group3` directory:
   ```bash
   cd group3
   ```

2. Create and activate a Python 3.12 virtual environment:
   ```bash
   # macOS / Linux
   python3.12 -m venv .venv
   source .venv/bin/activate

   # Windows
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Install required Python packages:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. Configure environment:
   ```bash
   cp .env.example .env
   ```
   *Edit `.env` if you have a Gemini or OpenAI key. If omitted, the service will run in deterministic fallback mode.*

5. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   *Verify: Open `http://localhost:8000/health` in your browser. Expected: `{"status":"ok"}`.*

---

### Step 2: Group 2 (Node.js / Express API Gateway)

1. Open a new terminal and navigate to `group2`:
   ```bash
   cd group2
   ```

2. Install npm dependencies:
   ```bash
   npm install
   ```

3. Configure environment:
   ```bash
   cp .env.example .env
   ```
   *For local development, the default values in `.env.example` point to `http://localhost:8000` for Group 3 and port `5001`.*

4. Start the Node.js API Gateway:
   ```bash
   npm run dev
   ```
   *Verify: Open `http://localhost:5001/api/health` in your browser. Expected: `{"status":"UP", ...}`.*

---

### Step 3: Group 1 (React 18 / Vite Frontend)

1. Open a new terminal and navigate to `group1`:
   ```bash
   cd group1
   ```

2. Install npm dependencies:
   ```bash
   npm install
   ```

3. Configure environment:
   ```bash
   cp .env.example .env.local
   ```
   *Verify that `VITE_API_BASE_URL` points to `http://localhost:5001/api`.*

4. Start the Vite development server:
   ```bash
   npm run dev
   ```
   *Open `http://localhost:5173` in your browser to interact with the full application.*

---

## 4. Environment Variables Reference

### Group 1 (Frontend)

| Variable | Required | Default / Local | Production Example | Description |
| :--- | :--- | :--- | :--- | :--- |
| `VITE_API_BASE_URL` | **Yes** | `http://localhost:5001/api` | `https://api.yourdomain.com/api` | API Gateway endpoint (supports `VITE_API_URL` as alias). |
| `VITE_SUPABASE_URL` | No | *(Empty)* | `https://xyz.supabase.co` | Optional cloud preference sync. |
| `VITE_SUPABASE_ANON_KEY` | No | *(Empty)* | `eyJhb...` | Public Supabase anon key. |

---

### Group 2 (Gateway)

| Variable | Required | Default / Local | Production Example | Description |
| :--- | :--- | :--- | :--- | :--- |
| `PORT` | **Yes** | `5001` | `10000` (Render default) | Port for the Express HTTP server. |
| `NODE_ENV` | **Yes** | `development` | `production` | Enables production security & logging. |
| `JWT_SECRET` | **Yes** | `dev-secret-123` | *(Secure random string)* | Key used to sign and verify user JWTs. |
| `GROUP3_URL` | **Yes** | `http://localhost:8000` | `https://sih26-weathergpt.onrender.com` | Live URL for Group 3 (without trailing slash). |
| `ALLOWED_ORIGINS` | No | `*` | `https://weathergpt.vercel.app` | Comma-separated CORS allowed origins. |
| `MONGODB_URI` | No | `mongodb://localhost:27017/weathergpt` | `mongodb+srv://...` | MongoDB connection string. |
| `REDIS_URL` | No | `redis://localhost:6379` | `rediss://...` | Redis cache connection string. |
| `OPEN_METEO_BASE_URL` | No | `https://api.open-meteo.com/v1` | `https://api.open-meteo.com/v1` | Open-Meteo endpoint. |

---

### Group 3 (AI Service)

| Variable | Required | Default / Local | Production Example | Description |
| :--- | :--- | :--- | :--- | :--- |
| `PORT` | No | `8000` | `8000` | FastAPI server port. |
| `LLM_PROVIDER` | No | `google` | `google` or `openai` | Active generative model provider. |
| `LLM_API_KEY` | No | *(Empty)* | *(Secret API Key)* | Gemini or OpenAI API key. |
| `LLM_MODEL` | No | `gemini-1.5-flash` | `gemini-1.5-flash` | Target LLM model name. |
| `CORS_ORIGINS` | No | `*` | `*` | Allowed CORS origins. |

---

## 5. Running Automated Tests

### Group 3 Test Suite (Pytest)
```bash
cd group3
source .venv/bin/activate
pytest tests/ -v
```
*Expected: 347 unit tests passing covering risk calculation, weather normalization, evidence synthesis, and prompt handling.*

### Group 2 Test Suite (Jest)
```bash
cd group2
npm test
```
*Expected: 15 integration tests passing covering auth, weather endpoints, alerts, and Group 3 proxying.*

### Group 1 Typecheck & Build
```bash
cd group1
npm run typecheck
npm run build
```
*Expected: 0 TypeScript errors and static assets compiled to `group1/dist/`.*
