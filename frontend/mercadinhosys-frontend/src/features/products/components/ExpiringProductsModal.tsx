import React, { useState, useEffect } from 'react';
import { X, Calendar, AlertTriangle, TrendingDown } from 'lucide-react';
import { Produto } from '../../../types';
import { productsService } from '../productsService';
import { formatCurrency } from '../../../utils/formatters';
import { toast } from 'react-hot-toast';

interface ExpiringProductsModalProps {
    isOpen: boolean;
    onClose: () => void;
    timeframe: 'vencidos' | '15' | '30' | '90';
}

const ExpiringProductsModal: React.FC<ExpiringProductsModalProps> = ({ isOpen, onClose, timeframe }) => {
    const [loading, setLoading] = useState(false);
    const [produtos, setProdutos] = useState<Produto[]>([]);

    useEffect(() => {
        if (isOpen) {
            carregarProdutos();
        }
    }, [isOpen, timeframe]);

    const carregarProdutos = async () => {
        try {
            setLoading(true);
            const params: any = { por_pagina: 100 };

            if (timeframe === 'vencidos') {
                params.vencidos = true;
            } else {
                params.validade_proxima = true;
                params.dias_validade = parseInt(timeframe);
            }

            const response = await productsService.getAllEstoque(1, 100, params);
            setProdutos(response.produtos);
        } catch (error) {
            console.error('Erro ao carregar produtos expirando:', error);
            toast.error('Erro ao carregar lista de produtos');
        } finally {
            setLoading(false);
        }
    };

    const getSugestao = () => {
        if (timeframe === 'vencidos') return { acao: 'Descarte', cor: 'text-red-600', desconto: 0 };
        if (timeframe === '15') return { acao: 'Queima de Estoque', cor: 'text-orange-600', desconto: 0.3 };
        if (timeframe === '30') return { acao: 'Promoção', cor: 'text-yellow-600', desconto: 0.15 };
        return { acao: 'Monitorar', cor: 'text-blue-600', desconto: 0 };
    };

    const handleApplyPromotions = async () => {
        const sugestao = getSugestao();
        if (sugestao.desconto === 0) return;

        try {
            setLoading(true);
            const atualizacoes = produtos.map(p => ({
                id: p.id,
                novo_preco: parseFloat((p.preco_venda * (1 - sugestao.desconto)).toFixed(2))
            }));

            const response = await productsService.bulkUpdatePrices(atualizacoes);

            if (response.success) {
                toast.success(response.message);
                onClose();
            } else {
                toast.error(response.message || 'Erro ao aplicar promoções');
            }
        } catch (error) {
            console.error('Erro ao aplicar promoções:', error);
            toast.error('Ocorreu um erro ao processar a solicitação');
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    const titulos = {
        'vencidos': 'Produtos Já Vencidos',
        '15': 'Produtos Vencendo em 15 dias',
        '30': 'Produtos Vencendo em 30 dias',
        '90': 'Produtos Vencendo em 90 dias'
    };

    const subtitulos = {
        'vencidos': 'Estes produtos devem ser retirados de venda imediatamente.',
        '15': 'Prioridade máxima para venda. Sugerimos descontos agressivos.',
        '30': 'Atenção necessária. Considere incluir em ofertas semanais.',
        '90': 'Acompanhamento preventivo para evitar perdas futuras.'
    };

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[100] p-4 animate-in fade-in duration-300">
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden border border-gray-100 dark:border-gray-700">
                {/* Header */}
                <div className="p-6 border-b dark:border-gray-700 flex items-center justify-between bg-gradient-to-r from-gray-50 to-white dark:from-gray-900 dark:to-gray-800">
                    <div className="flex items-center gap-4">
                        <div className={`p-3 rounded-xl ${timeframe === 'vencidos' ? 'bg-red-100 text-red-600' : timeframe === '15' ? 'bg-orange-100 text-orange-600' : 'bg-blue-100 text-blue-600'}`}>
                            {timeframe === 'vencidos' ? <AlertTriangle className="w-6 h-6" /> : <Calendar className="w-6 h-6" />}
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-gray-900 dark:text-white">{titulos[timeframe]}</h2>
                            <p className="text-sm text-gray-500 dark:text-gray-400">{subtitulos[timeframe]}</p>
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
                            <p className="text-gray-500 font-medium">Analisando estoque...</p>
                        </div>
                    ) : produtos.length === 0 ? (
                        <div className="text-center py-20">
                            <div className="inline-flex items-center justify-center w-20 h-20 bg-green-100 rounded-full mb-4">
                                <TrendingDown className="w-10 h-10 text-green-600" />
                            </div>
                            <h3 className="text-lg font-bold text-gray-800 dark:text-white">Nenhum produto crítico!</h3>
                            <p className="text-gray-500">Seu controle de validade está em dia.</p>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            <div className="grid grid-cols-12 gap-4 px-4 py-2 text-xs font-bold text-gray-400 uppercase tracking-wider border-b dark:border-gray-700">
                                <div className="col-span-4">Produto</div>
                                <div className="col-span-2">Validade</div>
                                <div className="col-span-2 text-right">Preço Atual</div>
                                <div className="col-span-2 text-right">Sugestão</div>
                                <div className="col-span-2 text-right">Ação</div>
                            </div>
                            {produtos.map(p => {
                                const sugestao = getSugestao();
                                const precoSugerido = p.preco_venda * (1 - sugestao.desconto);

                                return (
                                    <div key={p.id} className="grid grid-cols-12 gap-4 items-center p-4 bg-gray-50 dark:bg-gray-700/50 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-700 transition-all border border-transparent hover:border-gray-200 dark:hover:border-gray-600">
                                        <div className="col-span-4">
                                            <p className="font-bold text-gray-900 dark:text-white truncate">{p.nome}</p>
                                            <p className="text-xs text-gray-500">{p.categoria} | Qtd: {p.quantidade}</p>
                                        </div>
                                        <div className="col-span-2">
                                            <div className="flex flex-col">
                                                <span className={`text-sm font-medium ${timeframe === 'vencidos' ? 'text-red-600' : 'text-gray-700 dark:text-gray-300'}`}>
                                                    {p.data_validade ? new Date(p.data_validade).toLocaleDateString() : 'N/A'}
                                                </span>
                                                {p.data_validade && (
                                                    <span className="text-[10px] text-gray-400">
                                                        {Math.ceil((new Date(p.data_validade).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24))} dias restando
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                        <div className="col-span-2 text-right">
                                            <p className="text-sm font-medium">{formatCurrency(p.preco_venda)}</p>
                                        </div>
                                        <div className="col-span-2 text-right">
                                            {sugestao.desconto > 0 ? (
                                                <div className="flex flex-col items-end">
                                                    <span className="text-sm font-bold text-green-600">{formatCurrency(precoSugerido)}</span>
                                                    <span className="text-[10px] bg-green-100 text-green-700 px-1.5 py-0.5 rounded">-{sugestao.desconto * 100}%</span>
                                                </div>
                                            ) : (
                                                <span className="text-sm text-gray-400">---</span>
                                            )}
                                        </div>
                                        <div className="col-span-2 text-right">
                                            <span className={`text-xs font-bold px-2 py-1 rounded-full bg-white dark:bg-gray-800 shadow-sm border ${sugestao.cor} border-current opacity-80 uppercase tracking-tighter`}>
                                                {sugestao.acao}
                                            </span>
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
                        * Sugestões baseadas nas melhores práticas de gestão de perecíveis.
                    </p>
                    <div className="flex gap-3">
                        <button onClick={onClose} className="px-6 py-2 text-gray-600 dark:text-gray-400 font-medium hover:bg-gray-200 dark:hover:bg-gray-800 rounded-xl transition-all">
                            Fechar
                        </button>
                        {timeframe !== 'vencidos' && timeframe !== '90' && (
                            <button
                                onClick={handleApplyPromotions}
                                disabled={loading}
                                className="px-6 py-2 bg-blue-600 text-white font-bold rounded-xl shadow-lg shadow-blue-500/30 hover:bg-blue-700 transition-all flex items-center gap-2 disabled:opacity-50"
                            >
                                <TrendingDown className="w-5 h-5" /> {loading ? 'Aplicando...' : 'Aplicar Promoções'}
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ExpiringProductsModal;
