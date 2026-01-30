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
    }
};

export default settingsService;
