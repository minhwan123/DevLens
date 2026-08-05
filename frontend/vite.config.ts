import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Lets the Docker Compose setup point the proxy at the `backend` service
  // (VITE_PROXY_TARGET=http://backend:8000) while local dev keeps the default.
  const env = loadEnv(mode, process.cwd(), '')
  const proxyTarget = env.VITE_PROXY_TARGET || 'http://localhost:8000'

  return {
    plugins: [react()],
    server: {
      host: true,
      proxy: {
        '/analyze': proxyTarget,
        '/health': proxyTarget,
      },
    },
  }
})
