import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  base: '/miniapp/dashboard/',
  plugins: [react()],
  build: {
    rollupOptions: {
      input: {
        dashboard: 'index.html',
        dashboardPreview: 'design/index.html',
      },
    },
  },
  server: {
    host: '127.0.0.1',
    port: 5174,
    strictPort: true,
    allowedHosts: ['.trycloudflare.com'],
    proxy: {
      '/miniapp/api': 'http://127.0.0.1:8081',
    },
  },
})
