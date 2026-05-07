/**
 * Vite build configuration for the Finance Tracker frontend.
 *
 * Configures Vue 3 compilation (including JSX), Vue DevTools integration,
 * Tailwind CSS v4 processing, path aliasing (`@/` -> `src/`), and
 * a dev server proxy that forwards `/api` requests to the Django backend.
 */
import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import vueDevTools from 'vite-plugin-vue-devtools'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    vue(),           // Vue 3 SFC compilation
    vueJsx(),        // JSX/TSX support in Vue components
    vueDevTools(),   // Browser DevTools integration
    tailwindcss(),   // Tailwind CSS v4 processing
  ],
  resolve: {
    alias: {
      // Map `@/` imports to the `src/` directory
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    proxy: {
      // Forward all `/api` requests to the Django backend during development
      '/api': {
        target: process.env.VITE_API_URL || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
