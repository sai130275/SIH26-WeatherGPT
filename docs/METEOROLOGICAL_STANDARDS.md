# Meteorological Standards & Authority Attribution Reference

This document provides complete, transparent documentation of all meteorological standards, thresholds, formulas, and references implemented in the **Weather Intelligence & Data Fusion Engine (Module 1.2)**.

Every threshold is grounded either in an authoritative national/international standard (IMD, WMO, ICAO) or explicitly documented as an engineering heuristic proxy.

---

## 1. Summary of Standards & Verification Status

| Hazard / Parameter | Code Threshold | Standard / Authority | Authoritative Reference | Verification Status |
|---|---:|---|---|---|
| **Rainfall (24-hour)** | ≥ 64.5 mm/24h | IMD Heavy Rain | IMD Forecasters Manual / NWFC Terminology | **VERIFIED (24-Hour Only)** |
| **Rainfall (24-hour)** | ≥ 115.6 mm/24h | IMD Very Heavy Rain | IMD Forecasters Manual / NWFC Terminology | **VERIFIED (24-Hour Only)** |
| **Rainfall (24-hour)** | ≥ 204.5 mm/24h | IMD Extremely Heavy Rain | IMD Forecasters Manual / NWFC Terminology | **VERIFIED (24-Hour Only)** |
| **Rainfall (1-hour)** | ≥ 100.0 mm/h | IMD Cloudburst | IMD Meteorological Glossary | **VERIFIED (Hourly Only)** |
| **Extreme Heat** | ≥ 40.0 °C | IMD Heatwave Baseline | IMD Heat Wave Criteria (Plains Baseline) | **HEURISTIC ABSOLUTE PROXY** |
| **Extreme Heat (Severe)** | ≥ 45.0 °C | IMD Severe Heatwave | IMD Heat Wave Criteria (Absolute Max) | **HEURISTIC ABSOLUTE PROXY** |
| **Extreme Cold** | ≤ 5.0 °C | IMD Cold Wave Baseline | IMD Cold Wave Criteria (Plains Core) | **HEURISTIC ABSOLUTE PROXY** |
| **Extreme Cold (Severe)** | ≤ 2.0 °C | IMD Severe Cold Wave | IMD Cold Wave Criteria (Absolute Min) | **HEURISTIC ABSOLUTE PROXY** |
| **Wind (High Wind)** | ≥ 50.0 km/h | WMO Beaufort Scale 7 | WMO-No. 8 / Beaufort Wind Scale | **VERIFIED** |
| **Wind (Gale Force)** | ≥ 62.0 km/h | WMO Beaufort Scale 8 | WMO-No. 8 / Beaufort Wind Scale | **VERIFIED** |
| **Wind (Storm Force)** | ≥ 89.0 km/h | WMO Beaufort Scale 10 | WMO-No. 8 / Beaufort Wind Scale | **VERIFIED** |
| **Visibility (Low)** | ≤ 1.0 km | ICAO / WMO Aviation Fog | ICAO Annex 3 / WMO-No. 8 | **VERIFIED** |
| **Visibility (Dense Fog)** | ≤ 0.2 km (200 m) | ICAO Dense Fog | ICAO Annex 3 / WMO-No. 8 | **VERIFIED** |
| **Thunderstorm (CAPE)** | ≥ 1000 / 2000 J/kg | Convective Instability | NOAA NWS JetStream / Mesoscale Literature | **HEURISTIC CONVECTIVE PROXY** |
| **Thunderstorm (Lightning)**| WW 95, 96, 99 | WMO Weather Code | WMO Manual on Codes (WMO-No. 306) | **VERIFIED** |
| **Thermal Comfort / Heat Index**| Rothfusz Equation | NOAA / NWS | NWS Technical Attachment SR 90-23 | **VERIFIED** |
| **Wind Chill** | JAG/TI Formula | NOAA / NWS / Environment Canada | Joint Action Group on Temperature Indices | **VERIFIED** |
| **Flood Risk Score** | Weighted Composite | Engineering Proxy | System Heuristic (Rainfall + Condition + Pressure) | **HEURISTIC ENGINEERING PROXY** |

---

## 2. IMD 24-Hour Rainfall Criteria

