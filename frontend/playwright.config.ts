import { defineConfig, devices } from "@playwright/test";

// End-to-end tests run against the real Docker Compose stack (frontend +
// backend + Postgres), not `next dev` - closer to what actually ships, and
// it's how every flow in this app was manually verified during development.
//
// Locally: if `docker compose` is already running, tests reuse it as-is
// (fast iteration). If not, this starts it for you.
// In CI: always does a fresh `docker compose up --build`.
//
// Known limitation: the backend rate-limits registration (5/hour per IP,
// see app/routes/auth.py). Since local runs reuse a long-lived backend
// container, repeated `npx playwright test` runs share that counter and can
// eventually 429 on signup - restart the backend if that happens:
// `docker compose restart backend`. Fresh CI runs don't hit this since a
// new container means the in-memory limiter resets.
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: process.env.CI ? [["github"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3001",
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command:
      "docker compose up -d --build && until curl -sf http://localhost:5001/api/health >/dev/null; do sleep 1; done",
    cwd: "..",
    url: "http://localhost:3001",
    timeout: 180_000,
    reuseExistingServer: !process.env.CI,
  },
});
