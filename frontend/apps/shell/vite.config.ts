import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { designPreviews } from "./design/designPreviews";
const sourceRoot = new URL("./src", import.meta.url).pathname;

export default defineConfig({
  base: "/miniapp/react/",
  plugins: [react()],
  resolve: {
    alias: {
      "@": sourceRoot,
    },
  },
  build: {
    rollupOptions: {
      input: {
        shell: "index.html",
        ...designPreviews,
      },
    },
  },
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    allowedHosts: [".trycloudflare.com"],
    proxy: {
      "/miniapp/dashboard": {
        target: "http://127.0.0.1:5174",
        ws: true,
      },
      "/miniapp/api": "http://127.0.0.1:8081",
      "/miniapp/static": "http://127.0.0.1:8081",
      "/miniapp/specialty": "http://127.0.0.1:8081",
      "/miniapp/format": "http://127.0.0.1:8081",
      "/miniapp/salary": "http://127.0.0.1:8081",
      "/miniapp/level": "http://127.0.0.1:8081",
    },
  },
});
