import { apiClient } from '../../api/apiClient';
import { LoginRequest, LoginResponse, ApiResponse } from '../../types';

export const authService = {
    login: async (credentials: LoginRequest): Promise<LoginResponse> => {
        const response = await apiClient.post<ApiResponse<LoginResponse>>('/auth/login', credentials);
        return response.data.data!;
    },

    logout: async (): Promise<void> => {
        await apiClient.post('/auth/logout');
    },

    refreshToken: async (refreshToken: string): Promise<{ access_token: string }> => {
        const response = await apiClient.post<ApiResponse<{ access_token: string }>>('/auth/refresh', {
            refresh_token: refreshToken,
        });
        return response.data.data!;
    },

    getProfile: async (): Promise<any> => {
        const response = await apiClient.get<ApiResponse>('/auth/profile');
        return response.data.data;
    },
};