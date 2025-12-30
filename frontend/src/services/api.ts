import axios from 'axios';

// SEU BACKEND NA PORTA 5000
const API_URL = 'http://localhost:5000';

export const api = axios.create({
    baseURL: API_URL,
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    }
    
   });

// Interceptor para log
api.interceptors.request.use(
    (config) => {
        console.log(`🌐 [Frontend] ${config.method?.toUpperCase()} ${config.url}`);
        return config;
    },
    (error) => {
        console.error('❌ [Frontend] Erro na requisição:', error);
        return Promise.reject(error);
    }
);

api.interceptors.response.use(
    (response) => {
        console.log(`✅ [Frontend] ${response.status} ${response.config.url}`);
        return response;
    },
    (error) => {
        console.error('❌ [Frontend] Erro:', {
            url: error.config?.url,
            status: error.response?.status,
            message: error.message,
            data: error.response?.data
        });

        if (error.code === 'ERR_NETWORK') {
            alert('⚠️ Backend offline! Verifique se o Flask está rodando na porta 5000.');
        }

        return Promise.reject(error);
    }
);

export const setAuthToken = (token: string) => {
    if (token) {
        api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
};