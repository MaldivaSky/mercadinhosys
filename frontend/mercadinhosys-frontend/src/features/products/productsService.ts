import { apiClient } from '../../api/apiClient';
import { ApiResponse, Produto, ProdutosResponse, ProdutoFiltros } from '../../types';

export const productsService = {
    // ==================== ROTAS PDV ====================
    search: async (query: string, limit = 20): Promise<Produto[]> => {
        const response = await apiClient.get<Produto[]>('/produtos/search', {
            params: { q: query, limit },
        });
        return response.data;
    },

    getByBarcode: async (codigo: string): Promise<Produto> => {
        const response = await apiClient.get<Produto>(`/produtos/barcode/${codigo}`);
        return response.data;
    },

    quickAdd: async (data: Partial<Produto>): Promise<Produto> => {
        const response = await apiClient.post<Produto>('/produtos/quick-add', data);
        return response.data;
    },

    // ==================== CRUD COMPLETO ESTOQUE ====================
    getAllEstoque: async (pagina = 1, porPagina = 50, filtros?: ProdutoFiltros): Promise<ProdutosResponse> => {
        const params: any = {
            pagina,
            por_pagina: porPagina,
        };

        if (filtros) {
            if (filtros.busca) params.busca = filtros.busca;
            if (filtros.categoria) params.categoria = filtros.categoria;
            if (filtros.fornecedor_id) params.fornecedor_id = filtros.fornecedor_id;
            if (filtros.ativos !== undefined) params.ativos = filtros.ativos;
            if (filtros.preco_min) params.preco_min = filtros.preco_min;
            if (filtros.preco_max) params.preco_max = filtros.preco_max;
            if (filtros.estoque_status) params.estoque_status = filtros.estoque_status;
            if (filtros.tipo) params.tipo = filtros.tipo;
            if (filtros.ordenar_por) params.ordenar_por = filtros.ordenar_por;
            if (filtros.direcao) params.direcao = filtros.direcao;
        }

        const response = await apiClient.get<ProdutosResponse>('/produtos/estoque', { params });
        return response.data;
    },

    getById: async (id: number): Promise<Produto> => {
        const response = await apiClient.get<Produto>(`/produtos/estoque/${id}`);
        return response.data;
    },

    create: async (data: Partial<Produto>): Promise<{ success: boolean; message: string; produto: Produto }> => {
        const response = await apiClient.post<any>('/produtos/estoque', data);
        return response.data;
    },

    update: async (id: number, data: Partial<Produto>): Promise<{ success: boolean; message: string; produto: Produto }> => {
        const response = await apiClient.put<any>(`/produtos/estoque/${id}`, data);
        return response.data;
    },

    delete: async (id: number): Promise<{ success: boolean; message: string }> => {
        const response = await apiClient.delete<any>(`/produtos/estoque/${id}`);
        return response.data;
    },

    ajustarEstoque: async (
        id: number,
        quantidade: number,
        operacao: 'entrada' | 'saida',
        motivo?: string
    ): Promise<{ success: boolean; message: string; produto: any }> => {
        const response = await apiClient.put<any>(`/produtos/estoque/${id}/estoque`, {
            quantidade,
            operacao,
            motivo,
        });
        return response.data;
    },

    // ==================== CATEGORIAS E RELATÓRIOS ====================
    getCategorias: async (ativos = true): Promise<{ categorias: string[]; total_categorias: number }> => {
        const response = await apiClient.get<any>('/produtos/categorias', {
            params: { ativos },
        });
        return response.data;
    },

    getRelatorioEstoque: async (
        pagina = 1,
        porPagina = 100,
        filtros?: { categoria?: string; estoque_status?: string; ativos?: boolean }
    ): Promise<any> => {
        const params: any = { pagina, por_pagina: porPagina };
        if (filtros) {
            if (filtros.categoria) params.categoria = filtros.categoria;
            if (filtros.estoque_status) params.estoque_status = filtros.estoque_status;
            if (filtros.ativos !== undefined) params.ativos = filtros.ativos;
        }
        const response = await apiClient.get<any>('/produtos/relatorio/estoque', { params });
        return response.data;
    },

    exportarCSV: async (ativos = true): Promise<{ success: boolean; csv: string; total_produtos: number }> => {
        const response = await apiClient.get<any>('/produtos/exportar/csv', {
            params: { ativos },
        });
        return response.data;
    },

    // ==================== FUNÇÕES ANTIGAS (MANTER COMPATIBILIDADE) ====================
    getAll: async (page = 1, perPage = 20, filters?: any): Promise<ApiResponse<Produto[]>> => {
        const response = await productsService.getAllEstoque(page, perPage, filters);
        return {
            success: true,
            data: response.produtos,
            pagination: {
                page: response.paginacao.pagina_atual,
                per_page: response.paginacao.itens_por_pagina,
                total: response.paginacao.total_itens,
                total_pages: response.paginacao.total_paginas,
            },
        };
    },

    updateStock: async (id: number, quantidade: number): Promise<Produto> => {
        const response = await productsService.ajustarEstoque(id, quantidade, 'entrada');
        return response.produto;
    },

    getLowStock: async (): Promise<Produto[]> => {
        const response = await productsService.getAllEstoque(1, 100, { estoque_status: 'baixo' });
        return response.produtos;
    },

    getByCategory: async (categoria: string): Promise<Produto[]> => {
        const response = await productsService.getAllEstoque(1, 100, { categoria });
        return response.produtos;
    },
};