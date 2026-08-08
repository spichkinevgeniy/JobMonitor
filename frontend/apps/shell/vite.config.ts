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
  build: {
    rollupOptions: {
      input: {
        shell: 'index.html',
        buttonPreview: 'design/button/index.html',
        backButtonPreview: 'design/back-button/index.html',
        iconButtonPreview: 'design/icon-button/index.html',
        selectionCardPreview: 'design/selection-card/index.html',
        chipPreview: 'design/chip/index.html',
        textFieldPreview: 'design/text-field/index.html',
        progressStepperPreview: 'design/progress-stepper/index.html',
      },
    },
  },
  server: {
    proxy: {
      '/miniapp/api': 'http://127.0.0.1:8000',
      '/miniapp/static': 'http://127.0.0.1:8000',
    },
  },
})
