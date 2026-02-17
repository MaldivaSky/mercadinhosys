import React, { useState, useEffect, useMemo } from 'react';
import { X, Calendar, AlertTriangle, TrendingDown } from 'lucide-react';
import { Produto } from '../../../types';
import { productsService } from '../productsService';
import { formatCurrency } from '../../../utils/formatters';
import { toast } from 'react-hot-toast';

/** Lote no período de validade (vindo da API) */
export interface LoteNoPeriodo {
    id: number | null;
    numero_lote: string;
    data_validade: string | null;
    quantidade: number;
    preco_venda: number | null;
    preco_produto: number;
}

export type ProdutoComLotes = Produto & { lotes_no_periodo?: LoteNoPeriodo[] };

/** Uma linha da tabela: produto + lote (ou só produto quando não há lotes) */
interface LinhaValidade {
    produto: ProdutoComLotes;
    lote: LoteNoPeriodo | null;
}

interface ExpiringProductsModalProps {
    isOpen: boolean;
    onClose: () => void;
    timeframe: 'vencidos' | '15' | '30' | '90';
}

const ExpiringProductsModal: React.FC<ExpiringProductsModalProps> = ({ isOpen, onClose, timeframe }) => {
    const [loading, setLoading] = useState(false);
    const [produtos, setProdutos] = useState<ProdutoComLotes[]>([]);

    useEffect(() => {
        if (isOpen) {
            carregarProdutos();
        }
    }, [isOpen, timeframe]);

    const carregarProdutos = async () => {
        try {
            setLoading(true);
            const params: Record<string, unknown> = { por_pagina: 100 };

            if (timeframe === 'vencidos') {
                params.vencidos = true;
            } else {
                params.validade_proxima = true;
                params.dias_validade = parseInt(timeframe, 10);
            }

            const response = await productsService.getAllEstoque(1, 100, params as import('../../../types').ProdutoFiltros);
            setProdutos((response.produtos || []) as ProdutoComLotes[]);
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

    /** Linhas para exibição: uma por lote (ou uma por produto quando não há lotes) */
    const linhas = useMemo((): LinhaValidade[] => {
        const out: LinhaValidade[] = [];
        for (const p of produtos) {
            const lotes = p.lotes_no_periodo && p.lotes_no_periodo.length > 0 ? p.lotes_no_periodo : null;
            if (lotes) {
                for (const lote of lotes) {
                    out.push({ produto: p, lote });
                }
            } else {
                out.push({ produto: p, lote: null });
            }
        }
        return out;
    }, [produtos]);

    const handleApplyPromotions = async () => {
        const sugestao = getSugestao();
        if (sugestao.desconto === 0) return;

        const atualizacoes = linhas
            .filter(() => sugestao.desconto > 0)
            .map(({ produto, lote }) => {
                const precoAtual = lote
                    ? (lote.preco_venda ?? lote.preco_produto)
                    : produto.preco_venda;
                const novoPreco = parseFloat((precoAtual * (1 - sugestao.desconto)).toFixed(2));
                return {
                    id: produto.id,
                    lote_id: lote && lote.id != null ? lote.id : undefined,
                    novo_preco: novoPreco,
                };
            });

        if (atualizacoes.length === 0) return;

        try {
            setLoading(true);
            const response = await productsService.bulkUpdatePrices(atualizacoes);

            if (response.success) {
                toast.success(response.message);
                onClose();
            } else {
                toast.error(response.message || 'Erro ao aplicar promoções');
            }
        } catch (error: unknown) {
            const axiosError = error as { response?: { data?: { message?: string }; status?: number }; message?: string };
            const msg =
                axiosError.response?.data?.message ||
                (axiosError.response?.status === 401 ? 'Sessão expirada. Faça login novamente.' : null) ||
                (axiosError.response?.status === 403 ? 'Sem permissão para alterar preços.' : null) ||
                axiosError.message ||
                'Ocorreu um erro ao aplicar as promoções. Tente novamente.';
            console.error('Erro ao aplicar promoções:', error);
            toast.error(msg);
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
                    ) : linhas.length === 0 ? (
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
                                <div className="col-span-4">Produto / Lote</div>
                                <div className="col-span-2">Validade</div>
                                <div className="col-span-2 text-right">Preço Atual</div>
                                <div className="col-span-2 text-right">Sugestão</div>
                                <div className="col-span-2 text-right">Ação</div>
                            </div>
                            {linhas.map(({ produto: p, lote }, idx) => {
                                const sugestao = getSugestao();
                                const precoAtual = lote ? (lote.preco_venda ?? lote.preco_produto) : p.preco_venda;
                                const precoSugerido = precoAtual * (1 - sugestao.desconto);
                                const dataValidade = lote?.data_validade ?? p.data_validade;
                                const key = lote && lote.id != null ? `p-${p.id}-l-${lote.id}` : `p-${p.id}-${idx}`;

                                return (
                                    <div key={key} className="grid grid-cols-12 gap-4 items-center p-4 bg-gray-50 dark:bg-gray-700/50 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-700 transition-all border border-transparent hover:border-gray-200 dark:hover:border-gray-600">
                                        <div className="col-span-4">
                                            <p className="font-bold text-gray-900 dark:text-white truncate">{p.nome}</p>
                                            <p className="text-xs text-gray-500">
                                                {p.categoria}
                                                {lote ? ` | Lote: ${lote.numero_lote} (${lote.quantidade} un.)` : ` | Qtd: ${p.quantidade}`}
                                            </p>
                                        </div>
                                        <div className="col-span-2">
                                            <div className="flex flex-col">
                                                <span className={`text-sm font-medium ${timeframe === 'vencidos' ? 'text-red-600' : 'text-gray-700 dark:text-gray-300'}`}>
                                                    {dataValidade ? new Date(dataValidade).toLocaleDateString() : 'N/A'}
                                                </span>
                                                {dataValidade && (
                                                    <span className="text-[10px] text-gray-400">
                                                        {Math.ceil((new Date(dataValidade).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24))} dias
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                        <div className="col-span-2 text-right">
                                            <p className="text-sm font-medium">{formatCurrency(precoAtual)}</p>
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
