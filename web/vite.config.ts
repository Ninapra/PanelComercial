import { defineConfig } from 'vite';
import path from 'node:path';

export default defineConfig({
  root: '.',
  publicDir: 'public',
  envPrefix: 'VITE_',
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      input: {
        main: path.resolve(__dirname, 'index.html'),
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
      '@shared': path.resolve(__dirname, 'src/shared'),
      '@contexts': path.resolve(__dirname, 'src/contexts'),
    },
  },
  server: {
    port: 5173,
    strictPort: false,
    proxy: {
      // Proxy al backend Flask local durante desarrollo
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    include: ['src/**/*.{test,spec}.ts'],
  },
});
