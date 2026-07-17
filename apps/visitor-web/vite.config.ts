import { resolve } from 'node:path'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  build: {
    rollupOptions: {
      input: {
        app: resolve(__dirname, 'index.html'),
      },
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
  },
})
