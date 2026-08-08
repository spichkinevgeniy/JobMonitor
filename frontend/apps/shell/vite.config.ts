import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const sourceRoot = new URL('./src', import.meta.url).pathname

export default defineConfig({
  base: '/miniapp/react/',
  plugins: [react()],
  resolve: {
    alias: {
      '@': sourceRoot,
    },
  },
  server: {
    proxy: {
      '/miniapp/api': 'http://127.0.0.1:8000',
      '/miniapp/static': 'http://127.0.0.1:8000',
    },
  },
})
