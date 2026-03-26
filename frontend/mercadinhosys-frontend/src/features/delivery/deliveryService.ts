import { apiClient } from '../../api/apiClient';

export interface Motorista {
    id: number;
    nome: string;
    cpf: string;
    celular?: string;
    ativo: boolean;
    disponivel: boolean;
    total_entregas: number;
    avaliacao_media: number;
}

export interface Veiculo {
    id: number;
    placa: string;
    modelo: string;
    tipo: string;
    ativo: boolean;
}

export interface TaxaEntrega {
    id: number;
    nome_regiao: string;
    taxa_fixa: number;
    tempo_estimado_minutos: number;
}

export interface Entrega {
    id: number;
    codigo_rastreamento: string;
    venda_id: number;
    cliente_nome?: string;
    status: 'pendente' | 'em_preparo' | 'em_rota' | 'entregue' | 'cancelada';
    endereco_completo: string;
    endereco_bairro: string;
    data_prevista: string;
    taxa_entrega: number;
    motorista_nome?: string;
}

export const deliveryService = {
    getStats: async () => {
        const response = await apiClient.get('/delivery/stats');
        return response.data;
    },

    getEntregas: async (status?: string) => {
        const params = status && status !== 'todos' ? `?status=${status}` : '';
        const response = await apiClient.get(`/delivery/entregas${params}`);
        return response.data;
    },

    getMotoristas: async () => {
        const response = await apiClient.get('/delivery/motoristas');
        return response.data;
    },

    getVeiculos: async () => {
        const response = await apiClient.get('/delivery/veiculos');
        return response.data;
    },

    getTaxas: async () => {
        const response = await apiClient.get('/delivery/taxas');
        return response.data;
    },

    atualizarStatus: async (id: number, status: string, data: any) => {
        const response = await apiClient.put(`/delivery/entregas/${id}/status`, { status, ...data });
        return response.data;
    },

    getVendasPendentes: async () => {
        const response = await apiClient.get('/delivery/vendas-pendentes');
        return response.data;
    },

    criarEntrega: async (data: any) => {
        const response = await apiClient.post('/delivery/entregas', data);
        return response.data;
    },

    criarVendaEntrega: async (data: any) => {
        const response = await apiClient.post('/delivery/venda-entrega', data);
        return response.data;
    }
};
