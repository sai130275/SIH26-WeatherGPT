# WeatherGPT Judge & Evaluator Demo Guide

This guide outlines a step-by-step evaluation workflow demonstrating the working capabilities of WeatherGPT.

---

## Prerequisites for Live Demonstration

Ensure all three microservices are running locally, or access the deployed web application:
1. **Frontend**: `http://localhost:5173`
2. **API Gateway**: `http://localhost:5001/api/health` (Reports `status: UP`)
3. **AI Intelligence Engine**: `http://localhost:8000/health` or live at `https://sih26-weathergpt.onrender.com`

---

## Live Demo Walkthrough (12-Step Script)

### Step 1: Login & Role Selection
1. Navigate to `http://localhost:5173`.
2. Notice the clean authentication screen featuring instant demo login presets (*e.g., "Login as Dr. Rajesh Kumar - Disaster Manager"*).
3. Click the **Quick Demo Login** button or enter any demo email to enter the system immediately.

---

### Step 2: Live Weather Dashboard & Telemetry
1. Upon login, the **Dashboard** displays real-time atmospheric telemetry fetched live from the NWP models via Open-Meteo.
2. Note the telemetry cards:
   - **Temperature** & Feels-like index
   - **Humidity**, **Wind Velocity**, **Rain Probability**, and **Precipitation**
   - **Atmospheric Pressure**, **UV Index**, **Visibility**, and **Convective Available Potential Energy (CAPE)**
   - **Lightning Detection**: Real-time convective discharge flag.

---

### Step 3: Location Switching
1. Click the location selector dropdown in the top header (defaults to **Warangal, TS**).
2. Switch to **Hyderabad**, **Delhi**, **Mumbai**, or **Bengaluru**.
3. Observe the dashboard smoothly updating coordinates and fetching fresh numerical predictions without page reloads.

---

### Step 4: Hourly Timeline & 7-Day Model Consensus
1. Scroll down on the Dashboard to inspect the **Hourly Timeline**:
   - Displays 12-hour hourly trends with dynamic condition icons.
2. Inspect the **7-Day Outlook**:
   - Visual consensus bars showing daily highs, lows, and calibrated rain probability curves.

---

### Step 5: Real-Time Alerts
1. Click the **Alerts** tab on the bottom navigation bar (or click any active alert banner on the dashboard).
2. The alerts feed displays active warnings categorized by color-coded severity:
   - 🔴 **Red Alert (Warning)**: Immediate hazard requiring protective measures.
   - 🟠 **Orange Warning (Watch)**: Escalating threat.
   - 🟡 **Yellow Advisory (Advisory)**: Precautionary advisory.
3. Click on any alert card to open the **Alert Details Modal**, which shows the issuing agency, expiration timestamp, affected region, and safety actions.

---

### Step 6: Specialized Sector Modes (Disaster & Agriculture)
1. In the Dashboard grid, click on any sector action card:
   - **Farmer Advisory** (`map-farmer`): Agriculture-specific crop protection and rainfall outlook.
   - **Cyclone Tracker** (`map-cyclone`): Trajectory and pressure monitoring.
   - **Aviation** (`map-aviation`): Crosswind vectors, ceiling heights, and flight visibility metrics.
   - **Marine** (`map-marine`): Coastal conditions and wave heights.
2. Click **Back** to return to the Dashboard.

---

### Step 7: "Ask AI" Natural-Language Advisory
1. Click the **Ask AI** icon on the bottom navigation bar.
2. Type a contextual weather question, for example:
   > *"Is it safe to spray pesticides on paddy crops in Warangal tomorrow?"*
3. Press **Send**.
4. The frontend routes the request through the Node.js Gateway (Group 2), which retrieves current weather telemetry, passes it into the FastAPI Risk Engine (Group 3), and generates a scientifically grounded response.
5. Notice the response displays intent tags (`agriculture`) and source indicators (`weather`, `risk`).

---

### Step 8: Hands-Free Voice Input
1. In the Ask AI input bar, click the **Microphone** icon.
2. Speak your weather query aloud (using the Web Speech API).
3. The spoken audio is converted to text directly in the input box and sent to the intelligence engine.

---

### Step 9: Settings & Preferences
1. Click the **Settings** gear icon in the top header or through the bottom navigation.
2. Observe the granular unit toggles:
   - **Temperature**: Celsius (`°C`) ↔ Fahrenheit (`°F`)
   - **Wind Speed**: Kilometers per hour (`km/h`) ↔ Miles per hour (`mph`)
   - **Precipitation**: Millimeters (`mm`) ↔ Inches (`in`)
   - **Atmospheric Pressure**: Hectopascals (`hPa`) ↔ Inches of Mercury (`inHg`)

---

### Step 10: Global Unit Propagation Across the Platform
1. In Settings, toggle **Temperature** to **Fahrenheit (`°F`)** and **Wind Speed** to **Miles per hour (`mph`)**.
2. Return to the **Dashboard**:
   - All telemetry cards, hourly forecast badges, and 7-day outlook temperatures immediately convert to `°F` and `mph` seamlessly.
3. Switch to the sector views: the units remain synchronized globally via the application's unified `PreferencesContext`.

---

### Step 11: Resilient Fallback Demonstration
1. Explain to the judges how WeatherGPT prevents AI hallucination and maintains 100% uptime:
   - **Missing/Exhausted LLM Keys**: If Gemini/OpenAI API is unreachable or omitted, Group 3 automatically drops into `mode: "fallback"`. Rather than failing with a generic error, it evaluates deterministic meteorological rules and delivers structured safety guidance based directly on numerical sensor thresholds.
   - **Database & Cache Fallbacks**: If MongoDB or Redis are stopped, Group 2 continues running seamlessly using in-memory fallbacks.

---

### Step 12: Architectural Summary
Summarize the clean 3-tier separation:
1. **Group 1**: Client UI with global preference contexts and zero direct exposure of secrets.
2. **Group 2**: Robust Gateway providing auth, caching, rate-limiting, and external API orchestration.
3. **Group 3**: Mathematical risk evaluation, Pydantic type safety, and grounded LLM reasoning.
