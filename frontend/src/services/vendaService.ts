import api from './api';

// Interfaces ajustadas para snake_case (como o backend espera)
interface ItemVendaDTO {
    produto_id: number;  // ← AGORA É snake_case
    quantidade: number;
}

interface VendaDTO {
    cliente_id?: number | null;  // ← AGORA É snake_case
    itens: ItemVendaDTO[];
    forma_pagamento: string;  // ← AGORA É snake_case
}

interface Venda {
    id: number;
    numero: string;
    data: string;
    cliente_id?: number;
    forma_pagamento: string;
    total: number;
    itens: Array<{
        produto_id: number;
        quantidade: number;
        preco_unitario: number;
    }>;
}

export const vendaService = {
    listar: () => api.get<Venda[]>('/vendas'),
    buscarPorId: (id: number) => api.get<Venda>(`/vendas/${id}`),

    criar: (data: VendaDTO) => {
        console.log('📤 Enviando venda para API:', data);
        return api.post<Venda>('/vendas', data);
    },

    atualizar: (id: number, data: Partial<VendaDTO>) => api.put<Venda>(`/vendas/${id}`, data),
    deletar: (id: number) => api.delete(`/vendas/${id}`),
};