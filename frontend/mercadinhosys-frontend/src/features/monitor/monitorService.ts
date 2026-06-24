import { apiClient } from '../../api/apiClient';

export interface LogAuditoria {
    id: number;
    estabelecimento_id: number;
    estabelecimento_nome: string;
    usuario_id: number | null;
    usuario_nome: string;
    tipo_evento: string;
    descricao: string;
    valor: number;
    data_evento: string;
    detalhes: Record<string, unknown>;
}

export const monitorService = {
    listar: async (params: { page?: number; tipo?: string; q?: string } = {}): Promise<{
        logs: LogAuditoria[];
        paginacao: { pagina: number; total_paginas: number; total: number };
    }> => {
        const { data } = await apiClient.get('/auditoria/', { params: { per_page: 30, ...params } });
        return data;
    },

    resumo: async (): Promise<{ tipo: string; total: number }[]> => {
        const { data } = await apiClient.get('/auditoria/resumo');
        return data.tipos || [];
    },
};

export default monitorService;
