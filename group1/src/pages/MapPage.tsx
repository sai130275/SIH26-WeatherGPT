import { useState, useEffect } from 'react';
import { Icon } from '@/components/Icon';
import type { PageId } from '@/types';
import { apiClient } from '@/lib/api';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import { usePreferences } from '@/context/PreferencesContext';
import { formatTemp, formatWind, formatPrecip, formatPressure } from '@/utils/units';
import { locations } from '@/data/mockData';

interface MapPageProps {
  mode: 'farmer' | 'cyclone' | 'aviation' | 'marine' | 'climate';
  onNavigate: (page: PageId) => void;
  location: string;
}

const locationCoords: Record<string, { lat: number; lon: number }> = {
  warangal: { lat: 17.9689, lon: 79.5941 },
  hyderabad: { lat: 17.3850, lon: 78.4867 },
  delhi: { lat: 28.6139, lon: 77.2090 },
  mumbai: { lat: 19.0760, lon: 72.8777 },
  bengaluru: { lat: 12.9716, lon: 77.5946 },
};

// Fix default marker icon issues with leaflet in React
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const modes = [
  { id: 'farmer', label: 'Farmer', icon: 'agriculture' },
  { id: 'cyclone', label: 'Cyclone', icon: 'cyclone' },
  { id: 'aviation', label: 'Aviation', icon: 'flight_takeoff' },
  { id: 'marine', label: 'Marine', icon: 'sailing' },
];

function MapUpdater({ center }: { center: [number, number] }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center, map.getZoom());
  }, [center, map]);
  return null;
}

