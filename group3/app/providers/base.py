"""
providers/base.py
-----------------
Abstract base class and exceptions for all weather data providers.

Every provider implementation (Open-Meteo, Tomorrow.io, IMD, GFS NWP, etc.)
must inherit from WeatherProvider and return data normalized into canonical
schemas from app.schemas.unified_weather.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Set

from app.schemas.unified_weather import (
    CurrentWeather,
    ForecastWeather,
    HistoricalWeather,
    ProviderInfo,
)


# --------------------------------------------------------------------------- #
# Provider Exceptions                                                         #
# --------------------------------------------------------------------------- #

class WeatherProviderError(Exception):
    """Base exception for all weather provider failures."""

    def __init__(self, message: str, provider_name: str = "", status_code: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.provider_name = provider_name
        self.status_code = status_code


class ProviderUnavailableError(WeatherProviderError):
    """Raised when a provider API is unreachable, timed out, or returns a 5xx error."""
    pass


class ProviderRateLimitError(WeatherProviderError):
    """Raised when a provider rate limit is exceeded (e.g. HTTP 429)."""
    pass


class ProviderDataError(WeatherProviderError):
    """Raised when provider response data is malformed or unparseable."""
    pass


# --------------------------------------------------------------------------- #
# Abstract Weather Provider                                                   #
# --------------------------------------------------------------------------- #

class WeatherProvider(ABC):
    """
    Abstract base class for weather data providers.

    All methods are asynchronous to support non-blocking I/O with external APIs.
    Implementations must normalize all returned data into canonical units
    defined by unified_weather schemas.
    """

    name: str = "base"
    display_name: str = "Base Provider"
    supported_features: Set[str] = {"current", "forecast", "historical"}

    def __init__(self) -> None:
        self._is_healthy: bool = True
        self._last_error: Optional[str] = None

    @abstractmethod
    async def get_current(self, lat: float, lon: float) -> CurrentWeather:
        """
        Fetch and normalize current weather for the given coordinates.

        :param lat: Latitude in decimal degrees (-90 to +90).
        :param lon: Longitude in decimal degrees (-180 to +180).
        :return: CurrentWeather object in canonical schema.
        :raises ProviderUnavailableError: If provider API is unreachable or fails.
        """
        pass

    @abstractmethod
    async def get_forecast(
        self,
        lat: float,
        lon: float,
        days: int = 7,
    ) -> ForecastWeather:
        """
        Fetch and normalize weather forecast for the given coordinates.

        :param lat: Latitude in decimal degrees.
        :param lon: Longitude in decimal degrees.
        :param days: Number of forecast days (1 to 16).
        :return: ForecastWeather object with hourly and daily forecasts.
        :raises ProviderUnavailableError: If provider API is unreachable or fails.
        """
        pass

    @abstractmethod
    async def get_historical(
        self,
        lat: float,
        lon: float,
        start_date: str,
        end_date: str,
    ) -> HistoricalWeather:
        """
        Fetch and normalize historical weather data for the given date range.

        :param lat: Latitude in decimal degrees.
        :param lon: Longitude in decimal degrees.
        :param start_date: ISO date string 'YYYY-MM-DD'.
        :param end_date: ISO date string 'YYYY-MM-DD'.
        :return: HistoricalWeather object.
        :raises ProviderUnavailableError: If provider API is unreachable or fails.
        """
        pass

    async def health_check(self) -> bool:
        """
        Verify if the provider API is reachable and responding.
        Subclasses should override this with a lightweight ping or request.
        """
        return self._is_healthy

    @property
    def is_available(self) -> bool:
        """Indicates whether this provider is currently considered available."""
        return self._is_healthy

    def get_provider_info(self, model: Optional[str] = None) -> ProviderInfo:
        """Construct standard ProviderInfo metadata for this provider."""
        return ProviderInfo(
            name=self.name,
            display_name=self.display_name,
            model=model,
        )
