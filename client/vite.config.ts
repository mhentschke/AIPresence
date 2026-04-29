import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/devices': 'http://127.0.0.1:5000',
      '/trackers': 'http://127.0.0.1:5000',
      '/sensors': 'http://127.0.0.1:5000',
      '/rooms': 'http://127.0.0.1:5000',
      '/beacon_monitors': 'http://127.0.0.1:5000',
      '/device': 'http://127.0.0.1:5000',
      '/ha': 'http://127.0.0.1:5000',
      '/admin': 'http://127.0.0.1:5000',
    },
  },
  build: {
    outDir: 'dist',
    // Use relative paths so assets load correctly behind HA ingress proxy
    // (ingress serves the app under /api/hassio_ingress/<token>/, not /)
  },
  base: './',
})
