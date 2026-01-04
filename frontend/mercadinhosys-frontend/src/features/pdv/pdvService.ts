import { apiClient } from '../../api/apiClient';
import { ApiResponse, Produto, Cliente, Venda } from '../../types';

export const pdvService = {
    // Busca de produtos
    buscarProduto: async (query: string): Promise<Produto[]> => {
        const response = await apiClient.get<ApiResponse<Produto[]>>('/produtos/buscar', {
            params: { q: query },
        });
        return response.data.data!;
    },

    buscarProdutoPorCodigo: async (codigo: string): Promise<Produto> => {
        const response = await apiClient.get<ApiResponse<Produto>>(`/produtos/codigo/${codigo}`);
        return response.data.data!;
    },

    // Clientes
    buscarClientes: async (query: string): Promise<Cliente[]> => {
        const response = await apiClient.get<ApiResponse<Cliente[]>>('/clientes/buscar', {
            params: { q: query },
        });
        return response.data.data!;
    },

    // Criar venda
    criarVenda: async (data: any): Promise<Venda> => {
        const response = await apiClient.post<ApiResponse<Venda>>('/vendas', data);
        return response.data.data!;
    },

    // Cancelar venda
    cancelarVenda: async (id: number, motivo: string): Promise<void> => {
        await apiClient.delete(`/vendas/${id}`, { data: { motivo } });
    },

    // Formas de pagamento disponíveis
    getFormasPagamento: async (): Promise<any> => {
        const response = await apiClient.get<ApiResponse>('/configuracao/formas-pagamento');
        return response.data.data;
    },

    // Imprimir comprovante
    imprimirComprovante: async (vendaId: number): Promise<Blob> => {
        const response = await apiClient.get(`/vendas/${vendaId}/comprovante`, {
            responseType: 'blob',
        });
        return response.data;
    },
};