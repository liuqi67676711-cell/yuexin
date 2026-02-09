import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',  // 使用IPv4地址，避免IPv6连接问题
        changeOrigin: true,
        rewrite: (path) => path,
      },
    },
  },
})
