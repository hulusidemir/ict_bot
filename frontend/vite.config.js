import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 8080,
    proxy: {
      '/api': 'http://localhost:8083',
      '/socket.io': {
        target: 'http://localhost:8083',
        ws: true,
      },
    },
  },
});
