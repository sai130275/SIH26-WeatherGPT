import { useState } from 'react';
import { Icon } from '@/components/Icon';
import { Toggle } from '@/components/Toggle';
import { UpcomingPopup } from '@/components/UpcomingPopup';
import { languages } from '@/data/mockData';
import type { UserPreferences, DataSource, TempUnit, WindUnit } from '@/types';

interface SettingsPageProps {
  preferences: UserPreferences;
  setPreferences: (prefs: UserPreferences) => void;
}

export function SettingsPage({ preferences, setPreferences }: SettingsPageProps) {
  const [saved, setSaved] = useState(false);

  const dataSources: { id: DataSource; name: string; desc: string }[] = [
    { id: 'Open-Meteo', name: 'Open-Meteo', desc: 'Current weather and forecast' },
  ];

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="flex flex-col w-full pb-space-xl">
      {/* Header / Intro */}
      <div className="mb-space-lg">
        <h1 className="font-headline-lg text-on-surface">Configuration</h1>
        <p className="font-body-md text-on-surface-variant mt-space-xs">
          Manage meteorological data feeds, alert protocols, and system localization.
        </p>
      </div>

      {/* 1. Weather Data Sources */}
      <section className="mb-space-lg">
        <div className="flex items-center justify-between mb-space-sm">
          <h2 className="font-headline-sm text-on-surface flex items-center gap-space-xs">
            <Icon name="hub" size={20} className="text-primary" />
            Weather Data Sources
          </h2>
          <span className="text-label-sm text-on-secondary-container bg-secondary-container px-space-xs py-0.5 rounded">
            Primary Model
          </span>
        </div>
        <div className="bg-surface-container-low rounded-xl p-space-md flex flex-col gap-space-md">
          {dataSources.map((source) => (
            <label key={source.id} className="flex items-center justify-between cursor-pointer">
              <div className="flex flex-col">
                <span className="font-body-md text-on-surface font-medium">{source.name}</span>
                <span className="font-body-sm text-on-surface-variant">{source.desc}</span>
              </div>
              <input
                type="radio"
                name="data_source"
                checked={preferences.data_source === source.id}
                onChange={() => setPreferences({ ...preferences, data_source: source.id })}
                className="w-4 h-4 text-primary accent-primary"
              />
            </label>
          ))}
        </div>
      </section>

      {/* 2. Notification & Alert Preferences */}
      <section className="mb-space-lg">
        <div className="flex items-center justify-between mb-space-sm">
          <h2 className="font-headline-sm text-on-surface flex items-center gap-space-xs">
            <Icon name="notifications_active" size={20} className="text-primary" />
            Alert & Notification Toggles
          </h2>
        </div>
        <div className="bg-surface-container-low rounded-xl p-space-md flex flex-col gap-space-md">
          {[
            { key: 'red_alert_push' as const, label: 'Red Warning Push Alerts', desc: 'Instant overrides for flash floods and cyclones' },
            { key: 'severe_sirens' as const, label: 'Severe Weather Sirens', desc: 'Audio alarm on high-severity local triggers' },
            { key: 'sms_fallback' as const, label: 'Low-Bandwidth SMS Fallback', desc: 'Send compact text alerts during network outages' },
          ].map((item) => (
            <div key={item.key} className="flex items-center justify-between">
              <div className="flex flex-col pr-space-md">
                <span className="font-body-md text-on-surface font-medium">{item.label}</span>
                <span className="font-body-sm text-on-surface-variant">{item.desc}</span>
              </div>
              <UpcomingPopup featureName={item.label}>
                <div className="pointer-events-none">
                  <Toggle
                    checked={preferences[item.key]}
                    onChange={() => {}}
                  />
                </div>
              </UpcomingPopup>
            </div>
          ))}
        </div>
      </section>

      {/* 3. Language & Regional Settings */}
      <section className="mb-space-lg">
        <div className="flex items-center justify-between mb-space-sm">
          <h2 className="font-headline-sm text-on-surface flex items-center gap-space-xs">
            <Icon name="language" size={20} className="text-primary" />
            Language & Units
          </h2>
        </div>
        <div className="bg-surface-container-low rounded-xl p-space-md flex flex-col gap-space-md">
          <div>
            <label className="block font-body-md text-on-surface font-medium mb-space-xs">Interface Language</label>
            <UpcomingPopup featureName="Multilingual Support" className="w-full">
              <select
                value={preferences.language}
                disabled
                className="w-full bg-surface border border-outline-variant rounded-lg p-space-sm text-on-surface font-body-md focus:outline-none focus:border-primary pointer-events-none opacity-80"
              >
                {languages.map((lang) => (
                  <option key={lang.code} value={lang.code}>
                    {lang.native} ({lang.label})
                  </option>
                ))}
              </select>
            </UpcomingPopup>
          </div>
          <div className="grid grid-cols-2 gap-space-md">
            <div>
              <label className="block font-body-md text-on-surface font-medium mb-space-xs">Temperature</label>
              <div className="flex rounded-lg bg-surface border border-outline-variant p-1">
                {(['C', 'F'] as TempUnit[]).map((unit) => (
                  <button
                    key={unit}
                    onClick={() => setPreferences({ ...preferences, temperature_unit: unit })}
                    className={`flex-1 py-1 text-center text-label-md rounded font-medium transition-all ${
                      preferences.temperature_unit === unit
                        ? 'bg-primary text-on-primary'
                        : 'text-on-surface-variant'
                    }`}
                  >
                    °{unit}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="block font-body-md text-on-surface font-medium mb-space-xs">Wind Speed</label>
              <select
                value={preferences.wind_speed_unit}
                onChange={(e) => setPreferences({ ...preferences, wind_speed_unit: e.target.value as WindUnit })}
                className="w-full bg-surface border border-outline-variant rounded-lg p-2 text-on-surface font-body-md focus:outline-none focus:border-primary"
              >
                <option value="kmh">km/h</option>
                <option value="mph">mph</option>
              </select>
            </div>
            <div>
              <label className="block font-body-md text-on-surface font-medium mb-space-xs mt-space-sm">Precipitation</label>
              <select
                value={preferences.precip_unit || 'mm'}
                onChange={(e) => setPreferences({ ...preferences, precip_unit: e.target.value as 'mm' | 'in' })}
                className="w-full bg-surface border border-outline-variant rounded-lg p-2 text-on-surface font-body-md focus:outline-none focus:border-primary"
              >
                <option value="mm">mm</option>
                <option value="in">inches</option>
              </select>
            </div>
            <div>
              <label className="block font-body-md text-on-surface font-medium mb-space-xs mt-space-sm">Pressure</label>
              <select
                value={preferences.pressure_unit || 'hPa'}
                onChange={(e) => setPreferences({ ...preferences, pressure_unit: e.target.value as 'hPa' | 'inHg' })}
                className="w-full bg-surface border border-outline-variant rounded-lg p-2 text-on-surface font-body-md focus:outline-none focus:border-primary"
              >
                <option value="hPa">hPa</option>
                <option value="inHg">inHg</option>
              </select>
            </div>
          </div>
        </div>
      </section>

      {/* 4. Accessibility & UI */}
      <section className="mb-space-lg">
        <div className="flex items-center justify-between mb-space-sm">
          <h2 className="font-headline-sm text-on-surface flex items-center gap-space-xs">
            <Icon name="accessibility" size={20} className="text-primary" />
            Accessibility & Interface
          </h2>
        </div>
        <div className="bg-surface-container-low rounded-xl p-space-md flex flex-col gap-space-md">
          {[
            { key: 'high_contrast' as const, label: 'High Contrast Mode', desc: 'Enhanced boundary visibility for outdoor glare' },
            { key: 'large_font' as const, label: 'Large Font Scaling', desc: 'Boost typography size across all metrics' },
            { key: 'dark_mode' as const, label: 'Dark Mode Theme', desc: 'Low-light optimized palette for night monitoring' },
          ].map((item) => (
            <div key={item.key} className="flex items-center justify-between">
              <div className="flex flex-col pr-space-md">
                <span className="font-body-md text-on-surface font-medium">{item.label}</span>
                <span className="font-body-sm text-on-surface-variant">{item.desc}</span>
              </div>
              <UpcomingPopup featureName={item.label}>
                <div className="pointer-events-none">
                  <Toggle
                    checked={preferences[item.key]}
                    onChange={() => {}}
                  />
                </div>
              </UpcomingPopup>
            </div>
          ))}
        </div>
      </section>

      {/* 5. Offline & Storage */}
      <section className="mb-space-lg">
        <div className="flex items-center justify-between mb-space-sm">
          <h2 className="font-headline-sm text-on-surface flex items-center gap-space-xs">
            <Icon name="database" size={20} className="text-primary" />
            Offline & Storage Management
          </h2>
        </div>
        <div className="bg-surface-container-low rounded-xl p-space-md flex flex-col gap-space-md">
          <div className="flex items-center justify-between">
            <div className="flex flex-col">
              <span className="font-body-md text-on-surface font-medium">Radar & Map Cache</span>
              <span className="font-mono-data text-on-surface-variant">
                {preferences.cache_size_mb} MB used / {preferences.cache_limit_mb} MB limit
              </span>
            </div>
            <UpcomingPopup featureName="Clear Cache">
              <button
                className="bg-surface border border-outline-variant px-space-md py-2 rounded-lg text-label-md text-on-surface hover:bg-surface-container-high transition-colors"
              >
                Clear Cache
              </button>
            </UpcomingPopup>
          </div>
          <div>
            <label className="block font-body-md text-on-surface font-medium mb-space-xs">WIS 2.0 Sync Interval</label>
            <UpcomingPopup featureName="WIS 2.0 Sync Interval" className="w-full">
              <select
                value={String(preferences.sync_interval)}
                disabled
                className="w-full bg-surface border border-outline-variant rounded-lg p-2 text-on-surface font-body-md focus:outline-none focus:border-primary pointer-events-none opacity-80"
              >
                <option value="15">Every 15 minutes (High Data)</option>
                <option value="30">Every 30 minutes (Recommended)</option>
                <option value="60">Hourly Sync</option>
                <option value="0">Manual Only</option>
              </select>
            </UpcomingPopup>
          </div>
        </div>
      </section>

      {/* Save Button */}
      <button
        onClick={handleSave}
        className={`w-full py-3 rounded-xl font-headline-sm flex items-center justify-center gap-space-xs transition-all ${
          saved
            ? 'bg-green-600 text-white'
            : 'bg-primary text-on-primary hover:opacity-95'
        }`}
      >
        <Icon name={saved ? 'check_circle' : 'save'} size={20} filled={saved} />
        {saved ? 'Configuration Saved!' : 'Save Configuration'}
      </button>
    </div>
  );
}
