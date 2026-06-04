import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  optimizeDeps: {
    include: ['plotly.js/dist/plotly.js'],
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.JEEVES247_API_URL ?? 'http://127.0.0.1:8888',
        changeOrigin: true,
      },
    },
  },
})
