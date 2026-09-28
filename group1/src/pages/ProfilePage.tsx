import { Icon } from '@/components/Icon';
import { Toggle } from '@/components/Toggle';
import { UpcomingPopup } from '@/components/UpcomingPopup';
import type { PageId, UserPreferences } from '@/types';

interface ProfilePageProps {
  onNavigate: (page: PageId) => void;
  preferences: UserPreferences;
  setPreferences: (prefs: UserPreferences) => void;
  onLogout: () => void;
}

export function ProfilePage({ onNavigate, preferences, setPreferences, onLogout }: ProfilePageProps) {
  const languages = [
    { code: 'te', label: 'Telugu' },
    { code: 'en', label: 'English' },
    { code: 'hi', label: 'Hindi' },
  ];
  const activeLang = preferences.language === 'te' ? 'te' : preferences.language === 'hi' ? 'hi' : 'en';

  return (
    <div className="flex flex-col w-full pb-8 gap-space-md">
      {/* Profile Header */}
      <div className="flex flex-col items-center pt-space-md pb-space-sm">
        <div className="relative mb-space-md">
          <div className="w-24 h-24 rounded-full bg-primary-container flex items-center justify-center text-primary shadow-lg overflow-hidden relative">
            <Icon name="person" size={48} />
          </div>
          <div className="absolute bottom-0 right-0 w-8 h-8 rounded-full bg-primary text-on-primary flex items-center justify-center shadow-md">
            <Icon name="verified" size={16} filled />
          </div>
        </div>
        <div className="flex items-center gap-space-sm mb-1">
          <h2 className="font-headline-md text-on-surface text-center">Dr. Rajesh Kumar</h2>
          <UpcomingPopup featureName="Edit Profile">
            <button className="w-8 h-8 rounded-full bg-surface-container flex items-center justify-center hover:bg-surface-variant transition-colors text-primary">
              <Icon name="edit" size={16} />
            </button>
          </UpcomingPopup>
        </div>
        <div className="flex items-center gap-space-xs mt-space-xs">
          <span className="px-space-sm py-0.5 rounded-full bg-primary-container text-on-primary-container text-label-sm font-label-sm">
            Disaster Management & Agriculture Official
          </span>
        </div>
        <div className="flex items-center gap-space-xs text-secondary text-body-sm mt-space-xs">
          <Icon name="location_on" size={16} />
          <span>Warangal, Telangana</span>
        </div>
      </div>

      {/* Farmer Mode Toggle */}
      <div className="bg-surface-container-low rounded-xl p-space-md flex flex-col gap-space-md shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-space-sm">
            <div className="w-10 h-10 rounded-xl bg-surface-container flex items-center justify-center text-primary">
              <Icon name="agriculture" size={20} />
            </div>
            <div>
              <h3 className="font-headline-sm text-on-surface">Farmer Mode</h3>
              <p className="text-body-sm text-secondary">Localized advisory for Warangal Rural</p>
            </div>
          </div>
          <Toggle
            checked={preferences.farmer_mode}
            onChange={(val) => setPreferences({ ...preferences, farmer_mode: val })}
          />
        </div>
      </div>

      {/* Language Preferences */}
      <div className="bg-surface-container-low rounded-xl p-space-md flex flex-col gap-space-md shadow-sm">
        <h3 className="font-headline-sm text-on-surface flex items-center gap-space-sm">
          <Icon name="translate" size={20} className="text-primary" />
          Language Preferences
        </h3>
        <div className="flex flex-wrap gap-space-xs">
          {languages.map((lang) => (
            <UpcomingPopup key={lang.code} featureName={`Switch Language to ${lang.label}`}>
              <button
                className={`px-space-md py-1.5 rounded-xl text-label-md font-label-md transition-all ${
                  activeLang === lang.code
                    ? 'bg-primary text-on-primary'
                    : 'bg-surface-container text-on-surface'
                }`}
              >
                {lang.label}
              </button>
            </UpcomingPopup>
          ))}
        </div>
      </div>

      {/* Notification Channels */}
      <div className="bg-surface-container-low rounded-xl p-space-md flex flex-col gap-space-md shadow-sm">
        <h3 className="font-headline-sm text-on-surface flex items-center gap-space-sm">
          <Icon name="notifications_active" size={20} className="text-primary" />
          Notification Channels
        </h3>
        <div className="flex flex-col gap-space-sm">
          <UpcomingPopup featureName="Push Notification Settings" className="w-full">
            <div className="flex items-center justify-between py-1 hover:bg-surface-container/50 px-2 -mx-2 rounded transition-colors">
              <div className="flex items-center gap-space-sm">
                <Icon name="smartphone" size={20} className="text-secondary" />
                <span className="text-body-md text-on-surface">Push Notifications</span>
              </div>
              <input checked type="checkbox" className="w-4 h-4 accent-primary rounded" readOnly />
            </div>
          </UpcomingPopup>
          
          <UpcomingPopup featureName="SMS Broadcast Settings" className="w-full">
            <div className="flex items-center justify-between py-1 hover:bg-surface-container/50 px-2 -mx-2 rounded transition-colors">
              <div className="flex items-center gap-space-sm">
                <Icon name="sms" size={20} className="text-secondary" />
                <span className="text-body-md text-on-surface">SMS Broadcast</span>
              </div>
              <input checked type="checkbox" className="w-4 h-4 accent-primary rounded" readOnly />
            </div>
          </UpcomingPopup>

          <UpcomingPopup featureName="Emergency Siren Settings" className="w-full">
            <div className="flex items-center justify-between py-1 hover:bg-surface-container/50 px-2 -mx-2 rounded transition-colors">
              <div className="flex items-center gap-space-sm">
                <Icon name="campaign" size={20} className="text-tertiary" />
                <span className="text-body-md text-on-surface">Emergency Siren & Broadcast</span>
              </div>
              <input checked type="checkbox" className="w-4 h-4 accent-tertiary rounded" readOnly />
            </div>
          </UpcomingPopup>
        </div>
      </div>

      {/* Offline Cached Data */}
      <div className="bg-surface-container-low rounded-xl p-space-md flex flex-col gap-space-md shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-space-sm">
            <div className="w-10 h-10 rounded-xl bg-surface-container flex items-center justify-center text-primary">
              <Icon name="cloud_sync" size={20} />
            </div>
            <div>
              <h3 className="font-headline-sm text-on-surface">Offline Cached Data</h3>
              <p className="text-body-sm text-secondary">3.2 MB cached for field operations</p>
            </div>
          </div>
          <UpcomingPopup featureName="Clear Offline Cache">
            <button className="px-space-md py-2 rounded-xl bg-surface-container text-on-surface text-label-md font-label-md hover:bg-surface-variant transition-colors">
              Clear
            </button>
          </UpcomingPopup>
        </div>
      </div>

      {/* Account Security */}
      <div className="bg-surface-container-low rounded-xl p-space-md flex flex-col gap-space-md shadow-sm">
        <h3 className="font-headline-sm text-on-surface flex items-center gap-space-sm">
          <Icon name="security" size={20} className="text-primary" />
          Account Security
        </h3>
        <div className="flex flex-col gap-space-xs">
          <UpcomingPopup featureName="Change Password" className="w-full">
            <button className="flex items-center justify-between w-full py-2 px-space-sm rounded-lg hover:bg-surface-container transition-colors text-left">
              <span className="text-body-md text-on-surface">Change Password</span>
              <Icon name="chevron_right" size={18} className="text-secondary" />
            </button>
          </UpcomingPopup>
          
          <UpcomingPopup featureName="Two-Factor Authentication (2FA)" className="w-full">
            <button className="flex items-center justify-between w-full py-2 px-space-sm rounded-lg hover:bg-surface-container transition-colors text-left">
              <span className="text-body-md text-on-surface">Two-Factor Authentication</span>
              <span className="text-label-md font-label-md text-primary bg-primary-container px-space-xs py-0.5 rounded">
                Enabled
              </span>
            </button>
          </UpcomingPopup>

          <UpcomingPopup featureName="Sign Out All Devices" className="w-full">
            <button className="flex items-center justify-between w-full py-2 px-space-sm rounded-lg hover:bg-surface-container transition-colors text-left">
              <span className="text-body-md text-on-surface">Sign Out All Devices</span>
              <Icon name="devices" size={18} className="text-secondary" />
            </button>
          </UpcomingPopup>
          
          <button
            onClick={onLogout}
            className="flex items-center justify-between w-full py-2 px-space-sm rounded-lg hover:bg-error-container/30 transition-colors text-left text-error mt-2 pt-3 border-t border-outline-variant/30"
          >
            <span className="text-body-md font-bold">Sign Out</span>
            <Icon name="logout" size={18} />
          </button>
        </div>
      </div>

      {/* Quick link to settings */}
      <button
        onClick={() => onNavigate('settings')}
        className="bg-surface-container rounded-xl p-space-md flex items-center justify-between hover:bg-surface-variant/60 transition-all"
      >
        <div className="flex items-center gap-space-sm">
          <Icon name="settings" size={20} className="text-primary" />
          <span className="text-body-md text-on-surface font-medium">App Configuration</span>
        </div>
        <Icon name="chevron_right" size={20} className="text-secondary" />
      </button>
    </div>
  );
}
