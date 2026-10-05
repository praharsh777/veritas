"use client";
import { useEffect, useState } from "react";

type Theme = "dark" | "light";
const KEY = "veritas-theme";

export default function ThemeToggle() {
  const [theme, setTheme] = useState<Theme | null>(null);

  useEffect(() => {
    const t = document.documentElement.dataset.theme;
    setTheme(t === "light" ? "light" : "dark");
  }, []);

  function toggle() {
    const next: Theme = theme === "light" ? "dark" : "light";
    document.documentElement.dataset.theme = next;
    setTheme(next);
    try { localStorage.setItem(KEY, next); } catch { /* storage blocked: theme still applies for this visit */ }
  }

  const isLight = theme === "light";
  return (
    <button
      onClick={toggle}
      aria-label={isLight ? "Switch to dark theme" : "Switch to light theme"}
      title={isLight ? "Dark mode" : "Light mode"}
      className="relative grid h-9 w-9 place-items-center overflow-hidden rounded-xl border border-ink-500 text-mist-300 transition hover:border-brand-500/60 hover:text-mist-100 active:scale-95"
    >
      {/* sun */}
      <svg className={`absolute transition-all duration-500 ${isLight ? "rotate-0 scale-100 opacity-100" : "-rotate-90 scale-50 opacity-0"}`} width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden>
        <circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
      </svg>
      {/* moon */}
      <svg className={`absolute transition-all duration-500 ${isLight ? "rotate-90 scale-50 opacity-0" : "rotate-0 scale-100 opacity-100"}`} width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
        <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />
      </svg>
    </button>
  );
}
