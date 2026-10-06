"""
providers/open_meteo.py
-----------------------
Open-Meteo weather provider adapter.

Fetches data from Open-Meteo REST API (Forecast and Historical Archive APIs)
and normalizes all responses into the canonical unified schemas.
"""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings
from app.providers.base import (
    ProviderDataError,
    ProviderRateLimitError,
    ProviderUnavailableError,
    WeatherProvider,
)
from app.schemas.unified_weather import (
    CurrentWeather,
    DailyForecast,
    ForecastPoint,
    ForecastWeather,
    HistoricalWeather,
    ProviderInfo,
)

logger = logging.getLogger(__name__)

# WMO Weather Interpretation Codes (WW)
WMO_CODE_MAP: Dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


class OpenMeteoProvider(WeatherProvider):
    """
    Adapter for the Open-Meteo Weather API.
    Zero API-key requirement for non-commercial tier.
    """

    name: str = "open_meteo"
    display_name: str = "Open-Meteo"
    supported_features = {"current", "forecast", "historical"}

    def __init__(
        self,
        base_url: Optional[str] = None,
        archive_url: Optional[str] = None,
        timeout: Optional[float] = None,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        super().__init__()
        self.base_url = (base_url or settings.OPEN_METEO_BASE_URL).rstrip("/")
        self.archive_url = (archive_url or settings.OPEN_METEO_ARCHIVE_URL).rstrip("/")
        self.timeout = timeout or float(settings.OPEN_METEO_TIMEOUT_SECONDS)
        self._external_client = client

    def _get_client(self) -> httpx.AsyncClient:
        if self._external_client is not None:
            return self._external_client
        return httpx.AsyncClient(timeout=self.timeout)

    @staticmethod
    def map_wmo_code(code: Optional[int]) -> str:
        """Map numeric WMO code to human-readable condition description."""
        if code is None:
            return "Unknown"
        return WMO_CODE_MAP.get(code, "Cloudy")

    @staticmethod
    def _is_lightning(code: Optional[int]) -> bool:
        """WMO thunderstorm codes indicate lightning activity."""
        return code in (95, 96, 99)

    async def get_current(
        self,
        lat: float,
        lon: float,
        location_name: Optional[str] = None,
    ) -> CurrentWeather:
        """
        Fetch current weather observation and instantaneous telemetry.
        """
        params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": "true",
            "hourly": (
                "precipitation_probability,precipitation,relative_humidity_2m,"
                "wind_speed_10m,wind_gusts_10m,wind_direction_10m,weather_code,"
                "cape,visibility,surface_pressure,uv_index,dew_point_2m,"
                "apparent_temperature,cloud_cover"
            ),
            "timezone": "auto",
        }

        url = f"{self.base_url}/forecast"
        client = self._get_client()
        should_close = self._external_client is None

        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
        except httpx.TimeoutException as exc:
            self._is_healthy = False
            raise ProviderUnavailableError(
                f"Open-Meteo request timed out: {exc}",
                provider_name=self.name,
            ) from exc
        except httpx.HTTPStatusError as exc:
            self._is_healthy = False
            if exc.response.status_code == 429:
                raise ProviderRateLimitError(
                    "Open-Meteo rate limit exceeded (HTTP 429)",
                    provider_name=self.name,
                    status_code=429,
                ) from exc
            raise ProviderUnavailableError(
                f"Open-Meteo API returned HTTP {exc.response.status_code}: {exc}",
                provider_name=self.name,
                status_code=exc.response.status_code,
            ) from exc
        except Exception as exc:
            self._is_healthy = False
            raise ProviderUnavailableError(
                f"Open-Meteo request failed: {exc}",
                provider_name=self.name,
            ) from exc
        finally:
            if should_close:
                await client.aclose()

        self._is_healthy = True

        current = data.get("current_weather") or {}
        hourly = data.get("hourly") or {}

        # Align current_weather timestamp with hourly index for extended parameters
        idx = 0
        hourly_times = hourly.get("time") or []
        current_time_str = current.get("time")
        if hourly_times and current_time_str:
            try:
                idx = hourly_times.index(current_time_str)
            except ValueError:
                idx = 0

        def _val(key: str, default: Any = None) -> Any:
            arr = hourly.get(key)
            if arr and isinstance(arr, list) and 0 <= idx < len(arr):
                v = arr[idx]
                return v if v is not None else default
            return default

        # Basic fields from current_weather
        temp = current.get("temperature")
        wind_spd = current.get("windspeed")
        wind_dir = current.get("winddirection")
        w_code = current.get("weathercode")
        if w_code is None:
            w_code = current.get("weather_code")

        # Extended fields from hourly
        humidity = _val("relative_humidity_2m")
        rainfall = _val("precipitation", 0.0)
        wind_gusts = _val("wind_gusts_10m")
        pressure = _val("surface_pressure")
        visibility_m = _val("visibility")
        visibility_km = (visibility_m / 1000.0) if visibility_m is not None else None
        uv_index = _val("uv_index")
        cloud_cover = _val("cloud_cover")
        dew_point = _val("dew_point_2m")
        feels_like = _val("apparent_temperature")
        cape = _val("cape")

        ts_raw = current.get("time")
        if ts_raw:
            try:
                obs_time = datetime.fromisoformat(ts_raw)
                if obs_time.tzinfo is None:
                    obs_time = obs_time.replace(tzinfo=timezone.utc)
            except Exception:
                obs_time = datetime.now(tz=timezone.utc)
        else:
            obs_time = datetime.now(tz=timezone.utc)

        provider_info = self.get_provider_info(model="ECMWF / GFS seamless blend")

        return CurrentWeather(
            location=location_name or f"{lat:.2f}, {lon:.2f}",
            latitude=lat,
            longitude=lon,
            timestamp=obs_time,
            temperature=float(temp) if temp is not None else None,
            humidity=float(humidity) if humidity is not None else None,
            rainfall=float(rainfall) if rainfall is not None else 0.0,
            wind_speed=float(wind_spd) if wind_spd is not None else None,
            wind_direction=float(wind_dir) if wind_dir is not None else None,
            wind_gusts=float(wind_gusts) if wind_gusts is not None else None,
            pressure=float(pressure) if pressure is not None else None,
            visibility=float(visibility_km) if visibility_km is not None else None,
            uv_index=float(uv_index) if uv_index is not None else None,
            cloud_cover=float(cloud_cover) if cloud_cover is not None else None,
            dew_point=float(dew_point) if dew_point is not None else None,
            feels_like=float(feels_like) if feels_like is not None else None,
            weather_code=int(w_code) if w_code is not None else None,
            weather_condition=self.map_wmo_code(w_code),
            lightning=self._is_lightning(w_code),
            cape=float(cape) if cape is not None else None,
            provider=provider_info,
        )

    async def get_forecast(
        self,
        lat: float,
        lon: float,
        days: int = 7,
        location_name: Optional[str] = None,
    ) -> ForecastWeather:
        """
        Fetch forecast with hourly time-series and daily aggregates.
        """
        days = max(1, min(16, days))
        params = {
            "latitude": lat,
            "longitude": lon,
            "forecast_days": days,
            "hourly": (
                "temperature_2m,relative_humidity_2m,precipitation_probability,"
                "precipitation,wind_speed_10m,wind_gusts_10m,weather_code,cloud_cover"
            ),
            "daily": (
                "temperature_2m_max,temperature_2m_min,precipitation_probability_max,"
                "precipitation_sum,wind_speed_10m_max,weather_code,sunrise,sunset,uv_index_max"
            ),
            "timezone": "auto",
        }

        url = f"{self.base_url}/forecast"
        client = self._get_client()
        should_close = self._external_client is None

        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
        except httpx.TimeoutException as exc:
            self._is_healthy = False
            raise ProviderUnavailableError(
                f"Open-Meteo forecast timed out: {exc}",
                provider_name=self.name,
            ) from exc
        except httpx.HTTPStatusError as exc:
            self._is_healthy = False
            if exc.response.status_code == 429:
                raise ProviderRateLimitError(
                    "Open-Meteo rate limit exceeded",
                    provider_name=self.name,
                    status_code=429,
                ) from exc
            raise ProviderUnavailableError(
                f"Open-Meteo forecast HTTP {exc.response.status_code}: {exc}",
                provider_name=self.name,
                status_code=exc.response.status_code,
            ) from exc
        except Exception as exc:
            self._is_healthy = False
            raise ProviderUnavailableError(
                f"Open-Meteo forecast failed: {exc}",
                provider_name=self.name,
            ) from exc
        finally:
            if should_close:
                await client.aclose()

        self._is_healthy = True

        hourly_raw = data.get("hourly") or {}
        daily_raw = data.get("daily") or {}

        # Parse hourly points
        hourly_points: List[ForecastPoint] = []
        times = hourly_raw.get("time") or []
        t2m = hourly_raw.get("temperature_2m") or []
        rh = hourly_raw.get("relative_humidity_2m") or []
        pop = hourly_raw.get("precipitation_probability") or []
        precip = hourly_raw.get("precipitation") or []
        wspd = hourly_raw.get("wind_speed_10m") or []
        gusts = hourly_raw.get("wind_gusts_10m") or []
        wcode = hourly_raw.get("weather_code") or []
        clouds = hourly_raw.get("cloud_cover") or []

        for i, t_str in enumerate(times):
            try:
                dt = datetime.fromisoformat(t_str)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
            except Exception:
                dt = datetime.now(tz=timezone.utc)

            code = wcode[i] if i < len(wcode) else None
            hourly_points.append(
                ForecastPoint(
                    timestamp=dt,
                    temperature=float(t2m[i]) if i < len(t2m) and t2m[i] is not None else None,
                    rainfall=float(precip[i]) if i < len(precip) and precip[i] is not None else None,
                    humidity=float(rh[i]) if i < len(rh) and rh[i] is not None else None,
                    wind_speed=float(wspd[i]) if i < len(wspd) and wspd[i] is not None else None,
                    wind_gusts=float(gusts[i]) if i < len(gusts) and gusts[i] is not None else None,
                    weather_code=int(code) if code is not None else None,
                    weather_condition=self.map_wmo_code(code),
                    precipitation_probability=float(pop[i]) if i < len(pop) and pop[i] is not None else None,
                    cloud_cover=float(clouds[i]) if i < len(clouds) and clouds[i] is not None else None,
                )
            )

        # Parse daily points
        daily_points: List[DailyForecast] = []
        d_times = daily_raw.get("time") or []
        d_tmax = daily_raw.get("temperature_2m_max") or []
        d_tmin = daily_raw.get("temperature_2m_min") or []
        d_pop = daily_raw.get("precipitation_probability_max") or []
        d_precip = daily_raw.get("precipitation_sum") or []
        d_wspd = daily_raw.get("wind_speed_10m_max") or []
        d_wcode = daily_raw.get("weather_code") or []
        d_sunrise = daily_raw.get("sunrise") or []
        d_sunset = daily_raw.get("sunset") or []
        d_uv = daily_raw.get("uv_index_max") or []

        for j, date_str in enumerate(d_times):
            code = d_wcode[j] if j < len(d_wcode) else None
            daily_points.append(
                DailyForecast(
                    date=date_str,
                    temperature_max=float(d_tmax[j]) if j < len(d_tmax) and d_tmax[j] is not None else None,
                    temperature_min=float(d_tmin[j]) if j < len(d_tmin) and d_tmin[j] is not None else None,
                    precipitation_sum=float(d_precip[j]) if j < len(d_precip) and d_precip[j] is not None else None,
                    precipitation_probability_max=float(d_pop[j]) if j < len(d_pop) and d_pop[j] is not None else None,
                    wind_speed_max=float(d_wspd[j]) if j < len(d_wspd) and d_wspd[j] is not None else None,
                    weather_code=int(code) if code is not None else None,
                    weather_condition=self.map_wmo_code(code),
                    sunrise=str(d_sunrise[j]) if j < len(d_sunrise) and d_sunrise[j] is not None else None,
                    sunset=str(d_sunset[j]) if j < len(d_sunset) and d_sunset[j] is not None else None,
                    uv_index_max=float(d_uv[j]) if j < len(d_uv) and d_uv[j] is not None else None,
                )
            )

        provider_info = self.get_provider_info(model="ECMWF / GFS seamless blend")

        return ForecastWeather(
            location=location_name or f"{lat:.2f}, {lon:.2f}",
            latitude=lat,
            longitude=lon,
            hourly=hourly_points,
            daily=daily_points,
            provider=provider_info,
        )

    async def get_historical(
        self,
        lat: float,
        lon: float,
        start_date: str,
        end_date: str,
        location_name: Optional[str] = None,
    ) -> HistoricalWeather:
        """
        Fetch historical archive data for the given date range (YYYY-MM-DD).
        """
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date,
            "end_date": end_date,
            "hourly": "temperature_2m,precipitation,relative_humidity_2m,wind_speed_10m,weather_code",
            "timezone": "auto",
        }

        url = self.archive_url
        client = self._get_client()
        should_close = self._external_client is None

        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
        except httpx.TimeoutException as exc:
            self._is_healthy = False
            raise ProviderUnavailableError(
                f"Open-Meteo archive timed out: {exc}",
                provider_name=self.name,
            ) from exc
        except httpx.HTTPStatusError as exc:
            self._is_healthy = False
            if exc.response.status_code == 429:
                raise ProviderRateLimitError(
                    "Open-Meteo archive rate limit exceeded",
                    provider_name=self.name,
                    status_code=429,
                ) from exc
            raise ProviderUnavailableError(
                f"Open-Meteo archive HTTP {exc.response.status_code}: {exc}",
                provider_name=self.name,
                status_code=exc.response.status_code,
            ) from exc
        except Exception as exc:
            self._is_healthy = False
            raise ProviderUnavailableError(
                f"Open-Meteo archive failed: {exc}",
                provider_name=self.name,
            ) from exc
        finally:
            if should_close:
                await client.aclose()

        self._is_healthy = True

        hourly_raw = data.get("hourly") or {}
        times = hourly_raw.get("time") or []
        t2m = hourly_raw.get("temperature_2m") or []
        precip = hourly_raw.get("precipitation") or []
        rh = hourly_raw.get("relative_humidity_2m") or []
        wspd = hourly_raw.get("wind_speed_10m") or []
        wcode = hourly_raw.get("weather_code") or []

        points: List[ForecastPoint] = []
        for i, t_str in enumerate(times):
            try:
                dt = datetime.fromisoformat(t_str)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
            except Exception:
                dt = datetime.now(tz=timezone.utc)

            code = wcode[i] if i < len(wcode) else None
            points.append(
                ForecastPoint(
                    timestamp=dt,
                    temperature=float(t2m[i]) if i < len(t2m) and t2m[i] is not None else None,
                    rainfall=float(precip[i]) if i < len(precip) and precip[i] is not None else None,
                    humidity=float(rh[i]) if i < len(rh) and rh[i] is not None else None,
                    wind_speed=float(wspd[i]) if i < len(wspd) and wspd[i] is not None else None,
                    weather_code=int(code) if code is not None else None,
                    weather_condition=self.map_wmo_code(code),
                )
            )

        provider_info = self.get_provider_info(model="ERA5 reanalysis")

        return HistoricalWeather(
            location=location_name or f"{lat:.2f}, {lon:.2f}",
            latitude=lat,
            longitude=lon,
            start_date=start_date,
            end_date=end_date,
            hourly=points,
            provider=provider_info,
        )

    async def health_check(self) -> bool:
        """Lightweight verification that Open-Meteo API is responsive."""
        client = self._get_client()
        should_close = self._external_client is None
        try:
            resp = await client.get(
                f"{self.base_url}/forecast",
                params={"latitude": 0.0, "longitude": 0.0, "current_weather": "true"},
            )
            self._is_healthy = resp.status_code == 200
            return self._is_healthy
        except Exception:
            self._is_healthy = False
            return False
        finally:
            if should_close:
                await client.aclose()
