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
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false,
      }
      // Usunięto proxy dla /login i /authorize.
      // Zapytania do endpointów OAuth będą teraz musiały używać pełnych adresów URL.
    },
  }
})
