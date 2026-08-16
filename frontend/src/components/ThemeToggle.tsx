"use client";

import { useEffect, useState } from "react";
import { applyTheme, getStoredTheme, getSystemTheme, type Theme } from "@/lib/theme";

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme | null>(null);

  useEffect(() => {
    setTheme(getStoredTheme() ?? getSystemTheme());
  }, []);

  function toggle() {
    const next: Theme = theme === "dark" ? "light" : "dark";
    applyTheme(next);
    setTheme(next);
  }

  return (
    <button
      onClick={toggle}
      aria-label="Toggle color theme"
      title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
      className="rounded-lg px-3 py-1.5 text-sm font-medium text-text-secondary transition-colors hover:bg-text-muted/10 hover:text-text-primary"
    >
      {theme === "dark" ? "☀️" : theme === "light" ? "🌙" : " "}
    </button>
  );
}
