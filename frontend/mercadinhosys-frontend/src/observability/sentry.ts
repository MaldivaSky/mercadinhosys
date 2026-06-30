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
  });
}
