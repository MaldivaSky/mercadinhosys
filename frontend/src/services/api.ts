import axios from 'axios';

// Verifique qual URL seu backend está usando
//const API_URL = 'http://localhost:5000/api'; // ou 3000, 8000, etc.

const api = axios.create({
    baseURL: '/api',  // ← Usa proxy
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    },
});



// Adicionar interceptors para debug
api.interceptors.request.use(
    (config) => {
        console.log(`➡️ Enviando requisição: ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`);
        console.log('📦 Dados:', config.data);

        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }

        return config;
    },
    (error) => {
        console.error('❌ Erro na requisição:', error);
        return Promise.reject(error);
    }
);

api.interceptors.response.use(
    (response) => {
        console.log(`⬅️ Resposta recebida: ${response.status} ${response.config.url}`);
        console.log('📄 Dados da resposta:', response.data);
        return response;
    },
    (error) => {
        console.error('❌ Erro na resposta:', {
            status: error.response?.status,
            message: error.message,
            url: error.config?.url,
            data: error.response?.data
        });

        if (error.response?.status === 404) {
            console.error('⚠️ Endpoint não encontrado. Verifique se o backend está rodando.');
        }

        return Promise.reject(error);
    }
);

export default api;