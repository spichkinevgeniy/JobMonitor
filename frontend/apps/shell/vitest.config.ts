import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

const sourceRoot = new URL('./src', import.meta.url).pathname

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': sourceRoot,
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    restoreMocks: true,
  },
})
