import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.tsx';
import './index.css';

// Auto-remove any injected Bolt badges or watermarks
if (typeof window !== 'undefined') {
  const purgeBoltBadges = () => {
    const selectors = [
      '#bolt-badge',
      '.bolt-badge',
      '[class*="bolt-badge"]',
      '[id*="bolt-badge"]',
      '[data-bolt-badge]',
      'a[href*="bolt.new"]',
      'a[href*="stackblitz"]',
      '[aria-label*="Bolt" i]',
      '[title*="Bolt" i]',
    ];
    document.querySelectorAll(selectors.join(',')).forEach((el) => el.remove());
  };

  purgeBoltBadges();
  if ('MutationObserver' in window) {
    const observer = new MutationObserver(() => purgeBoltBadges());
    observer.observe(document.documentElement, { childList: true, subtree: true });
  }
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);

