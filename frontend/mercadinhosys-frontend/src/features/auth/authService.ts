// src/features/auth/authService.ts
import apiClient from '../../api/apiClient';

export const authService = {
    async login(email: string, password: string) {
        const response = await apiClient.post('/auth/login', { email, password });
        if (response.data.token) {
            localStorage.setItem('token', response.data.token);
        }
        return response.data;
    },

    async logout() {
        localStorage.removeItem('token');
    },

    async validateSession() {
        try {
            const response = await apiClient.get('/auth/validate');
            return response.data.valid === true;
        } catch {
            return false;
        }
    }
};