"""
schemas/intelligence.py
-----------------------
Canonical schemas for the Weather Intelligence & Data Fusion Layer (Module 1.2).

Defines the contract for downstream consumers (AI/RAG, Advisory, Group 2 backend):
  - Current weather analysis & comfort metrics
  - Forecast intelligence (rain onset, duration, peak periods, swings)
  - Weather trend reports
  - Extreme weather & hazard events
  - Comprehensive multi-hazard risk assessment
  - Multi-provider data fusion & conflict manifests
  - Data quality & explainable confidence reports
  - Top-level WeatherIntelligenceResponse
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from app.schemas.unified_weather import (
    CurrentWeather,
    ForecastWeather,
    ProviderInfo,
)


# --------------------------------------------------------------------------- #
# 1. Current Weather Analysis & Comfort Metrics                                #
# --------------------------------------------------------------------------- #

ThermalComfortLevel = Literal[
    "freezing",
    "cold",
    "comfortable",
    "caution",
    "extreme_caution",
    "danger",
    "extreme_danger",
]

HumidityComfortLevel = Literal[
    "dry",
    "comfortable",
    "humid",
    "oppressive",
]

BeaufortCategory = Literal[
    "calm",
    "light_air",
    "light_breeze",
    "gentle_breeze",
    "moderate_breeze",
    "fresh_breeze",
    "strong_breeze",
    "near_gale",
    "gale",
    "strong_gale",
    "storm",
    "violent_storm",
    "hurricane",
]

PrecipitationCategory = Literal[
    "none",
    "slight_rain",
    "moderate_rain",
    "heavy_rain",
    "violent_rain",
]

VisibilityCondition = Literal[
    "dense_fog",
    "fog",
    "mist",
    "haze",
    "clear",
]

BarometricState = Literal[
    "deep_low",
    "low_trough",
    "normal",
    "high_pressure",
]


class CurrentAnalysis(BaseModel):
    """
    Structured deterministic interpretation of current weather observations.
    Calculated purely via meteorological algorithms — no LLM speculation.
    """

    apparent_temperature: Optional[float] = Field(
        default=None,
        description="Calculated or observed apparent temperature in °C.",
    )
    thermal_comfort: ThermalComfortLevel = Field(
        ...,
        description="Thermal comfort classification based on temperature and humidity/wind.",
    )
    humidity_comfort: HumidityComfortLevel = Field(
        ...,
        description="Comfort category based on relative humidity and dew point.",
    )
    wind_beaufort_scale: int = Field(
        ...,
        ge=0,
        le=12,
        description="Beaufort wind scale rating (0 to 12).",
    )
    wind_classification: BeaufortCategory = Field(
        ...,
        description="Beaufort scale category descriptor.",
    )
    precipitation_category: PrecipitationCategory = Field(
        ...,
        description="Precipitation rate classification.",
    )
    precipitation_probability_rating: Optional[str] = Field(
        default=None,
        description="Descriptive rating for rain probability (e.g. unlikely, likely).",
    )
    visibility_condition: VisibilityCondition = Field(
        ...,
        description="Horizontal visibility categorization.",
    )
    barometric_state: BarometricState = Field(
        ...,
        description="Atmospheric pressure level and stability indicator.",
    )
    dew_point_depression: Optional[float] = Field(
        default=None,
        description="Difference between temperature and dew point in °C (low indicates near-saturation).",
    )
    summary: str = Field(
        ...,
        description="Deterministic, human-readable meteorological summary of conditions.",
    )


# --------------------------------------------------------------------------- #
# 2. Weather Trends                                                            #
# --------------------------------------------------------------------------- #

TrendState = Literal["increasing", "decreasing", "stable", "rapidly_changing"]


class MetricTrend(BaseModel):
    """Trend assessment for an individual meteorological variable."""

    metric: str = Field(..., description="Variable name (e.g. temperature, rainfall).")
    state: TrendState = Field(..., description="Direction / dynamic of the trend.")
    rate_per_hour: Optional[float] = Field(
        default=None,
        description="Average rate of change per hour in native units.",
    )
    description: str = Field(
        ...,
        description="Human-readable explanation of the trend.",
    )


class WeatherTrends(BaseModel):
    """Set of computed weather trends across all available parameters."""

    temperature: Optional[MetricTrend] = None
    rainfall: Optional[MetricTrend] = None
    wind: Optional[MetricTrend] = None
    humidity: Optional[MetricTrend] = None
    pressure: Optional[MetricTrend] = None


# --------------------------------------------------------------------------- #
# 3. Forecast Intelligence                                                     #
# --------------------------------------------------------------------------- #

class PeakRainPeriod(BaseModel):
    """Time window and intensity of the heaviest rainfall during the forecast."""

    start: datetime = Field(..., description="UTC start timestamp of the peak period.")
    end: datetime = Field(..., description="UTC end timestamp of the peak period.")
    peak_rate_mm_h: float = Field(..., ge=0, description="Highest hourly rainfall rate in mm.")
    accumulated_mm: float = Field(..., ge=0, description="Total rain expected in this window in mm.")


class RapidWeatherChange(BaseModel):
    """Detected abrupt atmospheric change (e.g. sudden drop in temperature or pressure)."""

    metric: str = Field(..., description="Metric that changed rapidly.")
    start_time: datetime = Field(..., description="UTC start timestamp.")
    end_time: datetime = Field(..., description="UTC end timestamp.")
    magnitude: float = Field(..., description="Magnitude of the change in native units.")
    description: str = Field(..., description="Human-readable explanation.")


class TemperatureDynamics(BaseModel):
    """Temperature range and variation across the forecast."""

    min_temp: float = Field(..., description="Minimum forecast temperature in °C.")
    max_temp: float = Field(..., description="Maximum forecast temperature in °C.")
    diurnal_swing: float = Field(..., ge=0, description="Difference between max and min in °C.")
    trend: TrendState = Field(..., description="General trajectory over the forecast.")


class ForecastIntelligence(BaseModel):
    """
    Temporal analysis of multi-day and hourly forecast time-series.
    """

    horizon_hours: int = Field(..., ge=1, description="Number of forecast hours analyzed.")
    rain_expected: bool = Field(..., description="True if measurable rain is expected.")
    rain_onset: Optional[datetime] = Field(
        default=None,
        description="UTC timestamp of the earliest predicted precipitation.",
    )
    rain_onset_hours_from_now: Optional[float] = Field(
        default=None,
        description="Hours from observation until expected rain onset.",
    )
    total_rain_duration_hours: float = Field(
        default=0.0,
        ge=0,
        description="Total hours where rain > 0.1 mm is predicted.",
    )
    total_precipitation_expected_mm: float = Field(
        default=0.0,
        ge=0,
        description="Total accumulated precipitation across the horizon.",
    )
    peak_rain_period: Optional[PeakRainPeriod] = Field(
        default=None,
        description="Heaviest rainfall window.",
    )
    heavy_rain_intervals_count: int = Field(
        default=0,
        description="Number of hourly intervals exceeding the heavy rain threshold.",
    )
    temperature_dynamics: Optional[TemperatureDynamics] = Field(
        default=None,
        description="Forecast temperature bounds and swings.",
    )
    wind_trend: Optional[MetricTrend] = Field(
        default=None,
        description="Trajectory of wind speeds across the forecast.",
    )
    rapid_changes: List[RapidWeatherChange] = Field(
        default_factory=list,
        description="List of detected rapid weather transitions.",
    )
    forecast_consistency: str = Field(
        default="stable",
        description="Consistency rating across consecutive forecast periods.",
    )


# --------------------------------------------------------------------------- #
# 4. Extreme Weather Detection                                                 #
# --------------------------------------------------------------------------- #

ExtremeEventType = Literal[
    "heavy_rain",
    "very_heavy_rain",
    "extremely_heavy_rain",
    "extreme_heat",
    "extreme_cold",
    "high_wind",
    "gale_wind",
    "storm_wind",
    "thunderstorm",
    "rapid_temperature_change",
    "low_visibility",
    "insufficient_rainfall_data",
]

SeverityLevel = Literal["low", "moderate", "high", "extreme"]


class DetectedExtremeEvent(BaseModel):
    """
    Extensible rule-based weather hazard detection.
    Explicitly tags the authority source (IMD standard vs heuristic).
    """

    event_type: ExtremeEventType = Field(..., description="Type of severe event.")
    severity: SeverityLevel = Field(..., description="Severity rating.")
    value: float = Field(..., description="Observed or forecast triggering value.")
    unit: str = Field(..., description="Unit of the triggering value.")
    threshold: float = Field(..., description="Threshold that was breached.")
    classification_source: str = Field(
        ...,
        description="Source of the threshold (e.g. 'IMD_STANDARD', 'HEURISTIC_RULE').",
    )
    is_official_warning: bool = Field(
        default=False,
        description="Always False for heuristic automated detections. Official warnings require government IMD bulletins.",
    )
    notice: str = Field(
        default="HEURISTIC METEOROLOGICAL DETECTION ONLY — NOT AN OFFICIAL GOVERNMENT WARNING",
        description="Clear regulatory and legal notice.",
    )
    description: str = Field(
        ...,
        description="Human-readable description of the event.",
    )


# --------------------------------------------------------------------------- #
# 5. Risk Assessment Layer                                                     #
# --------------------------------------------------------------------------- #

RiskLevel = Literal["LOW", "MODERATE", "HIGH", "SEVERE"]
HazardType = Literal["rain", "heat", "wind", "storm", "flood", "visibility", "overall"]


class HazardRisk(BaseModel):
    """Individual hazard risk assessment."""

    hazard: HazardType = Field(..., description="Hazard category.")
    score: int = Field(..., ge=0, le=100, description="Risk score 0 to 100.")
    level: RiskLevel = Field(..., description="Categorical risk level.")
    classification: Literal["HEURISTIC_RISK", "OFFICIAL_WARNING"] = Field(
        default="HEURISTIC_RISK",
        description="Clear distinction between heuristic calculation and official warning.",
    )
    contributing_factors: List[str] = Field(
        default_factory=list,
        description="Meteorological observations that contributed to the score.",
    )
    evidence: List[str] = Field(
        default_factory=list,
        description="Concrete mathematical and threshold evidence for the score.",
    )
    confidence: int = Field(
        ...,
        ge=0,
        le=100,
        description="Confidence in this specific risk score.",
    )


class RiskAssessment(BaseModel):
    """
    Structured multi-hazard risk assessment.
    """

    risks: List[HazardRisk] = Field(
        ...,
        description="List of evaluated hazard risks.",
    )
    overall_score: int = Field(..., ge=0, le=100, description="Composite risk score 0–100.")
    overall_level: RiskLevel = Field(..., description="Composite risk level.")
    classification: Literal["HEURISTIC_RISK", "OFFICIAL_WARNING"] = Field(
        default="HEURISTIC_RISK",
        description="Distinguishes heuristic assessment from official warnings.",
    )
    disclaimer: str = Field(
        default="Automated heuristic meteorological risk assessment. This is not an official disaster warning issued by government meteorological agencies.",
        description="Legal and informational disclaimer.",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        description="Assessment generation timestamp (UTC).",
    )


# --------------------------------------------------------------------------- #
# 6. Data Quality & Confidence Engine                                          #
# --------------------------------------------------------------------------- #

class ConflictingField(BaseModel):
    """Record of a disagreement across multiple weather providers."""

    field_name: str = Field(..., description="Meteorological field with conflicting values.")
    provider_values: Dict[str, Any] = Field(
        ...,
        description="Mapping of provider name to reported value.",
    )
    discrepancy: float = Field(
        ...,
        description="Absolute difference or variance among reported values.",
    )
    resolution: str = Field(
        ...,
        description="How the conflict was resolved (e.g. 'weighted_average', 'priority_selection').",
    )


class DataQualityReport(BaseModel):
    """
    Data quality assessment transparently tracking completeness, freshness,
    and cross-provider conflict.
    """

    quality_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall quality score between 0.0 (unusable) and 1.0 (perfect).",
    )
    completeness_score: int = Field(
        ...,
        ge=0,
        le=40,
        description="Field completeness score out of 40.",
    )
    freshness_score: int = Field(
        ...,
        ge=0,
        le=30,
        description="Observation freshness score out of 30.",
    )
    age_seconds: float = Field(
        ...,
        ge=0,
        description="Observation age in seconds relative to generation time.",
    )
    available_fields_count: int = Field(..., ge=0)
    missing_fields: List[str] = Field(
        default_factory=list,
        description="Fields not supplied by the provider(s).",
    )
    conflicting_fields: List[ConflictingField] = Field(
        default_factory=list,
        description="Fields where providers disagreed noticeably.",
    )
    providers: List[ProviderInfo] = Field(
        default_factory=list,
        description="Providers contributing to this quality evaluation.",
    )


class ConfidenceBreakdown(BaseModel):
    """Component factors explaining the confidence score."""

    completeness_points: int = Field(..., ge=0, le=40)
    freshness_points: int = Field(..., ge=0, le=30)
    provider_agreement_points: int = Field(..., ge=0, le=20)
    horizon_penalty: int = Field(..., ge=0, le=20)
    critical_missing_penalty: int = Field(..., ge=0, le=30)


class ConfidenceAssessment(BaseModel):
    """
    Explainable confidence assessment based on verifiable factors.
    """

    confidence_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Total confidence score (0 to 100).",
    )
    breakdown: ConfidenceBreakdown = Field(
        ...,
        description="Deterministic point breakdown.",
    )
    uncertainties: List[str] = Field(
        default_factory=list,
        description="Explanations of any data gaps or penalties applied.",
    )


# --------------------------------------------------------------------------- #
# 7. Multi-Provider Data Fusion                                                #
# --------------------------------------------------------------------------- #

class FusionSummary(BaseModel):
    """Metadata regarding how data from multiple providers was fused."""

    strategy: str = Field(
        ...,
        description="Fusion strategy used (e.g. 'priority_fallback', 'weighted_consensus').",
    )
    providers_evaluated: List[str] = Field(
        default_factory=list,
        description="Identifiers of all evaluated providers.",
    )
    primary_provider: str = Field(
        ...,
        description="Main provider used for baseline values.",
    )
    fields_imputed: List[str] = Field(
        default_factory=list,
        description="Fields that were missing in primary but supplied by secondary providers.",
    )
    conflicts_detected: int = Field(
        default=0,
        description="Total number of conflicting fields detected.",
    )


# --------------------------------------------------------------------------- #
# 8. Canonical Weather Intelligence Response Contract                         #
# --------------------------------------------------------------------------- #

class WeatherIntelligenceResponse(BaseModel):
    """
    Canonical contract returned by the Weather Intelligence & Data Fusion Engine.
    Consumable by downstream AI/RAG layers, Advisory services, and client applications.
    """

    location: str = Field(..., description="Place name.")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    timestamp: datetime = Field(..., description="Observation timestamp (UTC).")
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        description="Intelligence generation timestamp (UTC).",
    )

    # Core Intelligence Modules
    current_analysis: CurrentAnalysis = Field(
        ...,
        description="Deterministic meteorological interpretation of current conditions.",
    )
    forecast_intelligence: Optional[ForecastIntelligence] = Field(
        default=None,
        description="Temporal analysis of rain onset, duration, peaks, and swings.",
    )
    trends: WeatherTrends = Field(
        ...,
        description="Trends for temperature, rainfall, wind, humidity, and pressure.",
    )
    extreme_events: List[DetectedExtremeEvent] = Field(
        default_factory=list,
        description="Detected severe weather hazards with authoritative/heuristic source attribution.",
    )
    risk_assessment: RiskAssessment = Field(
        ...,
        description="Multi-hazard risk evaluation with explicit HEURISTIC_RISK classification.",
    )
    data_quality: DataQualityReport = Field(
        ...,
        description="Completeness, freshness, and conflict reporting.",
    )
    confidence: ConfidenceAssessment = Field(
        ...,
        description="Explainable confidence score and uncertainty breakdown.",
    )
    fusion_summary: Optional[FusionSummary] = Field(
        default=None,
        description="Details of multi-provider fusion if multiple providers contributed.",
    )
    providers_used: List[ProviderInfo] = Field(
        default_factory=list,
        description="All providers that contributed data to this intelligence result.",
    )


class WeatherIntelligenceRequest(BaseModel):
    """
    Direct input payload to run intelligence on caller-supplied observations.
    """

    current: CurrentWeather = Field(..., description="Current weather observation.")
    forecast: Optional[ForecastWeather] = Field(
        default=None,
        description="Optional forecast data.",
    )
