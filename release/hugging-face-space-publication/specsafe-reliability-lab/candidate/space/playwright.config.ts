import { defineConfig, devices } from "@playwright/test";

const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH;
const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:4173";
const serverHost = process.env.PLAYWRIGHT_SERVER_HOST ?? "127.0.0.1";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  retries: process.env.CI ? 2 : 0,
  reporter: "list",
  use: {
    baseURL,
    trace: "on-first-retry",
    launchOptions: executablePath ? { executablePath } : undefined,
  },
  webServer: {
    command: `npm run build && npm run preview -- --host ${serverHost} --port 4173`,
    url: baseURL,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
  projects: [
    {
      name: "desktop-chromium",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "mobile-chromium",
      use: { ...devices["Pixel 7"] },
    },
  ],
});
