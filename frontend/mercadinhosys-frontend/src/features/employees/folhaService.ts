import { apiClient } from '../../api/apiClient';

/** Serviço de Folha & RH+: retrospectiva, rescisão e provisões (custo real). */

export type TipoRescisao = 'PEDIDO' | 'S_JUSTA' | 'C_JUSTA' | 'ACORDO';

export interface LinhaFolha { descricao: string; referencia: string; valor: number; }

export interface HoleriteBreakdown {
    funcionario_id: number;
    nome: string;
    cargo: string;
    cpf: string;
    data_admissao: string | null;
    mes_referencia: string;
    salario_base: number;
    horas_extras_horas: number;
    atrasos_horas: number;
    vencimentos: LinhaFolha[];
    descontos: LinhaFolha[];
    totais: { vencimentos: number; descontos: number; liquido: number; base_inss: number; fgts_mes: number; };
    memoria_calculo: string[];
}

export interface ConfiguracaoFolha {
    divisor_horas_mensais: number;
    percentual_hora_extra: number;
    percentual_adicional_noturno: number;
    fgts_percentual: number;
    multa_fgts_dispensa: number;
    multa_fgts_acordo: number;
    desconto_vt_percentual: number;
    deducao_por_dependente: number;
    inss_faixas: { ate: number | null; aliquota: number }[];
    irrf_faixas: { ate: number | null; aliquota: number; deducao: number }[];
}

export interface RetrospectivaData {
    funcionario_id: number;
    nome: string;
    cargo: string;
    periodo: { inicio: string; fim: string };
    persona: string;
    ponto: {
        horas_trabalhadas: number;
        horas_extras: number;
        dias_trabalhados: number;
        total_atrasos: number;
    };
    vendas: {
        total_vendas: number;
        faturamento: number;
        ticket_medio: number;
        clientes_atendidos: number;
        produtos_passados: number;
    };
    estoque: {
        mercadorias_conferidas: number;
        itens_conferidos: number;
    };
    entrega?: {
        entregas_realizadas: number;
        km_percorridos: number;
        clientes_atendidos: number;
        bairros_visitados: number;
        produtos_transportados: number;
    };
}

export interface VerbaRescisoria {
    codigo: string;
    descricao: string;
    referencia: string;
    valor: number;
}

export interface RescisaoData {
    tipo_rescisao: TipoRescisao;
    data_admissao: string;
    data_demissao: string;
    anos_completos: number;
    salario_base: number;
    saldo_fgts: number;
    saldo_fgts_estimado: boolean;
    proventos: VerbaRescisoria[];
    descontos: VerbaRescisoria[];
    total_proventos: number;
    total_descontos: number;
    total_liquido_estimado: number;
    memoria_calculo: string[];
    aviso_legal: string;
}

export interface ProvisaoItem {
    funcionario_id: number;
    funcionario_nome: string;
    cargo?: string;
    ano_mes: string;
    salario_base: number;
    valor_ferias: number;
    valor_decimo_terceiro: number;
    encargos_provisionados: number;
    beneficios?: number;
    custo_real: number;
}

export interface ProvisoesResposta {
    data: ProvisaoItem[];
    resumo: {
        ano_mes: string;
        funcionarios: number;
        folha_nominal: number;
        custo_real_total: number;
        provisionamento_total: number;
    };
}

interface RescisaoPayload {
    funcionario_id: number;
    data_demissao: string;
    tipo_rescisao: TipoRescisao;
    saldo_fgts?: number | null;
    ferias_vencidas_dias?: number;
}

export interface RescisaoRegistro {
    id: number;
    funcionario_id: number;
    funcionario_nome: string | null;
    cargo: string | null;
    data_demissao: string;
    tipo_rescisao: TipoRescisao;
    total_liquido: number;
    registrada_em: string | null;
    detalhe: RescisaoData;
}

const folhaService = {
    getRetrospectiva: async (params: { funcionario_id?: number; ano_mes?: string; data_inicio?: string; data_fim?: string } = {}) => {
        const { data } = await apiClient.get<{ success: boolean; data: RetrospectivaData }>('/rh/retrospectiva', { params });
        return data.data;
    },

    simularRescisao: async (payload: RescisaoPayload) => {
        const { data } = await apiClient.post<{ success: boolean; data: RescisaoData }>('/rh/rescisao/simular', payload);
        return data.data;
    },

    registrarRescisao: async (payload: RescisaoPayload) => {
        const { data } = await apiClient.post<{ success: boolean; data: RescisaoData; rescisao_id: number }>('/rh/rescisao', payload);
        return data;
    },

    listarRescisoes: async (params: { funcionario_id?: number; tipo_rescisao?: string; data_inicio?: string; data_fim?: string } = {}) => {
        const { data } = await apiClient.get<{ success: boolean; data: RescisaoRegistro[]; total: number }>('/rh/rescisoes', { params });
        return data.data;
    },

    listarProvisoes: async (ano_mes?: string) => {
        const { data } = await apiClient.get<{ success: boolean } & ProvisoesResposta>('/rh/provisoes', { params: ano_mes ? { ano_mes } : {} });
        return { data: data.data, resumo: data.resumo };
    },

    getHolerite: async (params: { funcionario_id?: number; mes_referencia?: string } = {}) => {
        const { data } = await apiClient.get<{ success: boolean; data: HoleriteBreakdown }>('/rh/holerite', { params });
        return data.data;
    },

    getConfigFolha: async () => {
        const { data } = await apiClient.get<{ success: boolean; data: ConfiguracaoFolha }>('/rh/configuracao-folha');
        return data.data;
    },

    updateConfigFolha: async (payload: Partial<ConfiguracaoFolha>) => {
        const { data } = await apiClient.put<{ success: boolean; data: ConfiguracaoFolha }>('/rh/configuracao-folha', payload);
        return data.data;
    },
};

export default folhaService;
