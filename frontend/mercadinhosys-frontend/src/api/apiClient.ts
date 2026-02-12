import axios from 'axios';
import { API_CONFIG } from './apiConfig';

// Variáveis para controle de Concorrência no Refresh Token
let isRefreshing = false;
let failedQueue: Array<{
    resolve: (token: string) => void;
    reject: (error: any) => void;
}> = [];

const processQueue = (error: any, token: string | null = null) => {
    failedQueue.forEach((prom) => {
        if (error) {
            prom.reject(error);
        } else {
            prom.resolve(token!);
        }
    });
    failedQueue = [];
};

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
        if (token && token !== 'undefined' && token !== 'null') {
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
        const originalRequest = error.config;

        // Se for 401 e não for uma retentativa
        if (error.response?.status === 401 && !originalRequest._retry) {
            if (isRefreshing) {
                // Se já estiver atualizando, adiciona à fila
                return new Promise((resolve, reject) => {
                    failedQueue.push({ resolve, reject });
                })
                    .then((token) => {
                        originalRequest.headers['Authorization'] = `Bearer ${token}`;
                        return apiClient(originalRequest);
                    })
                    .catch((err) => Promise.reject(err));
            }

            originalRequest._retry = true;
            isRefreshing = true;

            try {
                const refreshToken = localStorage.getItem('refresh_token');

                if (!refreshToken) {
                    throw new Error('No refresh token available');
                }

                // Tenta renovar o token
                const response = await axios.post(`${API_CONFIG.BASE_URL}/auth/refresh`, {}, {
                    headers: {
                        'Authorization': `Bearer ${refreshToken}`
                    }
                });

                const { access_token } = response.data;

                if (!access_token) {
                    throw new Error('No access token returned');
                }

                localStorage.setItem('access_token', access_token);
                apiClient.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
                originalRequest.headers['Authorization'] = `Bearer ${access_token}`;

                // Processa fila com sucesso
                processQueue(null, access_token);

                // Retorna a requisição original
                return apiClient(originalRequest);

            } catch (refreshError) {
                // Processa fila com erro
                processQueue(refreshError, null);

                console.error('❌ Refresh token falhou, redirecionando para login');
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                window.location.href = '/login';
                return Promise.reject(refreshError);
            } finally {
                isRefreshing = false;
            }
        } else if (error.response?.status === 401 && originalRequest._retry) {
            // Se falhou mesmo após o refresh
            console.error('❌ Falha após refresh, mas NÃO forçando logout para evitar loop (debug)');
            // localStorage.removeItem('access_token');
            // localStorage.removeItem('refresh_token');
            // window.location.href = '/login';
            return Promise.reject(error);
        }

        // Se não for 401 ou se falhou após retry, loga o erro
        if (error.response) {
            // Ignora log de 401 se foi tratado (embora aqui só chegue se não foi tratado ou se falhou)
            // Se falhou o refresh, já logamos no catch acima.
            // Se for outro erro (500, 404, etc) logamos aqui.
            console.error('❌ API Error:', {
                url: error.config?.url,
                method: error.config?.method,
                status: error.response.status,
                statusText: error.response.statusText,
                data: error.response.data,
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

        // Tratamento específico para 422 (Token malformado etc)
        if (error.response?.status === 422) {
            const msg =
                typeof error.response.data === 'object' &&
                    error.response.data !== null &&
                    'msg' in error.response.data
                    ? String((error.response.data as { msg?: unknown }).msg || '')
                    : '';
            const looksLikeJwt =
                msg.toLowerCase().includes('token') ||
                msg.toLowerCase().includes('jwt') ||
                msg.toLowerCase().includes('segments') ||
                msg.toLowerCase().includes('authorization');
            const token = localStorage.getItem('access_token');
            if (looksLikeJwt || token === 'undefined' || token === 'null') {
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                window.location.href = '/login';
            }
        }

        return Promise.reject(error);
    }
);

export { apiClient };
