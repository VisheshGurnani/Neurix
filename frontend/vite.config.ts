import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/health': 'http://127.0.0.1:8000',
      '/config': 'http://127.0.0.1:8000',
      '/models': 'http://127.0.0.1:8000',
      '/explain': 'http://127.0.0.1:8000',
      '/analyze': 'http://127.0.0.1:8000',
    },
  },
});
