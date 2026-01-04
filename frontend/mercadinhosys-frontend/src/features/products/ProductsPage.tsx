import React, { useState, useEffect } from 'react';
import { Package, Plus, Search, Filter, Edit, Trash2, Eye } from 'lucide-react';
import { Produto } from '../../types';
import { productsService } from './productsService';
import { formatCurrency } from '../../utils/formatters';

const ProductsPage: React.FC = () => {
    const [produtos, setProdutos] = useState<Produto[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);

    useEffect(() => {
        loadProdutos();
    }, [page, searchTerm]);

    const loadProdutos = async () => {
        try {
            setLoading(true);
            const response = await productsService.getAll(page, 20, {
                search: searchTerm,
                ativo: true,
            });
            setProdutos(response.data || []);
            setTotalPages(response.pagination?.total_pages || 1);
        } catch (error) {
            console.error('Erro ao carregar produtos:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id: number) => {
        if (window.confirm('Tem certeza que deseja excluir este produto?')) {
            try {
                await productsService.delete(id);
                loadProdutos();
            } catch (error) {
                console.error('Erro ao excluir produto:', error);
                alert('Erro ao excluir produto');
            }
        }
    };

    return (
        <div className="space-y-6">
            {/* Cabeçalho */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-gray-800 dark:text-white">
                        Gestão de Produtos
                    </h1>
                    <p className="text-gray-600 dark:text-gray-400">
                        Gerencie o catálogo de produtos do seu estabelecimento
                    </p>
                </div>
                <button className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 flex items-center space-x-2">
                    <Plus className="w-5 h-5" />
                    <span>Novo Produto</span>
                </button>
            </div>

            {/* Filtros e Busca */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
                <div className="flex flex-col md:flex-row gap-4">
                    <div className="flex-1 relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                        <input
                            type="text"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            placeholder="Buscar produtos por nome, código ou categoria..."
                            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                    </div>
                    <div className="flex space-x-2">
                        <button className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg flex items-center space-x-2">
                            <Filter className="w-5 h-5" />
                            <span>Filtrar</span>
                        </button>
                        <button
                            onClick={loadProdutos}
                            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                        >
                            Atualizar
                        </button>
                    </div>
                </div>
            </div>

            {/* Cards de Resumo */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-500 dark:text-gray-400">Total Produtos</p>
                            <p className="text-2xl font-bold text-gray-800 dark:text-white">
                                {produtos.length}
                            </p>
                        </div>
                        <div className="p-3 bg-blue-100 dark:bg-blue-900 rounded-lg">
                            <Package className="w-6 h-6 text-blue-500 dark:text-blue-400" />
                        </div>
                    </div>
                </div>

                <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-500 dark:text-gray-400">Valor Total Estoque</p>
                            <p className="text-2xl font-bold text-gray-800 dark:text-white">
                                R$ {produtos.reduce((sum, p) => sum + (p.preco_custo * p.quantidade_estoque), 0).toFixed(2)}
                            </p>
                        </div>
                        <div className="p-3 bg-green-100 dark:bg-green-900 rounded-lg">
                            <Package className="w-6 h-6 text-green-500 dark:text-green-400" />
                        </div>
                    </div>
                </div>

                <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-500 dark:text-gray-400">Produtos Baixo Estoque</p>
                            <p className="text-2xl font-bold text-gray-800 dark:text-white">
                                {produtos.filter(p => p.quantidade_estoque <= p.estoque_minimo).length}
                            </p>
                        </div>
                        <div className="p-3 bg-yellow-100 dark:bg-yellow-900 rounded-lg">
                            <Package className="w-6 h-6 text-yellow-500 dark:text-yellow-400" />
                        </div>
                    </div>
                </div>

                <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-500 dark:text-gray-400">Média Margem Lucro</p>
                            <p className="text-2xl font-bold text-gray-800 dark:text-white">
                                {produtos.length > 0
                                    ? (produtos.reduce((sum, p) => sum + p.margem_lucro, 0) / produtos.length).toFixed(1) + '%'
                                    : '0%'
                                }
                            </p>
                        </div>
                        <div className="p-3 bg-purple-100 dark:bg-purple-900 rounded-lg">
                            <Package className="w-6 h-6 text-purple-500 dark:text-purple-400" />
                        </div>
                    </div>
                </div>
            </div>

            {/* Tabela de Produtos */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead className="bg-gray-50 dark:bg-gray-700">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                                    Produto
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                                    Estoque
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                                    Preços
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                                    Categoria
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                                    Status
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                                    Ações
                                </th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                            {loading ? (
                                <tr>
                                    <td colSpan={6} className="px-6 py-12 text-center">
                                        <div className="flex justify-center">
                                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
                                        </div>
                                    </td>
                                </tr>
                            ) : produtos.length === 0 ? (
                                <tr>
                                    <td colSpan={6} className="px-6 py-12 text-center">
                                        <div className="flex flex-col items-center">
                                            <Package className="w-16 h-16 text-gray-300 dark:text-gray-600 mb-4" />
                                            <p className="text-gray-500 dark:text-gray-400">
                                                Nenhum produto encontrado
                                            </p>
                                        </div>
                                    </td>
                                </tr>
                            ) : (
                                produtos.map((produto) => (
                                    <tr key={produto.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                                        <td className="px-6 py-4">
                                            <div className="flex items-center">
                                                <div className="flex-shrink-0 h-10 w-10 bg-gray-100 dark:bg-gray-600 rounded flex items-center justify-center">
                                                    {produto.imagem_url ? (
                                                        <img
                                                            src={produto.imagem_url}
                                                            alt={produto.nome}
                                                            className="h-10 w-10 rounded object-cover"
                                                        />
                                                    ) : (
                                                        <Package className="w-6 h-6 text-gray-500" />
                                                    )}
                                                </div>
                                                <div className="ml-4">
                                                    <div className="text-sm font-medium text-gray-900 dark:text-white">
                                                        {produto.nome}
                                                    </div>
                                                    <div className="text-sm text-gray-500 dark:text-gray-400">
                                                        {produto.codigo_barras}
                                                    </div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="text-sm text-gray-900 dark:text-white">
                                                {produto.quantidade_estoque} {produto.unidade_medida}
                                            </div>
                                            {produto.quantidade_estoque <= produto.estoque_minimo && (
                                                <div className="text-xs text-red-500">
                                                    Mínimo: {produto.estoque_minimo}
                                                </div>
                                            )}
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="text-sm">
                                                <div className="font-medium text-gray-900 dark:text-white">
                                                    Venda: {formatCurrency(produto.preco_venda)}
                                                </div>
                                                <div className="text-gray-500 dark:text-gray-400">
                                                    Custo: {formatCurrency(produto.preco_custo)}
                                                </div>
                                                <div className={`text-sm ${produto.margem_lucro >= 50 ? 'text-green-500' : 'text-yellow-500'}`}>
                                                    Margem: {produto.margem_lucro?.toFixed(1) || 0}%
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-300">
                                                {produto.categoria}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${produto.ativo
                                                    ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-300'
                                                    : 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-300'
                                                }`}>
                                                {produto.ativo ? 'Ativo' : 'Inativo'}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex space-x-2">
                                                <button className="p-1 text-blue-500 hover:text-blue-700">
                                                    <Eye className="w-5 h-5" />
                                                </button>
                                                <button className="p-1 text-yellow-500 hover:text-yellow-700">
                                                    <Edit className="w-5 h-5" />
                                                </button>
                                                <button
                                                    onClick={() => handleDelete(produto.id)}
                                                    className="p-1 text-red-500 hover:text-red-700"
                                                >
                                                    <Trash2 className="w-5 h-5" />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Paginação */}
                {totalPages > 1 && (
                    <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700">
                        <div className="flex items-center justify-between">
                            <button
                                onClick={() => setPage(p => Math.max(1, p - 1))}
                                disabled={page === 1}
                                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg disabled:opacity-50"
                            >
                                Anterior
                            </button>
                            <div className="text-sm text-gray-700 dark:text-gray-300">
                                Página <span className="font-medium">{page}</span> de{' '}
                                <span className="font-medium">{totalPages}</span>
                            </div>
                            <button
                                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                                disabled={page === totalPages}
                                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg disabled:opacity-50"
                            >
                                Próxima
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ProductsPage;