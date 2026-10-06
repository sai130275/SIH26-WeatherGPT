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
from app.schemas.unified_weather import (
    CurrentWeather,
    ForecastWeather,
    HistoricalWeather,
    WeatherResponse,
)
from app.services.weather_aggregator import WeatherAggregator, default_aggregator

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
