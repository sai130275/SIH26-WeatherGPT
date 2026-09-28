"""
services/condition_detector.py
--------------------------------
Detects weather hazard conditions from a ProcessedWeather snapshot.

Design rules
------------
* Each detector is a pure method — no side effects, no I/O.
* Thresholds come exclusively from the injected Settings instance.
  They are NEVER hard-coded inside detector functions.
* When a meteorological field is None (missing from source), the
  corresponding detector returns None — it does not guess or interpolate.
* Severity is computed by module-level pure functions so they can be
  unit-tested independently of the detector class.

Severity bands
--------------
Each detector uses proportional excess/deficit relative to its threshold:

  heavy_rain      (mm above threshold):   low <25 | moderate <50 | high <100 | extreme
  high_wind       (km/h above threshold): low <15 | moderate <30 | high <60  | extreme
  extreme_heat    (°C above threshold):   low <2  | moderate <5  | high <10  | extreme
  low_visibility  (ratio to threshold):   low >0.75 | moderate >0.5 | high >0.25 | extreme

Adding a new detector
---------------------
1. Add a `detect_<name>` method that returns Optional[DetectedCondition].
2. Add a corresponding pure severity function.
3. Append the method to `detect_all`.
4. Add the threshold to Settings (config.py) and .env.example.
"""

from __future__ import annotations

from typing import Optional

from app.core.config import Settings, settings as _default_settings
from app.schemas.analysis import DetectedCondition
from app.services.weather_processor import ProcessedWeather


# --------------------------------------------------------------------------- #
# Pure severity helper functions                                               #
# (no class dependency → easy to unit-test in isolation)                       #
# --------------------------------------------------------------------------- #

def _rain_severity(rainfall: float, threshold: float) -> str:
    """Classify heavy-rain severity by mm above threshold."""
    excess = rainfall - threshold
    if excess >= 100:
        return "extreme"
    if excess >= 50:
        return "high"
    if excess >= 25:
        return "moderate"
    return "low"


def _wind_severity(wind_speed: float, threshold: float) -> str:
    """Classify high-wind severity by km/h above threshold."""
    excess = wind_speed - threshold
    if excess >= 60:
        return "extreme"
    if excess >= 30:
        return "high"
    if excess >= 15:
        return "moderate"
    return "low"


def _heat_severity(temperature: float, threshold: float) -> str:
    """Classify extreme-heat severity by °C above threshold."""
    excess = temperature - threshold
    if excess >= 10:
        return "extreme"
    if excess >= 5:
        return "high"
    if excess >= 2:
        return "moderate"
    return "low"


def _visibility_severity(visibility: float, threshold: float) -> str:
    """
    Classify low-visibility severity by ratio to threshold.

    Lower visibility = higher severity.  Uses ratio so severity bands
    scale with any configured threshold value.
    """
    if threshold <= 0:
        return "low"  # degenerate threshold — avoid division by zero
    ratio = visibility / threshold
    if ratio <= 0.25:
        return "extreme"
    if ratio <= 0.50:
        return "high"
    if ratio <= 0.75:
        return "moderate"
    return "low"


# --------------------------------------------------------------------------- #
# ConditionDetector                                                            #
# --------------------------------------------------------------------------- #

