import React, { useState, useEffect } from 'react';
import {
    TrendingUp,
    TrendingDown,
    DollarSign,
    Package,
    AlertTriangle,
    BarChart3,
    PieChart,
    Activity,
    Zap,
    Clock,
    Target
} from 'lucide-react';
import { formatCurrency } from '../../../utils/formatters';
import { Produto } from '../../../types';

interface ProductAnalyticsDashboardProps {
    produtos: Produto[];
    stats: {
        total_produtos: number;
        produtos_baixo_estoque: number;
        produtos_esgotados: number;
        produtos_normal: number;
        valor_total_estoque: number;
        margem_media: number;
        classificacao_abc?: { A: number; B: number; C: number };
        giro_estoque?: { rapido: number; normal: number; lento: number };
        validade?: { vencidos: number; vence_15: number; vence_30: number; vence_90: number };
        top_produtos_margem?: any[];
        produtos_criticos?: any[];
    };
    onCardClick: (filterType: string) => void;
}

interface ClassificacaoABC {
    A: number;
    B: number;
    C: number;
}

interface StatusGiro {
    rapido: number;
    normal: number;
    lento: number;
}

const ProductAnalyticsDashboard: React.FC<ProductAnalyticsDashboardProps> = ({
    produtos,
    stats,
    onCardClick
}) => {
    const [classificacaoABC, setClassificacaoABC] = useState<ClassificacaoABC>({ A: 0, B: 0, C: 0 });
    const [statusGiro, setStatusGiro] = useState<StatusGiro>({ rapido: 0, normal: 0, lento: 0 });
    const [topProdutos, setTopProdutos] = useState<Produto[]>([]);
    const [produtosCriticos, setProdutosCriticos] = useState<Produto[]>([]);

    useEffect(() => {
        // Se não tiver produtos E não tiver stats do backend, limpa tudo
        if ((!produtos || produtos.length === 0) && !stats.classificacao_abc) {
            setClassificacaoABC({ A: 0, B: 0, C: 0 });
            setStatusGiro({ rapido: 0, normal: 0, lento: 0 });
            setTopProdutos([]);
            setProdutosCriticos([]);
            // Continuar execução para pegar stats se existirem
        }

        // ==================== USAR ESTATÍSTICAS DO BACKEND ====================
        // Se o backend forneceu as estatísticas, usar elas (já calculadas para TODOS os produtos)
        if (stats.classificacao_abc) {
            setClassificacaoABC(stats.classificacao_abc);
        } else {
            // Fallback: calcular localmente (apenas para os produtos da página)
            const faturamentoTotal = produtos.reduce((sum, p) => sum + (p.total_vendido || 0), 0);
            const abc = { A: 0, B: 0, C: 0 };

            if (faturamentoTotal === 0) {
                abc.C = produtos.length;
            } else {
                const produtosComFaturamento = produtos.map(p => ({
                    ...p,
                    faturamento: p.total_vendido || 0
                })).sort((a, b) => b.faturamento - a.faturamento);

                let acumulado = 0;
                produtosComFaturamento.forEach(p => {
                    acumulado += p.faturamento;
                    const percentualAcumulado = acumulado / faturamentoTotal;

                    if (percentualAcumulado <= 0.80) abc.A++;
                    else if (percentualAcumulado <= 0.95) abc.B++;
                    else abc.C++;
                });
            }
            setClassificacaoABC(abc);
        }

        // ==================== USAR GIRO DO BACKEND ====================
        if (stats.giro_estoque) {
            setStatusGiro(stats.giro_estoque);
        } else {
            // Fallback: calcular localmente
            const hoje = new Date();
            const giro = { rapido: 0, normal: 0, lento: 0 };

            produtos.forEach(p => {
                if (!p.ultima_venda) {
                    giro.lento++;
                } else {
                    const dataUltimaVenda = new Date(p.ultima_venda);
                    const diasDesdeVenda = Math.floor((hoje.getTime() - dataUltimaVenda.getTime()) / (1000 * 60 * 60 * 24));

                    if (diasDesdeVenda <= 7) {
                        giro.rapido++;
                    } else if (diasDesdeVenda <= 30) {
                        giro.normal++;
                    } else {
                        giro.lento++;
                    }
                }
            });
            setStatusGiro(giro);
        }

        // ==================== TOP 5 PRODUTOS POR MARGEM ====================
        if (stats.top_produtos_margem && stats.top_produtos_margem.length > 0) {
            setTopProdutos(stats.top_produtos_margem);
        } else if (produtos && produtos.length > 0) {
            // Fallback: calcular localmente
            const top = [...produtos]
                .filter(p => p.margem_lucro !== undefined && p.margem_lucro !== null)
                .sort((a, b) => (b.margem_lucro || 0) - (a.margem_lucro || 0))
                .slice(0, 5);
            setTopProdutos(top);
        } else {
            setTopProdutos([]);
        }

        // ==================== PRODUTOS CRÍTICOS (ESGOTADOS + BAIXO ESTOQUE) ====================
        if (stats.produtos_criticos && stats.produtos_criticos.length > 0) {
            setProdutosCriticos(stats.produtos_criticos);
        } else if (produtos && produtos.length > 0) {
            // Fallback: calcular localmente
            const criticos = produtos
                .filter(p => {
                    // Esgotado
                    if (p.quantidade === 0) return true;
                    if (p.estoque_status === 'esgotado') return true;

                    // Baixo estoque
                    if (p.estoque_status === 'baixo') return true;
                    if (p.quantidade <= (p.quantidade_minima || 0)) return true;

                    return false;
                })
                .sort((a, b) => {
                    // Ordenar: esgotados primeiro, depois por quantidade
                    if (a.quantidade === 0 && b.quantidade > 0) return -1;
                    if (a.quantidade > 0 && b.quantidade === 0) return 1;
                    return (a.quantidade || 0) - (b.quantidade || 0);
                })
                .slice(0, 10);

            setProdutosCriticos(criticos);
        } else {
            setProdutosCriticos([]);
        }
    }, [produtos, stats]);

    const percentualABC = {
        A: stats.total_produtos > 0 ? (classificacaoABC.A / stats.total_produtos * 100).toFixed(1) : '0',
        B: stats.total_produtos > 0 ? (classificacaoABC.B / stats.total_produtos * 100).toFixed(1) : '0',
        C: stats.total_produtos > 0 ? (classificacaoABC.C / stats.total_produtos * 100).toFixed(1) : '0',
    };

    const percentualGiro = {
        rapido: stats.total_produtos > 0 ? (statusGiro.rapido / stats.total_produtos * 100).toFixed(1) : '0',
        normal: stats.total_produtos > 0 ? (statusGiro.normal / stats.total_produtos * 100).toFixed(1) : '0',
        lento: stats.total_produtos > 0 ? (statusGiro.lento / stats.total_produtos * 100).toFixed(1) : '0',
    };

    const validade = stats.validade || { vencidos: 0, vence_15: 0, vence_30: 0, vence_90: 0 };

    return (
        <div className="space-y-6">
            {/* Cards Principais - Grid Responsivo */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
                {/* Total de Produtos */}
                <div
                    onClick={() => onCardClick('all')}
                    className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl shadow-lg p-6 text-white cursor-pointer hover:shadow-2xl hover:scale-105 transition-all duration-200"
                >
                    <div className="flex items-center justify-between mb-2">
                        <Package className="w-8 h-8 opacity-80" />
                        <TrendingUp className="w-5 h-5" />
                    </div>
                    <p className="text-sm opacity-90 mb-1">Total Produtos</p>
                    <p className="text-3xl font-bold">{stats.total_produtos}</p>
                    <p className="text-xs opacity-75 mt-2">📦 Clique para ver todos</p>
                </div>

                {/* Produtos Normais */}
                <div
                    onClick={() => onCardClick('normal')}
                    className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl shadow-lg p-6 text-white cursor-pointer hover:shadow-2xl hover:scale-105 transition-all duration-200"
                >
                    <div className="flex items-center justify-between mb-2">
                        <Target className="w-8 h-8 opacity-80" />
                        <BarChart3 className="w-5 h-5" />
                    </div>
                    <p className="text-sm opacity-90 mb-1">Estoque Normal</p>
                    <p className="text-3xl font-bold">{stats.produtos_normal}</p>
                    <p className="text-xs opacity-75 mt-2">✅ {((stats.produtos_normal / stats.total_produtos) * 100).toFixed(0)}% do total</p>
                </div>

                {/* Baixo Estoque */}
                <div
                    onClick={() => onCardClick('baixo')}
                    className="bg-gradient-to-br from-yellow-500 to-yellow-600 rounded-xl shadow-lg p-6 text-white cursor-pointer hover:shadow-2xl hover:scale-105 transition-all duration-200"
                >
                    <div className="flex items-center justify-between mb-2">
                        <AlertTriangle className="w-8 h-8 opacity-80" />
                        <TrendingDown className="w-5 h-5" />
                    </div>
                    <p className="text-sm opacity-90 mb-1">Baixo Estoque</p>
                    <p className="text-3xl font-bold">{stats.produtos_baixo_estoque}</p>
                    <p className="text-xs opacity-75 mt-2">⚠️ Requer atenção</p>
                </div>

                {/* Esgotados */}
                <div
                    onClick={() => onCardClick('esgotado')}
                    className="bg-gradient-to-br from-red-500 to-red-600 rounded-xl shadow-lg p-6 text-white cursor-pointer hover:shadow-2xl hover:scale-105 transition-all duration-200 animate-pulse"
                >
                    <div className="flex items-center justify-between mb-2">
                        <Activity className="w-8 h-8 opacity-80" />
                        <AlertTriangle className="w-5 h-5" />
                    </div>
                    <p className="text-sm opacity-90 mb-1">Esgotados</p>
                    <p className="text-3xl font-bold">{stats.produtos_esgotados}</p>
                    <p className="text-xs opacity-75 mt-2">🚨 URGENTE</p>
                </div>

                {/* Valor Total */}
                <div
                    onClick={() => onCardClick('valor')}
                    className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl shadow-lg p-6 text-white cursor-pointer hover:shadow-2xl hover:scale-105 transition-all duration-200"
                >
                    <div className="flex items-center justify-between mb-2">
                        <DollarSign className="w-8 h-8 opacity-80" />
                        <TrendingUp className="w-5 h-5" />
                    </div>
                    <p className="text-sm opacity-90 mb-1">Valor Estoque</p>
                    <p className="text-2xl font-bold">{formatCurrency(stats.valor_total_estoque)}</p>
                    <p className="text-xs opacity-75 mt-2">💰 Capital investido</p>
                </div>

                {/* Margem Média */}
                <div
                    onClick={() => onCardClick('margem')}
                    className="bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-xl shadow-lg p-6 text-white cursor-pointer hover:shadow-2xl hover:scale-105 transition-all duration-200"
                >
                    <div className="flex items-center justify-between mb-2">
                        <PieChart className="w-8 h-8 opacity-80" />
                        <BarChart3 className="w-5 h-5" />
                    </div>
                    <p className="text-sm opacity-90 mb-1">Margem Média</p>
                    <p className="text-3xl font-bold">{stats.margem_media.toFixed(1)}%</p>
                    <p className="text-xs opacity-75 mt-2">📊 Rentabilidade</p>
                </div>
            </div>

            {/* Análises Avançadas - Grid 3 Colunas */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Classificação ABC */}
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                            <BarChart3 className="w-6 h-6 text-blue-600 dark:text-blue-300" />
                        </div>
                        <div>
                            <h3 className="text-lg font-bold text-gray-800 dark:text-white">
                                Classificação ABC
                            </h3>
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                                Análise de Pareto (80/20)
                            </p>
                        </div>
                    </div>

                    <div className="mb-4 bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg border border-blue-100 dark:border-blue-800">
                        <p className="text-xs text-blue-800 dark:text-blue-200">
                            <strong>Nota:</strong> A classificação ABC ajuda a priorizar esforços.
                            <br />• <strong>Classe A:</strong> Produtos vitais (80% do faturamento). Nunca devem faltar.
                            <br />• <strong>Classe B:</strong> Intermediários (15%). Estoque moderado.
                            <br />• <strong>Classe C:</strong> Menor impacto (5%). Evitar excesso de estoque.
                        </p>
                    </div>

                    <div className="space-y-4">
                        {/* Classe A */}
                        <div>
                            <div className="flex justify-between items-center mb-2">
                                <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                                    Classe A - Alta Prioridade
                                </span>
                                <span className="text-sm font-bold text-green-600 dark:text-green-400">
                                    {classificacaoABC.A} ({percentualABC.A}%)
                                </span>
                            </div>
                            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                                <div
                                    className="bg-gradient-to-r from-green-500 to-green-600 h-3 rounded-full transition-all duration-500"
                                    style={{ width: `${percentualABC.A}%` }}
                                />
                            </div>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                80% do faturamento
                            </p>
                        </div>

                        {/* Classe B */}
                        <div>
                            <div className="flex justify-between items-center mb-2">
                                <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                                    Classe B - Média Prioridade
                                </span>
                                <span className="text-sm font-bold text-yellow-600 dark:text-yellow-400">
                                    {classificacaoABC.B} ({percentualABC.B}%)
                                </span>
                            </div>
                            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                                <div
                                    className="bg-gradient-to-r from-yellow-500 to-yellow-600 h-3 rounded-full transition-all duration-500"
                                    style={{ width: `${percentualABC.B}%` }}
                                />
                            </div>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                15% do faturamento
                            </p>
                        </div>

                        {/* Classe C */}
                        <div>
                            <div className="flex justify-between items-center mb-2">
                                <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                                    Classe C - Baixa Prioridade
                                </span>
                                <span className="text-sm font-bold text-red-600 dark:text-red-400">
                                    {classificacaoABC.C} ({percentualABC.C}%)
                                </span>
                            </div>
                            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                                <div
                                    className="bg-gradient-to-r from-red-500 to-red-600 h-3 rounded-full transition-all duration-500"
                                    style={{ width: `${percentualABC.C}%` }}
                                />
                            </div>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                5% do faturamento
                            </p>
                        </div>
                    </div>
                </div>

                {/* Status de Giro */}
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
                            <Zap className="w-6 h-6 text-purple-600 dark:text-purple-300" />
                        </div>
                        <div>
                            <h3 className="text-lg font-bold text-gray-800 dark:text-white">
                                Giro de Estoque
                            </h3>
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                                Velocidade de rotação
                            </p>
                        </div>
                    </div>

                    <div className="mb-4 bg-purple-50 dark:bg-purple-900/20 p-3 rounded-lg border border-purple-100 dark:border-purple-800">
                        <p className="text-xs text-purple-800 dark:text-purple-200">
                            <strong>Nota:</strong> Mede há quanto tempo o produto não é vendido.
                            <br />• <strong>Rápido:</strong> Venda nos últimos 7 dias.
                            <br />• <strong>Normal:</strong> Venda entre 8 e 30 dias.
                            <br />• <strong>Lento:</strong> Sem vendas há mais de 30 dias.
                        </p>
                    </div>

                    <div className="space-y-4">
                        {/* Giro Rápido */}
                        <div>
                            <div className="flex justify-between items-center mb-2">
                                <div className="flex items-center gap-2">
                                    <Zap className="w-4 h-4 text-green-600" />
                                    <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                                        Giro Rápido
                                    </span>
                                </div>
                                <span className="text-sm font-bold text-green-600 dark:text-green-400">
                                    {statusGiro.rapido} ({percentualGiro.rapido}%)
                                </span>
                            </div>
                            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                                <div
                                    className="bg-gradient-to-r from-green-500 to-green-600 h-3 rounded-full transition-all duration-500"
                                    style={{ width: `${percentualGiro.rapido}%` }}
                                />
                            </div>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                Vendido nos últimos 7 dias
                            </p>
                        </div>

                        {/* Giro Normal */}
                        <div>
                            <div className="flex justify-between items-center mb-2">
                                <div className="flex items-center gap-2">
                                    <Clock className="w-4 h-4 text-yellow-600" />
                                    <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                                        Giro Normal
                                    </span>
                                </div>
                                <span className="text-sm font-bold text-yellow-600 dark:text-yellow-400">
                                    {statusGiro.normal} ({percentualGiro.normal}%)
                                </span>
                            </div>
                            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                                <div
                                    className="bg-gradient-to-r from-yellow-500 to-yellow-600 h-3 rounded-full transition-all duration-500"
                                    style={{ width: `${percentualGiro.normal}%` }}
                                />
                            </div>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                Vendido entre 8-30 dias
                            </p>
                        </div>

                        {/* Giro Lento */}
                        <div>
                            <div className="flex justify-between items-center mb-2">
                                <div className="flex items-center gap-2">
                                    <TrendingDown className="w-4 h-4 text-red-600" />
                                    <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                                        Giro Lento
                                    </span>
                                </div>
                                <span className="text-sm font-bold text-red-600 dark:text-red-400">
                                    {statusGiro.lento} ({percentualGiro.lento}%)
                                </span>
                            </div>
                            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                                <div
                                    className="bg-gradient-to-r from-red-500 to-red-600 h-3 rounded-full transition-all duration-500"
                                    style={{ width: `${percentualGiro.lento}%` }}
                                />
                            </div>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                Mais de 30 dias sem venda
                            </p>
                        </div>
                    </div>
                </div>

                {/* Monitor de Validade */}
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 bg-orange-100 dark:bg-orange-900 rounded-lg">
                            <Clock className="w-6 h-6 text-orange-600 dark:text-orange-300" />
                        </div>
                        <div>
                            <h3 className="text-lg font-bold text-gray-800 dark:text-white">
                                Monitor de Validade
                            </h3>
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                                Prevenção de perdas
                            </p>
                        </div>
                    </div>

                    <div className="mb-4 bg-orange-50 dark:bg-orange-900/20 p-3 rounded-lg border border-orange-100 dark:border-orange-800">
                        <p className="text-xs text-orange-800 dark:text-orange-200">
                            <strong>Dica:</strong> Produtos vencendo devem ser colocados em oferta
                            ou movidos para frente nas prateleiras (FEFO).
                        </p>
                    </div>

                    <div className="space-y-4">
                        {/* Já Vencidos */}
                        <div onClick={() => onCardClick('vencido')} className="cursor-pointer group">
                            <div className="flex justify-between items-center mb-2">
                                <span className="text-sm font-semibold text-red-600 dark:text-red-400 group-hover:underline">
                                    Já Vencidos
                                </span>
                                <span className="text-sm font-bold text-red-600">
                                    {validade.vencidos}
                                </span>
                            </div>
                            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                                <div
                                    className="bg-red-600 h-3 rounded-full transition-all duration-500"
                                    style={{ width: `${stats.total_produtos > 0 ? (validade.vencidos / stats.total_produtos) * 100 : 0}%` }}
                                />
                            </div>
                        </div>

                        {/* Vence em 15 dias */}
                        <div onClick={() => onCardClick('vence_15')} className="cursor-pointer group">
                            <div className="flex justify-between items-center mb-2">
                                <span className="text-sm font-semibold text-gray-700 dark:text-gray-300 group-hover:underline">
                                    Vence em 15 dias
                                </span>
                                <span className="text-sm font-bold text-orange-600">
                                    {validade.vence_15}
                                </span>
                            </div>
                            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                                <div
                                    className="bg-orange-500 h-3 rounded-full transition-all duration-500"
                                    style={{ width: `${validade.vence_90 > 0 ? (validade.vence_15 / validade.vence_90) * 100 : 0}%` }}
                                />
                            </div>
                        </div>

                        {/* Vence em 30 dias */}
                        <div onClick={() => onCardClick('vence_30')} className="cursor-pointer group">
                            <div className="flex justify-between items-center mb-2">
                                <span className="text-sm font-semibold text-gray-700 dark:text-gray-300 group-hover:underline">
                                    Vence em 30 dias
                                </span>
                                <span className="text-sm font-bold text-yellow-600">
                                    {validade.vence_30}
                                </span>
                            </div>
                            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                                <div
                                    className="bg-yellow-500 h-3 rounded-full transition-all duration-500"
                                    style={{ width: `${validade.vence_90 > 0 ? (validade.vence_30 / validade.vence_90) * 100 : 0}%` }}
                                />
                            </div>
                        </div>

                        {/* Vence em 90 dias */}
                        <div onClick={() => onCardClick('vence_90')} className="cursor-pointer group">
                            <div className="flex justify-between items-center mb-2">
                                <span className="text-sm font-semibold text-gray-700 dark:text-gray-300 group-hover:underline">
                                    Vence em 90 dias
                                </span>
                                <span className="text-sm font-bold text-blue-600">
                                    {validade.vence_90}
                                </span>
                            </div>
                            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                                <div
                                    className="bg-blue-500 h-3 rounded-full transition-all duration-500"
                                    style={{ width: `${validade.vence_90 > 0 ? 100 : 0}%` }}
                                />
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Top Produtos e Produtos Críticos */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Top 5 Produtos por Margem */}
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
                            <TrendingUp className="w-6 h-6 text-green-600 dark:text-green-300" />
                        </div>
                        <div>
                            <h3 className="text-lg font-bold text-gray-800 dark:text-white">
                                Top 5 - Maior Margem
                            </h3>
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                                Produtos mais rentáveis
                            </p>
                        </div>
                    </div>

                    <div className="space-y-3">
                        {topProdutos.length === 0 ? (
                            <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
                                Nenhum produto disponível
                            </p>
                        ) : (
                            topProdutos.map((produto, index) => (
                                <div
                                    key={produto.id}
                                    className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
                                >
                                    <div className="flex items-center gap-3 flex-1 min-w-0">
                                        <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-green-500 to-green-600 rounded-full flex items-center justify-center text-white font-bold text-sm">
                                            {index + 1}
                                        </div>
                                        <div className="min-w-0 flex-1">
                                            <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">
                                                {produto.nome}
                                            </p>
                                            <p className="text-xs text-gray-500 dark:text-gray-400">
                                                {formatCurrency(produto.preco_venda)}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="text-right flex-shrink-0">
                                        <p className="text-lg font-bold text-green-600 dark:text-green-400">
                                            {produto.margem_lucro?.toFixed(1)}%
                                        </p>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>

                {/* Produtos Críticos */}
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 bg-red-100 dark:bg-red-900 rounded-lg">
                            <AlertTriangle className="w-6 h-6 text-red-600 dark:text-red-300" />
                        </div>
                        <div>
                            <h3 className="text-lg font-bold text-gray-800 dark:text-white">
                                Produtos Críticos
                            </h3>
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                                Requerem atenção imediata
                            </p>
                        </div>
                    </div>

                    <div className="space-y-3">
                        {produtosCriticos.length === 0 ? (
                            <div className="text-center py-8">
                                <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 dark:bg-green-900 rounded-full mb-3">
                                    <Target className="w-8 h-8 text-green-600 dark:text-green-300" />
                                </div>
                                <p className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                                    Tudo sob controle!
                                </p>
                                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                    Nenhum produto crítico no momento
                                </p>
                            </div>
                        ) : (
                            produtosCriticos.map((produto) => (
                                <div
                                    key={produto.id}
                                    className="flex items-center justify-between p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg"
                                >
                                    <div className="flex items-center gap-3 flex-1 min-w-0">
                                        <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0" />
                                        <div className="min-w-0 flex-1">
                                            <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">
                                                {produto.nome}
                                            </p>
                                            <p className="text-xs text-gray-500 dark:text-gray-400">
                                                {produto.categoria}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="text-right flex-shrink-0">
                                        <span className={`px-2 py-1 text-xs font-semibold rounded-full ${produto.estoque_status === 'esgotado'
                                            ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
                                            : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
                                            }`}>
                                            {produto.quantidade} un
                                        </span>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ProductAnalyticsDashboard;
