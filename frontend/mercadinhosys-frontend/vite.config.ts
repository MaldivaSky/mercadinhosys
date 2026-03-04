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
      port: 5173,
      host: true,
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
          secure: false,
          configure: (proxy, _options) => {
            proxy.on('proxyRes', (proxyRes, req, _res) => {
              if (proxyRes.headers['location']) {
                let location = proxyRes.headers['location'];
                // Converte redirecionamentos absolutos do backend para relativos ao proxy original
                location = location.replace(/^https?:\/\/backend:5000/, '');
                // Se o redirecionamento for para fora do /api mas dentro do mesmo host
                if (location.startsWith('http') && location.includes(req.headers.host || '')) {
                  const url = new URL(location);
                  location = url.pathname + url.search;
                }
                proxyRes.headers['location'] = location;
              }
            });
          },
        },
        '/uploads': {
          target: apiTarget,
          changeOrigin: true,
          secure: false,
        },
      },
    },
  }
})
