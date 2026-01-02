// src/features/auth/authService.ts
import apiClient from '../../api/apiClient';

export interface LoginData {
    email: string;
    password: string;
}

export const authService = {
    async login(data: LoginData) {
        const response = await apiClient.post('/api/auth/login', data);
        if (response.data.token) {
            localStorage.setItem('token', response.data.token);
        }
        return response.data;
    },

    async logout() {
        localStorage.removeItem('token');
        await apiClient.post('/api/auth/logout');
    },

    async getProfile() {
        const response = await apiClient.get('/api/auth/profile');
        return response.data;
    },

    async validateSession() {
        try {
            const response = await apiClient.get('/api/auth/validate');
            return response.data.valid === true;
        } catch {
            return false;
        }
    }
};