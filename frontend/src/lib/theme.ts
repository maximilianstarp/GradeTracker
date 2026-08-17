export type Theme = "light" | "dark";

const STORAGE_KEY = "theme";

/** Inline, must stay a single self-contained function body: its source is
 * injected verbatim into a blocking <script> in the document head so the
 * correct theme class is applied before first paint (no flash of the
 * wrong theme, no hydration mismatch). Do not import anything into it. */
export function themeInitScript() {
  try {
    const stored = localStorage.getItem("theme");
    const theme =
      stored === "light" || stored === "dark"
        ? stored
        : window.matchMedia("(prefers-color-scheme: dark)").matches
          ? "dark"
          : "light";
    document.documentElement.classList.add(theme);
  } catch {
    /* ignore, falls back to the CSS prefers-color-scheme media query */
  }
}

export function getStoredTheme(): Theme | null {
  if (typeof window === "undefined") return null;
  const value = window.localStorage.getItem(STORAGE_KEY);
  return value === "light" || value === "dark" ? value : null;
}

export function getSystemTheme(): Theme {
  if (typeof window === "undefined") return "light";
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function applyTheme(theme: Theme) {
  const root = document.documentElement;
  root.classList.remove("light", "dark");
  root.classList.add(theme);
  window.localStorage.setItem(STORAGE_KEY, theme);
}
