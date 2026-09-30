# WeatherGPT Repository Structure Guide

This document provides a comprehensive map of the WeatherGPT codebase to help judges, evaluators, and contributors quickly understand the project organization.

---

## High-Level Layout

```text
Weathergpt/
├── README.md               # Master documentation for judges & overview
├── LICENSE                 # MIT Open Source License
├── .gitignore              # Multi-tier exclusion for secrets, node_modules, and cache
├── docs/                   # Complete evaluation & technical documentation
│   ├── ARCHITECTURE.md     # System architecture, data flow & fallback mechanics
│   ├── SETUP.md            # Local installation & deployment guide
│   ├── API.md              # Complete API endpoint specification
│   ├── DEMO_GUIDE.md       # Step-by-step evaluation guide for judges
│   ├── DEMO_SCRIPT.md      # Timed 3-5 minute presenter demo script
│   ├── PROJECT_OVERVIEW.md # Problem, personas, workflow, and technology overview
│   ├── FEATURES.md         # Factual feature matrix (Current MVP vs Future Expansion)
│   ├── PROGRESS.md         # Milestone tracker ([x] Current MVP, [~] Partial, [ ] Future)
│   ├── FUTURE_EXPANSIONS.md# Detailed roadmap across Categories A through E
│   ├── JUDGE_GUIDE.md      # Judge evaluation hub, testing guide, and demo flow
│   ├── CHECKLIST.md        # Submission & future architecture readiness checklist
│   └── PROJECT_STRUCTURE.md# This codebase map
├── group1/                 # Group 1: React 18 / Vite / TypeScript Frontend
├── group2/                 # Group 2: Node.js / Express API Gateway
├── group3/                 # Group 3: Python 3.12 / FastAPI AI & Intelligence Engine
├── archive/                # Preserved roadmap code & architectural prototypes
│   └── map/                # Archived interactive Leaflet Map implementation
└── demo/                   # UI verification screenshots for visual reference
```

---

## Detailed Directory Breakdown

### 1. `group1/` — Frontend (React 18 + Vite + TypeScript)

The client application is built with React 18, Vite, TypeScript, and Tailwind CSS.

```text
group1/
├── index.html              # HTML shell & font definitions
├── vite.config.ts          # Vite configuration with '@/' path aliases
├── tailwind.config.js      # Design tokens, color palette, and spacing scales
├── tsconfig.json           # TypeScript configuration
├── package.json            # Frontend dependencies (Leaflet, Lucide, Axios)
├── .env.example            # Environment template for frontend
├── dist/                   # Production build distribution directory
└── src/
    ├── main.tsx            # React application root entrypoint
    ├── App.tsx             # Main routing orchestrator & JWT session manager
    ├── index.css           # Global typography, color tokens, and custom scrollbars
    ├── components/         # Reusable UI primitives
    │   ├── Header.tsx      # Top bar with location selector, time & settings trigger
    │   ├── BottomNav.tsx   # Mobile-first persistent navigation bar
    │   ├── Icon.tsx        # Dynamic Material Symbols icon wrapper
    │   └── UpcomingModal.tsx # Modal explaining roadmap features
    ├── context/            # Global React Contexts
    │   └── PreferencesContext.tsx # Context for global units (°C/°F, km/h/mph, etc.)
    ├── pages/              # Primary view controllers
    │   ├── DashboardPage.tsx # Live telemetry, hourly timeline, 7-day outlook
    │   ├── AskAIPage.tsx   # Natural-language weather assistant with speech-to-text
    │   ├── AlertsPage.tsx  # Color-coded geofenced alert cards with detail modal
    │   ├── SettingsPage.tsx# Unit preference controls & theme configuration
    │   ├── ProfilePage.tsx # User profile & agency role display
    │   ├── LoginPage.tsx   # Authentication view with demo login presets
    │   └── MapPage.tsx     # Active sector views (agriculture, cyclone, aviation)
    ├── lib/
    │   ├── api.ts          # Axios client with base URL auto-normalization & JWT interceptors
    │   └── supabase.ts     # Supabase client for preference synchronization
    ├── types/              # TypeScript definitions & API contract interfaces
    │   ├── index.ts        # App UI models (telemetry, alerts, preferences)
    │   └── api.ts          # Backend API response envelopes (ApiBaseResponse<T>)
    ├── utils/
    │   └── units.ts        # Pure conversion utilities for temperatures, winds, precip, pressure
    └── data/
        └── mockData.ts     # Default fallback values and initial state definitions
```

---

### 2. `group2/` — API Gateway (Node.js + Express)

The gateway acts as the central orchestrator and security perimeter for all backend services.

