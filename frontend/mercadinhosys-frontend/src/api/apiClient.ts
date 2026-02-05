import axios from 'axios';
import { API_CONFIG } from './apiConfig';

const apiClient = axios.create({
    baseURL: API_CONFIG.BASE_URL,
    timeout: API_CONFIG.TIMEOUT,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor para adicionar token
apiClient.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor para tratamento de erros
apiClient.interceptors.response.use(
    (response) => response,
    async (error) => {
        // Log detalhado do erro para debug
        if (error.response) {
            console.error('❌ API Error:', {
                url: error.config?.url,
                method: error.config?.method,
                status: error.response.status,
                statusText: error.response.statusText,
                data: error.response.data,
                headers: error.response.headers,
            });
        } else if (error.request) {
            console.error('❌ Network Error:', {
                url: error.config?.url,
                message: 'Sem resposta do servidor',
                baseURL: API_CONFIG.BASE_URL,
            });
        } else {
            console.error('❌ Request Error:', error.message);
        }

        if (error.response?.status === 401) {
            // Token expirado - tentar refresh
            const refreshToken = localStorage.getItem('refresh_token');
            if (refreshToken && !error.config._retry) {
                error.config._retry = true;
                try {
                    const response = await axios.post(`${API_CONFIG.BASE_URL}/auth/refresh`, {}, {
                        headers: {
                            'Authorization': `Bearer ${refreshToken}`
                        }
                    });
                    localStorage.setItem('access_token', response.data.access_token);
                    error.config.headers.Authorization = `Bearer ${response.data.access_token}`;
                    return apiClient(error.config);
                } catch (refreshError) {
                    console.error('❌ Refresh token falhou, redirecionando para login');
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('refresh_token');
                    window.location.href = '/login';
                    return Promise.reject(refreshError);
                }
            }
        }
        return Promise.reject(error);
    }
);

export { apiClient };