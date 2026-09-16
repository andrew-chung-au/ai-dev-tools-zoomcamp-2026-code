import { defineConfig, devices } from "@playwright/test";

/**
 * Targets the live docker-compose.yml stack (see `make e2e`), not a
 * dev server Playwright starts itself: the `app` service serves both the
 * built frontend and the API from the same origin on this port (see
 * backend/config.py DEFAULT_PORT and docker-compose.yml).
 */
const baseURL = process.env.E2E_BASE_URL ?? "http://localhost:8091";

export default defineConfig({
  testDir: "./tests",
  timeout: 30_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
