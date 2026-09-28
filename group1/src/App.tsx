import { useState, useEffect } from 'react';
import { Header } from '@/components/Header';
import { BottomNav } from '@/components/BottomNav';
import { LoginPage } from '@/pages/LoginPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { AlertsPage } from '@/pages/AlertsPage';
import { AskAIPage } from '@/pages/AskAIPage';
import { ProfilePage } from '@/pages/ProfilePage';
import { SettingsPage } from '@/pages/SettingsPage';
import { supabase } from '@/lib/supabase';
import { defaultPreferences } from '@/data/mockData';
import type { PageId, UserPreferences } from '@/types';

import { AdvisoryPage } from '@/pages/AdvisoryPage';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [currentPage, setCurrentPage] = useState<PageId>('dashboard');
  const [preferences, setPreferences] = useState<UserPreferences>(defaultPreferences);
  const [location, setLocation] = useState('Warangal, TS');

  useEffect(() => {
    // Check for existing JWT token
    const token = localStorage.getItem('jwt_token');
    if (token) {
      setIsLoggedIn(true);
    }

    // Listen for unauthorized events from axios interceptor
    const handleUnauthorized = () => {
      handleLogout();
    };
    window.addEventListener('auth-unauthorized', handleUnauthorized);

    return () => {
      window.removeEventListener('auth-unauthorized', handleUnauthorized);
    };
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const { data } = await supabase
          .from('user_preferences')
          .select('*')
          .order('updated_at', { ascending: false })
          .limit(1)
          .maybeSingle();

        if (data) {
          setPreferences(data as UserPreferences);
        } else {
          await supabase.from('user_preferences').insert(defaultPreferences);
        }
      } catch (err) {
        console.warn('Preferences sync skipped or offline:', err);
      }
    })();
  }, []);

  const handleSetPreferences = (prefs: UserPreferences) => {
    setPreferences(prefs);
    (async () => {
      try {
        await supabase
          .from('user_preferences')
          .update({ ...prefs, updated_at: new Date().toISOString() })
          .neq('id', '00000000-0000-0000-0000-000000000000');
      } catch (err) {
        console.warn('Failed to update preferences:', err);
      }
    })();
  };

  const handleNavigate = (page: PageId) => {
    if (!isLoggedIn && page !== 'login') {
      setIsLoggedIn(true);
    }
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleLogin = () => {
    setIsLoggedIn(true);
    setCurrentPage('dashboard');
  };

  const handleLogout = () => {
    localStorage.removeItem('jwt_token');
    setIsLoggedIn(false);
    setCurrentPage('login');
  };

  if (!isLoggedIn) {
    return (
      <div className="bg-surface text-on-surface font-body flex flex-col min-h-screen">
        <main className="flex flex-col relative w-full px-gutter pt-16 pb-24 bg-surface flex-grow">
          <LoginPage onLogin={handleLogin} onNavigate={handleNavigate} />
        </main>
        <BottomNav active={currentPage} onNavigate={handleNavigate} />
      </div>
    );
  }

  const showHeader = currentPage !== 'login';

  return (
    <div className="bg-surface text-on-surface font-body flex flex-col min-h-screen">
      {showHeader && (
        <Header 
          onNavigate={handleNavigate} 
          location={location} 
          onLocationChange={setLocation}
          preferences={preferences}
          setPreferences={handleSetPreferences}
        />
      )}
      <main className="flex flex-col relative w-full px-gutter pt-16 pb-24 bg-surface flex-grow">
        {currentPage === 'dashboard' && (
          <DashboardPage onNavigate={handleNavigate} location={location} onLocationChange={setLocation} />
        )}
        {currentPage.startsWith('advisory-') && (
          <AdvisoryPage mode={currentPage.replace('advisory-', '') as any} onNavigate={handleNavigate} />
        )}
        {currentPage === 'ask-ai' && <AskAIPage />}
        {currentPage === 'alerts' && <AlertsPage location={location} />}
        {currentPage === 'profile' && (
          <ProfilePage
            onNavigate={handleNavigate}
            preferences={preferences}
            setPreferences={handleSetPreferences}
            onLogout={handleLogout}
          />
        )}
        {currentPage === 'settings' && (
          <SettingsPage preferences={preferences} setPreferences={handleSetPreferences} />
        )}
      </main>
      <BottomNav active={currentPage} onNavigate={handleNavigate} />
    </div>
  );
}

export default App;
