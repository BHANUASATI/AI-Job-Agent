import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],

  // ── Dev proxy: forward /api/* to FastAPI on :8000 ──────────────────────────
  // This means you can use relative URLs like /api/auth/login in the app
  // instead of hardcoding http://localhost:8000. For production, the FastAPI
  // server serves the built frontend directly, so no proxy is needed.
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },

  // ── Build output ─────────────────────────────────────────────────────────
  build: {
    outDir: 'dist',
    sourcemap: false,
    // Chunk splitting for better caching
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules/react') || id.includes('node_modules/react-dom') || id.includes('node_modules/react-router')) {
            return 'vendor'
          }
          if (id.includes('node_modules/axios')) {
            return 'utils'
          }
        },
      },
    },
  },
})
