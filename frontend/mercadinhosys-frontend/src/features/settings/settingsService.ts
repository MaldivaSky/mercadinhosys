import { apiClient } from '../../api/apiClient';

export interface Estabelecimento {
    id: number;
    nome_fantasia: string;
    razao_social: string;
    cnpj: string;
    inscricao_estadual?: string;
    telefone: string;
    email: string;
    cep: string;
    logradouro: string;
    numero: string;
    complemento?: string;
    bairro: string;
    cidade: string;
    estado: string;
    regime_tributario?: string;
}

export interface Configuracao {
    id: number;
    estabelecimento_id: number;
    logo_url?: string;
    logo_base64?: string;
    cor_principal: string;
    tema_escuro: boolean;

    // Vendas
    emitir_nfe: boolean;
    emitir_nfce: boolean;
    impressao_automatica: boolean;
    tipo_impressora: 'termica_80mm' | 'termica_58mm' | 'a4';
    exibir_preco_tela: boolean;
    permitir_venda_sem_estoque: boolean;
    desconto_maximo_percentual: number;
    desconto_maximo_funcionario: number;
    arredondamento_valores: boolean;
    formas_pagamento: string[];

    // Estoque
    controlar_validade: boolean;
    alerta_estoque_minimo: boolean;
    dias_alerta_validade: number;
    estoque_minimo_padrao: number;

    // Sistema
    tempo_sessao_minutos: number;
    tentativas_senha_bloqueio: number;
    alertas_email: boolean;
    alertas_whatsapp: boolean;

    // Localização do estabelecimento
    latitude_estabelecimento?: number;
    longitude_estabelecimento?: number;
    raio_validacao_metros?: number;

    // Horários de ponto
    hora_entrada_ponto?: string;
    hora_saida_almoco_ponto?: string;
    hora_retorno_almoco_ponto?: string;
    hora_saida_ponto?: string;

    // Validação de ponto
    exigir_foto_ponto?: boolean;
    exigir_localizacao_ponto?: boolean;
    tolerancia_atraso_minutos?: number;
}

export interface SubscriptionStatus {
    plano: string;
    status: string;
    vencimento: string | null;
    is_active: boolean;
}

const settingsService = {
    getConfig: async () => {
        const response = await apiClient.get<{ success: boolean; config: Configuracao }>('/configuracao/');
        return response.data.config;
    },

    updateConfig: async (data: Partial<Configuracao>) => {
        const response = await apiClient.put<{ success: boolean; config: Configuracao }>('/configuracao/', data);
        return response.data.config;
    },

    getEstabelecimento: async () => {
        const response = await apiClient.get<{ success: boolean; estabelecimento: Estabelecimento }>('/configuracao/estabelecimento');
        return response.data.estabelecimento;
    },

    updateEstabelecimento: async (data: Partial<Estabelecimento>) => {
        const response = await apiClient.put<{ success: boolean; estabelecimento: Estabelecimento }>('/configuracao/estabelecimento', data);
        return response.data.estabelecimento;
    },

    uploadLogo: async (file: File) => {
        const formData = new FormData();
        formData.append('logo', file);
        const response = await apiClient.post<{ success: boolean; logo_url: string }>('/configuracao/logo', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data.logo_url;
    },

    getSubscriptionStatus: async () => {
        const response = await apiClient.get<{ success: boolean; data: SubscriptionStatus }>('/saas/assinatura/status');
        return response.data.data;
    },

    createCheckoutSession: async (planName: string) => {
        const response = await apiClient.post<{ success: boolean; checkout_url: string }>('/stripe/checkout', { plan_name: planName });
        return response.data;
    },

    openPortal: async () => {
        const response = await apiClient.post<{ success: boolean; portal_url: string }>('/stripe/portal', {});
        return response.data;
    }
};

export default settingsService;
