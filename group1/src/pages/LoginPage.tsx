import { useState } from 'react';
import { Icon } from '@/components/Icon';
import { UpcomingPopup } from '@/components/UpcomingPopup';
import { roles } from '@/data/mockData';
import type { PageId } from '@/types';
import { apiClient } from '@/lib/api';
import type { ApiBaseResponse, AuthLoginResponse } from '@/types/api';
import { AxiosError } from 'axios';

interface LoginPageProps {
  onLogin: () => void;
  onNavigate: (page: PageId) => void;
}

export function LoginPage({ onLogin, onNavigate }: LoginPageProps) {
  const [loginMethod, setLoginMethod] = useState<'phone' | 'email'>('phone');
  const [selectedRole, setSelectedRole] = useState(roles[0]);
  const [language, setLanguage] = useState('en');

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleAuth = async () => {
    setErrorMsg('');
    if (loginMethod === 'phone') {
      setErrorMsg('Phone login not currently implemented. Use Email.');
      return;
    }
    if (!email || !password) {
      setErrorMsg('Please enter email and password.');
      return;
    }

    setIsLoading(true);
    try {
      const response = await apiClient.post<ApiBaseResponse<AuthLoginResponse>>('/auth/login', {
        email,
        password,
      });
      if (response.data.success && response.data.data.token) {
        localStorage.setItem('jwt_token', response.data.data.token);
        onLogin();
      }
    } catch (err: unknown) {
      const axiosErr = err as AxiosError<ApiBaseResponse<null>>;
      if (axiosErr.response) {
        if (axiosErr.response.status === 401 || axiosErr.response.status === 400) {
          setErrorMsg(axiosErr.response.data.message || 'Invalid credentials');
        } else {
          setErrorMsg('Backend error. Try again later.');
        }
      } else {
        setErrorMsg('Network error. Backend unavailable.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col w-full pb-8 gap-space-md">
      <div className="flex flex-col items-center pt-space-xl pb-space-md">
        <div className="w-14 h-14 rounded-xl bg-primary-container flex items-center justify-center text-primary shadow-lg mb-space-md">
          <Icon name="weather_mix" size={32} />
        </div>
        <h1 className="font-headline-lg text-on-surface text-center">WeatherGPT</h1>
        <p className="text-body-md text-secondary text-center mt-space-xs">
          Ask the Weather. Understand the Risk. Act Early.
        </p>
      </div>

      <div className="flex justify-center gap-space-xs">
        {[
          { code: 'en', label: 'English' },
          { code: 'te', label: 'తెలుగు' },
          { code: 'hi', label: 'हिन्दी' },
        ].map((lang) => (
          <UpcomingPopup key={lang.code} featureName={`Switch Language to ${lang.label}`}>
            <button
              className={`px-space-md py-1.5 rounded-xl text-label-md font-label-md transition-all ${
                language === lang.code
                  ? 'bg-primary text-on-primary'
                  : 'bg-surface-container text-on-surface'
              }`}
            >
              {lang.label}
            </button>
          </UpcomingPopup>
        ))}
      </div>

      <div className="bg-surface-container-low rounded-xl p-space-md flex flex-col gap-space-md shadow-sm mt-space-sm">
        <div className="flex rounded-lg bg-surface-container p-1">
          <button
            onClick={() => setLoginMethod('phone')}
            className={`flex-1 py-2 text-center rounded-md text-label-md font-label-md transition-all ${
              loginMethod === 'phone'
                ? 'bg-surface text-on-surface shadow-sm'
                : 'text-secondary'
            }`}
          >
            Phone OTP
          </button>
          <button
            onClick={() => setLoginMethod('email')}
            className={`flex-1 py-2 text-center rounded-md text-label-md font-label-md transition-all ${
              loginMethod === 'email'
                ? 'bg-surface text-on-surface shadow-sm'
                : 'text-secondary'
            }`}
          >
            Email / Govt ID
          </button>
        </div>

        {loginMethod === 'phone' ? (
          <div className="flex flex-col gap-space-xs">
            <label className="text-label-md text-secondary">Mobile Number</label>
            <div className="flex gap-space-xs">
              <select className="bg-surface-container px-space-md py-2 rounded-xl text-on-surface text-body-md">
                <option>+91</option>
                <option>+1</option>
                <option>+44</option>
              </select>
              <input
                className="flex-grow bg-surface-container px-space-md py-2 rounded-xl text-on-surface text-body-md focus:outline-none"
                placeholder="98765 43210"
                type="tel"
              />
            </div>
          </div>
        ) : (
          <div className="flex flex-col gap-space-xs">
            <label className="text-label-md text-secondary">Email or Government ID</label>
            <input
              className="bg-surface-container px-space-md py-2 rounded-xl text-on-surface text-body-md focus:outline-none"
              placeholder="official@gov.in"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <label className="text-label-md text-secondary mt-1">Password</label>
            <input
              className="bg-surface-container px-space-md py-2 rounded-xl text-on-surface text-body-md focus:outline-none"
              placeholder="••••••••"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
        )}

        <div className="flex flex-col gap-space-xs">
          <label className="text-label-md text-secondary">Select Role</label>
          <select
            value={selectedRole}
            onChange={(e) => setSelectedRole(e.target.value)}
            className="bg-surface-container px-space-md py-2 rounded-xl text-on-surface text-body-md"
          >
            {roles.map((role) => (
              <option key={role} value={role}>
                {role}
              </option>
            ))}
          </select>
        </div>

        {errorMsg && (
          <div className="text-error text-body-sm font-medium mt-1">{errorMsg}</div>
        )}

        <button
          onClick={handleAuth}
          disabled={isLoading}
          className="w-full py-3 rounded-xl bg-primary text-on-primary font-headline-sm text-center shadow-md hover:bg-surface-tint transition-colors mt-space-xs disabled:opacity-50"
        >
          {isLoading ? 'Authenticating...' : 'Login Securely'}
        </button>
      </div>

      <div className="bg-surface-container-low rounded-xl p-space-md flex flex-col gap-space-sm shadow-sm">
        <h3 className="font-headline-sm text-on-surface">Quick Demo Login</h3>
        <button
          onClick={onLogin}
          className="w-full py-2 px-space-sm bg-surface-container rounded-lg text-left text-body-md text-on-surface hover:bg-surface-variant transition-colors"
        >
          Login as Dr. Rajesh Kumar (Disaster Manager)
        </button>
      </div>

      <div className="flex justify-center items-center gap-space-md pt-space-md text-secondary text-label-sm">
        <span className="px-2 py-1 bg-surface-container rounded">IMD</span>
        <span className="px-2 py-1 bg-surface-container rounded">ECMWF</span>
        <span className="px-2 py-1 bg-surface-container rounded">NWP Consensus</span>
      </div>

      <button
        onClick={() => onNavigate('dashboard')}
        className="text-center text-label-md text-secondary underline mt-space-sm"
      >
        Skip to Demo Dashboard
      </button>
    </div>
  );
}
