// src/api/apiConfig.ts

// Detectar ambiente automaticamente
const isDevelopment =
    import.meta.env.DEV ||
    window.location.port === '5173' ||
    window.location.port === '3000' ||
    window.location.hostname === 'localhost' ||
    window.location.hostname === '127.0.0.1' ||
    window.location.hostname.startsWith('192.168.') ||
    window.location.hostname.startsWith('10.') ||
    window.location.hostname.startsWith('172.') ||
    window.location.hostname.endsWith('.local');

// Normaliza URL: remove barras extras e garante protocolo consistente
const normalizeUrl = (url: string): string => {
    if (!url) return url;
    let out = url.trim();

    // CORREÇÃO DE SEGURANÇA: NUNCA permitir que o navegador tente resolver o host 'backend'
    if (out.includes('backend') || out.includes(':5000')) {
        return '/api';
    }

    out = out.replace(/\/+$/g, '');
    if (!/\/api$/.test(out)) {
        out = `${out}/api`;
    }
    const isLocalHost = /^(localhost|127\.0\.0\.1)(:\d+)?$/i.test(window.location.host);
    if (window.location.protocol === 'https:' && out.startsWith('http://') && !isLocalHost) {
        out = out.replace(/^http:\/\//, 'https://');
    }
    return out;
};

// Tenta obter URL em tempo de execução via variável global (permitindo override sem rebuild)
const getRuntimeApiUrl = (): string | undefined => {
    const w: any = window as any;
    const candidate = w.__API_URL__ || w.API_URL;
    return typeof candidate === 'string' && candidate.length > 0 ? candidate : undefined;
};

// URL do backend baseada no ambiente com fallback robusto
const getBaseUrl = (): string => {
    // 1. PRIORIDADE ABSOLUTA: Se estiver rodando localmente, SEMPRE usar /api (Proxy do Vite)
    // Isso evita que o navegador tente resolver hosts internos como 'backend:5000'
    const isLocal =
        window.location.hostname === 'localhost' ||
        window.location.hostname === '127.0.0.1' ||
        window.location.hostname.startsWith('192.168.') ||
        window.location.hostname.startsWith('10.') ||
        window.location.hostname.startsWith('172.');

    if (isLocal) return '/api';

    // 2. Produção ou Fallback
    const runtimeUrl = getRuntimeApiUrl();
    if (runtimeUrl) return normalizeUrl(runtimeUrl);

    if (import.meta.env.VITE_API_URL) return normalizeUrl(import.meta.env.VITE_API_URL as string);

    return normalizeUrl(window.location.origin);
};

export const API_CONFIG = {
    BASE_URL: getBaseUrl(),
    // Docker/local e produção podem ter cold start/consultas pesadas.
    TIMEOUT: 60000,
    IS_DEVELOPMENT: isDevelopment,
} as const;

// Log para debug
{
    console.log('🔧 API Config:', {
        BASE_URL: API_CONFIG.BASE_URL,
        ENVIRONMENT: isDevelopment ? 'development' : 'production',
        VITE_API_URL: import.meta.env.VITE_API_URL,
        RUNTIME_API_URL: (window as any).__API_URL__ || (window as any).API_URL,
    });
}
