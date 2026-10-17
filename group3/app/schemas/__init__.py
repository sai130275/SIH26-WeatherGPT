"""
schemas/__init__.py
-------------------
Export canonical schemas for the Weather + AI Intelligence Engine.
"""

from app.schemas.unified_weather import (
    CurrentWeather,
    DailyForecast,
    ForecastPoint,
    ForecastWeather,
    HistoricalWeather,
    ProviderInfo,
    WeatherResponse,
)
from app.schemas.intelligence import (
    CurrentAnalysis,
    ForecastIntelligence,
    MetricTrend,
    WeatherTrends,
    DetectedExtremeEvent,
    HazardRisk,
    RiskAssessment,
    DataQualityReport,
    ConfidenceAssessment,
    WeatherIntelligenceResponse,
    WeatherIntelligenceRequest,
)

__all__ = [
    "ProviderInfo",
    "CurrentWeather",
    "ForecastPoint",
    "DailyForecast",
    "ForecastWeather",
    "HistoricalWeather",
    "WeatherResponse",
    "CurrentAnalysis",
    "ForecastIntelligence",
    "MetricTrend",
    "WeatherTrends",
    "DetectedExtremeEvent",
    "HazardRisk",
    "RiskAssessment",
    "DataQualityReport",
    "ConfidenceAssessment",
    "WeatherIntelligenceResponse",
    "WeatherIntelligenceRequest",
]
