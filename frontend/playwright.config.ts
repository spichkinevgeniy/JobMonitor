import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./visual-tests",

  use: {
    baseURL: "http://127.0.0.1:4173",
    browserName: "chromium",
  },

  webServer: {
    command: "npm --prefix apps/shell run dev -- --host 127.0.0.1 --port 4173",

    url: "http://127.0.0.1:4173/miniapp/react/",

    reuseExistingServer: true,
    timeout: 30_000,
  },
});
