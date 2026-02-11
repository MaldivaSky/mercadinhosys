import React from 'react';
import { X, Package, Calendar, Truck, DollarSign, User, FileText } from 'lucide-react';
import { PedidoCompra, PedidoCompraItem } from '../purchaseOrderService';
import { formatCurrency, formatDate } from '../../../utils/formatters';

interface PurchaseOrderDetailsModalProps {
    isOpen: boolean;
    onClose: () => void;
    pedido: PedidoCompra | null;
}

const PurchaseOrderDetailsModal: React.FC<PurchaseOrderDetailsModalProps> = ({
    isOpen,
    onClose,
    pedido
}) => {
    if (!isOpen || !pedido) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                            <Package className="w-6 h-6 text-blue-600 dark:text-blue-300" />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-gray-800 dark:text-white">
                                Pedido {pedido.numero_pedido}
                            </h2>
                            <p className="text-sm text-gray-500 dark:text-gray-400">
                                Criado em {formatDate(pedido.data_pedido)}
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                    {/* Status Bar */}
                    <div className="flex items-center gap-4 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-700">
                        <div className={`px-3 py-1 rounded-full text-sm font-medium ${pedido.status === 'recebido'
                            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
                            : pedido.status === 'cancelado'
                                ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
                                : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
                            }`}>
                            {pedido.status.toUpperCase()}
                        </div>
                        {pedido.data_previsao_entrega && (
                            <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300">
                                <Truck className="w-4 h-4" />
                                <span>Previsão: {formatDate(pedido.data_previsao_entrega)}</span>
                            </div>
                        )}
                        {pedido.data_recebimento && (
                            <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300">
                                <Calendar className="w-4 h-4" />
                                <span>Recebido: {formatDate(pedido.data_recebimento)}</span>
                            </div>
                        )}
                    </div>

                    {/* Info Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-4">
                            <h3 className="font-semibold text-gray-800 dark:text-white flex items-center gap-2">
                                <Truck className="w-4 h-4" /> Fornecedor
                            </h3>
                            <div className="p-4 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg">
                                <p className="font-medium text-gray-900 dark:text-white">{pedido.fornecedor_nome}</p>
                                {pedido.fornecedor && (
                                    <>
                                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{pedido.fornecedor.cnpj}</p>
                                        <p className="text-sm text-gray-500 dark:text-gray-400">{pedido.fornecedor.email}</p>
                                    </>
                                )}
                            </div>
                        </div>

                        <div className="space-y-4">
                            <h3 className="font-semibold text-gray-800 dark:text-white flex items-center gap-2">
                                <User className="w-4 h-4" /> Solicitante
                            </h3>
                            <div className="p-4 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg">
                                <p className="font-medium text-gray-900 dark:text-white">{pedido.funcionario_nome || 'N/A'}</p>
                                {pedido.funcionario && (
                                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{pedido.funcionario.cargo || 'Funcionário'}</p>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Items Table */}
                    <div className="space-y-4">
                        <h3 className="font-semibold text-gray-800 dark:text-white flex items-center gap-2">
                            <Package className="w-4 h-4" /> Itens do Pedido
                        </h3>
                        <div className="overflow-x-auto border border-gray-200 dark:border-gray-700 rounded-lg">
                            <table className="w-full">
                                <thead className="bg-gray-50 dark:bg-gray-700 text-xs uppercase text-gray-500 dark:text-gray-400 font-medium">
                                    <tr>
                                        <th className="px-4 py-3 text-left">Produto</th>
                                        <th className="px-4 py-3 text-center">Unidade</th>
                                        <th className="px-4 py-3 text-center">Qtd. Solicitada</th>
                                        <th className="px-4 py-3 text-center">Qtd. Recebida</th>
                                        <th className="px-4 py-3 text-right">Preço Unit.</th>
                                        <th className="px-4 py-3 text-right">Desc. %</th>
                                        <th className="px-4 py-3 text-right">Total</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                                    {pedido.itens?.map((item: PedidoCompraItem) => (
                                        <tr key={item.id} className="bg-white dark:bg-gray-800">
                                            <td className="px-4 py-3">
                                                <p className="font-medium text-gray-900 dark:text-white text-sm">{item.produto_nome}</p>
                                            </td>
                                            <td className="px-4 py-3 text-center text-sm text-gray-600 dark:text-gray-400">
                                                {item.produto_unidade}
                                            </td>
                                            <td className="px-4 py-3 text-center text-sm font-medium text-gray-900 dark:text-white">
                                                {item.quantidade_solicitada}
                                            </td>
                                            <td className="px-4 py-3 text-center text-sm">
                                                <span className={`${item.quantidade_recebida && item.quantidade_recebida < item.quantidade_solicitada
                                                    ? 'text-orange-600 font-medium'
                                                    : item.quantidade_recebida === item.quantidade_solicitada
                                                        ? 'text-green-600 font-medium'
                                                        : 'text-gray-500'
                                                    }`}>
                                                    {item.quantidade_recebida || '-'}
                                                </span>
                                            </td>
                                            <td className="px-4 py-3 text-right text-sm text-gray-600 dark:text-gray-400">
                                                {formatCurrency(item.preco_unitario)}
                                            </td>
                                            <td className="px-4 py-3 text-right text-sm text-gray-600 dark:text-gray-400">
                                                {item.desconto_percentual}%
                                            </td>
                                            <td className="px-4 py-3 text-right text-sm font-medium text-gray-900 dark:text-white">
                                                {formatCurrency(item.total_item)}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                                <tfoot className="bg-gray-50 dark:bg-gray-700 font-semibold text-gray-900 dark:text-white text-sm">
                                    <tr>
                                        <td colSpan={6} className="px-4 py-3 text-right">Subtotal:</td>
                                        <td className="px-4 py-3 text-right">{formatCurrency(pedido.subtotal)}</td>
                                    </tr>
                                    {pedido.desconto > 0 && (
                                        <tr>
                                            <td colSpan={6} className="px-4 py-3 text-right text-green-600">Desconto:</td>
                                            <td className="px-4 py-3 text-right text-green-600">-{formatCurrency(pedido.desconto)}</td>
                                        </tr>
                                    )}
                                    {pedido.frete > 0 && (
                                        <tr>
                                            <td colSpan={6} className="px-4 py-3 text-right text-orange-600">Frete:</td>
                                            <td className="px-4 py-3 text-right text-orange-600">+{formatCurrency(pedido.frete)}</td>
                                        </tr>
                                    )}
                                    <tr>
                                        <td colSpan={6} className="px-4 py-3 text-right text-base font-bold">Total:</td>
                                        <td className="px-4 py-3 text-right text-base font-bold text-blue-600 dark:text-blue-400">{formatCurrency(pedido.total)}</td>
                                    </tr>
                                </tfoot>
                            </table>
                        </div>
                    </div>

                    {/* Observations & Payment Info */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {pedido.observacoes && (
                            <div className="bg-yellow-50 dark:bg-yellow-900/10 p-4 rounded-lg border border-yellow-200 dark:border-yellow-800">
                                <h3 className="text-sm font-bold text-yellow-800 dark:text-yellow-200 mb-2 flex items-center gap-2">
                                    <FileText className="w-4 h-4" /> Observações
                                </h3>
                                <p className="text-sm text-yellow-800 dark:text-yellow-200 whitespace-pre-line">
                                    {pedido.observacoes}
                                </p>
                            </div>
                        )}

                        <div className="bg-gray-50 dark:bg-gray-700/50 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
                            <h3 className="text-sm font-bold text-gray-800 dark:text-white mb-2 flex items-center gap-2">
                                <DollarSign className="w-4 h-4" /> Pagamento
                            </h3>
                            <div className="space-y-2 text-sm">
                                <div className="flex justify-between">
                                    <span className="text-gray-600 dark:text-gray-400">Condição:</span>
                                    <span className="font-medium text-gray-900 dark:text-white">{pedido.condicao_pagamento || 'N/A'}</span>
                                </div>
                                {pedido.numero_nota_fiscal && (
                                    <div className="flex justify-between">
                                        <span className="text-gray-600 dark:text-gray-400">Nota Fiscal:</span>
                                        <span className="font-medium text-gray-900 dark:text-white">{pedido.numero_nota_fiscal} (Série: {pedido.serie_nota_fiscal})</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                </div>

                {/* Footer */}
                <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end">
                    <button
                        onClick={onClose}
                        className="px-6 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-white rounded-lg transition-colors font-medium"
                    >
                        Fechar
                    </button>
                </div>
            </div>
        </div>
    );
};

export default PurchaseOrderDetailsModal;
