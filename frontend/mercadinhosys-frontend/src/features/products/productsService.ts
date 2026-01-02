// src/features/products/productsService.ts
import apiClient from '../../api/apiClient';

export const productsService = {
    async getEstoque() {
        const response = await apiClient.get('/api/produtos/estoque');
        return response.data;
    },

    async searchProdutos(query: string) {
        const response = await apiClient.get('/api/produtos/search', {
            params: { q: query }
        });
        return response.data;
    },

    async getProdutoByBarcode(codigo: string) {
        const response = await apiClient.get(`/api/produtos/barcode/${codigo}`);
        return response.data;
    }
};