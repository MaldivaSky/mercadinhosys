/**
 * registerServiceWorker.ts
 *
 * Registro manual do Service Worker do PWA.
 * Controla falhas silenciosamente para que erros esperados (ex: HTTP,
 * Safari modo privado, CSP restrito) não apareçam como crashes no Sentry.
 */

export function registerServiceWorker() {
  // Só registra em produção e se o browser suporta SW
  if (!('serviceWorker' in navigator)) return;

  // Em desenvolvimento, pular — evita cache stale interferindo no HMR
  if (import.meta.env.DEV) return;

  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/sw.js', { scope: '/' })
      .then((registration) => {
        // Força atualização imediata se houver novo SW em espera
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          if (newWorker) {
            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                // Novo conteúdo disponível — o workbox skipWaiting cuida do refresh
                console.info('[PWA] Nova versão disponível. Atualizando...');
              }
            });
          }
        });
      })
      .catch((error) => {
        // Captura silenciosa: falha no registro do SW é tolerável (o app segue funcionando)
        // NÃO relança o erro para evitar que o Sentry trate isso como crítico.
        if (import.meta.env.VITE_DEBUG_SW === 'true') {
          console.warn('[PWA] Service Worker não pôde ser registrado:', error);
        }
      });
  });
}
