// src/api/apiConfig.ts

// Detectar ambiente automaticamente
const isDevelopment = import.meta.env.DEV || window.location.hostname === 'localhost';

// Normaliza URL: remove barras extras e garante protocolo consistente
const normalizeUrl = (url: string): string => {
    if (!url) return url;
    let out = url.trim();
    // troca postgres:// etc não aplicável aqui; apenas http/https
    // remove barra duplicada antes de /api
    out = out.replace(/\/+$/g, '');
    // garante sufixo /api
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
    // Em desenvolvimento com Vite proxy, usar caminho relativo para evitar CORS
    if (isDevelopment) return '/api';
    
    const host = window.location.hostname || '';
    const isVercel = host.endsWith('.vercel.app');
    
    // 1. Prioridade: Runtime override (window.__API_URL__)
    const runtimeUrl = getRuntimeApiUrl();
    if (runtimeUrl) return normalizeUrl(runtimeUrl);
    
    // 2. Variável de ambiente do Vite
    if (import.meta.env.VITE_API_URL) return normalizeUrl(import.meta.env.VITE_API_URL as string);
    
    // 3. Fallback para Vercel: usar URL do Render
    if (isVercel) {
        const renderUrl = import.meta.env.VITE_RENDER_API_URL || 'https://mercadinhosys.onrender.com';
        return normalizeUrl(renderUrl);
    }
    
    // 4. Último fallback: mesma origem
    return normalizeUrl(window.location.origin);
};

export const API_CONFIG = {
    BASE_URL: getBaseUrl(),
    TIMEOUT: 20000,
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
