import { apiClient } from '../../api/apiClient';
import { ApiResponse, DashboardMetrics, DashboardDonoMetrics } from '../../types';

// Mapeia a resposta do backend para o formato esperado pelo frontend
const mapBackendToDashboardMetrics = (backendData: any): DashboardMetrics => {
    console.log('Backend raw data:', backendData);
    
    return {
        total_vendas_hoje: backendData?.hoje?.total_vendas || 0,
        total_vendas_mes: backendData?.mes?.total_vendas || 0,
        ticket_medio: backendData?.hoje?.ticket_medio || 0,
        clientes_novos_mes: backendData?.analise_temporal?.clientes_novos_mes || 0,
        produtos_baixo_estoque: backendData?.alertas?.estoque_baixo?.length || 0,
        despesas_mes: backendData?.mes?.total_despesas || 0,
        lucro_mes: backendData?.mes?.lucro_bruto || 0,
        vendas_por_categoria: backendData?.analise_temporal?.vendas_por_categoria || [],
        vendas_ultimos_7_dias: backendData?.analise_temporal?.vendas_ultimos_7_dias || [],
    };
};

export const dashboardService = {
    getMetrics: async (): Promise<DashboardMetrics> => {
        const response = await apiClient.get<ApiResponse<any>>('/dashboard/resumo');
        console.log('API Response:', response.data);
        
        // O backend retorna {success: true, data: {hoje: {...}, mes: {...}}}
        const backendData = response.data.data;
        return mapBackendToDashboardMetrics(backendData);
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