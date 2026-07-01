import * as Sentry from '@sentry/react';

/**
 * Inicializa o Sentry no frontend.
 *
 * É um NO-OP quando `VITE_SENTRY_DSN` não está definido — assim dev/local
 * não envia eventos nem exige configuração. Em produção (Vercel), basta
 * definir a env `VITE_SENTRY_DSN` no projeto.
 *
 * Envs suportadas:
 *  - VITE_SENTRY_DSN                  (obrigatória p/ ativar)
 *  - VITE_SENTRY_RELEASE              (opcional — ex.: hash do commit)
 *  - VITE_SENTRY_TRACES_SAMPLE_RATE   (opcional — default 0.1 = 10%)
 */
// DSN do projeto (frontend/JavaScript). É PÚBLICO por natureza — sempre vai
// embutido no bundle que roda no navegador —, então é seguro versioná-lo.
// Pode ser sobrescrito pela env VITE_SENTRY_DSN.
const FALLBACK_DSN =
  'https://322d96621010f0403946446be4460662@o4511655329923072.ingest.us.sentry.io/4511655345192960';

export function initSentry(): void {
  // Só ativa quando há DSN E estamos em build de produção — assim o dev local
  // não envia erros de teste para o painel.
  const envDsn = import.meta.env.VITE_SENTRY_DSN as string | undefined;
  const dsn = envDsn || (import.meta.env.PROD ? FALLBACK_DSN : undefined);
  if (!dsn) return;

  const tracesRaw = import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE as string | undefined;
  const tracesSampleRate = Math.max(0, Math.min(1, Number(tracesRaw ?? 0.1) || 0.1));

  Sentry.init({
    dsn,
    environment: import.meta.env.MODE,
    release: import.meta.env.VITE_SENTRY_RELEASE as string | undefined,
    integrations: [Sentry.browserTracingIntegration()],
    tracesSampleRate,
    sendDefaultPii: false, // não enviar dados pessoais por padrão (LGPD)

    /**
     * Filtro de eventos: evita que ruído de infraestrutura (SW, rede, extensões)
     * polua o painel de erros com falsos positivos.
     */
    beforeSend(event, hint) {
      const err = hint?.originalException;
      if (err instanceof Error) {
        const msg = err.message?.toLowerCase() ?? '';
        // Erros de Service Worker — esperados em HTTP ou Safari privado
        if (msg.includes('serviceworker') || msg.includes('sw.js') || msg.includes('rejected')) {
          return null; // Descartar
        }
        // Erros de rede genéricos (offline, proxy, CORS de terceiros)
        if (msg.includes('networkerror') || msg.includes('failed to fetch') || msg.includes('load failed')) {
          return null;
        }
        // Erros de extensão de browser
        if (event.exception?.values?.[0]?.stacktrace?.frames?.some(
          (f) => f.filename?.includes('chrome-extension') || f.filename?.includes('moz-extension')
        )) {
          return null;
        }
      }
      return event;
    },
  });
}