### 2.1 Authoritative Source
- **Authority**: India Meteorological Department (IMD), Ministry of Earth Sciences (MoES), Government of India.
- **Publication**: *Terminology and Criteria for Weather Forecasts and Warnings*, National Weather Forecasting Centre (NWFC), Mausam Bhawan, New Delhi.
- **Reference URL**: [https://mausam.imd.gov.in](https://mausam.imd.gov.in)
- **Applicability**: 24-hour accumulated rainfall recorded between 08:30 IST on day $D$ and 08:30 IST on day $D+1$.

### 2.2 Standard Classification Table

| Category | 24-Hour Accumulation (mm) | Severity Rating |
|---|---|---|
| **No Rain** | 0.0 mm | None |
| **Very Light Rain** | 0.1 to 2.4 mm | Low |
| **Light Rain** | 2.5 to 15.5 mm | Low |
| **Moderate Rain** | 15.6 to 64.4 mm | Low / Moderate |
| **Heavy Rain** | 64.5 to 115.5 mm | Moderate / High |
| **Very Heavy Rain** | 115.6 to 204.4 mm | High |
| **Extremely Heavy Rain** | ≥ 204.5 mm | Extreme |

### 2.3 Cloudburst Definition
- **Definition**: Rain intensity of **≥ 100 mm within 1 hour** over a localized geographical region (approx. 20–30 km²).
- **Code implementation**: Evaluated on hourly precipitation rates (`mm/h`) under `IMD_CLOUDBURST_CRITERIA`.

### 2.4 Implementation Integrity Rules
1. **Never compare hourly precipitation against 24-hour thresholds**: An hourly precipitation rate (e.g. 70 mm/h) must not be directly compared against the 64.5 mm 24-hour threshold.
2. **Data Availability Requirement**: If valid 24-hour accumulation (`rainfall_24h` or `daily[0].precipitation_sum`) is absent, the engine returns an explicit `insufficient_rainfall_data` event explaining that 24-hour accumulation data is unavailable.

---

## 3. IMD Heatwave & Cold Wave Criteria

### 3.1 IMD Heatwave Criteria & Distinctions

#### Official IMD Standard
- **Source**: IMD Guidelines on Heat Wave Warning (FAQs on Heat Wave, IMD National Weather Forecasting Centre).
- **Official Definition**:
  - Baseline requirement: Maximum temperature must reach at least **40 °C for Plains**, **37 °C for Coastal stations**, and **30 °C for Hilly stations**.
  - **Departure from Normal**:
    - *Heat Wave*: Departure from climatological normal is $+4.5\text{ }^\circ\text{C}$ to $+6.4\text{ }^\circ\text{C}$.
    - *Severe Heat Wave*: Departure from climatological normal is $\ge +6.5\text{ }^\circ\text{C}$.
  - **Actual Maximum Temperature (independent of normal)**:
    - *Heat Wave*: Maximum temperature $\ge 45.0\text{ }^\circ\text{C}$.
    - *Severe Heat Wave*: Maximum temperature $\ge 47.0\text{ }^\circ\text{C}$.

#### Distinction & Code Limitation
> [!WARNING]
> The engine evaluates **absolute temperature thresholds** ($\ge 40.0\text{ }^\circ\text{C}$ for high heat, $\ge 45.0\text{ }^\circ\text{C}$ for severe heat).
> The system does **not** evaluate 30-year station climatology departures because long-term climatological records are not provided in real-time provider APIs.
> Therefore, these detections are classified as **Heuristic Absolute Proxies** and are tagged `is_official_warning=False`.

---

### 3.2 IMD Cold Wave Criteria & Distinctions

#### Official IMD Standard
- **Source**: IMD Criteria for Cold Wave & Severe Cold Wave.
- **Official Definition**:
  - Baseline requirement: Minimum temperature must be $\le 10.0\text{ }^\circ\text{C}$ for Plains and $\le 0.0\text{ }^\circ\text{C}$ for Hilly stations.
  - **Departure from Normal**:
    - *Cold Wave*: Departure from normal is $-4.5\text{ }^\circ\text{C}$ to $-6.4\text{ }^\circ\text{C}$.
    - *Severe Cold Wave*: Departure from normal is $\le -6.5\text{ }^\circ\text{C}$.
  - **Actual Minimum Temperature (for Plains)**:
    - *Cold Wave*: Minimum temperature $\le 4.0\text{ }^\circ\text{C}$ (or core baseline $\le 5.0\text{ }^\circ\text{C}$).
    - *Severe Cold Wave*: Minimum temperature $\le 2.0\text{ }^\circ\text{C}$.

#### Distinction & Code Limitation
> [!NOTE]
> The engine implements absolute cold thresholds ($\le 5.0\text{ }^\circ\text{C}$ for moderate cold, $\le 2.0\text{ }^\circ\text{C}$ for severe cold wave).
> As with heatwave criteria, station climatology departures are not evaluated at runtime.

---

## 4. WMO / Beaufort Scale Wind Standards

### 4.1 Authoritative Source
- **Authority**: World Meteorological Organization (WMO).
- **Publication**: *WMO-No. 8: Guide to Meteorological Instruments and Methods of Observation*; *WMO-No. 558: Manual on Marine Meteorological Services*.
- **Standard**: 10-meter standard surface wind speed over open, level terrain.

### 4.2 Beaufort Wind Scale Breakdown

| Beaufort Force | Descriptor | Wind Speed (km/h) | Wind Speed (m/s) | Engine Classification |
|---|---|---|---|---|
| **0** | Calm | < 1.0 | < 0.3 | `calm` |
| **1** | Light Air | 1.0 – 5.9 | 0.3 – 1.5 | `light_air` |
| **2** | Light Breeze | 6.0 – 11.9 | 1.6 – 3.3 | `light_breeze` |
| **3** | Gentle Breeze | 12.0 – 19.9 | 3.4 – 5.4 | `gentle_breeze` |
| **4** | Moderate Breeze | 20.0 – 28.9 | 5.5 – 7.9 | `moderate_breeze` |
| **5** | Fresh Breeze | 29.0 – 38.9 | 8.0 – 10.7 | `fresh_breeze` |
| **6** | Strong Breeze | 39.0 – 49.9 | 10.8 – 13.8 | `strong_breeze` |
| **7** | Near Gale / High Wind | 50.0 – 61.9 | 13.9 – 17.1 | `near_gale` / `high_wind` |
| **8** | Gale | 62.0 – 74.9 | 17.2 – 20.7 | `gale` / `gale_wind` |
| **9** | Strong Gale | 75.0 – 88.9 | 20.8 – 24.4 | `strong_gale` / `gale_wind` |
| **10** | Storm | 89.0 – 102.9 | 24.5 – 28.4 | `storm` / `storm_wind` |
| **11** | Violent Storm | 103.0 – 117.9 | 28.5 – 32.6 | `violent_storm` / `storm_wind` |
| **12** | Hurricane Force | ≥ 118.0 | ≥ 32.7 | `hurricane` / `storm_wind` |

---

## 5. Aviation Visibility Standards (ICAO Annex 3)

### 5.1 Authoritative Source
- **Authority**: International Civil Aviation Organization (ICAO) in coordination with WMO.
- **Publication**: *ICAO Annex 3: Meteorological Service for International Air Navigation* (20th Edition).
- **Definitions**:
  - **Dense Fog**: Horizontal visibility $\le 0.2\text{ km}$ ($200\text{ m}$).
  - **Fog**: Horizontal visibility $\le 1.0\text{ km}$ ($1000\text{ m}$) with relative humidity near saturation.
  - **Mist**: Horizontal visibility $1.0\text{ km}$ to $5.0\text{ km}$ with relative humidity $\ge 80\%$.
  - **Clear**: Horizontal visibility $> 10.0\text{ km}$.

---

## 6. Apparent Temperature Formulas

### 6.1 Steadman / Rothfusz Heat Index Formula
- **Authority**: US National Oceanic and Atmospheric Administration (NOAA) / National Weather Service (NWS).
- **Publication**: NWS Technical Attachment SR 90-23 (Rothfusz, 1990).
- **Applicability**: Valid for ambient temperatures $T \ge 27\text{ }^\circ\text{C}$ and relative humidity $RH \ge 40\%$.

$$\begin{aligned}
HI = & -42.379 + 2.04901523\,T + 10.14333127\,RH - 0.22475541\,T\,RH \\
     & - 0.00683783\,T^2 - 0.05481717\,RH^2 + 0.00122874\,T^2\,RH \\
     & + 0.00085282\,T\,RH^2 - 0.00000199\,T^2\,RH^2
\end{aligned}$$

### 6.2 JAG/TI Wind Chill Formula
- **Authority**: Joint Action Group on Temperature Indices (NOAA NWS / Environment Canada).
- **Applicability**: Valid for $T \le 10\text{ }^\circ\text{C}$ and wind speeds $V \ge 4.8\text{ km/h}$.

$$WC = 13.12 + 0.6215\,T - 11.37\,V^{0.16} + 0.3965\,T\,V^{0.16}$$

---

## 7. Heuristic Engineering Proxies & Non-Official Models

The following calculations are explicitly designated as **engineering heuristic proxies** developed for deterministic application scoring, **not** certified physical models:

1. **Flood Proxy Score**:
   - $60\%$ rainfall sub-score
   - $25\%$ detected condition flag
   - $15\%$ auxiliary signals (pressure $< 1000\text{ hPa}$, humidity $\ge 85\%$)
   - *Limitation*: This is an atmospheric moisture proxy. It does **not** model hydrological drainage, river basin run-off, soil saturation, or topography.
2. **Multi-Hazard Risk Escalation**:
   - Base overall score is $\max(\text{hazard scores})$.
   - If two or more hazards are in the `HIGH` band ($\ge 50$), an escalation of $+10$ points is added (capped at 100).
3. **Thunderstorm Potential Proxy**:
   - CAPE $\ge 1000\text{ J/kg}$ indicates moderate convective instability.
   - CAPE $\ge 2000\text{ J/kg}$ or active lightning flags high/extreme convective potential.

---

## 8. Safety & Regulatory Notices

All intelligence outputs produced by Module 1.2 enforce:
1. `is_official_warning = False` on all automated detected events.
2. `classification = "HEURISTIC_RISK"` on all risk assessments.
3. Explicit legal disclaimer:
   > *"Automated heuristic meteorological risk assessment. This is not an official disaster warning issued by government meteorological agencies (such as IMD)."*
