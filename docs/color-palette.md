# Color Palette (Light & Dark Mode)

The frontend supports a light and a dark theme. All colors are defined as CSS
custom properties in [`frontend/src/app/globals.css`](../frontend/src/app/globals.css)
and mapped to Tailwind utility colors (e.g. `bg-page`, `text-text-primary`,
`border-border`) via `@theme inline`.

## How theme switching works

- The theme is toggled with the button in the top navigation bar
  (`ThemeToggle` component) and persisted in `localStorage` under the key
  `theme` (`"light"` or `"dark"`).
- An inline script (`themeInitScript` in `frontend/src/lib/theme.ts`) runs in
  `<head>` before the page is painted. It reads the stored preference and, if
  none exists yet, falls back to the OS preference
  (`prefers-color-scheme`) — then adds a `light`/`dark` class to `<html>`.
  This means the chosen theme survives a full page reload with no
  flash-of-wrong-theme and no hydration mismatch.
- The CSS variables below live on `:root` (light, default) and are
  overridden by `:root.dark`. A `@media (prefers-color-scheme: dark)` block
  is kept as a fallback for the brief pre-hydration/no-JS case.

## Light mode

| Token             | Value                     | Usage                              |
| ------------------ | ------------------------- | ----------------------------------- |
| `--page`            | `#f9f9f7`                 | Page background                     |
| `--surface`         | `#fcfcfb`                 | Card / panel background             |
| `--surface-raised`  | `#ffffff`                 | Raised surfaces (modals, popovers)  |
| `--text-primary`    | `#0b0b0b`                 | Primary text                        |
| `--text-secondary`  | `#52514e`                 | Secondary text                      |
| `--text-muted`      | `#898781`                 | Muted / placeholder text            |
| `--border`          | `rgba(11, 11, 11, 0.1)`   | Default border                      |
| `--gridline`        | `#e1e0d9`                 | Chart gridlines                     |
| `--series-1`        | `#2a78d6`                 | Chart series — blue                 |
| `--series-2`        | `#eb6834`                 | Chart series — orange               |
| `--series-3`        | `#1baf7a`                 | Chart series — aqua                 |
| `--series-4`        | `#eda100`                 | Chart series — yellow               |
| `--series-7`        | `#4a3aa7`                 | Chart series — violet               |
| `--status-good`      | `#0ca30c`                 | Status — good                       |
| `--status-warning`   | `#fab219`                 | Status — warning                    |
| `--status-serious`   | `#ec835a`                 | Status — serious                    |
| `--status-critical`  | `#d03b3b`                 | Status — critical                   |

## Dark mode

| Token             | Value                       | Usage                              |
| ------------------ | ---------------------------- | ----------------------------------- |
| `--page`            | `#0d0d0d`                   | Page background                     |
| `--surface`         | `#1a1a19`                   | Card / panel background             |
| `--surface-raised`  | `#212120`                   | Raised surfaces (modals, popovers)  |
| `--text-primary`    | `#ffffff`                   | Primary text                        |
| `--text-secondary`  | `#c3c2b7`                   | Secondary text                      |
| `--text-muted`      | `#898781`                   | Muted / placeholder text            |
| `--border`          | `rgba(255, 255, 255, 0.1)`  | Default border                      |
| `--gridline`        | `#2c2c2a`                   | Chart gridlines                     |
| `--series-1`        | `#3987e5`                   | Chart series — blue                 |
| `--series-2`        | `#d95926`                   | Chart series — orange               |
| `--series-3`        | `#199e70`                   | Chart series — aqua                 |
| `--series-4`        | `#c98500`                   | Chart series — yellow               |
| `--series-7`        | `#9085e9`                   | Chart series — violet               |
| `--status-good`      | `#0ca30c`                   | Status — good                       |
| `--status-warning`   | `#fab219`                   | Status — warning                    |
| `--status-serious`   | `#ec835a`                   | Status — serious                    |
| `--status-critical`  | `#e66767`                   | Status — critical                   |

`--status-good`, `--status-warning` and `--status-serious` are identical in
both themes by design (they already have enough contrast against both
backgrounds); only `--status-critical` is adjusted for dark mode readability.
