export type PageId =
  | 'login'
  | 'dashboard'
  | 'ask-ai'
  | 'alerts'
  | 'profile'
  | 'settings'
  | 'advisory-farmers'
  | 'advisory-climate'
  | 'advisory-cyclone'
  | 'advisory-aviation'
  | 'advisory-marine';

export type TempUnit = 'C' | 'F';
export type WindUnit = 'kmh' | 'ms' | 'kts' | 'mph';
export type DataSource = 'IMD' | 'ECMWF' | 'NOAA' | 'NWP';

export interface UserPreferences {
  language: string;
  temperature_unit: TempUnit;
  wind_speed_unit: WindUnit;
  data_source: DataSource;
  red_alert_push: boolean;
  severe_sirens: boolean;
  sms_fallback: boolean;
  high_contrast: boolean;
  large_font: boolean;
  dark_mode: boolean;
  farmer_mode: boolean;
  sync_interval: number;
  cache_size_mb: number;
  cache_limit_mb: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  language: string;
  created_at: string;
}

export interface HourlyForecast {
  time: string;
  icon: string;
  temp: number;
  rainProb: number;
  isNow?: boolean;
  isHighlighted?: boolean;
}

export interface DayForecast {
  day: string;
  high: number;
  low: number;
  rainProb: number;
  consensusLabel: string;
  icon: string;
  barColor: string;
}

export interface TelemetryItem {
  icon: string;
  label: string;
  value: string;
  status: string;
  statusColor: string;
}

export interface WeatherAlert {
  id: string;
  severity: 'red' | 'orange' | 'yellow';
  title: string;
  region: string;
  description: string;
  validUntil: string;
  action: string;
  icon: string;
  source: string;
  issuedAt: string;
}
