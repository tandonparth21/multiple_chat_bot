import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  // **NEW:** Added this to ensure relative paths are handled correctly,
  // especially for serving assets from the root or subdirectories.
  base: './',

  // **NEW:** Added this to ensure pdfjs-dist is pre-bundled by Vite,
  // which can help with resolving its dependencies and assets more consistently.
  optimizeDeps: {
    include: ['pdfjs-dist'],
  },
});