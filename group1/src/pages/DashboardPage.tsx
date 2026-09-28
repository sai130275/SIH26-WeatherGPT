import { useState, useEffect } from 'react';
import { Icon } from '@/components/Icon';
import { locations } from '@/data/mockData';
import { apiClient } from '@/lib/api';
import type { PageId, HourlyForecast, DayForecast, TelemetryItem } from '@/types';

interface DashboardPageProps {
  onNavigate: (page: PageId) => void;
  location: string;
  onLocationChange?: (location: string) => void;
}

const locationCoords: Record<string, { lat: number; lon: number }> = {
  warangal: { lat: 17.9689, lon: 79.5941 },
  hyderabad: { lat: 17.3850, lon: 78.4867 },
  delhi: { lat: 28.6139, lon: 77.2090 },
  mumbai: { lat: 19.0760, lon: 72.8777 },
  bengaluru: { lat: 12.9716, lon: 77.5946 },
};

const getWeatherIcon = (code: number): string => {
  if (code <= 3) return 'clear_day';
  if (code <= 49) return 'cloud';
  if (code <= 69) return 'rainy';
  if (code <= 79) return 'snowing';
  if (code <= 99) return 'thunderstorm';
  return 'partly_cloudy_day';
};

export function DashboardPage({ onNavigate, location, onLocationChange }: DashboardPageProps) {
  const [currentWeather, setCurrentWeather] = useState<any>(null);
  const [hourlyData, setHourlyData] = useState<HourlyForecast[]>([]);
  const [dailyData, setDailyData] = useState<DayForecast[]>([]);
  const [telemetry, setTelemetry] = useState<TelemetryItem[]>([]);
  const [severeAlert, setSevereAlert] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    const locValue = locations.find((l) => l.label === location || location.toLowerCase().includes(l.value))?.value || 'warangal';
    const coords = locationCoords[locValue] || locationCoords.warangal;

    const fetchData = async () => {
      setLoading(true);
      setError('');
      try {
        const [currentRes, forecastRes, alertsRes] = await Promise.all([
          apiClient.get(`/weather/current?lat=${coords.lat}&lon=${coords.lon}`),
          apiClient.get(`/weather/forecast?lat=${coords.lat}&lon=${coords.lon}&days=7`),
          apiClient.get(`/alerts?lat=${coords.lat}&lon=${coords.lon}`)
        ]);

        if (!active) return;

        const current = currentRes.data.data;
        const forecast = forecastRes.data.data;
        const alerts = alertsRes.data.data.alerts || [];

        const severe = alerts.find((a: any) => a.level === 'WARNING' || a.level === 'WATCH');
        setSevereAlert(severe || null);

        setCurrentWeather(current);

        setTelemetry([
          { icon: 'humidity_percentage', label: 'Humidity', value: `${current.humidity ?? 0}%`, status: (current.humidity ?? 0) > 75 ? 'High' : 'Normal', statusColor: (current.humidity ?? 0) > 75 ? 'text-error' : 'text-secondary' },
          { icon: 'air', label: 'Wind', value: `${current.wind_speed ?? 0} km/h`, status: 'Current', statusColor: 'text-secondary' },
          { icon: 'water_drop', label: 'Rain Prob', value: `${current.rain_probability ?? 0}%`, status: 'Forecast', statusColor: 'text-secondary' },
          { icon: 'visibility', label: 'Precip', value: `${current.precipitation ?? 0} mm`, status: 'Accumulation', statusColor: 'text-secondary' },
          { icon: 'compress', label: 'Pressure', value: `${current.pressure ?? 1013} hPa`, status: 'Surface', statusColor: 'text-secondary' },
          { icon: 'wb_sunny', label: 'UV Index', value: `${current.uv_index ?? 0}`, status: (current.uv_index ?? 0) > 6 ? 'High' : 'Moderate', statusColor: (current.uv_index ?? 0) > 6 ? 'text-error' : 'text-secondary' },
          { icon: 'visibility', label: 'Visibility', value: `${current.visibility ?? 10} km`, status: (current.visibility ?? 10) < 5 ? 'Low' : 'Clear', statusColor: (current.visibility ?? 10) < 5 ? 'text-error' : 'text-secondary' },
          { icon: 'speed', label: 'CAPE', value: `${current.cape ?? 0} J/kg`, status: 'Convective Energy', statusColor: 'text-tertiary' },
          { icon: 'bolt', label: 'Lightning', value: current.lightning ? 'Active' : 'Clear', status: 'Detection', statusColor: current.lightning ? 'text-error' : 'text-on-surface-variant' },
        ]);

        const mappedHourly = forecast.hourly.slice(0, 12).map((h: any, i: number) => ({
          time: new Date(h.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          icon: getWeatherIcon(h.weather_code),
          temp: Math.round(h.temperature),
          rainProb: h.rain_probability,
          isHighlighted: i === 1 // Just highlight second item like mock
        }));
        setHourlyData(mappedHourly);

        const mappedDaily = forecast.daily.map((d: any) => {
          const dateObj = new Date(d.date);
          const dayStr = dateObj.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' });
          return {
            day: dayStr,
            high: Math.round(d.max_temp),
            low: Math.round(d.min_temp),
            rainProb: d.max_rain_prob,
            consensusLabel: `${d.max_rain_prob}% (NWP)`,
            icon: getWeatherIcon(d.max_rain_prob > 50 ? 61 : 0),
            barColor: d.max_rain_prob >= 80 ? 'bg-error' : d.max_rain_prob >= 50 ? 'bg-secondary' : 'bg-primary'
          };
        });
        setDailyData(mappedDaily);
      } catch (err) {
        if (active) setError('Failed to load weather data');
      } finally {
        if (active) setLoading(false);
      }
    };

    fetchData();
    return () => { active = false; };
  }, [location]);

  if (loading) {
    return <div className="flex justify-center p-10"><div className="animate-spin text-secondary"><Icon name="sync" size={32} /></div></div>;
  }
  if (error) {
    return <div className="text-error p-10 text-center bg-error-container rounded-xl">{error}</div>;
  }
  return (
    <div className="flex flex-col w-full gap-space-md">
      {severeAlert && (
        <div 
          onClick={() => onNavigate('alerts')}
          className={`cursor-pointer bg-${severeAlert.level === 'WARNING' ? 'error' : 'tertiary'}-container text-on-${severeAlert.level === 'WARNING' ? 'error' : 'tertiary'}-container rounded-xl p-space-md flex flex-col gap-space-sm shadow-xl relative overflow-hidden transition-transform active:scale-[0.98]`}
        >
          <div className={`absolute -right-6 -bottom-6 w-32 h-32 bg-${severeAlert.level === 'WARNING' ? 'error' : 'tertiary'}/20 rounded-full blur-xl pointer-events-none`} />
          <div className="flex items-start justify-between gap-space-sm">
            <div className="flex items-center gap-space-sm">
              <div className={`w-10 h-10 rounded-full bg-${severeAlert.level === 'WARNING' ? 'error' : 'tertiary'} text-on-${severeAlert.level === 'WARNING' ? 'error' : 'tertiary'} flex items-center justify-center animate-pulse`}>
                <Icon name="crisis_alert" size={22} filled />
              </div>
              <div>
                <span className={`text-label-sm uppercase tracking-wider text-${severeAlert.level === 'WARNING' ? 'error' : 'tertiary'} font-bold block`}>
                  {severeAlert.level === 'WARNING' ? 'Red Alert' : 'Orange Alert'} • {severeAlert.sourceType}
                </span>
                <h2 className={`text-headline-sm text-on-${severeAlert.level === 'WARNING' ? 'error' : 'tertiary'}-container`}>{severeAlert.title}</h2>
              </div>
            </div>
            <span className={`text-mono-data bg-${severeAlert.level === 'WARNING' ? 'error' : 'tertiary'}/30 px-space-sm py-1 rounded text-on-${severeAlert.level === 'WARNING' ? 'error' : 'tertiary'}-container`}>
              Next 12 Hours
            </span>
          </div>
          <p className={`text-body-sm text-on-${severeAlert.level === 'WARNING' ? 'error' : 'tertiary'}-container/90 leading-relaxed`}>
            {severeAlert.description}
          </p>
          <div className={`bg-${severeAlert.level === 'WARNING' ? 'error' : 'tertiary'}/20 rounded-lg p-space-sm flex items-center gap-space-sm`}>
            <Icon name="security" size={20} className={`text-${severeAlert.level === 'WARNING' ? 'error' : 'tertiary'}`} />
            <span className="text-body-sm font-medium">Recommended Action: {severeAlert.disclaimer}</span>
          </div>
        </div>
      )}

      {/* Current Weather Card */}
      <div className="bg-surface-container rounded-xl p-space-md flex flex-col gap-space-md shadow-md">
        <div className="flex justify-between items-start">
          <div>
            <div className="flex items-center gap-space-xs text-secondary text-label-md">
              <Icon name="schedule" size={16} />
              <span>Live Telemetry • Updated 2m ago</span>
            </div>
            <div className="flex items-baseline gap-space-sm mt-space-xs">
              <span className="text-headline-xl text-on-surface">{Math.round(currentWeather?.temperature || 0)}°C</span>
              <span className="text-body-md text-on-surface-variant">Feels like {Math.round((currentWeather?.temperature || 0) + 1)}°C</span>
            </div>
            <p className="text-body-md text-on-surface font-medium mt-space-xs">
              {currentWeather?.weather_condition || 'Clear sky'}
            </p>
          </div>
          <div className="w-16 h-16 rounded-2xl bg-surface-variant flex items-center justify-center text-secondary">
            <Icon name={getWeatherIcon(currentWeather?.weather_code || 0)} size={36} filled />
          </div>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-space-sm pt-space-sm border-t border-outline-variant/20">
          {telemetry.map((item) => (
            <div key={item.label} className="bg-surface rounded-lg p-space-sm flex flex-col">
              <span className="text-label-sm text-on-surface-variant flex items-center gap-1">
                <Icon name={item.icon} size={14} />
                {item.label}
              </span>
              <span className="text-mono-data text-on-surface font-bold text-lg mt-1">{item.value}</span>
              <span className={`text-label-sm ${item.statusColor}`}>{item.status}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Hourly Forecast */}
      <div className="bg-surface-container rounded-xl p-space-md">
        <div className="flex items-center justify-between mb-space-sm">
          <h3 className="text-headline-sm text-on-surface">Hourly Timeline</h3>
          <span className="text-label-sm text-secondary">Next 24 Hours</span>
        </div>
        <div className="flex gap-space-sm overflow-x-auto pb-space-xs no-scrollbar">
          {hourlyData.map((hour, i) => (
            <div
              key={i}
              className={`flex flex-col items-center justify-between rounded-xl p-space-sm min-w-[76px] shrink-0 ${
                hour.isHighlighted
                  ? 'bg-secondary-container text-on-secondary-container shadow-md'
                  : 'bg-surface-variant/40'
              }`}
            >
              <span className={`text-label-sm ${hour.isHighlighted ? 'font-bold' : 'text-on-surface-variant'}`}>
                {hour.time}
              </span>
              <Icon
                name={hour.icon}
                size={24}
                filled={hour.isHighlighted}
                className={`my-2 ${hour.isHighlighted ? '' : 'text-secondary'}`}
              />
              <span className="text-mono-data font-bold text-on-surface">{hour.temp}°C</span>
              <span
                className={`text-label-sm mt-1 ${
                  hour.rainProb >= 80
                    ? 'text-error font-semibold'
                    : hour.isHighlighted
                    ? 'font-semibold'
                    : 'text-secondary'
                }`}
              >
                {hour.rainProb}%
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* 7-Day Forecast */}
      <div className="bg-surface-container rounded-xl p-space-md flex flex-col gap-space-md">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-headline-sm text-on-surface">7-Day Outlook</h3>
            <span className="text-label-sm text-on-surface-variant">NWP Model Consensus (GFS, ECMWF, IMD)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-secondary" />
            <span className="text-label-sm text-secondary font-medium">Synced</span>
          </div>
        </div>
        <div className="flex flex-col gap-space-sm">
          {dailyData.map((day, i) => (
            <div key={i} className="bg-surface rounded-lg p-space-sm flex items-center justify-between">
              <div className="w-24">
                <span className="text-body-md font-medium text-on-surface block">{day.day}</span>
                <span className="text-label-sm text-secondary">High {day.high}° / Low {day.low}°</span>
              </div>
              <div className="flex-1 mx-space-md">
                <div className="flex justify-between text-label-sm mb-1 text-on-surface-variant">
                  <span>Rain Probability</span>
                  <span
                    className={`font-semibold ${
                      day.rainProb >= 80
                        ? 'text-error'
                        : day.rainProb >= 50
                        ? 'text-secondary'
                        : 'text-on-surface-variant'
                    }`}
                  >
                    {day.consensusLabel}
                  </span>
                </div>
                <div className="w-full bg-surface-variant h-2 rounded-full overflow-hidden">
                  <div
                    className={`${day.barColor} h-full rounded-full transition-all`}
                    style={{ width: `${day.rainProb}%` }}
                  />
                </div>
              </div>
              <Icon
                name={day.icon}
                size={24}
                className={
                  day.rainProb >= 80
                    ? 'text-error'
                    : day.rainProb >= 50
                    ? 'text-secondary'
                    : 'text-on-surface-variant'
                }
              />
            </div>
          ))}
        </div>
      </div>

      {/* Quick Access Specialist Cards */}
      <div className="grid grid-cols-2 gap-space-sm">
        {[
          {
            icon: 'agriculture',
            title: 'Farmer Advisory',
            desc: 'Paddy crop protection & pesticide application advisories for Warangal rural.',
            bgColor: 'bg-secondary/20',
            textColor: 'text-secondary',
            action: 'advisory-farmers',
            actionText: 'View Advisory',
          },
          {
            icon: 'cyclone',
            title: 'Cyclone Tracker',
            desc: 'Bay of Bengal depression monitoring & inland wind trajectory prediction.',
            bgColor: 'bg-error/20',
            textColor: 'text-error',
            action: 'advisory-cyclone',
            actionText: 'Open Radar',
          },
          {
            icon: 'analytics',
            title: 'Climate Analytics',
            desc: 'Decadal temperature anomalies & monsoon progression charts.',
            bgColor: 'bg-primary/20',
            textColor: 'text-primary',
            action: 'advisory-climate',
            actionText: 'Explore Stats',
          },
          {
            icon: 'flight_takeoff',
            title: 'Aviation',
            desc: 'Ceiling heights, visibility, & crosswind vectors.',
            bgColor: 'bg-secondary-container/30',
            textColor: 'text-secondary',
            action: 'advisory-aviation',
            actionText: 'Check Metrics',
          },
          {
            icon: 'sailing',
            title: 'Marine',
            desc: 'Sea state, wave heights, and reservoir water level feeds.',
            bgColor: 'bg-tertiary/20',
            textColor: 'text-tertiary',
            action: 'advisory-marine',
            actionText: 'Check Metrics',
          },
        ].map((card) => (
          <button
            key={card.title}
            onClick={() => onNavigate(card.action as PageId)}
            className="bg-surface-container rounded-xl p-space-md flex flex-col justify-between hover:bg-surface-variant/60 transition-all cursor-pointer text-left"
          >
            <div>
              <div className={`w-10 h-10 rounded-xl ${card.bgColor} flex items-center justify-center ${card.textColor} mb-space-sm`}>
                <Icon name={card.icon} size={20} />
              </div>
              <h4 className="text-headline-sm text-on-surface">{card.title}</h4>
              <p className="text-body-sm text-on-surface-variant mt-space-xs">{card.desc}</p>
            </div>
            <div className="flex items-center gap-1 text-secondary text-label-md font-medium mt-space-md">
              <span>{card.actionText}</span>
              <Icon name="arrow_forward" size={16} />
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
