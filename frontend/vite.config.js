import { defineConfig } from 'vite';

export default defineConfig({
  base: './',
  server: {
    host: '0.0.0.0',
    port: 7000,
    allowedHosts: true,
    watch: {
        usePolling: true,
      },
  },
});
