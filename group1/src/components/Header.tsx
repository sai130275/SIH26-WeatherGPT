import { useState } from 'react';
import { Icon } from '@/components/Icon';
import { locations } from '@/data/mockData';
import type { PageId, UserPreferences } from '@/types';

interface HeaderProps {
  onNavigate: (page: PageId) => void;
  location: string;
  onLocationChange?: (location: string) => void;
  preferences?: UserPreferences;
  setPreferences?: (prefs: UserPreferences) => void;
}

export function Header({ onNavigate, location, onLocationChange, preferences, setPreferences }: HeaderProps) {
  const [showLocationModal, setShowLocationModal] = useState(false);
  const [showLanguageModal, setShowLanguageModal] = useState(false);

  const supportedLanguages = [
    { code: 'en', label: 'English' },
    { code: 'te', label: 'తెలుగు' },
    { code: 'hi', label: 'हिन्दी' },
    { code: 'ta', label: 'தமிழ்' },
  ];

  return (
    <header className="fixed top-0 inset-x-0 z-50 bg-surface/80 backdrop-blur-xl pt-safe">
      <div className="h-16 px-gutter flex items-center justify-between">
        <div className="flex items-center gap-space-sm relative">
          <div className="w-10 h-10 rounded-xl bg-primary-container flex items-center justify-center text-primary shrink-0">
            <Icon name="weather_mix" size={22} />
          </div>
          <div>
            <span className="font-headline-sm text-on-surface block leading-tight">WeatherGPT</span>
            <button 
              onClick={() => setShowLocationModal(true)}
              className="flex items-center gap-space-xs text-secondary text-label-md cursor-pointer hover:opacity-80"
            >
              <Icon name="location_on" size={14} />
              <span>{location}</span>
              <Icon name="expand_more" size={14} />
            </button>
          </div>
          
          {/* Anchored Location Popover */}
          {showLocationModal && (
            <>
              <div className="fixed inset-0 z-40 cursor-default" onClick={() => setShowLocationModal(false)} />
              <div className="absolute top-[calc(100%+0.5rem)] left-0 w-56 bg-surface rounded-xl p-2 shadow-xl border border-outline-variant/30 z-50 flex flex-col gap-1 max-h-60 overflow-y-auto no-scrollbar origin-top-left animate-in fade-in zoom-in-95 duration-200">
                <span className="text-label-sm text-on-surface-variant px-3 py-2 font-medium">Select Location</span>
                {locations.map((loc) => (
                  <button
                    key={loc.value}
                    onClick={() => {
                      if (onLocationChange) onLocationChange(loc.label);
                      setShowLocationModal(false);
                    }}
                    className={`px-3 py-2 rounded-lg text-left text-body-md ${location === loc.label ? 'bg-primary/10 text-primary font-medium' : 'hover:bg-surface-variant text-on-surface'}`}
                  >
                    {loc.label}
                  </button>
                ))}
              </div>
            </>
          )}
        </div>

        <div className="flex items-center gap-space-xs relative">
          <button
            onClick={() => setShowLanguageModal(true)}
            className="w-11 h-11 flex items-center justify-center text-on-surface-variant hover:text-on-surface rounded-full cursor-pointer shrink-0"
            title="Language"
          >
            <Icon name="translate" size={20} />
          </button>
          <button
            onClick={() => onNavigate('alerts')}
            className="w-11 h-11 flex items-center justify-center text-on-surface-variant hover:text-on-surface rounded-full relative cursor-pointer shrink-0"
            title="Alerts"
          >
            <Icon name="notifications" size={20} />
            <span className="absolute top-2.5 right-2.5 w-2.5 h-2.5 bg-error rounded-full" />
          </button>
          <button
            onClick={() => onNavigate('profile')}
            className="w-8 h-8 rounded-full bg-primary flex items-center justify-center ml-space-xs text-on-primary cursor-pointer shrink-0"
            title="Profile"
          >
            <Icon name="person" size={18} />
          </button>

          {/* Anchored Language Popover */}
          {showLanguageModal && (
            <>
              <div className="fixed inset-0 z-40 cursor-default" onClick={() => setShowLanguageModal(false)} />
              <div className="absolute top-[calc(100%+0.5rem)] right-0 w-48 bg-surface rounded-xl p-2 shadow-xl border border-outline-variant/30 z-50 flex flex-col gap-1 origin-top-right animate-in fade-in zoom-in-95 duration-200">
                <span className="text-label-sm text-on-surface-variant px-3 py-2 font-medium">Select Language</span>
                {supportedLanguages.map((lang) => (
                  <button
                    key={lang.code}
                    onClick={() => {
                      if (preferences && setPreferences) {
                        setPreferences({ ...preferences, language: lang.code });
                      }
                      setShowLanguageModal(false);
                    }}
                    className={`px-3 py-2 rounded-lg text-left text-body-md ${preferences?.language === lang.code ? 'bg-primary/10 text-primary font-medium' : 'hover:bg-surface-variant text-on-surface'}`}
                  >
                    {lang.label}
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
