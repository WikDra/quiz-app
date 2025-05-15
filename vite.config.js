import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    cors: true,
    proxy: {
      // Forward API calls to Flask backend
      '/api': {
        // Use IPv4 address to avoid IPv6 connection errors
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
        secure: false,
      },
      // Support OAuth endpoints without /api prefix
      '/login': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/login/, '/api/login')
      },
      '/authorize': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/authorize/, '/api/authorize')
      }
    },
  }
})
