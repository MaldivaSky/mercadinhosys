// src/api/apiConfig.ts

const getBaseUrl = () => {
    // Se estiver rodando no seu computador (npm run dev)
    if (import.meta.env.MODE === 'development') {
        return 'http://localhost:5000/api';
    }

    // Se estiver na Vercel (Produção), usa o link do Render
    // IMPORTANTE: Confirme se este link é exatamente o do seu Render
    return 'https://mercadinhosys.onrender.com/api';
};

export const API_CONFIG = {
    BASE_URL: getBaseUrl(),
    // Aumentamos o tempo limite para conexões móveis (30s)
    TIMEOUT: 30000,
} as const;