import { createContext, useContext } from 'react';
import type { UserPreferences } from '@/types';

// Global user preferences context enabling synchronous unit system conversions
// (°C/°F, kmh/mph, mm/in, hPa/inHg) across all active views without re-fetching data.
export const PreferencesContext = createContext<{
  preferences: UserPreferences | null;
  setPreferences: (p: UserPreferences) => void;
}>({
  preferences: null,
  setPreferences: () => {},
});

export const usePreferences = () => useContext(PreferencesContext);
