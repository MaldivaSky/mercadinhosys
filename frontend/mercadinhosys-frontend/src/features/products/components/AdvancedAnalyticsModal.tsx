import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { X, BarChart3, Zap, Clock, TrendingDown } from 'lucide-react';
import { Produto } from '../../../types';
import { productsService } from '../productsService';
import { formatCurrency } from '../../../utils/formatters';
import { showToast } from '../../../utils/toast';

interface AdvancedAnalyticsModalProps {
    isOpen: boolean;
    onClose: () => void;
    type: string; // 'abc_a', 'abc_b', 'abc_c', 'giro_rapido', 'giro_normal', 'giro_lento'
}

const AdvancedAnalyticsModal: React.FC<AdvancedAnalyticsModalProps> = ({ isOpen, onClose, type }) => {
    const [loading, setLoading] = useState(false);
    const [produtosFiltrados, setProdutosFiltrados] = useState<Produto[]>([]);
    const navigate = useNavigate();

    useEffect(() => {
        if (isOpen && type) {
            carregarProdutos();
        }
    }, [isOpen, type]);

    const carregarProdutos = async () => {
        try {
            setLoading(true);
            // Fetch up to 1000 items to classify properly on frontend
            const response = await productsService.getAllEstoque(1, 1000, {});
            const allProducts = response.produtos || [];

            let filtered: Produto[] = [];

            if (type.startsWith('abc_')) {
                const faturamentoTotal = allProducts.reduce((sum, p) => sum + (p.total_vendido || 0), 0);
                const produtosComFaturamento = allProducts.map(p => ({
                    ...p,
                    faturamento: p.total_vendido || 0
                })).sort((a, b) => b.faturamento - a.faturamento);

                let acumulado = 0;
                const classA: Produto[] = [];
                const classB: Produto[] = [];
                const classC: Produto[] = [];

                if (faturamentoTotal === 0) {
                    classC.push(...allProducts);
                } else {
                    produtosComFaturamento.forEach(p => {
                        acumulado += p.faturamento;
                        const percentualAcumulado = acumulado / faturamentoTotal;

                        if (percentualAcumulado <= 0.80) classA.push(p);
                        else if (percentualAcumulado <= 0.95) classB.push(p);
                        else classC.push(p);
                    });
                }

                if (type === 'abc_a') filtered = classA;
                if (type === 'abc_b') filtered = classB;
                if (type === 'abc_c') filtered = classC;

            } else if (type.startsWith('giro_')) {
                const hoje = new Date();
                const rapido: Produto[] = [];
                const normal: Produto[] = [];
                const lento: Produto[] = [];

                allProducts.forEach(p => {
                    if (!p.ultima_venda) {
                        lento.push(p);
                    } else {
                        const dataUltimaVenda = new Date(p.ultima_venda);
                        const diasDesdeVenda = Math.floor((hoje.getTime() - dataUltimaVenda.getTime()) / (1000 * 60 * 60 * 24));

                        if (diasDesdeVenda <= 7) rapido.push(p);
                        else if (diasDesdeVenda <= 30) normal.push(p);
                        else lento.push(p);
                    }
                });

                if (type === 'giro_rapido') filtered = rapido;
                if (type === 'giro_normal') filtered = normal;
                if (type === 'giro_lento') filtered = lento;
            }

            setProdutosFiltrados(filtered);
        } catch (error) {
            console.error('Erro ao carregar produtos avançados:', error);
            showToast.error('Erro ao carregar lista de produtos');
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    const titulos: Record<string, string> = {
        'abc_a': 'Produtos Classe A (80% Faturamento)',
        'abc_b': 'Produtos Classe B (15% Faturamento)',
        'abc_c': 'Produtos Classe C (5% Faturamento)',
        'giro_rapido': 'Giro Rápido (Cobertura de até 15 dias)',
        'giro_normal': 'Giro Normal (Cobertura de 16 a 60 dias)',
        'giro_lento': 'Giro Lento (Cobertura acima de 60 dias)'
    };

    const isABC = type.startsWith('abc_');
    const headerColor = isABC ? 'bg-blue-100 text-blue-600' : 'bg-purple-100 text-purple-600';
    const Icon = isABC ? BarChart3 : (type === 'giro_rapido' ? Zap : (type === 'giro_normal' ? Clock : TrendingDown));

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[100] p-4 animate-in fade-in duration-300">
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden border border-gray-100 dark:border-gray-700">
                {/* Header */}
                <div className="p-6 border-b dark:border-gray-700 flex items-center justify-between bg-gradient-to-r from-gray-50 to-white dark:from-gray-900 dark:to-gray-800">
                    <div className="flex items-center gap-4">
                        <div className={`p-3 rounded-xl ${headerColor}`}>
                            <Icon className="w-6 h-6" />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-gray-900 dark:text-white">{titulos[type] || 'Análise de Produtos'}</h2>
                            <p className="text-sm text-gray-500 dark:text-gray-400">Total de {produtosFiltrados.length} produtos listados nesta categoria.</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full transition-colors">
                        <X className="w-6 h-6 text-gray-400" />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6">
                    {loading ? (
                        <div className="flex flex-col items-center justify-center py-20 gap-4">
                            <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
                            <p className="text-gray-500 font-medium">Analisando dados...</p>
                        </div>
                    ) : produtosFiltrados.length === 0 ? (
                        <div className="text-center py-20">
                            <div className="inline-flex items-center justify-center w-20 h-20 bg-gray-100 dark:bg-gray-700 rounded-full mb-4">
                                <Icon className="w-10 h-10 text-gray-400" />
                            </div>
                            <h3 className="text-lg font-bold text-gray-800 dark:text-white">Nenhum produto nesta categoria</h3>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            <div className="grid grid-cols-12 gap-4 px-4 py-2 text-xs font-bold text-gray-400 uppercase tracking-wider border-b dark:border-gray-700">
                                <div className="col-span-5">Produto</div>
                                <div className="col-span-2 text-right">Estoque</div>
                                <div className="col-span-2 text-right">Preço Venda</div>
                                <div className="col-span-3 text-right">Métrica Relevante</div>
                            </div>
                            {produtosFiltrados.map((p, idx) => {
                                return (
                                    <div key={`p-${p.id}-${idx}`} 
                                         onClick={() => {
                                             onClose();
                                             navigate(`/products/${p.id}`);
                                         }}
                                         className="grid grid-cols-12 gap-4 items-center p-4 bg-gray-50 dark:bg-gray-700/50 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-700 transition-all border border-transparent hover:border-blue-300 cursor-pointer">
                                        <div className="col-span-5">
                                            <p className="font-bold text-gray-900 dark:text-white truncate">{p.nome}</p>
                                            <p className="text-xs text-gray-500">
                                                {p.categoria} | Código: {p.codigo_barras || p.id}
                                            </p>
                                        </div>
                                        <div className="col-span-2 text-right">
                                            <p className={`text-sm font-bold ${p.quantidade <= 0 ? 'text-red-500' : 'text-gray-900 dark:text-white'}`}>
                                                {p.quantidade} {p.unidade_medida}
                                            </p>
                                        </div>
                                        <div className="col-span-2 text-right">
                                            <p className="text-sm font-medium text-green-600 dark:text-green-400">{formatCurrency(p.preco_venda)}</p>
                                        </div>
                                        <div className="col-span-3 text-right">
                                            {isABC ? (
                                                <div className="flex flex-col items-end">
                                                    <span className="text-sm font-bold text-blue-600">Fat: {formatCurrency(p.total_vendido || 0)}</span>
                                                </div>
                                            ) : (
                                                <div className="flex flex-col items-end">
                                                    <span className="text-sm font-medium text-purple-600">
                                                        {p.ultima_venda ? new Date(p.ultima_venda).toLocaleDateString() : 'Nunca vendido'}
                                                    </span>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="p-6 border-t dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50 flex justify-between items-center">
                    <p className="text-xs text-gray-500 italic">
                        {isABC ? '* A Classificação ABC é baseada no faturamento (preço x vendas).' : '* O Giro de Estoque é baseado na cobertura em dias considerando a Venda Média Diária.'}
                    </p>
                    <button onClick={onClose} className="px-6 py-2 text-gray-600 dark:text-gray-400 font-medium hover:bg-gray-200 dark:hover:bg-gray-800 rounded-xl transition-all">
                        Fechar
                    </button>
                </div>
            </div>
        </div>
    );
};

export default AdvancedAnalyticsModal;
