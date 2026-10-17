"""
api/routes/weather.py
---------------------
API endpoints for fetching normalized weather data via the Weather Provider
Aggregation Layer.

Endpoints:
  GET /weather/current     — Current observations + telemetry in unified schema
  GET /weather/forecast    — Multi-day hourly and daily forecast
  GET /weather/historical  — Historical weather archive
  GET /weather/providers   — Health and capability status of registered providers
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.providers.base import (
    ProviderRateLimitError,
    ProviderUnavailableError,
)
from app.schemas.intelligence import (
    WeatherIntelligenceRequest,
    WeatherIntelligenceResponse,
)
from app.schemas.unified_weather import (
    CurrentWeather,
    ForecastWeather,
    HistoricalWeather,
    WeatherResponse,
)
from app.services.weather_aggregator import WeatherAggregator, default_aggregator
from app.services.weather_intelligence import (
    WeatherIntelligenceService,
    default_intelligence_service,
)

router = APIRouter(prefix="/weather", tags=["Weather"])


@router.get(
    "/current",
    response_model=WeatherResponse,
    summary="Get current weather",
    description=(
        "Retrieves current meteorological observation for coordinates in "
        "canonical unified schema with full source attribution."
    ),
)
async def get_current_weather(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees"),
    location: Optional[str] = Query(None, description="Human-readable location label"),
    force_refresh: bool = Query(False, description="Bypass cache and force new provider fetch"),
) -> WeatherResponse:
    try:
        current: CurrentWeather = await default_aggregator.get_current(
            lat=lat,
            lon=lon,
            location_name=location,
            force_refresh=force_refresh,
        )
        return WeatherResponse(
            current=current,
            providers_used=[current.provider],
        )
    except ProviderRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        ) from exc
    except ProviderUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch current weather: {exc}",
        ) from exc


@router.get(
    "/forecast",
    response_model=WeatherResponse,
    summary="Get weather forecast",
    description=(
        "Retrieves multi-day hourly and daily forecast in canonical schema."
    ),
)
async def get_forecast_weather(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees"),
    days: int = Query(7, ge=1, le=16, description="Forecast horizon in days (1 to 16)"),
    location: Optional[str] = Query(None, description="Human-readable location label"),
    force_refresh: bool = Query(False, description="Bypass cache and force new fetch"),
) -> WeatherResponse:
    try:
        forecast: ForecastWeather = await default_aggregator.get_forecast(
            lat=lat,
            lon=lon,
            days=days,
            location_name=location,
            force_refresh=force_refresh,
        )
        return WeatherResponse(
            forecast=forecast,
            providers_used=[forecast.provider],
        )
    except ProviderRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        ) from exc
    except ProviderUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch weather forecast: {exc}",
        ) from exc


@router.get(
    "/historical",
    response_model=WeatherResponse,
    summary="Get historical weather data",
    description=(
        "Retrieves historical weather time series in canonical schema (YYYY-MM-DD)."
    ),
)
async def get_historical_weather(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees"),
    start_date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="End date (YYYY-MM-DD)"),
    location: Optional[str] = Query(None, description="Human-readable location label"),
    force_refresh: bool = Query(False, description="Bypass cache and force new fetch"),
) -> WeatherResponse:
    try:
        historical: HistoricalWeather = await default_aggregator.get_historical(
            lat=lat,
            lon=lon,
            start_date=start_date,
            end_date=end_date,
            location_name=location,
            force_refresh=force_refresh,
        )
        return WeatherResponse(
            historical=historical,
            providers_used=[historical.provider],
        )
    except ProviderRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        ) from exc
    except ProviderUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch historical weather: {exc}",
        ) from exc


@router.get(
    "/providers",
    response_model=List[Dict[str, Any]],
    summary="List provider health and capabilities",
    description="Lists all registered weather data providers, their supported features, and health status.",
)
async def get_provider_status() -> List[Dict[str, Any]]:
    return await default_aggregator.get_provider_status()


@router.get(
    "/intelligence",
    response_model=WeatherIntelligenceResponse,
    summary="Get complete weather intelligence",
    description=(
        "Retrieves multi-provider weather observations and forecast, runs deterministic meteorological analysis, "
        "trends, extreme weather detection, risk assessment, data quality evaluation, and explainable confidence scoring."
    ),
)
async def get_weather_intelligence(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees"),
    days: int = Query(7, ge=1, le=16, description="Forecast horizon in days"),
    location: Optional[str] = Query(None, description="Location name label"),
    force_refresh: bool = Query(False, description="Bypass cache and force new provider fetch"),
) -> WeatherIntelligenceResponse:
    try:
        # Fetch current observations from available providers
        try:
            current_list = await default_aggregator.get_all_current(
                lat=lat, lon=lon, location_name=location
            )
        except Exception:
            # Fall back to single get_current
            single_current = await default_aggregator.get_current(
                lat=lat, lon=lon, location_name=location, force_refresh=force_refresh
            )
            current_list = [single_current]

        # Fetch forecast
        forecast: Optional[ForecastWeather] = None
        try:
            forecast = await default_aggregator.get_forecast(
                lat=lat, lon=lon, days=days, location_name=location, force_refresh=force_refresh
            )
        except Exception as exc:
            # Forecast is optional for current intelligence
            pass

        return default_intelligence_service.generate_intelligence(
            current_observations=current_list,
            forecast=forecast,
            forecast_days=days,
        )
    except ProviderRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        ) from exc
    except ProviderUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate weather intelligence: {exc}",
        ) from exc


@router.post(
    "/intelligence/analyze",
    response_model=WeatherIntelligenceResponse,
    summary="Analyze caller-supplied weather observations",
    description=(
        "Runs deterministic meteorological analysis, trends, hazard detection, and risk scoring "
        "on caller-supplied CurrentWeather and optional ForecastWeather data."
    ),
)
async def analyze_weather_intelligence(
    request: WeatherIntelligenceRequest,
) -> WeatherIntelligenceResponse:
    try:
        return default_intelligence_service.generate_intelligence(
            current_observations=request.current,
            forecast=request.forecast,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze weather intelligence: {exc}",
        ) from exc
