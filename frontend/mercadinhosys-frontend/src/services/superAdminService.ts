import { apiClient } from '../api/apiClient';

export interface EstabelecimentoAtivo {
    id: number;
    nome_fantasia: string;
    razao_social: string;
    cnpj: string;
    cidade: string;
    estado: string;
    plano: string;
    plano_status: string;
    ativo: boolean;
    vendas_hoje: number;
    total_vendas: number;
    produtos_count: number;
    funcionarios_count: number;
    created_at?: string;
    vencimento_assinatura?: string;
}

export interface DashboardEspecifico {
    estabelecimento: EstabelecimentoAtivo;
    metricas: {
        vendas_periodo: {
            quantidade: number;
            valor: number;
        };
        vendas_hoje: {
            quantidade: number;
            valor: number;
        };
        produtos: {
            ativos: number;
            baixo_estoque: number;
        };
        funcionarios: {
            ativos: number;
        };
    };
    periodo_analise: number;
    data_geracao: string;
}

export interface ResumoSistema {
    sistema: {
        total_estabelecimentos: number;
        total_funcionarios: number;
        total_produtos: number;
        vendas_totais: {
            quantidade: number;
            valor: number;
        };
        vendas_30_dias: {
            quantidade: number;
            valor: number;
        };
    };
    top_estabelecimentos: Array<{
        estabelecimento_id: number;
        nome_fantasia: string;
        vendas_quantidade: number;
        vendas_valor: number;
    }>;
    data_geracao: string;
}

export const superAdminService = {
    // Listar estabelecimentos ativos
    listarEstabelecimentosAtivos: async (): Promise<{ success: boolean; estabelecimentos: EstabelecimentoAtivo[] }> => {
        const response = await apiClient.get('/super-admin-dashboard/estabelecimentos-ativos');
        return response.data;
    },

    // Obter dashboard de estabelecimento específico
    getDashboardEstabelecimento: async (estabelecimentoId: number): Promise<{ success: boolean; dashboard: DashboardEspecifico }> => {
        const response = await apiClient.get(`/super-admin-dashboard/selecionar-estabelecimento/${estabelecimentoId}`);
        return response.data;
    },

    // Obter resumo do sistema
    getResumoSistema: async (): Promise<{ success: boolean; resumo: ResumoSistema }> => {
        const response = await apiClient.get('/super-admin-dashboard/resumo-sistema');
        return response.data;
    },

    // Sincronizar dados
    sincronizarDados: async (): Promise<{ success: boolean; message: string; status: string; timestamp: string }> => {
        const response = await apiClient.post('/super-admin-dashboard/sincronizar-dados');
        return response.data;
    },

    // Health check
    healthCheck: async (): Promise<{ success: boolean; message: string; timestamp: string }> => {
        const response = await apiClient.get('/super-admin-dashboard/health');
        return response.data;
    }
};
