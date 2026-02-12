import { Edit, Trash2, Archive, ShoppingCart, FileText, ChevronLeft, ChevronRight, ArrowUpDown, ArrowUp, ArrowDown, Layers } from 'lucide-react';
import { Produto } from '../../../types';
import { formatCurrency } from '../../../utils/formatters';

interface ProductsTableProps {
    produtos: Produto[];
    loading: boolean;
    totalItems: number;
    page: number;
    totalPages: number;
    onPageChange: (page: number) => void;
    onEdit: (produto: Produto) => void;
    onDelete: (id: number) => void;
    onStockAdjust: (produto: Produto) => void;
    onHistory: (produto: Produto) => void;
    onMakeOrder: (produto: Produto) => void;
    onViewLotes?: (produto: Produto) => void;
    onSort?: (key: string) => void;
    sortConfig?: { key: string; direction: 'asc' | 'desc' };
}

export const ProductsTable: React.FC<ProductsTableProps> = ({
    produtos,
    loading,
    totalItems,
    page,
    totalPages,
    onPageChange,
    onEdit,
    onDelete,
    onStockAdjust,
    onHistory,
    onMakeOrder,
    onViewLotes,
    onSort,
    sortConfig,
}) => {

    const SortIcon = ({ columnKey }: { columnKey: string }) => {
        if (!sortConfig || sortConfig.key !== columnKey) {
            return <ArrowUpDown className="w-4 h-4 ml-1 text-gray-400 opacity-50" />;
        }
        return sortConfig.direction === 'asc' ?
            <ArrowUp className="w-4 h-4 ml-1 text-blue-600" /> :
            <ArrowDown className="w-4 h-4 ml-1 text-blue-600" />;
    };

    const handleSort = (key: string) => {
        if (onSort) onSort(key);
    };

    const getStockBadge = (produto: Produto) => {
        if (produto.quantidade <= 0) return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300';
        if (produto.quantidade <= produto.quantidade_minima) return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300';
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300';
    };

    const getStockLabel = (produto: Produto) => {
        if (produto.quantidade <= 0) return 'Esgotado';
        if (produto.quantidade <= produto.quantidade_minima) return 'Baixo';
        return 'Normal';
    };

    if (loading) {
        return (
            <div className="flex justify-center py-12">
                <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
            </div>
        );
    }

    return (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
            <div className="overflow-x-auto">
                <table className="w-full">
                    <thead className="bg-gray-50 dark:bg-gray-700">
                        <tr>
                            <th
                                className="px-4 py-3 text-left text-sm font-medium cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors group"
                                onClick={() => handleSort('nome')}
                            >
                                <div className="flex items-center">
                                    Produto
                                    <SortIcon columnKey="nome" />
                                </div>
                            </th>
                            <th
                                className="px-4 py-3 text-center text-sm font-medium cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors group"
                                onClick={() => handleSort('quantidade')}
                            >
                                <div className="flex items-center justify-center">
                                    Estoque
                                    <SortIcon columnKey="quantidade" />
                                </div>
                            </th>
                            <th className="px-4 py-3 text-center text-sm font-medium">Status</th>
                            <th className="px-4 py-3 text-center text-sm font-medium">Lote</th>
                            <th
                                className="px-4 py-3 text-center text-sm font-medium cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors group"
                                onClick={() => handleSort('data_validade')}
                            >
                                <div className="flex items-center justify-center">
                                    Validade
                                    <SortIcon columnKey="data_validade" />
                                </div>
                            </th>
                            <th
                                className="px-4 py-3 text-right text-sm font-medium cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors group"
                                onClick={() => handleSort('preco_custo')}
                            >
                                <div className="flex items-center justify-end">
                                    Custo
                                    <SortIcon columnKey="preco_custo" />
                                </div>
                            </th>
                            <th
                                className="px-4 py-3 text-right text-sm font-medium cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors group"
                                onClick={() => handleSort('preco_venda')}
                            >
                                <div className="flex items-center justify-end">
                                    Venda
                                    <SortIcon columnKey="preco_venda" />
                                </div>
                            </th>
                            <th
                                className="px-4 py-3 text-center text-sm font-medium cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors group"
                                onClick={() => handleSort('margem_lucro')}
                            >
                                <div className="flex items-center justify-center">
                                    Margem
                                    <SortIcon columnKey="margem_lucro" />
                                </div>
                            </th>
                            <th className="px-4 py-3 text-center text-sm font-medium">Ações</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                        {produtos.map((produto) => (
                            <tr key={produto.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                                <td className="px-4 py-3">
                                    <div className="font-medium text-gray-900 dark:text-white">{produto.nome}</div>
                                    <div className="text-sm text-gray-500">
                                        {produto.categoria} {produto.codigo_barras && `• ${produto.codigo_barras}`}
                                    </div>
                                </td>
                                <td className="px-4 py-3 text-center font-medium">
                                    {produto.quantidade} {produto.unidade_medida}
                                </td>
                                <td className="px-4 py-3 text-center">
                                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStockBadge(produto)}`}>
                                        {getStockLabel(produto)}
                                    </span>
                                </td>
                                <td className="px-4 py-3 text-center text-sm font-mono text-gray-600 dark:text-gray-400">
                                    {produto.lote || '-'}
                                </td>
                                <td className="px-4 py-3 text-center text-sm">
                                    {produto.data_validade ? (
                                        (() => {
                                            const hoje = new Date();
                                            const validade = new Date(produto.data_validade);
                                            const dias = Math.floor((validade.getTime() - hoje.getTime()) / (1000 * 60 * 60 * 24));
                                            return (
                                                <span className={`${dias < 0 ? 'text-red-700 font-bold' : dias <= 30 ? 'text-red-600 font-medium' : dias <= 90 ? 'text-yellow-600' : 'text-green-600'}`}>
                                                    {new Date(produto.data_validade).toLocaleDateString('pt-BR')}
                                                </span>
                                            );
                                        })()
                                    ) : (
                                        <span className="text-gray-400">-</span>
                                    )}
                                </td>
                                <td className="px-4 py-3 text-right">{formatCurrency(produto.preco_custo)}</td>
                                <td className="px-4 py-3 text-right font-medium">{formatCurrency(produto.preco_venda)}</td>
                                <td className="px-4 py-3 text-center">
                                    <span className={`font-medium ${(produto.margem_lucro || 0) >= 30 ? 'text-green-600' : 'text-orange-600'}`}>
                                        {(produto.margem_lucro || 0).toFixed(1)}%
                                    </span>
                                </td>
                                <td className="px-4 py-3">
                                    <div className="flex justify-center gap-1">
                                        <button
                                            onClick={() => onMakeOrder(produto)}
                                            className="p-1.5 text-orange-600 hover:bg-orange-50 rounded"
                                            title="Fazer Pedido"
                                        >
                                            <ShoppingCart className="w-4 h-4" />
                                        </button>
                                        {onViewLotes && (
                                            <button
                                                onClick={() => onViewLotes(produto)}
                                                className="p-1.5 text-purple-600 hover:bg-purple-50 rounded"
                                                title="Ver Lotes (FIFO)"
                                            >
                                                <Layers className="w-4 h-4" />
                                            </button>
                                        )}
                                        <button
                                            onClick={() => onHistory(produto)}
                                            className="p-1.5 text-blue-600 hover:bg-blue-50 rounded"
                                            title="Histórico"
                                        >
                                            <FileText className="w-4 h-4" />
                                        </button>
                                        <button
                                            onClick={() => onStockAdjust(produto)}
                                            className="p-1.5 text-green-600 hover:bg-green-50 rounded"
                                            title="Ajustar Estoque"
                                        >
                                            <Archive className="w-4 h-4" />
                                        </button>
                                        <button
                                            onClick={() => onEdit(produto)}
                                            className="p-1.5 text-yellow-600 hover:bg-yellow-50 rounded"
                                            title="Editar"
                                        >
                                            <Edit className="w-4 h-4" />
                                        </button>
                                        <button
                                            onClick={() => onDelete(produto.id)}
                                            className="p-1.5 text-red-600 hover:bg-red-50 rounded"
                                            title="Desativar"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 dark:border-gray-700">
                <div className="text-sm text-gray-600 dark:text-gray-400">
                    Mostrando {produtos.length} de {totalItems} produtos
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => onPageChange(Math.max(1, page - 1))}
                        disabled={page === 1}
                        className="p-2 border rounded-lg disabled:opacity-50"
                    >
                        <ChevronLeft className="w-5 h-5" />
                    </button>
                    <span className="px-3 py-1">
                        Página {page} de {totalPages}
                    </span>
                    <button
                        onClick={() => onPageChange(Math.min(totalPages, page + 1))}
                        disabled={page === totalPages}
                        className="p-2 border rounded-lg disabled:opacity-50"
                    >
                        <ChevronRight className="w-5 h-5" />
                    </button>
                </div>
            </div>
        </div>
    );
};
