import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import compression from 'vite-plugin-compression'
import path from 'path';

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd())
  const deviceTarget = env.VITE_DEVICE_IP
    ? `http://${env.VITE_DEVICE_IP}`
    : 'http://localhost'

  return {
    plugins: [
      react(),       
      compression({
        algorithm: 'gzip',
        ext: '.gz',
        deleteOriginFile: true,
      }),
    ],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },    
    server: {
      proxy: {
        '/api': {
          target: deviceTarget,
          changeOrigin: true,
        },
      },
    },
  }
})