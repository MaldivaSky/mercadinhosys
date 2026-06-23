import { useState, useEffect } from 'react';
import { X, Clock, Package, DollarSign, Calendar } from 'lucide-react';
import { Fornecedor } from '../../../types';
import { apiClient } from '../../../api/apiClient';
import { formatCurrency, formatDate } from '../../../utils/formatters';

interface SupplierHistoryModalProps {
    fornecedor: Fornecedor;
    onClose: () => void;
}

const SupplierHistoryModal = ({ fornecedor, onClose }: SupplierHistoryModalProps) => {
    const [activeTab, setActiveTab] = useState<'compras' | 'financeiro'>('compras');
    const [pedidos, setPedidos] = useState<any[]>([]);
    const [despesas, setDespesas] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadData = async () => {
            setLoading(true);
            try {
                // 1. Carregar Pedidos
                const resPedidos = await apiClient.get('/pedidos-compra/', { params: { fornecedor_id: fornecedor.id, per_page: 50 } });
                setPedidos(resPedidos.data.pedidos || []);

                // 2. Carregar Despesas
                // Nota: O backend precisa permitir filtrar despesas por fornecedor_id, 
                // assumindo que buscarDespesas permite isso ou pelo menos retorna as do mes
                const resDespesas = await apiClient.get('/despesas', { params: { fornecedor_id: fornecedor.id, por_pagina: 50 } });
                setDespesas(resDespesas.data.data || []);
            } catch (error) {
                console.error("Erro ao carregar histórico", error);
            } finally {
                setLoading(false);
            }
        };
        loadData();
    }, [fornecedor.id]);

    const stats = {
        totalPedidos: pedidos.length,
        valorTotalPedidos: pedidos.reduce((sum, p) => sum + (p.total || 0), 0),
        pedidosConcluidos: pedidos.filter(p => p.status === 'Entregue' || p.status === 'Concluído').length,
        totalDespesasPagas: despesas.filter(d => d.forma_pagamento && !d.data_vencimento || new Date(d.data_vencimento) < new Date()).reduce((sum, d) => sum + (d.valor || 0), 0)
    };

    return (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-[130] p-4">
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden">
                <div className="p-6 bg-gradient-to-r from-blue-600 to-indigo-700 flex items-center justify-between">
                    <div>
                        <h2 className="text-2xl font-black text-white flex items-center gap-2">
                            <Clock className="w-6 h-6" /> Dossiê: {fornecedor.nome_fantasia || fornecedor.razao_social}
                        </h2>
                        <p className="text-blue-100 mt-1 opacity-80 text-sm">{fornecedor.cnpj}</p>
                    </div>
                    <button onClick={onClose} className="p-2 text-white hover:bg-white/20 rounded-xl transition-all">
                        <X className="w-5 h-5" />
                    </button>
                </div>

                <div className="flex border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50 px-6">
                    <button
                        onClick={() => setActiveTab('compras')}
                        className={`py-4 px-6 font-bold text-sm border-b-2 transition-colors flex items-center gap-2 ${activeTab === 'compras' ? 'border-blue-600 text-blue-600 dark:text-blue-400' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
                    >
                        <Package className="w-4 h-4" /> Histórico de Pedidos
                    </button>
                    <button
                        onClick={() => setActiveTab('financeiro')}
                        className={`py-4 px-6 font-bold text-sm border-b-2 transition-colors flex items-center gap-2 ${activeTab === 'financeiro' ? 'border-blue-600 text-blue-600 dark:text-blue-400' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
                    >
                        <DollarSign className="w-4 h-4" /> Financeiro (Contas)
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto p-6 bg-gray-50 dark:bg-gray-900">
                    {loading ? (
                        <div className="py-20 flex justify-center"><div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600"></div></div>
                    ) : activeTab === 'compras' ? (
                        <div className="space-y-6">
                            <div className="grid grid-cols-3 gap-4">
                                <div className="bg-white dark:bg-gray-800 p-4 rounded-xl border border-gray-200 dark:border-gray-700">
                                    <p className="text-xs font-bold text-gray-500 uppercase">Pedidos Emitidos</p>
                                    <p className="text-2xl font-black text-gray-900 dark:text-white">{stats.totalPedidos}</p>
                                </div>
                                <div className="bg-white dark:bg-gray-800 p-4 rounded-xl border border-gray-200 dark:border-gray-700">
                                    <p className="text-xs font-bold text-gray-500 uppercase">Pedidos Atendidos</p>
                                    <p className="text-2xl font-black text-green-600 dark:text-green-400">{stats.pedidosConcluidos}</p>
                                </div>
                                <div className="bg-white dark:bg-gray-800 p-4 rounded-xl border border-gray-200 dark:border-gray-700">
                                    <p className="text-xs font-bold text-gray-500 uppercase">Volume Comprado</p>
                                    <p className="text-2xl font-black text-blue-600 dark:text-blue-400">{formatCurrency(stats.valorTotalPedidos)}</p>
                                </div>
                            </div>
                            
                            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
                                <table className="w-full text-left text-sm">
                                    <thead className="bg-gray-100 dark:bg-gray-700/50 text-gray-500 font-bold uppercase text-xs">
                                        <tr>
                                            <th className="px-4 py-3">Data</th>
                                            <th className="px-4 py-3">Pedido N.</th>
                                            <th className="px-4 py-3 text-right">Valor</th>
                                            <th className="px-4 py-3 text-center">Status</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                                        {pedidos.map(p => (
                                            <tr key={p.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                                                <td className="px-4 py-3 font-medium text-gray-800 dark:text-white">{formatDate(p.data_pedido || p.created_at)}</td>
                                                <td className="px-4 py-3 text-gray-600 dark:text-gray-300">#{p.numero_pedido}</td>
                                                <td className="px-4 py-3 text-right font-bold text-gray-900 dark:text-white">{formatCurrency(p.total)}</td>
                                                <td className="px-4 py-3 text-center">
                                                    <span className={`px-2 py-1 text-[10px] uppercase font-black rounded-full ${p.status === 'Entregue' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>{p.status}</span>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-6">
                            <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-200 dark:border-gray-700">
                                <h3 className="font-bold text-gray-800 dark:text-white mb-4">Lançamentos Financeiros (Contas a Pagar/Pagas)</h3>
                                {despesas.length > 0 ? (
                                    <div className="space-y-3">
                                        {despesas.map(d => (
                                            <div key={d.id} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg border border-gray-100 dark:border-gray-700">
                                                <div>
                                                    <p className="font-bold text-gray-800 dark:text-white">{d.descricao}</p>
                                                    <p className="text-xs text-gray-500 flex items-center gap-1 mt-1"><Calendar className="w-3 h-3"/> {formatDate(d.data_despesa)}</p>
                                                </div>
                                                <div className="text-right">
                                                    <p className="font-black text-red-500">{formatCurrency(d.valor)}</p>
                                                    <p className="text-xs text-gray-500 mt-1">{d.forma_pagamento || 'Boleto'}</p>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="py-10 text-center opacity-50">
                                        <DollarSign className="w-10 h-10 mx-auto mb-2 text-gray-400"/>
                                        <p className="text-sm font-bold">Nenhuma despesa vinculada diretamente a este fornecedor.</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default SupplierHistoryModal;
