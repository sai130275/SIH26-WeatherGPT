# Group 1 Frontend Integration Plan

## 1. Current Frontend Architecture
- **Framework**: React 18 + Vite + TypeScript + Tailwind CSS.
- **Routing**: Manual state-based routing (`currentPage` in `App.tsx`).
- **State**: Primarily local React hooks. Supabase is used directly on the client to persist `user_preferences` and `chat_messages`.
- **API Status**: No REST API calls are currently made to any backend.

## 2. Current Mock-Data Usage
The entire UI is driven by hardcoded data located in `src/data/mockData.ts` and `src/pages/AskAIPage.tsx`:
- `hourlyForecast`, `dayForecast`, `telemetryData`, `weatherAlerts`, `locations`, `mapLayers`.
- `defaultRichData` (Hardcoded responses mimicking AI intent detection).

## 3. Backend API Mapping
The frontend should **only** communicate with Group 2 (`http://localhost:5001`), which acts as the gateway to Group 3 (`http://localhost:8000`).

| UI Component / Page | Target Group 2 Endpoint (Gateway) | Proxied to Group 3? |
| :--- | :--- | :--- |
| `LoginPage.tsx` | `POST /api/auth/login` | No |
| `DashboardPage.tsx` | `GET /api/weather/current` | No |
| `DashboardPage.tsx` | `GET /api/weather/forecast` | No |
| `DashboardPage.tsx`, `AlertsPage.tsx` | `GET /api/alerts` | No |
| `AskAIPage.tsx` | `POST /api/chat` | Yes (`/chat`) |
| `MapPage.tsx` | `GET /api/risk/map` | No |

## 4. Schema Mismatches
**Critical Misalignments:**
1. **Chat UI vs API**: `AskAIPage.tsx` renders rich cards requiring `floodRisk`, `lightningRisk`, and `hourlyRain` (defined as `RichAIData`). Group 3's backend currently only returns a flat `{ answer, intent, sources, mode, conversation_id }`. The UI must either safely degrade to a standard text bubble or Group 3 must be updated.
2. **Weather Data vs UI**: The frontend expects pre-formatted `TelemetryItem[]` (with Tailwind color codes like `text-error`). Group 2 returns raw JSON data (`temperature`, `humidity`, etc.). The frontend will need a data transformer utility.
3. **Alerts**: The frontend expects `WeatherAlert[]` with specific fields (`severity`, `validUntil`, `icon`). Group 2 returns alerts from its `alertService` which will need mapping to the frontend's expected properties.

## 5. Files That Must Change
- `src/App.tsx`: Must add global JWT token state and pass it down.
- `src/pages/LoginPage.tsx`: Implement `axios.post` to `/api/auth/login`.
- `src/pages/DashboardPage.tsx`: Fetch from `/api/weather/*` instead of importing mock data.
- `src/pages/AskAIPage.tsx`: Fetch from `/api/chat` and map the simplified backend response to the UI.
- `src/pages/AlertsPage.tsx`: Fetch from `/api/alerts`.

## 6. Files That Should NOT Change
- `src/components/*` (Header, BottomNav, Icon, Toggle) - UI primitives are sound.
- `src/pages/SettingsPage.tsx` & `src/pages/ProfilePage.tsx` - Local preference handling via Supabase is currently fine for MVP.
- `index.html`, `tailwind.config.js`, `vite.config.ts`.
- Group 2 and Group 3 backend business logic (unless the Chat schema mismatch is addressed backend-side).

## 7. Required Environment Variables
Add to `group1/.env` (or `.env.local`):
```env
VITE_API_BASE_URL=http://localhost:5001/api
```

## 8. Required TypeScript Interfaces/Types
Update `src/types/index.ts` to match Group 2/3 contracts:
```typescript
// Add these to match the backend
export interface ChatRequest {
  message: string;
  latitude: number;
  longitude: number;
  language?: string;
  conversation_id?: string;
}

export interface ChatResponse {
  answer: string;
  intent: string;
  sources: string[];
  mode: string;
  conversation_id: string;
}

export interface ApiBaseResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}
```

## 9. Authentication Flow
1. User enters credentials in `LoginPage`.
2. Frontend calls `POST /api/auth/login`.
3. Group 2 validates and returns a JWT.
4. `App.tsx` stores the JWT in React State (or localStorage).
5. All subsequent requests (Weather, Alerts, Chat) attach `Authorization: Bearer <token>`.

## 10. Chat Flow (`AskAIPage`)
1. User submits a text/voice query.
2. Frontend constructs `ChatRequest` (including hardcoded or GPS location).
3. `axios.post('/api/chat', ...)` is executed.
4. Group 2 fetches live weather, constructs context, and proxies to Group 3 `/chat`.
5. Frontend receives `ChatResponse` and appends it to the `messages` state.
6. Supabase `chat_messages` insert is retained for analytics/history.

## 11. Weather/Risk/Advisory Data Flow
1. `DashboardPage` mounts.
2. `axios.get('/api/weather/current?lat=X&lon=Y')` is called.
3. Raw data is mapped into the `TelemetryItem[]` array using a transformer function.
4. `axios.get('/api/weather/forecast?lat=X&lon=Y&days=3')` is called.
5. Raw hourly/daily data is mapped to `HourlyForecast[]` and `DayForecast[]`.

## 12. Exact Implementation Order
1. **Setup**: Install `axios` and add `VITE_API_BASE_URL` to env. Create an `api.ts` utility with an Axios interceptor for JWT injection.
2. **Auth Integration**: Update `LoginPage.tsx` to handle real login and bubble the token to `App.tsx`.
3. **Chat Integration**: Update `AskAIPage.tsx` to hit `/api/chat` and map the response. Create fallback UI for missing rich data.
4. **Weather Integration**: Update `DashboardPage.tsx` to fetch current weather and forecasts.
5. **Alerts Integration**: Update `AlertsPage.tsx` to fetch from `/api/alerts`.

## 13. Integration Risks
- **Cross-Origin Resource Sharing (CORS)**: Group 2's `cors` middleware must explicitly allow `http://localhost:5173` (Vite's default port), or allow `*` (which it currently does).
- **Graceful Degradation**: The frontend will look "broken" if it blindly expects arrays/objects (like `telemetryData`) that APIs fail to provide. Optional chaining `?.` must be heavily utilized during the mapping phase.

## 14. Definition of Done
Integration is complete when:
- The user can log in via the backend.
- The Dashboard reflects real weather data from Open-Meteo via Group 2.
- The Chat interface queries the real Group 3 AI pipeline and displays the answer.
- All mocked files (`src/data/mockData.ts`) are safely deleted or completely bypassed in production flow.
