import api from './api';

interface Produto {
    id: number;
    nome: string;
    preco: number;
    quantidadeEstoque: number;
    codigoBarras?: string;
}

export const produtoService = {
    listar: () => {
        console.log('🔄 Tentando listar produtos...');
        return api.get<Produto[]>('/produtos');
    },

    buscarPorId: (id: number) => {
        console.log(`🔍 Buscando produto ID: ${id}`);
        return api.get<Produto>(`/produtos/${id}`);
    },

    criar: (data: Omit<Produto, 'id'>) => {
        console.log('➕ Criando produto:', data);
        return api.post<Produto>('/produtos', data);
    },

    atualizar: (id: number, data: Partial<Produto>) => {
        console.log(`✏️ Atualizando produto ${id}:`, data);
        return api.put<Produto>(`/produtos/${id}`, data);
    },

    deletar: (id: number) => {
        console.log(`🗑️ Deletando produto ${id}`);
        return api.delete(`/produtos/${id}`);
    },
};