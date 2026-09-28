import { Icon } from '@/components/Icon';
import type { PageId } from '@/types';

interface BottomNavProps {
  active: PageId;
  onNavigate: (page: PageId) => void;
}

const navItems: { id: PageId; icon: string; label: string }[] = [
  { id: 'dashboard', icon: 'dashboard', label: 'Home' },
  { id: 'ask-ai', icon: 'smart_toy', label: 'Ask AI' },
  { id: 'alerts', icon: 'crisis_alert', label: 'Alerts' },
  { id: 'profile', icon: 'person', label: 'Profile' },
  { id: 'settings', icon: 'settings', label: 'Settings' },
];

export function BottomNav({ active, onNavigate }: BottomNavProps) {
  return (
    <nav className="fixed bottom-0 inset-x-0 z-50 pb-safe bg-surface/90 backdrop-blur-xl">
      <div className="flex justify-around items-center h-20 px-space-xs">
        {navItems.map((item) => {
          const isActive = active === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`flex flex-col items-center justify-center gap-space-xs w-14 h-16 transition-all ${
                isActive
                  ? 'text-secondary bg-surface-variant/40 rounded-xl'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              <Icon name={item.icon} size={22} filled={isActive} />
              <span className="text-label-sm">{item.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
