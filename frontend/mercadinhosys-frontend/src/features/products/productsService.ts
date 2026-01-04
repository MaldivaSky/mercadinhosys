import { apiClient } from '../../api/apiClient';
import { ApiResponse, Produto } from '../../types';

export const productsService = {
    getAll: async (page = 1, perPage = 20, filters?: any): Promise<ApiResponse<Produto[]>> => {
        const response = await apiClient.get<ApiResponse<Produto[]>>('/produtos', {
            params: {
                page,
                per_page: perPage,
                ...filters
            },
        });
        return response.data;
    },

    getById: async (id: number): Promise<Produto> => {
        const response = await apiClient.get<ApiResponse<Produto>>(`/produtos/${id}`);
        return response.data.data!;
    },

    create: async (data: Partial<Produto>): Promise<Produto> => {
        const response = await apiClient.post<ApiResponse<Produto>>('/produtos', data);
        return response.data.data!;
    },

    update: async (id: number, data: Partial<Produto>): Promise<Produto> => {
        const response = await apiClient.put<ApiResponse<Produto>>(`/produtos/${id}`, data);
        return response.data.data!;
    },

    delete: async (id: number): Promise<void> => {
        await apiClient.delete(`/produtos/${id}`);
    },

    updateStock: async (id: number, quantidade: number): Promise<Produto> => {
        const response = await apiClient.patch<ApiResponse<Produto>>(`/produtos/${id}/estoque`, {
            quantidade,
        });
        return response.data.data!;
    },

    getLowStock: async (): Promise<Produto[]> => {
        const response = await apiClient.get<ApiResponse<Produto[]>>('/produtos/baixo-estoque');
        return response.data.data!;
    },

    // Novas funções baseadas no models.py
    search: async (query: string): Promise<Produto[]> => {
        const response = await apiClient.get<ApiResponse<Produto[]>>('/produtos/buscar', {
            params: { q: query },
        });
        return response.data.data!;
    },

    getByCategory: async (categoria: string): Promise<Produto[]> => {
        const response = await apiClient.get<ApiResponse<Produto[]>>('/produtos/categoria', {
            params: { categoria },
        });
        return response.data.data!;
    },

    getByBarcode: async (codigo: string): Promise<Produto> => {
        const response = await apiClient.get<ApiResponse<Produto>>(`/produtos/codigo/${codigo}`);
        return response.data.data!;
    },
};