```text
group2/
├── package.json            # Gateway dependencies (Express, Axios, Socket.IO, ioredis)
├── .env.example            # Environment template for gateway
├── Dockerfile              # Container configuration for production hosting
├── docker-compose.yml      # Local orchestration with optional MongoDB & Redis
├── tests/                  # Automated integration test suite
│   │   ├── api.test.js     # End-to-end API route tests
│   │   └── group3Integration.test.js # Proxy and fallback tests for Group 3
│   └── test_integration_flow.js # Standalone integration verification script
└── src/
    ├── app.js              # Express app factory, CORS, helmet, socket.io, and routes
    ├── config/             # System configuration
    │   ├── env.js          # Centralized environment variable validation
    │   ├── db.js           # Mongoose connector with automatic in-memory fallback
    │   └── redis.js        # Redis connector with automatic in-memory Map fallback
    ├── controllers/        # Request handling logic
    │   ├── authController.js   # User registration and JWT authentication
    │   ├── weatherController.js# Telemetry retrieval with caching layer
    │   ├── chatController.js   # Enrichment & proxying to Group 3
    │   ├── alertController.js  # Geofenced alert queries
    │   └── mapController.js    # GeoJSON hazard layer rendering
    ├── routes/             # Express route definitions
    │   ├── authRoutes.js   # /api/auth/*
    │   ├── weatherRoutes.js# /api/weather/*
    │   ├── chatRoutes.js   # /api/chat
    │   ├── alertRoutes.js  # /api/alerts/*
    │   ├── mapRoutes.js    # /api/risk/*
    │   └── healthRoutes.js # /api/health
    ├── middleware/         # Custom Express middlewares
    │   ├── auth.js         # JWT bearer token verification
    │   └── errorHandler.js # Standardized error formatter
    ├── providers/          # External data provider adapters
    │   ├── WeatherProvider.js # Abstract provider base class
    │   └── OpenMeteoProvider.js # Concrete Open-Meteo NWP adapter
    ├── services/           # Gateway client adapters
    │   ├── riskClient.js   # HTTP client calling Group 3 /risk
    │   ├── advisoryClient.js # HTTP client calling Group 3 /advisory
    │   └── alertService.js # Alert aggregation & persistence service
    ├── models/             # Mongoose database models
    │   ├── User.js         # User credential & profile schema
    │   └── Alert.js        # Meteorological alert schema
    └── utils/
        └── responseFormatter.js # Standardized JSON envelope { success, data, error }
```

---

### 3. `group3/` — AI & Intelligence Engine (Python 3.12 + FastAPI)

The intelligence layer implements scientific risk modeling, prompt synthesis, and LLM inference.

```text
group3/
├── requirements.txt        # Python dependencies (fastapi, pydantic, uvicorn, numpy, pandas)
├── .python-version         # Pinned Python version (3.12.4) for Render/Railway
├── .env.example            # Environment template for AI service
├── README.md               # Group 3 specific technical overview
├── tests/                  # Pytest unit & regression test suite (347 tests)
│   ├── test_health.py      # Liveness probe tests
│   ├── test_risk_engine.py # Multi-hazard risk math & threshold tests
│   ├── test_weather_processor.py # Observation normalization tests
│   ├── test_condition_detector.py # Heavy rain, heat, and storm detection tests
│   ├── test_evidence.py    # Evidence grounding & confidence scoring tests
│   ├── test_chat.py        # Conversational reasoning & fallback mode tests
│   ├── test_advisory.py    # Sector advisory generation tests
│   └── test_integration.py # End-to-end FastAPI endpoint tests
└── app/
    ├── main.py             # FastAPI application factory & router registration
    ├── core/
    │   └── config.py       # Pydantic BaseSettings loading from environment
    ├── schemas/            # Pydantic data validation models
    │   ├── weather.py      # WeatherData & Observation input schemas
    │   ├── risk.py         # RiskResult & RiskAnalysis output schemas
    │   ├── chat.py         # ChatRequest & ChatResponse schemas
    │   └── advisory.py     # AdvisoryPayload & ImpactAdvisory schemas
    ├── services/           # Mathematical & AI processing engines
    │   ├── weather_processor.py # Normalizes and validates incoming weather data
    │   ├── condition_detector.py# Heuristic feature extractor (rain, heat, wind)
    │   ├── risk_engine.py  # Multi-hazard risk scoring algorithm (0-100)
    │   ├── evidence_engine.py # RAG evidence synthesis & confidence calculator
    │   ├── llm_service.py  # Gemini & OpenAI provider adapter with fallback mode
    │   └── advisory_engine.py # Sector impact rule generator
    └── api/
        └── routes/
            ├── health.py   # GET /health
            ├── chat.py     # POST /chat
            ├── risk.py     # POST /risk
            └── advisory.py # POST /advisory
```

---

### 4. `archive/` — Archived Features

Contains code intentionally separated from the active MVP:
*   `archive/map/MapPage.tsx`: Full interactive Leaflet map implementation with vector tiles and GeoJSON overlays, preserved for future roadmap deployment.
*   `archive/map/README.md`: Explanatory notice detailing why the map was separated and how to restore it.
