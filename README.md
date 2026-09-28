# WeatherGPT

WeatherGPT is a cutting-edge weather dashboard MVP demonstrating a microservice architecture built with React, Node.js, and FastAPI. It integrates live weather data, local hazard assessment, and a Google Gemini AI-powered natural language chat interface, which falls back natively to deterministic templates when AI limits are reached.

## 🏗️ Architecture

```text
+------------------+         +-----------------+         +---------------------+
|                  |         |                 |         |                     |
|  React Group 1   |  ---->  | Node.js Group 2 |  ---->  | FastAPI Group 3     |
|  (Frontend UI)   |         | (API Gateway)   |         | (AI / Risk Engine)  |
|  Port: 5173      |  <----  | Port: 5001      |  <----  | Port: 8000          |
+------------------+         +-----------------+         +---------------------+
                                                                |
                                                                v
                                                       +-------------------+
                                                       |                   |
                                                       | Google Gemini AI  |
                                                       |                   |
                                                       +-------------------+
```

## ⚙️ Prerequisites
- **Node.js**: v18+ (for Group 1 and Group 2)
- **Python**: 3.10+ (for Group 3)
- **npm**: v9+
- **pip**: Latest
- **Redis (Optional)**: Group 2 uses in-memory caching natively but attempts to connect to Redis on port 6379 for robust distributed caching if available.

## 🔑 Environment Variables

### Group 1 (`group1/.env.local`)
```env
VITE_API_BASE_URL=http://localhost:5001/api
```

### Group 2 (`group2/.env`)
```env
PORT=5001
NODE_ENV=development
GROUP3_URL=http://localhost:8000
REDIS_URL=redis://localhost:6379
JWT_SECRET=super_secret_jwt_key
```

### Group 3 (`group3/.env`)
```env
LLM_PROVIDER=google
LLM_API_KEY=your_gemini_api_key_here
LLM_MODEL=gemini-2.5-flash
OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
```

> **Security Note:** Never commit actual API keys to source control. `.env` and `.env.local` files are explicitly included in `.gitignore`.

## 🚀 How to Run

### Start Group 3 (AI / Risk Engine)
```bash
cd group3
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --port 8000 --env-file .env
```

### Start Group 2 (API Gateway)
```bash
cd group2
npm install
npm run dev
```

### Start Group 1 (Frontend UI)
```bash
cd group1
npm install
npm run dev
```
Navigate to `http://localhost:5173` to view the application.

## 🧪 Testing

### Group 3 (Pytest)
```bash
cd group3
source .venv/bin/activate
pytest tests/
```

### Group 2 (Jest)
```bash
cd group2
npm run test
```

### Group 1 (Typecheck & Build)
```bash
cd group1
npm run typecheck
npm run build
```

## 🧠 Gemini Configuration & Fallback Behavior

Group 3 handles external LLM interactions. It is natively configured to communicate with Google Gemini via the `OpenAI Python SDK` mapped to Gemini's OpenAI compatibility endpoint.
- **Gemini (mode: "llm")**: Used by default when `LLM_API_KEY` is provided and the model is available.
- **Fallback (mode: "fallback")**: Automatically triggered if the Gemini API is rate-limited (e.g. 503 errors), unreachable, or the API key is missing. This deterministic engine safely resolves the user's intent without failing the application request.
