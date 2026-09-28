import { createContext, useContext } from 'react';
import type { UserPreferences } from '@/types';

export const PreferencesContext = createContext<{
  preferences: UserPreferences | null;
  setPreferences: (p: UserPreferences) => void;
}>({
  preferences: null,
  setPreferences: () => {},
});

export const usePreferences = () => useContext(PreferencesContext);