class ConditionDetector:
    """
    Stateless condition detector.

    Inject a custom Settings instance to override thresholds in tests:

    >>> from app.core.config import Settings
    >>> cfg = Settings(HEAVY_RAIN_THRESHOLD_MM=20.0)
    >>> detector = ConditionDetector(cfg=cfg)
    >>> conditions = detector.detect_all(processed_weather)
    """

    def __init__(self, cfg: Optional[Settings] = None) -> None:
        self._cfg: Settings = cfg if cfg is not None else _default_settings

    # ------------------------------------------------------------------ #
    # Individual detectors                                                 #
    # ------------------------------------------------------------------ #

    def detect_heavy_rain(
        self, weather: ProcessedWeather
    ) -> Optional[DetectedCondition]:
        """
        Trigger when rainfall exceeds HEAVY_RAIN_THRESHOLD_MM.

        Returns None when:
          - rainfall is None (field not provided by source)
          - rainfall ≤ threshold (no hazard)
        """
        if weather.rainfall is None:
            return None

        threshold = self._cfg.HEAVY_RAIN_THRESHOLD_MM

        if weather.rainfall <= threshold:
            return None

        return DetectedCondition(
            type="heavy_rain",
            severity=_rain_severity(weather.rainfall, threshold),  # type: ignore[arg-type]
            value=weather.rainfall,
            unit="mm",
            threshold=threshold,
            reason=(
                f"Rainfall of {weather.rainfall} mm exceeds the configured "
                f"heavy-rain threshold of {threshold} mm."
            ),
        )

    def detect_high_wind(
        self, weather: ProcessedWeather
    ) -> Optional[DetectedCondition]:
        """
        Trigger when wind_speed exceeds HIGH_WIND_THRESHOLD_KMH.

        Returns None when:
          - wind_speed is None (field not provided by source)
          - wind_speed ≤ threshold (no hazard)
        """
        if weather.wind_speed is None:
            return None

        threshold = self._cfg.HIGH_WIND_THRESHOLD_KMH

        if weather.wind_speed <= threshold:
            return None

        return DetectedCondition(
            type="high_wind",
            severity=_wind_severity(weather.wind_speed, threshold),  # type: ignore[arg-type]
            value=weather.wind_speed,
            unit="km/h",
            threshold=threshold,
            reason=(
                f"Wind speed of {weather.wind_speed} km/h exceeds the "
                f"configured high-wind threshold of {threshold} km/h."
            ),
        )

    def detect_extreme_heat(
        self, weather: ProcessedWeather
    ) -> Optional[DetectedCondition]:
        """
        Trigger when temperature exceeds EXTREME_HEAT_THRESHOLD_C.

        Returns None when:
          - temperature is None (field not provided by source)
          - temperature ≤ threshold (no hazard)
        """
        if weather.temperature is None:
            return None

        threshold = self._cfg.EXTREME_HEAT_THRESHOLD_C

        if weather.temperature <= threshold:
            return None

        return DetectedCondition(
            type="extreme_heat",
            severity=_heat_severity(weather.temperature, threshold),  # type: ignore[arg-type]
            value=weather.temperature,
            unit="°C",
            threshold=threshold,
            reason=(
                f"Temperature of {weather.temperature} °C exceeds the "
                f"configured extreme-heat threshold of {threshold} °C."
            ),
        )

    def detect_low_visibility(
        self, weather: ProcessedWeather
    ) -> Optional[DetectedCondition]:
        """
        Trigger when visibility falls below LOW_VISIBILITY_THRESHOLD_KM.

        Returns None when:
          - visibility is None (field not provided by source)
          - visibility ≥ threshold (no hazard)
        """
        if weather.visibility is None:
            return None

        threshold = self._cfg.LOW_VISIBILITY_THRESHOLD_KM

        if weather.visibility >= threshold:
            return None

        return DetectedCondition(
            type="low_visibility",
            severity=_visibility_severity(weather.visibility, threshold),  # type: ignore[arg-type]
            value=weather.visibility,
            unit="km",
            threshold=threshold,
            reason=(
                f"Visibility of {weather.visibility} km is below the "
                f"configured low-visibility threshold of {threshold} km."
            ),
        )

    # ------------------------------------------------------------------ #
    # Aggregate                                                            #
    # ------------------------------------------------------------------ #

    def detect_all(
        self, weather: ProcessedWeather
    ) -> list[DetectedCondition]:
        """
        Run all registered detectors and return every triggered condition.

        Order matches the registration order below; conditions that are
        not triggered (None returns) are excluded from the result.
        """
        detectors = [
            self.detect_heavy_rain,
            self.detect_high_wind,
            self.detect_extreme_heat,
            self.detect_low_visibility,
        ]
        return [
            condition
            for detector in detectors
            if (condition := detector(weather)) is not None
        ]
