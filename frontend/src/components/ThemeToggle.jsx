import { useState, useEffect } from 'react';

export default function ThemeToggle({ className = '' }) {
  const [dark, setDark] = useState(() => localStorage.getItem('theme') === 'dark');

  useEffect(() => {
    document.body.className = dark ? 'dark' : '';
    localStorage.setItem('theme', dark ? 'dark' : 'light');
  }, [dark]);

  return (
    <button className={`theme-toggle ${className}`} onClick={() => setDark(!dark)}>
      {dark ? '☀️ Light Mode' : '🌙 Dark Mode'}
    </button>
  );
}
