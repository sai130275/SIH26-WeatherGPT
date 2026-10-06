"""
services/weather_aggregator.py
------------------------------
Weather aggregator orchestrator.

Coordinates weather data retrieval across multiple providers with:
- Priority-based provider fallback
- Time-to-Live (TTL) based in-memory caching
- Multi-provider status reporting
"""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings
from app.providers.base import (
    ProviderUnavailableError,
    WeatherProvider,
    WeatherProviderError,
)
from app.providers.registry import ProviderRegistry, default_registry
from app.schemas.unified_weather import (
    CurrentWeather,
    ForecastWeather,
    HistoricalWeather,
)

logger = logging.getLogger(__name__)


class WeatherAggregator:
    """
    Orchestrates fetching weather data with caching and fallback.
    """

    def __init__(
        self,
        registry: Optional[ProviderRegistry] = None,
        cache_ttl_current: Optional[int] = None,
        cache_ttl_forecast: Optional[int] = None,
        cache_ttl_historical: Optional[int] = None,
    ) -> None:
        self.registry = registry or default_registry
        self.ttl_current = cache_ttl_current if cache_ttl_current is not None else settings.WEATHER_CACHE_TTL_CURRENT
        self.ttl_forecast = cache_ttl_forecast if cache_ttl_forecast is not None else settings.WEATHER_CACHE_TTL_FORECAST
        self.ttl_historical = cache_ttl_historical if cache_ttl_historical is not None else settings.WEATHER_CACHE_TTL_HISTORICAL

        # In-memory cache: key -> (timestamp_epoch, cached_object)
        self._cache: Dict[str, Tuple[float, Any]] = {}

    def _get_from_cache(self, key: str, ttl: int) -> Optional[Any]:
        if key in self._cache:
            stored_at, data = self._cache[key]
            now = datetime.now(tz=timezone.utc).timestamp()
            if now - stored_at <= ttl:
                logger.debug("Cache hit for key '%s'", key)
                return data
            # Expired
            del self._cache[key]
        return None

    def _set_in_cache(self, key: str, data: Any) -> None:
        now = datetime.now(tz=timezone.utc).timestamp()
        self._cache[key] = (now, data)

    def clear_cache(self) -> None:
        """Clear all cached weather data."""
        self._cache.clear()

    async def get_current(
        self,
        lat: float,
        lon: float,
        location_name: Optional[str] = None,
        force_refresh: bool = False,
    ) -> CurrentWeather:
        """
        Get current weather with cache check and multi-provider fallback.
        """
        cache_key = f"current:{round(lat, 4)}:{round(lon, 4)}"
        if not force_refresh:
            cached = self._get_from_cache(cache_key, self.ttl_current)
            if cached is not None:
                return cached

        providers = self.registry.get_providers_for_feature("current")
        if not providers:
            raise ProviderUnavailableError("No providers configured for current weather")

        errors: List[str] = []
        for provider in providers:
            try:
                data = await provider.get_current(lat, lon, location_name=location_name)
                self._set_in_cache(cache_key, data)
                return data
            except Exception as exc:
                err_msg = f"{provider.name}: {exc}"
                logger.warning("Provider failed during get_current: %s", err_msg)
                errors.append(err_msg)

        raise ProviderUnavailableError(
            f"All current weather providers failed: {'; '.join(errors)}"
        )

    async def get_forecast(
        self,
        lat: float,
        lon: float,
        days: int = 7,
        location_name: Optional[str] = None,
        force_refresh: bool = False,
    ) -> ForecastWeather:
        """
        Get weather forecast with cache check and fallback.
        """
        cache_key = f"forecast:{round(lat, 4)}:{round(lon, 4)}:{days}"
        if not force_refresh:
            cached = self._get_from_cache(cache_key, self.ttl_forecast)
            if cached is not None:
                return cached

        providers = self.registry.get_providers_for_feature("forecast")
        if not providers:
            raise ProviderUnavailableError("No providers configured for forecast weather")

        errors: List[str] = []
        for provider in providers:
            try:
                data = await provider.get_forecast(lat, lon, days=days, location_name=location_name)
                self._set_in_cache(cache_key, data)
                return data
            except Exception as exc:
                err_msg = f"{provider.name}: {exc}"
                logger.warning("Provider failed during get_forecast: %s", err_msg)
                errors.append(err_msg)

        raise ProviderUnavailableError(
            f"All forecast providers failed: {'; '.join(errors)}"
        )

    async def get_historical(
        self,
        lat: float,
        lon: float,
        start_date: str,
        end_date: str,
        location_name: Optional[str] = None,
        force_refresh: bool = False,
    ) -> HistoricalWeather:
        """
        Get historical weather with cache check and fallback.
        """
        cache_key = f"history:{round(lat, 4)}:{round(lon, 4)}:{start_date}:{end_date}"
        if not force_refresh:
            cached = self._get_from_cache(cache_key, self.ttl_historical)
            if cached is not None:
                return cached

        providers = self.registry.get_providers_for_feature("historical")
        if not providers:
            raise ProviderUnavailableError("No providers configured for historical weather")

        errors: List[str] = []
        for provider in providers:
            try:
                data = await provider.get_historical(
                    lat, lon, start_date, end_date, location_name=location_name
                )
                self._set_in_cache(cache_key, data)
                return data
            except Exception as exc:
                err_msg = f"{provider.name}: {exc}"
                logger.warning("Provider failed during get_historical: %s", err_msg)
                errors.append(err_msg)

        raise ProviderUnavailableError(
            f"All historical providers failed: {'; '.join(errors)}"
        )

    async def get_provider_status(self) -> List[Dict[str, Any]]:
        """
        Return health and feature coverage status for all registered providers.
        """
        results: List[Dict[str, Any]] = []
        for provider in self.registry.list_all():
            healthy = await provider.health_check()
            results.append(
                {
                    "name": provider.name,
                    "display_name": provider.display_name,
                    "supported_features": sorted(list(provider.supported_features)),
                    "is_available": healthy,
                }
            )
        return results


# Shared default singleton
default_aggregator = WeatherAggregator()
