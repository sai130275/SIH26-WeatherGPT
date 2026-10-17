"""
services/weather_intelligence.py
--------------------------------
Master orchestrator service for the Weather Intelligence Layer (Module 1.2).

Coordinates:
  - Multi-provider data fusion & conflict detection
  - Current meteorological analysis & comfort indices
  - Weather trend calculation
  - Forecast temporal intelligence (onset, duration, peaks, swings)
  - Extensible extreme weather & hazard detection
  - Comprehensive risk assessment with heuristic disclaimers
  - Data quality evaluation & conflict manifest
  - Explainable confidence calculation

Produces the canonical WeatherIntelligenceResponse for downstream AI/RAG consumers.
"""

from __future__ import annotations

from typing import List, Optional

from app.schemas.intelligence import (
    ConflictingField,
    FusionSummary,
    WeatherIntelligenceResponse,
)
from app.schemas.unified_weather import CurrentWeather, ForecastWeather, ProviderInfo
from app.services.confidence_engine import ExplainableConfidenceEngine
from app.services.data_fusion import DataFusionEngine
from app.services.data_quality import DataQualityEngine
from app.services.extreme_weather import ExtremeWeatherDetector
from app.services.forecast_intelligence import ForecastIntelligenceEngine
from app.services.risk_assessment import ComprehensiveRiskEngine
from app.services.weather_analysis import WeatherAnalysisEngine
from app.services.weather_trend import WeatherTrendEngine


class WeatherIntelligenceService:
    """
    Central service that coordinates all intelligence engines.
    """

    def __init__(
        self,
        analysis_engine: Optional[WeatherAnalysisEngine] = None,
        forecast_engine: Optional[ForecastIntelligenceEngine] = None,
        trend_engine: Optional[WeatherTrendEngine] = None,
        extreme_detector: Optional[ExtremeWeatherDetector] = None,
        risk_engine: Optional[ComprehensiveRiskEngine] = None,
        quality_engine: Optional[DataQualityEngine] = None,
        confidence_engine: Optional[ExplainableConfidenceEngine] = None,
        fusion_engine: Optional[DataFusionEngine] = None,
    ) -> None:
        self.trend_engine = trend_engine or WeatherTrendEngine()
        self.analysis_engine = analysis_engine or WeatherAnalysisEngine()
        self.forecast_engine = forecast_engine or ForecastIntelligenceEngine(trend_engine=self.trend_engine)
        self.extreme_detector = extreme_detector or ExtremeWeatherDetector()
        self.risk_engine = risk_engine or ComprehensiveRiskEngine()
        self.quality_engine = quality_engine or DataQualityEngine()
        self.confidence_engine = confidence_engine or ExplainableConfidenceEngine()
        self.fusion_engine = fusion_engine or DataFusionEngine()

    def generate_intelligence(
        self,
        current_observations: List[CurrentWeather] | CurrentWeather,
        forecast: Optional[ForecastWeather] = None,
        forecast_days: int = 1,
    ) -> WeatherIntelligenceResponse:
        """
        Generate comprehensive weather intelligence from observations and optional forecast.
        """
        # 1. Normalize observations list
        if isinstance(current_observations, CurrentWeather):
            observations = [current_observations]
        else:
            observations = current_observations

        if not observations:
            raise ValueError("At least one CurrentWeather observation is required.")

        # 2. Multi-provider Data Fusion
        conflicts: List[ConflictingField] = []
        fusion_summary: Optional[FusionSummary] = None
        if len(observations) > 1:
            fused_weather, conflicts, fusion_summary = self.fusion_engine.fuse_current(observations)
        else:
            fused_weather = observations[0]

        # 3. Forecast Intelligence
        forecast_intel = None
        trends = None
        rain_prob = None

        if forecast and forecast.hourly:
            forecast_intel = self.forecast_engine.analyze(forecast)
            trends = self.trend_engine.analyze_trends_from_forecast(forecast.hourly)
            # Find rain probability for the current hour if present
            if forecast.hourly[0].precipitation_probability is not None:
                rain_prob = forecast.hourly[0].precipitation_probability

        if trends is None:
            # Empty / single-point trends
            trends = self.trend_engine.analyze_trends_from_forecast([], max_hours=1)

        # 4. Current Meteorological Analysis
        current_analysis = self.analysis_engine.analyze(fused_weather, rain_probability=rain_prob)

        # 5. Extreme Weather Event Detection
        extreme_events = self.extreme_detector.detect_all(fused_weather, forecast=forecast)

        # 6. Risk Assessment
        risk_assessment = self.risk_engine.assess(fused_weather)

        # 7. Data Quality Engine
        quality_report = self.quality_engine.evaluate(
            weather=fused_weather,
            conflicting_fields=conflicts,
        )

        # 8. Explainable Confidence Engine
        confidence_report = self.confidence_engine.compute(
            quality=quality_report,
            weather=fused_weather,
            forecast=forecast,
            forecast_days=forecast_days,
        )

        # 9. Attribution
        all_providers: List[ProviderInfo] = [obs.provider for obs in observations]

        return WeatherIntelligenceResponse(
            location=fused_weather.location,
            latitude=fused_weather.latitude,
            longitude=fused_weather.longitude,
            timestamp=fused_weather.timestamp,
            current_analysis=current_analysis,
            forecast_intelligence=forecast_intel,
            trends=trends,
            extreme_events=extreme_events,
            risk_assessment=risk_assessment,
            data_quality=quality_report,
            confidence=confidence_report,
            fusion_summary=fusion_summary,
            providers_used=all_providers,
        )


# Shared default singleton
default_intelligence_service = WeatherIntelligenceService()
