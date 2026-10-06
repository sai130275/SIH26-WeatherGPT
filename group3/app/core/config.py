"""
core/config.py
--------------
Centralised application settings loaded from environment variables / .env file.

Uses pydantic-settings so every value is type-validated at startup.
No secrets are hard-coded; all sensitive values must be supplied via the
environment or the .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide configuration."""

    # ------------------------------------------------------------------ #
    # General                                                              #
    # ------------------------------------------------------------------ #
    APP_NAME: str = "WeatherGPT – AI & Weather Intelligence (Group 3)"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # ------------------------------------------------------------------ #
    # Server & Security                                                    #
    # ------------------------------------------------------------------ #
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: list[str] = ["*"]  # overridden via env var in production

    # ------------------------------------------------------------------ #
    # LLM (placeholder – wired in a later phase)                          #
    # ------------------------------------------------------------------ #
    LLM_PROVIDER: str = "openai"          # openai | anthropic | google
    LLM_API_KEY: str = ""                 # set in .env – never commit
    LLM_MODEL: str = "gpt-4o"

    # ------------------------------------------------------------------ #
    # Condition Detection Thresholds (Phase 2)                            #
    #                                                                     #
    # All values use canonical units (mm, km/h, °C, km).                 #
    # Override via environment variables when needed.                     #
    # ------------------------------------------------------------------ #

    # Rainfall threshold above which "heavy rain" is triggered (mm)
    HEAVY_RAIN_THRESHOLD_MM: float = 50.0

    # Wind speed threshold above which "high wind" is triggered (km/h)
    HIGH_WIND_THRESHOLD_KMH: float = 60.0

    # Temperature threshold above which "extreme heat" is triggered (°C)
    EXTREME_HEAT_THRESHOLD_C: float = 40.0

    # Visibility threshold below which "low visibility" is triggered (km)
    LOW_VISIBILITY_THRESHOLD_KM: float = 1.0

    # ------------------------------------------------------------------ #
    # Weather Provider Configuration                                      #
    # ------------------------------------------------------------------ #
    OPEN_METEO_BASE_URL: str = "https://api.open-meteo.com/v1"
    OPEN_METEO_ARCHIVE_URL: str = "https://archive-api.open-meteo.com/v1/archive"
    OPEN_METEO_TIMEOUT_SECONDS: int = 8

    # Weather Cache TTLs (seconds)
    WEATHER_CACHE_TTL_CURRENT: int = 900       # 15 minutes
    WEATHER_CACHE_TTL_FORECAST: int = 1800     # 30 minutes
    WEATHER_CACHE_TTL_HISTORICAL: int = 86400  # 24 hours

    # ------------------------------------------------------------------ #
    # Pydantic-settings: load from .env, ignore extra keys                #
    # ------------------------------------------------------------------ #
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Single shared instance – import this everywhere.
settings = Settings()
