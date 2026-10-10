import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/auth': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/users': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '^/assess$': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '^/risk$': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '^/plan$': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/foods': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '^/report$': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '^/health$': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
});
