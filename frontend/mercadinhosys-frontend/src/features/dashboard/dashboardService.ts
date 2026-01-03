import { apiClient } from '../../api/apiClient';
import { ApiResponse, DashboardMetrics, DashboardDonoMetrics } from '../../types';

export const dashboardService = {
    getMetrics: async (): Promise<DashboardMetrics> => {
        const response = await apiClient.get<ApiResponse<DashboardMetrics>>('/dashboard');
        return response.data.data!;
    },

    getOwnerMetrics: async (): Promise<DashboardDonoMetrics> => {
        const response = await apiClient.get<ApiResponse<DashboardDonoMetrics>>('/dashboard/dono');
        return response.data.data!;
    },

    getSalesByPeriod: async (startDate: string, endDate: string) => {
        const response = await apiClient.get<ApiResponse>('/dashboard/vendas-periodo', {
            params: { start_date: startDate, end_date: endDate },
        });
        return response.data.data;
    },
};