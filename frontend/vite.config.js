import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// The API is reached through Vite's dev proxy rather than by absolute URL, so
// the browser sees same-origin requests and CORS never enters the picture -
// whether you open the app on localhost or 127.0.0.1.
//
// Point the proxy somewhere else with:  VITE_PROXY_TARGET=http://127.0.0.1:5000 npm run dev
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: env.VITE_PROXY_TARGET,
        changeOrigin: true,
      },
    },
  },
  }
})
