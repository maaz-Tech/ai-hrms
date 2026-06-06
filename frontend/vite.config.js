import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Proxies /api and other backend routes to FastAPI during development.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
})
