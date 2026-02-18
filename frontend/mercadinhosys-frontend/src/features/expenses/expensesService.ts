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

export interface AlertaFinanceiro {
    tipo: string;
    severidade: 'critica' | 'alta' | 'media' | 'baixa';
    titulo: string;
    descricao: string;
    acao: string;
}

export interface ResumoFinanceiro {
    success: boolean;
    periodo: {
        inicio: string;
        fim: string;
    };
    indicadores_gestao: {
        indice_comprometimento: number;
        pressao_caixa_diaria: number;
        venda_media_diaria: number;
        vence_hoje_valor: number;
    };
    contas_pagar: {
        total_aberto: number;
        total_vencido: number;
        vence_hoje: number;
        vence_7_dias: number;
        vence_30_dias: number;
        pago_no_mes: number;
        qtd_vencidos: number;
        qtd_vence_hoje: number;
        qtd_vence_7d: number;
    };
    despesas_mes: {
        total: number;
        recorrentes: number;
        variaveis: number;
    };
    fluxo_caixa_real: {
        entradas: number;
        saidas: number;
        saldo: number;
    };
    dre_consolidado: {
        receita_bruta: number;
        custo_mercadoria: number;
        lucro_bruto: number;
        despesas_operacionais: number;
        lucro_liquido: number;
    };
    alertas: AlertaFinanceiro[];
    total_alertas: number;
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

    async resumoFinanceiro(): Promise<ResumoFinanceiro> {
        const response = await apiClient.get("/despesas/resumo-financeiro/");
        return response.data;
    },
};
