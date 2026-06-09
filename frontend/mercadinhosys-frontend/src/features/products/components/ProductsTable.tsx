import React from 'react';
import { Edit, Trash2, Archive, ShoppingCart, FileText, ChevronLeft, ChevronRight, ArrowUpDown, ArrowUp, ArrowDown, Layers, PackageX, MoreHorizontal } from 'lucide-react';
import { Produto } from '../../../types';
import { formatCurrency } from '../../../utils/formatters';

export interface LinhaProdutoLote {
    produto: Produto & { lotes_no_periodo?: Array<{ id: number | null; numero_lote: string; data_validade: string | null; quantidade: number; preco_venda: number | null; preco_produto: number }> };
    lote: { id: number | null; numero_lote: string; data_validade: string | null; quantidade: number; preco_venda: number | null; preco_produto: number } | null;
}

interface ProductsTableProps {
    produtos: Produto[];
    linhasPorLote?: LinhaProdutoLote[];
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
    onDiscard: (produto: Produto) => void;
    onViewLotes?: (produto: Produto) => void;
    onProductClick?: (produto: Produto) => void;
    onSort?: (key: string) => void;
    sortConfig?: { key: string; direction: 'asc' | 'desc' };
}

export const ProductsTable: React.FC<ProductsTableProps> = ({
    produtos = [],
    linhasPorLote,
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
    onDiscard,
    onViewLotes,
    onProductClick,
    onSort,
    sortConfig,
}) => {

    const SortIcon = ({ columnKey }: { columnKey: string }) => {
        if (!sortConfig || sortConfig.key !== columnKey) {
            return <ArrowUpDown className="w-3.5 h-3.5 ml-1 text-slate-600 opacity-0 group-hover:opacity-100 transition-opacity" />;
        }
        return sortConfig.direction === 'asc' ?
            <ArrowUp className="w-3.5 h-3.5 ml-1 text-blue-500" /> :
            <ArrowDown className="w-3.5 h-3.5 ml-1 text-blue-500" />;
    };

    const handleSort = (key: string) => {
        if (onSort) onSort(key);
    };

    const getStockBadge = (produto: Produto) => {
        if (produto.quantidade <= 0) return 'bg-rose-500/10 text-rose-500 border-rose-500/20';
        if (produto.quantidade <= produto.quantidade_minima) return 'bg-amber-500/10 text-amber-500 border-amber-500/20';
        return 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20';
    };

    const getStockLabel = (produto: Produto) => {
        if (produto.quantidade <= 0) return 'Esgotado';
        if (produto.quantidade <= produto.quantidade_minima) return 'Baixo';
        return 'Normal';
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center py-24 bg-slate-900 rounded-2xl border border-slate-800">
                <div className="relative w-12 h-12">
                    <div className="absolute inset-0 border-t-2 border-blue-500 rounded-full animate-spin"></div>
                    <div className="absolute inset-2 border-r-2 border-emerald-500 rounded-full animate-spin reverse"></div>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl shadow-xl overflow-hidden flex flex-col">
            <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                    <thead className="bg-slate-900/90 backdrop-blur-sm sticky top-0 z-10 border-b border-slate-800">
                        <tr>
                            <th 
                                className="px-5 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider cursor-pointer hover:text-white transition-colors group"
                                onClick={() => handleSort('nome')}
                            >
                                <div className="flex items-center">
                                    Produto
                                    <SortIcon columnKey="nome" />
                                </div>
                            </th>
                            <th 
                                className="px-5 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider cursor-pointer hover:text-white transition-colors group"
                                onClick={() => handleSort('quantidade')}
                            >
                                <div className="flex items-center">
                                    Estoque
                                    <SortIcon columnKey="quantidade" />
                                </div>
                            </th>
                            <th className="px-5 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Status</th>
                            <th className="px-5 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Lote</th>
                            <th 
                                className="px-5 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider cursor-pointer hover:text-white transition-colors group"
                                onClick={() => handleSort('data_validade')}
                            >
                                <div className="flex items-center">
                                    Validade
                                    <SortIcon columnKey="data_validade" />
                                </div>
                            </th>
                            <th 
                                className="px-5 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider cursor-pointer hover:text-white transition-colors group text-right"
                                onClick={() => handleSort('preco_custo')}
                            >
                                <div className="flex items-center justify-end">
                                    Custo
                                    <SortIcon columnKey="preco_custo" />
                                </div>
                            </th>
                            <th 
                                className="px-5 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider cursor-pointer hover:text-white transition-colors group text-right"
                                onClick={() => handleSort('preco_venda')}
                            >
                                <div className="flex items-center justify-end">
                                    Venda
                                    <SortIcon columnKey="preco_venda" />
                                </div>
                            </th>
                            <th 
                                className="px-5 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider cursor-pointer hover:text-white transition-colors group text-right"
                                onClick={() => handleSort('margem_lucro')}
                            >
                                <div className="flex items-center justify-end">
                                    Margem
                                    <SortIcon columnKey="margem_lucro" />
                                </div>
                            </th>
                            <th className="px-5 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider text-right">
                                {/* Placeholder for actions */}
                            </th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/50">
                        {(produtos || []).map((produto) => (
                            <tr key={produto.id} className="hover:bg-slate-800/50 transition-colors group cursor-pointer" onClick={(e) => {
                                // Prevent navigating if clicking on buttons
                                const target = e.target as HTMLElement;
                                if (!target.closest('.actions-container')) {
                                    onProductClick?.(produto);
                                }
                            }}>
                                <td className="px-5 py-3">
                                    <div className="font-semibold text-slate-200">{produto.nome}</div>
                                    <div className="text-xs text-slate-500 mt-0.5 flex items-center gap-2">
                                        <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">{produto.categoria}</span>
                                        {produto.codigo_barras && <span>{produto.codigo_barras}</span>}
                                    </div>
                                </td>
                                <td className="px-5 py-3 tabular-nums font-medium text-slate-300">
                                    {produto.quantidade} <span className="text-xs text-slate-500">{produto.unidade_medida}</span>
                                </td>
                                <td className="px-5 py-3">
                                    <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border ${getStockBadge(produto)}`}>
                                        {getStockLabel(produto)}
                                    </span>
                                </td>
                                <td className="px-5 py-3">
                                    {produto.lote ? (
                                        <span className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono text-[10px] uppercase tracking-wider">
                                            {produto.lote}
                                        </span>
                                    ) : (
                                        <span className="text-slate-600">-</span>
                                    )}
                                </td>
                                <td className="px-5 py-3 text-sm">
                                    {produto.data_validade ? (
                                        (() => {
                                            const hoje = new Date();
                                            const validade = new Date(produto.data_validade);
                                            const dias = Math.floor((validade.getTime() - hoje.getTime()) / (1000 * 60 * 60 * 24));

                                            if (dias < 0) {
                                                return (
                                                    <div className="flex flex-col">
                                                        <span className="text-rose-500 font-medium tabular-nums">{new Date(produto.data_validade).toLocaleDateString('pt-BR')}</span>
                                                        <span className="text-[9px] text-rose-500/70 uppercase tracking-widest font-bold">Vencido</span>
                                                    </div>
                                                );
                                            }
                                            if (dias <= 30) {
                                                return (
                                                    <div className="flex flex-col">
                                                        <span className="text-amber-500 font-medium tabular-nums">{new Date(produto.data_validade).toLocaleDateString('pt-BR')}</span>
                                                        <span className="text-[9px] text-amber-500/70 uppercase tracking-widest font-bold">{dias} Dias</span>
                                                    </div>
                                                );
                                            }
                                            return (
                                                <div className="flex flex-col">
                                                    <span className="text-emerald-500 font-medium tabular-nums">
                                                        {new Date(produto.data_validade).toLocaleDateString('pt-BR')}
                                                    </span>
                                                    <span className="text-[9px] text-emerald-500/70 uppercase tracking-widest font-bold">No Prazo</span>
                                                </div>
                                            );
                                        })()
                                    ) : (
                                        <span className="text-slate-600">-</span>
                                    )}
                                </td>
                                <td className="px-5 py-3 text-right tabular-nums text-slate-400 font-medium">
                                    {formatCurrency(produto.preco_custo)}
                                </td>
                                <td className="px-5 py-3 text-right tabular-nums text-white font-bold">
                                    {formatCurrency(produto.preco_venda)}
                                </td>
                                <td className="px-5 py-3 text-right">
                                    <div className="flex items-center justify-end gap-2">
                                        <span className={`font-semibold tabular-nums ${(produto.margem_lucro || 0) >= 30 ? 'text-emerald-400' : 'text-amber-400'}`}>
                                            {(produto.margem_lucro || 0).toFixed(1)}%
                                        </span>
                                        <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: (produto.margem_lucro || 0) >= 30 ? '#10b981' : '#f59e0b' }}></div>
                                    </div>
                                </td>
                                <td className="px-5 py-3 text-right actions-container">
                                    <div className="flex justify-end opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                                        <div className="flex items-center gap-1 bg-slate-800 p-1 rounded-lg border border-slate-700 shadow-xl">
                                            <button onClick={() => onMakeOrder(produto)} className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded-md transition-colors" title="Fazer Pedido">
                                                <ShoppingCart className="w-4 h-4" />
                                            </button>
                                            <button onClick={() => onStockAdjust(produto)} className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded-md transition-colors" title="Ajustar Estoque">
                                                <Archive className="w-4 h-4" />
                                            </button>
                                            <button onClick={() => onEdit(produto)} className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded-md transition-colors" title="Editar">
                                                <Edit className="w-4 h-4" />
                                            </button>
                                            
                                            {/* Dropdown for secondary actions if needed, or just keep them inline for now */}
                                            <div className="w-px h-4 bg-slate-700 mx-1"></div>
                                            
                                            {onViewLotes && (
                                                <button onClick={() => onViewLotes(produto)} className="p-1.5 text-slate-400 hover:text-purple-400 hover:bg-slate-700 rounded-md transition-colors" title="Ver Lotes (FIFO)">
                                                    <Layers className="w-4 h-4" />
                                                </button>
                                            )}
                                            <button onClick={() => onHistory(produto)} className="p-1.5 text-slate-400 hover:text-blue-400 hover:bg-slate-700 rounded-md transition-colors" title="Histórico">
                                                <FileText className="w-4 h-4" />
                                            </button>
                                            <button onClick={() => onDiscard(produto)} className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-700 rounded-md transition-colors" title="Descartar (Prejuízo)">
                                                <PackageX className="w-4 h-4" />
                                            </button>
                                            <button onClick={() => onDelete(produto.id)} className="p-1.5 text-slate-400 hover:text-rose-500 hover:bg-slate-700 rounded-md transition-colors" title="Excluir">
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </div>
                                    {/* Small dots icon when not hovered to indicate actions exist */}
                                    <div className="flex justify-end opacity-100 group-hover:opacity-0 transition-opacity duration-200 absolute right-8 mt-[-10px]">
                                        <MoreHorizontal className="w-5 h-5 text-slate-600" />
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Pagination - Sleek Dark */}
            <div className="flex items-center justify-between px-6 py-4 bg-slate-900 border-t border-slate-800">
                <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                    {linhasPorLote && linhasPorLote.length > 0
                        ? `Exibindo ${linhasPorLote.length} de ${produtos.length}`
                        : `Mostrando ${produtos.length} de ${totalItems} registros`}
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => onPageChange(Math.max(1, page - 1))}
                        disabled={page === 1}
                        className="p-2 border border-slate-700 rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white disabled:opacity-30 disabled:hover:bg-transparent disabled:hover:text-slate-400 transition-colors"
                    >
                        <ChevronLeft className="w-4 h-4" />
                    </button>
                    <span className="px-4 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-sm font-semibold text-slate-200 tabular-nums">
                        {page} / {totalPages}
                    </span>
                    <button
                        onClick={() => onPageChange(Math.min(totalPages, page + 1))}
                        disabled={page === totalPages}
                        className="p-2 border border-slate-700 rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white disabled:opacity-30 disabled:hover:bg-transparent disabled:hover:text-slate-400 transition-colors"
                    >
                        <ChevronRight className="w-4 h-4" />
                    </button>
                </div>
            </div>
        </div>
    );
};
