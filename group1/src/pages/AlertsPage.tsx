import { useState, useEffect } from 'react';
import { Icon } from '@/components/Icon';
import { apiClient } from '@/lib/api';
import { locations } from '@/data/mockData';
import type { WeatherAlert } from '@/types';

interface AlertsPageProps {
  location: string;
}

const severityConfig: Record<
  WeatherAlert['severity'],
  { bg: string; text: string; border: string; badge: string; iconBg: string; label: string }
> = {
  red: {
    bg: 'bg-error-container',
    text: 'text-on-error-container',
    border: 'border-error/30',
    badge: 'bg-error text-on-error',
    iconBg: 'bg-error text-on-error',
    label: 'Red Alert',
  },
  orange: {
    bg: 'bg-tertiary-container',
    text: 'text-on-tertiary-container',
    border: 'border-tertiary/30',
    badge: 'bg-tertiary text-on-tertiary',
    iconBg: 'bg-tertiary text-on-tertiary',
    label: 'Orange Warning',
  },
  yellow: {
    bg: 'bg-secondary-fixed',
    text: 'text-on-secondary-fixed',
    border: 'border-secondary/30',
    badge: 'bg-secondary text-on-secondary',
    iconBg: 'bg-secondary text-on-secondary',
    label: 'Yellow Advisory',
  },
};

const locationCoords: Record<string, { lat: number; lon: number }> = {
  warangal: { lat: 17.9689, lon: 79.5941 },
  hyderabad: { lat: 17.3850, lon: 78.4867 },
  delhi: { lat: 28.6139, lon: 77.2090 },
  mumbai: { lat: 19.0760, lon: 72.8777 },
  bengaluru: { lat: 12.9716, lon: 77.5946 },
};

