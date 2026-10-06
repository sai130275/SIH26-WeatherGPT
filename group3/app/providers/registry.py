"""
providers/registry.py
---------------------
Registry for weather data providers.

Manages provider lifecycle, registration, feature discovery, and priority order.
Future providers (Tomorrow.io, IMD, GFS, etc.) register themselves here.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from app.providers.base import WeatherProvider
from app.providers.open_meteo import OpenMeteoProvider

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """
    Central registry for weather providers.

    Maintains an ordered list of providers for priority-based fallback.
    """

    def __init__(self) -> None:
        self._providers: Dict[str, WeatherProvider] = {}
        self._priority: List[str] = []

    def register(
        self,
        provider: WeatherProvider,
        priority: Optional[int] = None,
    ) -> None:
        """
        Register a new weather provider.

        :param provider: Instance of WeatherProvider.
        :param priority: Optional insertion index in priority list (0 = highest).
        """
        self._providers[provider.name] = provider
        if provider.name in self._priority:
            self._priority.remove(provider.name)

        if priority is not None and 0 <= priority <= len(self._priority):
            self._priority.insert(priority, provider.name)
        else:
            self._priority.append(provider.name)

        logger.info(
            "Registered weather provider '%s' (features: %s)",
            provider.name,
            provider.supported_features,
        )

    def get(self, name: str) -> Optional[WeatherProvider]:
        """Retrieve a provider by name."""
        return self._providers.get(name)

    def get_providers_for_feature(self, feature: str) -> List[WeatherProvider]:
        """
        Return all registered providers supporting a feature in priority order.

        :param feature: 'current', 'forecast', or 'historical'.
        """
        ordered: List[WeatherProvider] = []
        for name in self._priority:
            p = self._providers[name]
            if feature in p.supported_features:
                ordered.append(p)
        return ordered

    def list_all(self) -> List[WeatherProvider]:
        """Return all registered providers in priority order."""
        return [self._providers[name] for name in self._priority]

    def clear(self) -> None:
        """Clear all registered providers (primarily for tests)."""
        self._providers.clear()
        self._priority.clear()


# Default singleton registry populated with OpenMeteoProvider
default_registry = ProviderRegistry()
default_registry.register(OpenMeteoProvider())
