import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import tailwind from '@astrojs/tailwind';

// https://astro.build/config
export default defineConfig({
  devToolbar: {
    enabled: false
  },
  integrations: [
    react(),
    tailwind({
      applyBaseStyles: false,
    })
  ],
  output: 'static',
  server: {
    port: 4321,
    host: true
  },
  vite: {
    server: {
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true
        }
      }
    }
  }
});
