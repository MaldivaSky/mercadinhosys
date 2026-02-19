// src/features/auth/authService.ts
import axios from 'axios';
import { LoginApiResponse } from '../../types';
import { API_CONFIG } from '../../api/apiConfig';

const API_URL = API_CONFIG.BASE_URL;

class AuthService {
    async login(identifier: string, password: string): Promise<LoginApiResponse> {
        console.log('📤 Enviando para backend:', { identifier });

        // ✅ Estrutura CORRETA para o backend
        const loginData = {
            email: identifier.includes('@') ? identifier : undefined,
            username: !identifier.includes('@') ? identifier : undefined,
            senha: password
        };

        try {
            const response = await axios.post(
                `${API_URL}/auth/login`,
                loginData,
                {
                    headers: { 'Content-Type': 'application/json' },
                    timeout: 10000
                }
            );

            const data = response.data;

            // ✅ Validação robusta da resposta
            if (!data || typeof data !== 'object') {
                throw new Error('Resposta inválida do servidor');
            }

            if (!data.success) {
                throw new Error(data.error || 'Login falhou');
            }

            if (!data.data?.access_token || !data.data?.user) {
                throw new Error('Dados de autenticação incompletos');
            }

            // ✅ Salva tokens
            localStorage.setItem('access_token', data.data.access_token);
            if (data.data.refresh_token) {
                localStorage.setItem('refresh_token', data.data.refresh_token);
            }
            localStorage.setItem('user_data', JSON.stringify(data.data.user));
            localStorage.setItem('estabelecimento_data', JSON.stringify(data.data.estabelecimento));

            // Dispara evento para atualizar estado de autenticação
            window.dispatchEvent(new Event('auth-change'));

            console.log('✅ Tokens salvos com sucesso');
            return data;

        } catch (error: unknown) {
            const err = error as { message?: string; response?: { status?: number; data?: unknown } };
            console.error('❌ Erro no authService:', {
                message: err.message,
                status: err.response?.status,
                data: err.response?.data
            });

            // ✅ Limpa tokens em caso de erro
            this.logout();
            throw error;
        }
    }

    async bootstrapAdmin(identifier: string, password: string): Promise<{ success: boolean; message?: string; error?: string; code?: string }> {
        const bootstrapData = {
            email: identifier.includes('@') ? identifier : undefined,
            username: !identifier.includes('@') ? identifier : undefined,
            identifier,
            senha: password,
            password
        };

        try {
            const response = await axios.post(
                `${API_URL}/auth/bootstrap`,
                bootstrapData,
                {
                    headers: { 'Content-Type': 'application/json' },
                    timeout: 10000
                }
            );
            const data = response.data as { success: boolean; message?: string; error?: string; code?: string };
            if (!data || typeof data !== 'object') {
                throw new Error('Resposta inválida do servidor');
            }
            return data;
        } catch (error: unknown) {
            const err = error as { message?: string; response?: { status?: number; data?: any } };
            const serverData = err.response?.data;
            return {
                success: false,
                error: serverData?.error || err.message || 'Erro ao executar bootstrap',
                code: serverData?.code
            };
        }
    }

    async updateProfile(payload: { nome?: string; email?: string; telefone?: string; foto_url?: string }): Promise<{ success: boolean; data?: { nome?: string; email?: string; telefone?: string; foto_url?: string }; message?: string }> {
        const token = this.getToken();
        if (!token) {
            throw new Error('Usuário não autenticado');
        }
        try {
            const response = await axios.put(
                `${API_URL}/auth/profile`,
                payload,
                {
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    timeout: 10000
                }
            );
            const data = response.data as { success: boolean; data?: { nome?: string; email?: string; telefone?: string; foto_url?: string }; message?: string; error?: string };
            if (!data || typeof data !== 'object') {
                throw new Error('Resposta inválida do servidor');
            }
            if (!data.success) {
                throw new Error(data.error || 'Falha ao atualizar perfil');
            }
            return { success: true, data: data.data, message: data.message || 'Perfil atualizado' };
        } catch (error: unknown) {
            const err = error as { message?: string; response?: { status?: number; data?: unknown } };
            const respData = err.response?.data as { error?: string; message?: string } | undefined;
            const serverMessage = respData?.error || respData?.message;
            throw new Error(serverMessage || err.message || 'Erro ao atualizar perfil');
        }
    }

    async changePassword(senhaAtual: string, novaSenha: string): Promise<{ success: boolean; message?: string }> {
        const token = this.getToken();
        if (!token) {
            throw new Error('Usuário não autenticado');
        }
        try {
            const response = await axios.put(
                `${API_URL}/auth/profile`,
                { senha_atual: senhaAtual, nova_senha: novaSenha },
                {
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    timeout: 10000
                }
            );
            const data = response.data;
            if (!data || typeof data !== 'object') {
                throw new Error('Resposta inválida do servidor');
            }
            if (!data.success) {
                throw new Error(data.error || 'Falha ao alterar senha');
            }
            this.logout();
            return { success: true, message: data.message || 'Senha alterada com sucesso' };
        } catch (error: unknown) {
            const err = error as { message?: string; response?: { status?: number; data?: unknown } };
            const respData = err.response?.data as { error?: string; message?: string } | undefined;
            const serverMessage = respData?.error || respData?.message;
            throw new Error(serverMessage || err.message || 'Erro ao alterar senha');
        }
    }

    logout(): void {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_data');
        localStorage.removeItem('estabelecimento_data');

        // Dispara evento para atualizar estado de autenticação
        window.dispatchEvent(new Event('auth-change'));

        console.log('🗑️ Sessão limpa');
    }

    getToken(): string | null {
        return localStorage.getItem('access_token');
    }

    getCurrentUser(): { nome: string; role: string } | null {
        const userStr = localStorage.getItem('user_data');
        try {
            return userStr ? JSON.parse(userStr) : null;
        } catch {
            return null;
        }
    }

    isAuthenticated(): boolean {
        const token = this.getToken();
        return !!token && token !== 'undefined' && token !== 'null';
    }
}

export const authService = new AuthService();
