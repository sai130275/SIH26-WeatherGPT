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
    # Server                                                               #
    # ------------------------------------------------------------------ #
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ------------------------------------------------------------------ #
    # LLM (placeholder – wired in a later phase)                          #
    # ------------------------------------------------------------------ #
    LLM_PROVIDER: str = "openai"          # openai | anthropic | google
    LLM_API_KEY: str = ""                 # set in .env – never commit
    LLM_MODEL: str = "gpt-4o"

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
