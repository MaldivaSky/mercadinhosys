// src/api/apiConfig.ts

// Esta função decide qual link usar automaticamente
const getBaseUrl = () => {
    // Se estiver rodando no seu computador (npm run dev)
    if (import.meta.env.MODE === 'development') {
        return 'http://localhost:5000/api';
    }

    // Se estiver rodando na Vercel ou produção (npm run build)
    return 'https://mercadinhosys.onrender.com/api';
};

export const API_CONFIG = {
    BASE_URL: getBaseUrl(),
    TIMEOUT: 20000, // Aumentei um pouco para garantir no 3G/4G
} as const;