export function MapPage({ mode: initialMode, onNavigate, location }: MapPageProps) {
  const { preferences } = usePreferences();
  const [activeMode, setActiveMode] = useState(initialMode === 'climate' ? 'farmer' : initialMode);
  const [currentWeather, setCurrentWeather] = useState<any>(null);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const locValue = locations.find((l) => l.label === location || location.toLowerCase().includes(l.value))?.value || 'warangal';
  const coords = locationCoords[locValue] || locationCoords.warangal;

  useEffect(() => {
    let active = true;

    const fetchData = async () => {
      setLoading(true);
      setError('');
      try {
        const [currentRes, alertsRes] = await Promise.all([
          apiClient.get(`/weather/current?lat=${coords.lat}&lon=${coords.lon}`),
          apiClient.get(`/alerts?lat=${coords.lat}&lon=${coords.lon}`)
        ]);

        if (!active) return;
        setCurrentWeather(currentRes.data.data);
        setAlerts(alertsRes.data.data.alerts || []);
      } catch (err: any) {
        if (!active) return;
        console.error(err);
        setError('Failed to fetch weather data for the map.');
      } finally {
        if (active) setLoading(false);
      }
    };

    fetchData();

    return () => {
      active = false;
    };
  }, [coords.lat, coords.lon]);

  const renderMetrics = () => {
    if (!currentWeather) return null;
    const c = currentWeather;

    switch (activeMode) {
      case 'farmer':
        return (
          <>
            <Metric label="Temperature" value={formatTemp(c.temperature ?? 0, preferences)} icon="thermostat" />
            <Metric label="Rain Prob" value={`${c.rain_probability ?? 0}%`} icon="water_drop" />
            <Metric label="Precipitation" value={formatPrecip(c.precipitation ?? 0, preferences)} icon="rainy" />
            <Metric label="Humidity" value={`${c.humidity ?? 0}%`} icon="humidity_percentage" />
            <Metric label="Wind Speed" value={formatWind(c.wind_speed ?? 0, preferences)} icon="air" />
            <Metric label="UV Index" value={`${c.uv_index ?? 0}`} icon="wb_sunny" />
            <div className="col-span-2 mt-2">
              <span className="text-label-sm text-on-surface-variant block mb-1">Advisory</span>
              <span className="text-body-sm">
                {(c.rain_probability ?? 0) > 50 ? 'High chance of rain. Delay pesticide application.' : 'Favorable conditions for farming activities.'}
              </span>
            </div>
          </>
        );
      case 'cyclone':
        return (
          <>
            <Metric label="Wind Speed" value={formatWind(c.wind_speed ?? 0, preferences)} icon="air" />
            <Metric label="Pressure" value={formatPressure(c.pressure ?? 1013, preferences)} icon="compress" />
            <Metric label="Rainfall" value={formatPrecip(c.precipitation ?? 0, preferences)} icon="rainy" />
            <Metric label="Alerts" value={alerts.length > 0 ? `${alerts.length} Active` : 'None'} icon="warning" color={alerts.length > 0 ? 'text-error' : 'text-secondary'} />
            <div className="col-span-2 mt-2">
              <span className="text-label-sm text-on-surface-variant block mb-1">Risk Info</span>
              <span className="text-body-sm">
                {alerts.length > 0 ? 'Severe weather warnings in effect. Check alerts.' : 'No active cyclonic risks in this region.'}
              </span>
            </div>
          </>
        );
      case 'aviation':
        return (
          <>
            <Metric label="Wind Speed" value={formatWind(c.wind_speed ?? 0, preferences)} icon="air" />
            <Metric label="Visibility" value={`${c.visibility ?? 10} km`} icon="visibility" />
            <Metric label="Precipitation" value={formatPrecip(c.precipitation ?? 0, preferences)} icon="rainy" />
            <Metric label="Pressure" value={formatPressure(c.pressure ?? 1013, preferences)} icon="compress" />
            <div className="col-span-2 mt-2">
              <span className="text-label-sm text-on-surface-variant block mb-1">Aviation Risk</span>
              <span className="text-body-sm">
                {c.lightning ? 'Thunderstorms detected in the vicinity. Expect turbulence.' : (c.visibility ?? 10) < 5 ? 'Low visibility conditions (IFR).' : 'VFR conditions prevailing.'}
              </span>
            </div>
          </>
        );
      case 'marine':
        return (
          <>
            <Metric label="Wind Speed" value={formatWind(c.wind_speed ?? 0, preferences)} icon="air" />
            <Metric label="Pressure" value={formatPressure(c.pressure ?? 1013, preferences)} icon="compress" />
            <Metric label="Rainfall" value={formatPrecip(c.precipitation ?? 0, preferences)} icon="rainy" />
            <Metric label="Visibility" value={`${c.visibility ?? 10} km`} icon="visibility" />
            <div className="col-span-2 mt-2">
              <span className="text-label-sm text-on-surface-variant block mb-1">Marine Risk</span>
              <span className="text-body-sm">
                {(c.wind_speed ?? 0) > 40 ? 'Small craft advisory. Rough seas expected.' : 'Normal marine conditions.'}
              </span>
            </div>
          </>
        );
    }
  };

  return (
    <div className="flex flex-col w-full h-full pb-8">
      {/* Header */}
      <div className="flex items-center gap-space-sm mb-space-md mt-space-sm">
        <button 
          onClick={() => onNavigate('dashboard')} 
          className="w-10 h-10 rounded-full bg-surface-container flex items-center justify-center text-on-surface hover:bg-surface-variant transition-colors cursor-pointer"
        >
          <Icon name="arrow_back" size={20} />
        </button>
        <h2 className="text-headline-sm text-on-surface">Interactive Map</h2>
      </div>

      {/* Mode Selector */}
      <div className="overflow-x-auto no-scrollbar -mx-gutter px-gutter mb-space-md">
        <div className="flex gap-space-xs pb-space-xs shrink-0 w-max">
          {modes.map((m) => (
            <button
              key={m.id}
              onClick={() => setActiveMode(m.id as any)}
              className={`flex items-center gap-space-xs px-space-md py-space-sm rounded-full text-label-md transition-all ${
                activeMode === m.id
                  ? 'bg-secondary text-on-secondary font-semibold shadow-sm'
                  : 'bg-surface-container-high hover:bg-surface-container-highest text-on-surface-variant'
              }`}
            >
              <Icon name={m.icon} size={16} filled={activeMode === m.id} />
              {m.label}
            </button>
          ))}
        </div>
      </div>

      {/* Map Container */}
      <div className="relative w-full h-[400px] rounded-xl overflow-hidden bg-surface-container-lowest shadow-lg mb-space-md z-0">
        <MapContainer center={[coords.lat, coords.lon]} zoom={10} style={{ height: '100%', width: '100%', zIndex: 0 }} zoomControl={false}>
          <MapUpdater center={[coords.lat, coords.lon]} />
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          />
          <Marker position={[coords.lat, coords.lon]}>
            <Popup>
              {location} <br /> {coords.lat.toFixed(2)}, {coords.lon.toFixed(2)}
            </Popup>
          </Marker>
        </MapContainer>

        {/* Map Controls Overlay */}
        <div className="absolute bottom-4 right-4 z-[400] flex flex-col gap-2">
           <div className="bg-surface/90 backdrop-blur-md px-3 py-1.5 rounded-lg shadow-sm text-label-sm font-mono-data text-secondary flex items-center gap-2 border border-outline-variant">
              <Icon name="my_location" size={14} />
              {location}
           </div>
        </div>
      </div>

      {/* Mode-specific Metrics Card */}
      <div className="bg-surface-container-low rounded-xl p-space-md shadow-sm relative overflow-hidden">
        {loading && (
          <div className="absolute inset-0 bg-surface-container-low/80 backdrop-blur-sm z-10 flex items-center justify-center">
            <span className="text-on-surface font-semibold animate-pulse">Loading Map Data...</span>
          </div>
        )}
        {error && (
          <div className="absolute inset-0 bg-error-container/90 backdrop-blur-sm z-10 flex items-center justify-center p-4 text-center text-on-error-container">
            {error}
          </div>
        )}
        
        <div className="flex items-center gap-2 mb-4 pb-2 border-b border-outline-variant">
          <Icon name={modes.find(m => m.id === activeMode)?.icon || 'public'} size={20} className="text-primary" />
          <h3 className="text-title-md font-semibold text-on-surface capitalize">{activeMode} Telemetry</h3>
        </div>

        <div className="grid grid-cols-2 gap-4">
          {renderMetrics()}
        </div>
      </div>
    </div>
  );
}

function Metric({ label, value, icon, color = 'text-primary' }: { label: string; value: string | number; icon: string; color?: string }) {
  return (
    <div className="flex flex-col">
      <div className="flex items-center gap-1.5 mb-1">
        <Icon name={icon} size={16} className={color} />
        <span className="text-label-sm text-on-surface-variant">{label}</span>
      </div>
      <span className="text-body-lg font-semibold text-on-surface">{value}</span>
    </div>
  );
}
