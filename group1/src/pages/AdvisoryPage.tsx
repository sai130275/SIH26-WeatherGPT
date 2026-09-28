import { Icon } from '@/components/Icon';
import type { PageId } from '@/types';

interface AdvisoryPageProps {
  mode: 'farmers' | 'climate' | 'cyclone' | 'aviation' | 'marine';
  onNavigate: (page: PageId) => void;
}

const advisoryConfig = {
  farmers: { title: 'Farmer Advisory', icon: 'agriculture', desc: 'Agricultural weather guidance', color: 'text-secondary', bg: 'bg-secondary' },
  climate: { title: 'Climate Analytics', icon: 'analytics', desc: 'Long-term climate trends', color: 'text-primary', bg: 'bg-primary' },
  cyclone: { title: 'Cyclone Tracker', icon: 'cyclone', desc: 'Severe storm monitoring', color: 'text-error', bg: 'bg-error' },
  aviation: { title: 'Aviation Metrics', icon: 'flight_takeoff', desc: 'Flight visibility & winds', color: 'text-secondary', bg: 'bg-secondary' },
  marine: { title: 'Marine State', icon: 'sailing', desc: 'Sea state & wave heights', color: 'text-tertiary', bg: 'bg-tertiary' },
};

export function AdvisoryPage({ mode, onNavigate }: AdvisoryPageProps) {
  const config = advisoryConfig[mode];

  return (
    <div className="flex flex-col w-full h-full">
      <div className="flex items-center gap-space-sm mb-space-lg">
        <button 
          onClick={() => onNavigate('dashboard')} 
          className="w-10 h-10 rounded-full bg-surface-container flex items-center justify-center text-on-surface hover:bg-surface-variant transition-colors cursor-pointer"
        >
          <Icon name="arrow_back" size={20} />
        </button>
        <div>
          <h2 className="text-headline-sm text-on-surface">{config.title}</h2>
          <p className="text-body-sm text-on-surface-variant">{config.desc}</p>
        </div>
      </div>

      <div className="flex-1 flex flex-col items-center justify-center py-20 text-center">
        <div className={`w-20 h-20 rounded-full ${config.bg}/20 flex items-center justify-center ${config.color} mb-space-md`}>
          <Icon name={config.icon} size={40} />
        </div>
        <h3 className="text-headline-md text-on-surface mb-space-sm">Data Coming Soon</h3>
        <p className="text-body-md text-on-surface-variant max-w-sm">
          Detailed {config.title.toLowerCase()} metrics and intelligent recommendations are currently being integrated with the Group 3 forecasting engine.
        </p>
      </div>
    </div>
  );
}
