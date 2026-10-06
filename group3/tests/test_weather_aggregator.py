"""
tests/test_weather_aggregator.py
--------------------------------
Unit tests for WeatherAggregator and ProviderRegistry.
Tests fallback behavior, caching, and multi-provider coordination.
"""

from datetime import datetime, timezone
import pytest

from app.providers.base import (
    ProviderUnavailableError,
    WeatherProvider,
)
from app.providers.registry import ProviderRegistry
from app.schemas.unified_weather import (
    CurrentWeather,
    ForecastWeather,
    HistoricalWeather,
    ProviderInfo,
)
from app.services.weather_aggregator import WeatherAggregator


class MockWorkingProvider(WeatherProvider):
    name = "mock_working"
    display_name = "Mock Working"
    supported_features = {"current", "forecast", "historical"}

    def __init__(self, temp: float = 25.0):
        super().__init__()
        self.temp = temp
        self.call_count = 0

    async def get_current(self, lat: float, lon: float, location_name=None) -> CurrentWeather:
        self.call_count += 1
        return CurrentWeather(
            location=location_name or "Mock Loc",
            latitude=lat,
            longitude=lon,
            timestamp=datetime.now(tz=timezone.utc),
            temperature=self.temp,
            provider=ProviderInfo(name=self.name),
        )

    async def get_forecast(self, lat: float, lon: float, days: int = 7, location_name=None) -> ForecastWeather:
        self.call_count += 1
        return ForecastWeather(
            location=location_name or "Mock Loc",
            latitude=lat,
            longitude=lon,
            hourly=[],
            daily=[],
            provider=ProviderInfo(name=self.name),
        )

    async def get_historical(self, lat: float, lon: float, start_date: str, end_date: str, location_name=None) -> HistoricalWeather:
        self.call_count += 1
        return HistoricalWeather(
            location=location_name or "Mock Loc",
            latitude=lat,
            longitude=lon,
            start_date=start_date,
            end_date=end_date,
            hourly=[],
            provider=ProviderInfo(name=self.name),
        )

    async def health_check(self) -> bool:
        return True


class MockFailingProvider(WeatherProvider):
    name = "mock_failing"
    display_name = "Mock Failing"
    supported_features = {"current", "forecast", "historical"}

    async def get_current(self, lat: float, lon: float, location_name=None) -> CurrentWeather:
        raise ProviderUnavailableError("Simulated primary provider outage", provider_name=self.name)

    async def get_forecast(self, lat: float, lon: float, days: int = 7, location_name=None) -> ForecastWeather:
        raise ProviderUnavailableError("Simulated primary forecast outage", provider_name=self.name)

    async def get_historical(self, lat: float, lon: float, start_date: str, end_date: str, location_name=None) -> HistoricalWeather:
        raise ProviderUnavailableError("Simulated primary archive outage", provider_name=self.name)

    async def health_check(self) -> bool:
        return False


@pytest.mark.asyncio
async def test_aggregator_caching_and_force_refresh():
    registry = ProviderRegistry()
    working_p = MockWorkingProvider(temp=30.0)
    registry.register(working_p)

    aggregator = WeatherAggregator(registry=registry, cache_ttl_current=60)

    # First call: hits provider
    res1 = await aggregator.get_current(17.97, 79.59)
    assert res1.temperature == 30.0
    assert working_p.call_count == 1

    # Second call: hits cache, provider call count remains 1
    res2 = await aggregator.get_current(17.97, 79.59)
    assert res2.temperature == 30.0
    assert working_p.call_count == 1

    # Force refresh: bypasses cache, provider call count increases to 2
    res3 = await aggregator.get_current(17.97, 79.59, force_refresh=True)
    assert res3.temperature == 30.0
    assert working_p.call_count == 2


@pytest.mark.asyncio
async def test_aggregator_fallback_on_primary_failure():
    registry = ProviderRegistry()
    failing_p = MockFailingProvider()
    backup_p = MockWorkingProvider(temp=22.0)

    # Failing is priority 0 (first), backup is priority 1 (second)
    registry.register(failing_p, priority=0)
    registry.register(backup_p, priority=1)

    aggregator = WeatherAggregator(registry=registry)

    # When get_current is called, failing_p raises an error, aggregator catches it and falls back to backup_p
    current = await aggregator.get_current(17.97, 79.59)
    assert current.temperature == 22.0
    assert current.provider.name == "mock_working"
    assert backup_p.call_count == 1


@pytest.mark.asyncio
async def test_aggregator_all_providers_fail():
    registry = ProviderRegistry()
    failing_p = MockFailingProvider()
    registry.register(failing_p)

    aggregator = WeatherAggregator(registry=registry)
    with pytest.raises(ProviderUnavailableError) as exc_info:
        await aggregator.get_current(17.97, 79.59)

    assert "All current weather providers failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_aggregator_provider_status():
    registry = ProviderRegistry()
    working_p = MockWorkingProvider()
    failing_p = MockFailingProvider()
    registry.register(working_p)
    registry.register(failing_p)

    aggregator = WeatherAggregator(registry=registry)
    status = await aggregator.get_provider_status()

    assert len(status) == 2
    w_status = next(s for s in status if s["name"] == "mock_working")
    f_status = next(s for s in status if s["name"] == "mock_failing")
    assert w_status["is_available"] is True
    assert f_status["is_available"] is False
