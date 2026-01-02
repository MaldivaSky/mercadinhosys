// src/features/dashboard/dashboardService.ts
import apiClient from '../../api/apiClient';

export const dashboardService = {
    async getResumo() {
        const response = await apiClient.get('/api/dashboard/resumo');
        return response.data;
    },

    async getPainelAdmin() {
        const response = await apiClient.get('/api/dashboard/painel-admin');
        return response.data;
    },

    async getVendasPeriodo(startDate: string, endDate: string) {
        const response = await apiClient.get('/api/dashboard/vendas-periodo', {
            params: { start_date: startDate, end_date: endDate }
        });
        return response.data;
    }
};