export function AlertsPage({ location }: AlertsPageProps) {
  const [alerts, setAlerts] = useState<WeatherAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Filter state
  const [activeFilter, setActiveFilter] = useState<'all' | 'red' | 'orange' | 'yellow'>('all');
  
  // Modal state
  const [selectedAlert, setSelectedAlert] = useState<WeatherAlert | null>(null);

  const fetchAlerts = async (activeObj = { active: true }) => {
    setLoading(true);
    setError('');
    try {
      const locValue = locations.find((l) => l.label === location || location.toLowerCase().includes(l.value))?.value || 'warangal';
      const coords = locationCoords[locValue] || locationCoords.warangal;

      const res = await apiClient.get(`/alerts?lat=${coords.lat}&lon=${coords.lon}`);
      if (!activeObj.active) return;
      const apiAlerts = res.data.data.alerts || [];
      
      const now = new Date();
      const mappedAlerts: WeatherAlert[] = [];

      for (let i = 0; i < apiAlerts.length; i++) {
        const a = apiAlerts[i];
        
        // Exclude if expired (using expiresAt from DB)
        if (a.expiresAt) {
          const expiresDate = new Date(a.expiresAt);
          if (expiresDate < now) continue;
        }

        mappedAlerts.push({
          id: a.id || a._id || `alert-${i}`,
          severity: a.level === 'WARNING' ? 'red' : a.level === 'WATCH' ? 'orange' : 'yellow',
          title: a.title || 'Weather Alert',
          region: location || 'Local Area',
          description: a.description || 'No additional details provided.',
          validUntil: a.expiresAt ? new Date(a.expiresAt).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' }) : 'Until further notice',
          action: a.disclaimer || 'Take necessary precautions.',
          icon: a.title?.toLowerCase().includes('rain') ? 'rainy' : 'crisis_alert',
          source: a.sourceType || 'Weather Service',
          issuedAt: a.createdAt ? new Date(a.createdAt).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' }) : new Date().toLocaleString([], { dateStyle: 'short', timeStyle: 'short' }),
        });
      }
      setAlerts(mappedAlerts);
    } catch (err) {
      if (activeObj.active) setError('Failed to load alerts');
    } finally {
      if (activeObj.active) setLoading(false);
    }
  };

  useEffect(() => {
    const activeObj = { active: true };
    fetchAlerts(activeObj);
    return () => { activeObj.active = false; };
  }, [location]);

  // Handle keyboard escape for modal
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setSelectedAlert(null);
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const filteredAlerts = alerts.filter(a => activeFilter === 'all' || a.severity === activeFilter);
  const activeCount = alerts.filter((a) => a.severity === 'red' || a.severity === 'orange').length;

  if (loading) {
    return <div className="flex justify-center p-10"><div className="animate-spin text-secondary"><Icon name="sync" size={32} /></div></div>;
  }
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center p-10 gap-space-md">
        <div className="text-error bg-error-container rounded-xl p-space-md shadow-md">{error}</div>
        <button onClick={() => fetchAlerts()} className="flex items-center gap-2 text-primary hover:underline">
          <Icon name="refresh" size={20} /> Retry
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col w-full gap-space-md pb-10 relative">
      {/* Summary Header */}
      <div className="bg-surface-container rounded-xl p-space-md flex items-center justify-between shadow-sm">
        <div>
          <h2 className="font-headline-md text-on-surface">Active Alerts for {location}</h2>
          <p className="text-body-sm text-secondary mt-space-xs">
            {activeCount} severe warnings • {alerts.length} total active
          </p>
        </div>
        <button 
          onClick={() => fetchAlerts()}
          className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary hover:bg-primary/20 transition-colors"
          title="Refresh Alerts"
        >
          <Icon name="refresh" size={22} />
        </button>
      </div>

      {/* Filter Pills */}
      <div className="overflow-x-auto no-scrollbar -mx-gutter px-gutter">
        <div className="flex gap-space-xs pb-space-xs shrink-0 w-max">
          <button 
            onClick={() => setActiveFilter('all')}
            className={`px-space-md py-1.5 rounded-full text-label-md font-medium shadow-sm transition-colors ${activeFilter === 'all' ? 'bg-primary text-on-primary' : 'bg-surface-container-high text-on-surface-variant hover:text-on-surface'}`}
          >
            All Alerts ({alerts.length})
          </button>
          <button 
            onClick={() => setActiveFilter('red')}
            className={`px-space-md py-1.5 rounded-full text-label-md font-medium shadow-sm transition-colors ${activeFilter === 'red' ? 'bg-error text-on-error' : 'bg-surface-container-high text-on-surface-variant hover:text-on-surface'}`}
          >
            Red ({alerts.filter(a => a.severity === 'red').length})
          </button>
          <button 
            onClick={() => setActiveFilter('orange')}
            className={`px-space-md py-1.5 rounded-full text-label-md font-medium shadow-sm transition-colors ${activeFilter === 'orange' ? 'bg-tertiary text-on-tertiary' : 'bg-surface-container-high text-on-surface-variant hover:text-on-surface'}`}
          >
            Orange ({alerts.filter(a => a.severity === 'orange').length})
          </button>
          <button 
            onClick={() => setActiveFilter('yellow')}
            className={`px-space-md py-1.5 rounded-full text-label-md font-medium shadow-sm transition-colors ${activeFilter === 'yellow' ? 'bg-secondary text-on-secondary' : 'bg-surface-container-high text-on-surface-variant hover:text-on-surface'}`}
          >
            Yellow ({alerts.filter(a => a.severity === 'yellow').length})
          </button>
        </div>
      </div>

      {/* Alert Cards */}
      {filteredAlerts.length === 0 && (
        <div className="bg-surface-container rounded-xl p-space-xl flex flex-col items-center justify-center text-center shadow-sm">
          <Icon name="check_circle" size={48} className="text-secondary mb-space-sm opacity-50" />
          <h3 className="font-headline-sm text-on-surface mb-1">No active alerts</h3>
          <p className="text-body-md text-on-surface-variant">
            There are no {activeFilter !== 'all' ? activeFilter : ''} active alerts for this location.
          </p>
        </div>
      )}
      
      {filteredAlerts.map((alert) => {
        const config = severityConfig[alert.severity];
        return (
          <div
            key={alert.id}
            onClick={() => setSelectedAlert(alert)}
            className={`${config.bg} ${config.text} rounded-xl p-space-md flex flex-col gap-space-sm shadow-md relative overflow-hidden cursor-pointer hover:shadow-lg transition-shadow active:scale-[0.99]`}
          >
            <div className="absolute -right-6 -bottom-6 w-24 h-24 bg-current opacity-10 rounded-full blur-xl pointer-events-none" />
            <div className="flex items-start justify-between gap-space-sm">
              <div className="flex items-center gap-space-sm">
                <div
                  className={`w-10 h-10 rounded-full ${config.iconBg} flex items-center justify-center ${
                    alert.severity === 'red' ? 'animate-pulse' : ''
                  }`}
                >
                  <Icon name={alert.icon} size={22} filled />
                </div>
                <div>
                  <span className="text-label-sm uppercase tracking-wider font-bold block opacity-80">
                    {config.label}
                  </span>
                  <h3 className="text-headline-sm line-clamp-1">{alert.title}</h3>
                </div>
              </div>
            </div>
            <p className="text-body-sm opacity-90 leading-relaxed line-clamp-2 mt-1">{alert.description}</p>
            <div className="flex items-center justify-between pt-2 mt-1 border-t border-current/20 text-label-md">
              <div className="flex items-center gap-space-xs font-bold">
                <Icon name="schedule" size={14} />
                <span>Until: {alert.validUntil}</span>
              </div>
              <div className="flex items-center gap-space-xs font-medium bg-black/10 px-2 py-0.5 rounded">
                <span>Details</span>
                <Icon name="chevron_right" size={16} />
              </div>
            </div>
          </div>
        );
      })}

      {/* Detail Modal Overlay */}
      {selectedAlert && (
        <div className="fixed inset-0 z-50 flex items-center justify-center px-4 animate-in fade-in duration-200">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setSelectedAlert(null)} />
          <div className={`relative w-full max-w-md rounded-2xl p-space-lg shadow-2xl flex flex-col gap-space-md ${severityConfig[selectedAlert.severity].bg} ${severityConfig[selectedAlert.severity].text} animate-in zoom-in-95 duration-200 max-h-[90vh] overflow-y-auto`}>
            <button 
              onClick={() => setSelectedAlert(null)}
              className="absolute top-4 right-4 w-8 h-8 rounded-full bg-black/10 flex items-center justify-center hover:bg-black/20 transition-colors"
            >
              <Icon name="close" size={20} />
            </button>
            
            <div className="flex items-center gap-space-sm pr-8">
              <div className={`w-12 h-12 rounded-full ${severityConfig[selectedAlert.severity].iconBg} flex items-center justify-center shadow-inner shrink-0`}>
                <Icon name={selectedAlert.icon} size={28} filled />
              </div>
              <div>
                <span className="text-label-sm uppercase tracking-widest font-bold block opacity-80 mb-0.5">
                  {severityConfig[selectedAlert.severity].label}
                </span>
                <h2 className="text-headline-md leading-tight">{selectedAlert.title}</h2>
              </div>
            </div>

            <div className="bg-black/5 rounded-xl p-space-md flex flex-col gap-space-sm my-1">
              <div className="flex items-start gap-space-sm">
                <Icon name="location_on" size={18} className="mt-0.5 opacity-80" />
                <div>
                  <span className="text-label-sm font-bold uppercase opacity-70 block">Affected Area</span>
                  <span className="text-body-md font-medium">{selectedAlert.region}</span>
                </div>
              </div>
              <div className="w-full h-px bg-current/10 my-1" />
              <div className="flex items-start gap-space-sm">
                <Icon name="schedule" size={18} className="mt-0.5 opacity-80" />
                <div className="flex flex-col gap-1 w-full">
                  <div className="flex justify-between items-center">
                    <span className="text-label-sm font-bold uppercase opacity-70">Issued</span>
                    <span className="text-label-sm font-medium">{selectedAlert.issuedAt}</span>
                  </div>
                  <div className="flex justify-between items-center text-error font-bold">
                    <span className="text-label-sm uppercase opacity-90">Expires</span>
                    <span className="text-label-sm">{selectedAlert.validUntil}</span>
                  </div>
                </div>
              </div>
            </div>

            <div>
              <span className="text-label-sm font-bold uppercase opacity-70 block mb-1">Description</span>
              <p className="text-body-md opacity-90 leading-relaxed whitespace-pre-wrap">
                {selectedAlert.description}
              </p>
            </div>

            <div className="bg-black/10 border border-current/20 rounded-xl p-space-md flex flex-col gap-2 mt-2">
              <span className="text-label-sm font-bold uppercase opacity-70 flex items-center gap-1">
                <Icon name="security" size={16} /> Action Required
              </span>
              <p className="text-body-md font-medium">
                {selectedAlert.action}
              </p>
            </div>

            <div className="flex items-center justify-center pt-2 text-label-md opacity-70">
              <Icon name="hub" size={14} className="mr-1" />
              Source: {selectedAlert.source}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
