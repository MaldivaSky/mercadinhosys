import { apiClient } from "../../api/apiClient";

export interface Despesa {
    id: number;
    descricao: string;
    categoria: string;
    tipo: 'fixa' | 'variavel';
    valor: number;
    data_despesa: string;
    forma_pagamento?: string;
    recorrente: boolean;
    fornecedor?: {
        id: number;
        nome: string;
    };
    observacoes?: string;
    created_at: string;
}

export interface Estatisticas {
    total_despesas: number;
    soma_total: number;
    media_valor: number;
    despesas_mes_atual: number;
    despesas_mes_anterior: number;
    variacao_percentual: number;
    despesas_recorrentes: number;
    despesas_nao_recorrentes: number;
    despesas_por_categoria: Array<{
        categoria: string;
        total: number;
        quantidade: number;
        percentual: number;
    }>;
    evolucao_mensal?: Array<{
        mes: string;
        total: number;
        mes_nome: string;
    }>;
}

export interface FiltrosDespesas {
    inicio?: string;
    fim?: string;
    categoria?: string;
    tipo?: string;
    recorrente?: string;
    busca?: string;
    pagina?: number;
    por_pagina?: number;
}

export const expensesService = {
    async listar(filtros: FiltrosDespesas = {}) {
        const response = await apiClient.get("/despesas", { params: filtros });
        return response.data;
    },

    async obterEstatisticas(filtros: { inicio?: string; fim?: string } = {}) {
        const response = await apiClient.get("/despesas/estatisticas", { params: filtros });
        return response.data.estatisticas;
    },

    async criar(despesa: Partial<Despesa>) {
        const response = await apiClient.post("/despesas", despesa);
        return response.data.data;
    },

    async atualizar(id: number, despesa: Partial<Despesa>) {
        const response = await apiClient.put(`/despesas/${id}`, despesa);
        return response.data.data;
    },

    async excluir(id: number) {
        const response = await apiClient.delete(`/despesas/${id}`);
        return response.data;
    },
};
