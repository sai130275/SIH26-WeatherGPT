import type {
  HourlyForecast,
  DayForecast,
  TelemetryItem,
  WeatherAlert,
} from '@/types';

export const hourlyForecast: HourlyForecast[] = [
  { time: '12 PM', icon: 'partly_cloudy_day', temp: 32, rainProb: 20 },
  { time: '3 PM', icon: 'thunderstorm', temp: 34, rainProb: 65, isHighlighted: true },
  { time: '6 PM', icon: 'rainy', temp: 29, rainProb: 85 },
  { time: '9 PM', icon: 'cloudy', temp: 26, rainProb: 40 },
  { time: '12 AM', icon: 'clear_night', temp: 24, rainProb: 10 },
  { time: '3 AM', icon: 'clear_night', temp: 23, rainProb: 5 },
];

export const dayForecast: DayForecast[] = [
  { day: 'Today', high: 34, low: 25, rainProb: 85, consensusLabel: '85% (IMD/ECMWF)', icon: 'thunderstorm', barColor: 'bg-error' },
  { day: 'Thu, Oct 24', high: 31, low: 24, rainProb: 60, consensusLabel: '60% Consensus', icon: 'rainy', barColor: 'bg-secondary' },
  { day: 'Fri, Oct 25', high: 33, low: 24, rainProb: 30, consensusLabel: '30% Consensus', icon: 'partly_cloudy_day', barColor: 'bg-primary' },
  { day: 'Sat, Oct 26', high: 35, low: 25, rainProb: 15, consensusLabel: '15% Consensus', icon: 'sunny', barColor: 'bg-primary' },
  { day: 'Sun, Oct 27', high: 34, low: 24, rainProb: 20, consensusLabel: '20% Consensus', icon: 'partly_cloudy_day', barColor: 'bg-primary' },
];

export const telemetryData: TelemetryItem[] = [
  { icon: 'humidity_percentage', label: 'Humidity', value: '78%', status: 'Very Humid', statusColor: 'text-error' },
  { icon: 'air', label: 'Wind', value: '14 km/h', status: 'SW Vector', statusColor: 'text-secondary' },
  { icon: 'mobile_share_stack', label: 'AQI Index', value: '84', status: 'Moderate', statusColor: 'text-tertiary' },
  { icon: 'wb_sunny', label: 'UV Index', value: '6.2', status: 'High Risk', statusColor: 'text-tertiary' },
  { icon: 'speed', label: 'Pressure', value: '1012 hPa', status: 'Stable', statusColor: 'text-on-surface-variant' },
  { icon: 'visibility', label: 'Visibility', value: '8.5 km', status: 'Hazy Mist', statusColor: 'text-secondary' },
];

export const weatherAlerts: WeatherAlert[] = [
  {
    id: '1',
    severity: 'red',
    title: 'Thunderstorm & Lightning Hazard',
    region: 'Warangal Urban & Rural Districts',
    description: 'Heavy thunderstorm and lightning warning active for Warangal & surrounding districts. Severe wind gusts expected up to 45 km/h.',
    validUntil: '18:00 IST',
    action: 'Stay indoors, avoid open fields and water bodies.',
    icon: 'crisis_alert',
    source: 'IMD Hyderabad',
    issuedAt: '16:30 IST',
  },
  {
    id: '2',
    severity: 'orange',
    title: 'Heavy Rain Warning',
    region: 'Karimnagar & Khammam Districts',
    description: 'Heavy rainfall (64-115 mm) expected within 24 hours. Risk of localized waterlogging in low-lying areas.',
    validUntil: 'Tomorrow 06:00 IST',
    action: 'Avoid travel on waterlogged roads. Secure loose outdoor items.',
    icon: 'rainy',
    source: 'IMD Hyderabad',
    issuedAt: '15:00 IST',
  },
  {
    id: '3',
    severity: 'yellow',
    title: 'Heat Wave Advisory',
    region: 'Nalgonda & Mahabubnagar',
    description: 'Maximum temperatures likely to exceed 40°C. Moderate risk of heat-related illness for vulnerable populations.',
    validUntil: 'Oct 27 18:00 IST',
    action: 'Stay hydrated, avoid prolonged sun exposure between 11 AM - 4 PM.',
    icon: 'wb_sunny',
    source: 'IMD Hyderabad',
    issuedAt: '12:00 IST',
  },
  {
    id: '4',
    severity: 'orange',
    title: 'Cyclone Formation Alert',
    region: 'Bay of Bengal (Andhra Coast)',
    description: 'Low-pressure system intensifying. Likely to develop into a depression within 48 hours. Fishermen advised not to venture into sea.',
    validUntil: 'Oct 30 23:59 IST',
    action: 'Coastal residents prepare for strong winds. Follow evacuation orders if issued.',
    icon: 'cyclone',
    source: 'IMD Cyclone Warning Division',
    issuedAt: '14:00 IST',
  },
  {
    id: '5',
    severity: 'yellow',
    title: 'Fog Advisory',
    region: 'Adilabad & Northern Telangana',
    description: 'Dense fog expected in early morning hours. Visibility may drop below 200 meters on highways.',
    validUntil: 'Tomorrow 09:00 IST',
    action: 'Drive slowly with fog lights. Avoid highway travel before 8 AM.',
    icon: 'foggy',
    source: 'IMD Hyderabad',
    issuedAt: '05:30 IST',
  },
];

