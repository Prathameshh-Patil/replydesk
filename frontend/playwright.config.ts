import { defineConfig, devices } from "@playwright/test";

// The tests drive a real browser against the running app (see e2e/run.sh, which starts an
// isolated Docker copy of the whole stack with the fake model).
export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3020",
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
