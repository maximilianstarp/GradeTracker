"use client";

import { useEffect, useState } from "react";
import { applyTheme, getStoredTheme, getSystemTheme, type Theme } from "@/lib/theme";

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme | null>(null);

  useEffect(() => {
    // Browser-only theme source (localStorage / matchMedia): the initial
    // render must match the server's markup, which has neither, so this can
    // only be synced client-side after mount.
    // eslint-disable-next-line react-hooks/set-state-in-effect
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
