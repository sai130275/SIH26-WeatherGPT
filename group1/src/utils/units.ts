import type { UserPreferences } from '@/types';

export function formatTemp(celsiusValue: number, prefs: UserPreferences | null): string {
  const unit = prefs?.temperature_unit || 'C';
  if (unit === 'F') {
    return `${Math.round((celsiusValue * 9) / 5 + 32)}°F`;
  }
  return `${Math.round(celsiusValue)}°C`;
}

export function formatWind(kmhValue: number, prefs: UserPreferences | null): string {
  const unit = prefs?.wind_speed_unit || 'kmh';
  if (unit === 'mph') {
    return `${(kmhValue * 0.621371).toFixed(1)} mph`;
  }
  return `${kmhValue.toFixed(1)} km/h`;
}

export function formatPrecip(mmValue: number, prefs: UserPreferences | null): string {
  const unit = prefs?.precip_unit || 'mm';
  if (unit === 'in') {
    return `${(mmValue * 0.0393701).toFixed(2)} in`;
  }
  return `${mmValue} mm`;
}

export function formatPressure(hpaValue: number, prefs: UserPreferences | null): string {
  const unit = prefs?.pressure_unit || 'hPa';
  if (unit === 'inHg') {
    return `${(hpaValue * 0.02953).toFixed(2)} inHg`;
  }
  return `${hpaValue.toFixed(1)} hPa`;
}