export const mapLayers = [
  { id: 'radar', icon: 'radar', label: 'Radar', active: true },
  { id: 'satellite', icon: 'satellite', label: 'Satellite' },
  { id: 'lightning', icon: 'bolt', label: 'Lightning' },
  { id: 'rain', icon: 'rainy', label: 'Rain' },
  { id: 'wind', icon: 'air', label: 'Wind' },
  { id: 'temp', icon: 'thermostat', label: 'Temp' },
  { id: 'aqi', icon: 'stream_apps', label: 'AQI' },
  { id: 'flood', icon: 'flood', label: 'Flood Risk' },
  { id: 'cyclone', icon: 'cyclone', label: 'Cyclone Track' },
];

export const timelineLabels = [
  'Now (17:42 IST)',
  '+1h (18:42 IST)',
  '+3h (20:42 IST)',
  '+6h (23:42 IST)',
  '+12h (05:42 IST)',
  '+24h (17:42 IST)',
];

export const timelineNodes = ['Now', '+1h', '+3h', '+6h', '+12h', '+24h'];

export const languages = [
  { code: 'en', label: 'English', native: 'English' },
  { code: 'hi', label: 'Hindi', native: 'हिन्दी' },
  { code: 'te', label: 'Telugu', native: 'తెలుగు' },
  { code: 'ta', label: 'Tamil', native: 'தமிழ்' },
  { code: 'bn', label: 'Bengali', native: 'বাংলা' },
  { code: 'mr', label: 'Marathi', native: 'मराठी' },
  { code: 'gu', label: 'Gujarati', native: 'ગુજરાતી' },
  { code: 'kn', label: 'Kannada', native: 'ಕನ್ನಡ' },
  { code: 'ml', label: 'Malayalam', native: 'മലയാളം' },
  { code: 'pa', label: 'Punjabi', native: 'ਪੰਜਾਬੀ' },
  { code: 'or', label: 'Odia', native: 'ଓଡ଼ିଆ' },
  { code: 'as', label: 'Assamese', native: 'অসমীয়া' },
  { code: 'ur', label: 'Urdu', native: 'اردو' },
];

export const roles = [
  'Disaster Manager & Agriculture Official',
  'Citizen',
  'Farmer',
  'Researcher',
  'Aviation / Marine',
  'Government Official',
];

export const locations = [
  { value: 'warangal', label: 'Warangal, Telangana (HQ)' },
  { value: 'hyderabad', label: 'Hyderabad, Telangana' },
  { value: 'delhi', label: 'New Delhi, NCR' },
  { value: 'mumbai', label: 'Mumbai, Maharashtra' },
  { value: 'bengaluru', label: 'Bengaluru, Karnataka' },
];

export const aiSuggestions = [
  'Will it rain in Warangal tomorrow?',
  'Cyclone risk for Andhra coast?',
  'Best time to spray pesticide today?',
  'Reservoir levels in Godavari basin?',
];

export const defaultPreferences = {
  language: 'en',
  temperature_unit: 'C' as const,
  wind_speed_unit: 'kmh' as const,
  precip_unit: 'mm' as const,
  pressure_unit: 'hPa' as const,
  data_source: 'Open-Meteo' as const,
  red_alert_push: true,
  severe_sirens: true,
  sms_fallback: false,
  high_contrast: false,
  large_font: false,
  dark_mode: false,
  farmer_mode: true,
  sync_interval: 30,
  cache_size_mb: 142,
  cache_limit_mb: 500,
};
