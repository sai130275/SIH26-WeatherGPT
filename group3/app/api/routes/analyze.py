"""
api/routes/analyze.py
----------------------
POST /analyze — Weather condition analysis endpoint.

Flow:
  1. Receive a WeatherData payload (validated by Pydantic on entry).
  2. Pass it through WeatherProcessor to produce a ProcessedWeather snapshot.
  3. Run all condition detectors via ConditionDetector.detect_all().
  4. Return a WeatherAnalysis response with detected conditions + metadata.

No external API calls, no database, no LLM — pure computation.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from app.schemas.analysis import WeatherAnalysis
from app.schemas.weather import WeatherData
from app.services.condition_detector import ConditionDetector
from app.services.weather_processor import WeatherProcessor

router = APIRouter(tags=["Analysis"])

# Reuse single instances — both services are stateless.
_processor = WeatherProcessor()
_detector = ConditionDetector()


@router.post(
    "/analyze",
    response_model=WeatherAnalysis,
    summary="Analyse weather data for hazard conditions",
    description=(
        "Accepts a WeatherData payload and returns a WeatherAnalysis containing "
        "all detected weather conditions (heavy rain, high wind, extreme heat, "
        "low visibility) with severity ratings and human-readable reasons. "
        "Fields absent from the input are noted in `missing_fields`; their "
        "detectors are skipped rather than run on invented values."
    ),
)
async def analyze_weather(data: WeatherData) -> WeatherAnalysis:
    """
    Run the full condition-detection pipeline on a weather observation.

    Parameters
    ----------
    data:
        A WeatherData payload from Group 2 (Node.js backend) or any caller.

    Returns
    -------
    WeatherAnalysis:
        Detected conditions, severity levels, and field availability metadata.
    """
    processed = _processor.process(data)
    conditions = _detector.detect_all(processed)

    return WeatherAnalysis(
        location=processed.location,
        latitude=processed.latitude,
        longitude=processed.longitude,
        timestamp=processed.timestamp,
        processed_at=datetime.now(tz=timezone.utc),
        conditions=conditions,
        available_fields=list(processed.available_fields),
        missing_fields=list(processed.missing_fields),
    )
