import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig(() => {
  // VITE_API_TARGET é injetado pelo docker-compose.dev.yml como http://backend:5000
  // Se estivermos fora do Docker, 'backend' não será resolvido, então usamos localhost:5000 como fallback.
  // Como não podemos testar DNS de forma síncrona aqui de maneira trivial, 
  // confiamos na variável de ambiente ou assumimos localhost se não estivermos explicitly em um container.
  const apiTarget = process.env.VITE_API_TARGET || 'http://localhost:5000';

  console.log('🔧 Vite proxy configurado para:', apiTarget);

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port: 5173,           // porta INTERNA do container
      host: true,           // escuta em 0.0.0.0 (necessário no Docker)
      strictPort: true,
      // Detecta mudanças de arquivo dentro do Docker (Windows/WSL precisa de polling)
      watch: {
        usePolling: true,
        interval: 100,
      },
      // HMR (hot reload) através do Docker:
      // o navegador acessa pela porta do HOST (ex.: 80), então o cliente HMR
      // precisa abrir o WebSocket nessa mesma porta — não na porta interna 5173.
      hmr: {
        host: 'localhost',
        clientPort: Number(process.env.VITE_HMR_CLIENT_PORT) || 80,
        protocol: 'ws',
      },
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path.replace(/^\/api/, '/api'),
        },
        '/uploads': {
          target: apiTarget,
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path.replace(/^\/uploads/, '/uploads'),
        },
      },
    },
  }
})
