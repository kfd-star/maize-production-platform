import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, __dirname, '')
  const apiTarget = env.VITE_DEV_API_TARGET || 'http://127.0.0.1:8001'
  const legacyApiTarget = env.VITE_DEV_LEGACY_API_TARGET || apiTarget
  const arcgisTarget = env.VITE_DEV_ARCGIS_TARGET || 'http://127.0.0.1:6080'

  return {
    base: '/',
    plugins: [vue()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      host: '0.0.0.0',
      port: 5173,
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
        },
        '/hggy': {
          target: legacyApiTarget,
          changeOrigin: true,
        },
        '/arcgis': {
          target: arcgisTarget,
          changeOrigin: true,
          rewrite: (requestPath) => requestPath.replace(/^\/arcgis/, '/arcgis'),
        },
      },
    },
    build: {
      entryFileNames: 'assets/[name].[hash].js',
      rollupOptions: {
        input: {
          main: path.resolve(__dirname, 'index.html'),
        },
      },
    },
    publicDir: 'public',
  }
})
