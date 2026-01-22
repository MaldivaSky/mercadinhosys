// src/api/apiConfig.ts

// Detectar ambiente automaticamente
const isDevelopment = import.meta.env.DEV || window.location.hostname === 'localhost';

// URL do backend baseada no ambiente
const getBaseUrl = (): string => {
    // 1. Variável de ambiente (Render, Vercel, etc)
    if (import.meta.env.VITE_API_URL) {
        return import.meta.env.VITE_API_URL;
    }
    
    // 2. Desenvolvimento local
    if (isDevelopment) {
        return 'http://localhost:5000/api';
    }
    
    // 3. Produção (mesma origem)
    return `${window.location.origin}/api`;
};

export const API_CONFIG = {
    BASE_URL: getBaseUrl(),
    TIMEOUT: 30000,
    IS_DEVELOPMENT: isDevelopment,
} as const;

// Log para debug (apenas em desenvolvimento)
if (isDevelopment) {
    console.log('🔧 API Config:', {
        BASE_URL: API_CONFIG.BASE_URL,
        ENVIRONMENT: isDevelopment ? 'development' : 'production',
        VITE_API_URL: import.meta.env.VITE_API_URL,
    });
}