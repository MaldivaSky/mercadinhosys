import React, { useState, useEffect } from 'react';
import { X, TrendingUp, Calendar, DollarSign, Package, Clock, AlertTriangle, Users, BarChart3 } from 'lucide-react';
import { Produto } from '../../../types';
import { formatCurrency } from '../../../utils/formatters';
import { apiClient } from '../../../api/apiClient';

interface ProductHistoryModalProps {
    produto: Produto;
    onClose: () => void;
}

interface HistoricoPreco {
    id: number;
    data_alteracao: string;
    preco_custo_anterior: number;
    preco_custo_novo: number;
    preco_venda_anterior: number;
    preco_venda_novo: number;
    margem_anterior: number;
    margem_nova: number;
    motivo: string;
    funcionario_nome?: string;
}

interface VendaHistorico {
    data: string;
    quantidade: number;
    valor_total: number;
}

interface VendaHistorico {
    data: string;
    quantidade: number;
    valor_total: number;
    numero_vendas: number;
    ticket_medio: number;
}

interface EstatisticasVendas {
    total_vendido_90d: number;
    faturamento_90d: number;
    dias_com_venda: number;
    dias_sem_venda: number;
    media_diaria: number;
    ticket_medio: number;
}

const ProductHistoryModal: React.FC<ProductHistoryModalProps> = ({ produto, onClose }) => {
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'vendas' | 'precos' | 'fornecedor'>('vendas');
    const [historicoPrecos, setHistoricoPrecos] = useState<HistoricoPreco[]>([]);
    const [vendasHistorico, setVendasHistorico] = useState<VendaHistorico[]>([]);
    const [estatisticasVendas, setEstatisticasVendas] = useState<EstatisticasVendas | null>(null);
    const [fornecedorInfo, setFornecedorInfo] = useState<any>(null);

    useEffect(() => {
        loadData();
    }, [produto.id]);

    const loadData = async () => {
        try {
            setLoading(true);
            
            // Carregar histórico de preços
            try {
                const precosRes = await apiClient.get(`/produtos/${produto.id}/historico-precos`);
                setHistoricoPrecos(precosRes.data.historico || []);
            } catch (error) {
                console.error('Erro ao carregar histórico de preços:', error);
                setHistoricoPrecos([]);
            }
            
            // Carregar histórico de vendas (últimos 90 dias)
            try {
                const vendasRes = await apiClient.get(`/produtos/${produto.id}/vendas-historico`);
                setVendasHistorico(vendasRes.data.historico || []);
                setEstatisticasVendas(vendasRes.data.estatisticas || null);
            } catch (error) {
                console.error('Erro ao carregar histórico de vendas:', error);
                setVendasHistorico([]);
                setEstatisticasVendas(null);
            }
            
            // Carregar informações do fornecedor
            if (produto.fornecedor_id) {
                try {
                    const fornecedorRes = await apiClient.get(`/fornecedores/${produto.fornecedor_id}`);
                    setFornecedorInfo(fornecedorRes.data.fornecedor || fornecedorRes.data);
                } catch (error) {
                    console.error('Erro ao carregar fornecedor:', error);
                    setFornecedorInfo(null);
                }
            } else {
                setFornecedorInfo(null);
            }
        } catch (error) {
            console.error('Erro ao carregar dados:', error);
        } finally {
            setLoading(false);
        }
    };

    const calcularDiasDesdeUltimaVenda = () => {
        if (!produto.ultima_venda) return null;
        const hoje = new Date();
        const ultimaVenda = new Date(produto.ultima_venda);
        return Math.floor((hoje.getTime() - ultimaVenda.getTime()) / (1000 * 60 * 60 * 24));
    };

    const diasDesdeUltimaVenda = calcularDiasDesdeUltimaVenda();

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
                {/* Header */}
                <div className="bg-gradient-to-r from-indigo-500 to-indigo-600 px-6 py-4 flex justify-between items-center">
                    <div>
                        <h2 className="text-2xl font-bold text-white">{produto.nome}</h2>
                        <p className="text-indigo-100 text-sm mt-1">
                            {produto.categoria} • {produto.codigo_barras || 'Sem código'}
                        </p>
                    </div>
                    <button
                        onClick={onClose}
                        className="text-white hover:text-gray-200 transition-colors"
                    >
                        <X className="w-6 h-6" />
                    </button>
                </div>

                {/* Tabs */}
                <div className="border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-750">
                    <div className="flex gap-1 px-6">
                        <button
                            onClick={() => setActiveTab('vendas')}
                            className={`px-4 py-3 font-medium text-sm transition-colors relative ${
                                activeTab === 'vendas'
                                    ? 'text-indigo-600 dark:text-indigo-400'
                                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                            }`}
                        >
                            <div className="flex items-center gap-2">
                                <TrendingUp className="w-4 h-4" />
                                Histórico de Vendas
                            </div>
                            {activeTab === 'vendas' && (
                                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-600 dark:bg-indigo-400" />
                            )}
                        </button>
                        <button
                            onClick={() => setActiveTab('precos')}
                            className={`px-4 py-3 font-medium text-sm transition-colors relative ${
                                activeTab === 'precos'
                                    ? 'text-indigo-600 dark:text-indigo-400'
                                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                            }`}
                        >
                            <div className="flex items-center gap-2">
                                <DollarSign className="w-4 h-4" />
                                Histórico de Preços
                            </div>
                            {activeTab === 'precos' && (
                                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-600 dark:bg-indigo-400" />
                            )}
                        </button>
                        <button
                            onClick={() => setActiveTab('fornecedor')}
                            className={`px-4 py-3 font-medium text-sm transition-colors relative ${
                                activeTab === 'fornecedor'
                                    ? 'text-indigo-600 dark:text-indigo-400'
                                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                            }`}
                        >
                            <div className="flex items-center gap-2">
                                <Users className="w-4 h-4" />
                                Fornecedor
                            </div>
                            {activeTab === 'fornecedor' && (
                                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-600 dark:bg-indigo-400" />
                            )}
                        </button>
                    </div>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6">
                    {loading ? (
                        <div className="flex justify-center items-center h-64">
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500"></div>
                        </div>
                    ) : (
                        <>
                            {/* Tab: Histórico de Vendas */}
                            {activeTab === 'vendas' && (
                                <div className="space-y-6">
                                    {/* Cards de Resumo */}
                                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                                        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
                                            <div className="flex items-center gap-2 mb-2">
                                                <Package className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                                                <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Total Vendido</p>
                                            </div>
                                            <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                                                {produto.quantidade_vendida || 0} un
                                            </p>
                                        </div>
                                        <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 border border-green-200 dark:border-green-800">
                                            <div className="flex items-center gap-2 mb-2">
                                                <DollarSign className="w-5 h-5 text-green-600 dark:text-green-400" />
                                                <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Faturamento</p>
                                            </div>
                                            <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                                                {formatCurrency(produto.total_vendido || 0)}
                                            </p>
                                        </div>
                                        <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4 border border-purple-200 dark:border-purple-800">
                                            <div className="flex items-center gap-2 mb-2">
                                                <Clock className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                                                <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Última Venda</p>
                                            </div>
                                            <p className="text-lg font-bold text-purple-600 dark:text-purple-400">
                                                {produto.ultima_venda 
                                                    ? new Date(produto.ultima_venda).toLocaleDateString('pt-BR')
                                                    : 'Nunca'
                                                }
                                            </p>
                                            {diasDesdeUltimaVenda !== null && (
                                                <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                                                    {diasDesdeUltimaVenda === 0 ? 'Hoje' : `Há ${diasDesdeUltimaVenda} dias`}
                                                </p>
                                            )}
                                        </div>
                                        <div className="bg-orange-50 dark:bg-orange-900/20 rounded-lg p-4 border border-orange-200 dark:border-orange-800">
                                            <div className="flex items-center gap-2 mb-2">
                                                <BarChart3 className="w-5 h-5 text-orange-600 dark:text-orange-400" />
                                                <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Ticket Médio</p>
                                            </div>
                                            <p className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                                                {formatCurrency(
                                                    (produto.quantidade_vendida || 0) > 0
                                                        ? (produto.total_vendido || 0) / (produto.quantidade_vendida || 1)
                                                        : 0
                                                )}
                                            </p>
                                        </div>
                                    </div>

                                    {/* Análise Temporal */}
                                    <div className="bg-gray-50 dark:bg-gray-750 rounded-lg p-6">
                                        <h3 className="text-lg font-bold text-gray-800 dark:text-white mb-4 flex items-center gap-2">
                                            <Calendar className="w-5 h-5" />
                                            Análise Temporal (Últimos 90 dias)
                                        </h3>
                                        
                                        {vendasHistorico.length > 0 ? (
                                            <div className="space-y-4">
                                                {/* Estatísticas Resumidas */}
                                                {estatisticasVendas && (
                                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                                                        <div className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700">
                                                            <p className="text-xs text-gray-600 dark:text-gray-400">Total Vendido</p>
                                                            <p className="text-lg font-bold text-blue-600 dark:text-blue-400">
                                                                {estatisticasVendas.total_vendido_90d} un
                                                            </p>
                                                        </div>
                                                        <div className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700">
                                                            <p className="text-xs text-gray-600 dark:text-gray-400">Faturamento</p>
                                                            <p className="text-lg font-bold text-green-600 dark:text-green-400">
                                                                {formatCurrency(estatisticasVendas.faturamento_90d)}
                                                            </p>
                                                        </div>
                                                        <div className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700">
                                                            <p className="text-xs text-gray-600 dark:text-gray-400">Dias com Venda</p>
                                                            <p className="text-lg font-bold text-purple-600 dark:text-purple-400">
                                                                {estatisticasVendas.dias_com_venda} / 90
                                                            </p>
                                                        </div>
                                                        <div className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700">
                                                            <p className="text-xs text-gray-600 dark:text-gray-400">Média Diária</p>
                                                            <p className="text-lg font-bold text-orange-600 dark:text-orange-400">
                                                                {estatisticasVendas.media_diaria.toFixed(1)} un
                                                            </p>
                                                        </div>
                                                    </div>
                                                )}
                                                
                                                {/* Gráfico Simples de Barras */}
                                                <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
                                                    <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                                                        Vendas por Dia
                                                    </p>
                                                    <div className="h-48 flex items-end justify-between gap-0.5">
                                                        {vendasHistorico.map((venda, index) => {
                                                            const maxQuantidade = Math.max(...vendasHistorico.map(v => v.quantidade));
                                                            const altura = maxQuantidade > 0 ? (venda.quantidade / maxQuantidade) * 100 : 0;
                                                            const data = new Date(venda.data);
                                                            const dia = data.getDate();
                                                            
                                                            return (
                                                                <div
                                                                    key={index}
                                                                    className="flex-1 flex flex-col items-center group relative"
                                                                    style={{ minWidth: '2px' }}
                                                                >
                                                                    <div
                                                                        className="w-full bg-gradient-to-t from-blue-500 to-blue-400 rounded-t hover:from-blue-600 hover:to-blue-500 transition-all cursor-pointer"
                                                                        style={{ height: `${altura}%` }}
                                                                        title={`${dia}/${data.getMonth() + 1}: ${venda.quantidade} un - ${formatCurrency(venda.valor_total)}`}
                                                                    />
                                                                    {/* Tooltip on hover */}
                                                                    <div className="absolute bottom-full mb-2 hidden group-hover:block bg-gray-900 text-white text-xs rounded py-1 px-2 whitespace-nowrap z-10">
                                                                        <div className="font-semibold">{dia}/{data.getMonth() + 1}</div>
                                                                        <div>{venda.quantidade} un</div>
                                                                        <div>{formatCurrency(venda.valor_total)}</div>
                                                                    </div>
                                                                </div>
                                                            );
                                                        })}
                                                    </div>
                                                    <div className="mt-2 flex justify-between text-xs text-gray-500 dark:text-gray-400">
                                                        <span>Início</span>
                                                        <span>Hoje</span>
                                                    </div>
                                                </div>
                                                
                                                {diasDesdeUltimaVenda && diasDesdeUltimaVenda > 30 && (
                                                    <div className="bg-orange-50 dark:bg-orange-900/20 rounded-lg p-4 border border-orange-200 dark:border-orange-800">
                                                        <p className="text-sm font-semibold text-orange-800 dark:text-orange-300 flex items-center gap-2">
                                                            <AlertTriangle className="w-4 h-4" />
                                                            Atenção: Produto parado há {diasDesdeUltimaVenda} dias
                                                        </p>
                                                        <p className="text-xs text-orange-700 dark:text-orange-400 mt-1">
                                                            Considere ações de liquidação ou promoção
                                                        </p>
                                                    </div>
                                                )}
                                            </div>
                                        ) : (
                                            <div className="text-center py-8">
                                                <BarChart3 className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
                                                <p className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">
                                                    Nenhuma venda nos últimos 90 dias
                                                </p>
                                                <p className="text-sm text-gray-600 dark:text-gray-400">
                                                    Este produto não teve vendas registradas no período analisado
                                                </p>
                                                
                                                {diasDesdeUltimaVenda && diasDesdeUltimaVenda > 90 && (
                                                    <div className="mt-6 bg-red-50 dark:bg-red-900/20 rounded-lg p-4 max-w-md mx-auto border border-red-200 dark:border-red-800">
                                                        <p className="text-sm font-semibold text-red-800 dark:text-red-300 flex items-center justify-center gap-2">
                                                            <AlertTriangle className="w-5 h-5" />
                                                            Produto CRÍTICO: {diasDesdeUltimaVenda} dias sem vender
                                                        </p>
                                                    </div>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* Tab: Histórico de Preços */}
                            {activeTab === 'precos' && (
                                <div className="space-y-6">
                                    {historicoPrecos.length === 0 ? (
                                        <div className="text-center py-12">
                                            <DollarSign className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
                                            <p className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">
                                                Nenhuma alteração de preço registrada
                                            </p>
                                            <p className="text-sm text-gray-500 dark:text-gray-400">
                                                Este produto ainda não teve alterações de preço desde o cadastro inicial
                                            </p>
                                            <div className="mt-6 bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 max-w-md mx-auto">
                                                <p className="text-sm text-gray-700 dark:text-gray-300">
                                                    <strong>Preço Atual:</strong>
                                                </p>
                                                <div className="mt-2 space-y-1">
                                                    <p className="text-sm">Custo: <span className="font-bold">{formatCurrency(produto.preco_custo)}</span></p>
                                                    <p className="text-sm">Venda: <span className="font-bold">{formatCurrency(produto.preco_venda)}</span></p>
                                                    <p className="text-sm">Margem: <span className="font-bold">{(produto.margem_lucro || 0).toFixed(1)}%</span></p>
                                                </div>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="space-y-4">
                                            {historicoPrecos.map((hist) => {
                                                const variacaoCusto = hist.preco_custo_novo - hist.preco_custo_anterior;
                                                const variacaoVenda = hist.preco_venda_novo - hist.preco_venda_anterior;
                                                const variacaoMargemPct = hist.margem_nova - hist.margem_anterior;
                                                
                                                return (
                                                    <div
                                                        key={hist.id}
                                                        className="bg-white dark:bg-gray-750 border border-gray-200 dark:border-gray-700 rounded-lg p-4"
                                                    >
                                                        <div className="flex items-start justify-between mb-3">
                                                            <div>
                                                                <p className="text-sm font-semibold text-gray-900 dark:text-white">
                                                                    {hist.motivo}
                                                                </p>
                                                                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                                                    {new Date(hist.data_alteracao).toLocaleString('pt-BR')}
                                                                    {hist.funcionario_nome && ` • ${hist.funcionario_nome}`}
                                                                </p>
                                                            </div>
                                                        </div>
                                                        
                                                        <div className="grid grid-cols-3 gap-4">
                                                            {/* Custo */}
                                                            <div>
                                                                <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Preço de Custo</p>
                                                                <div className="flex items-center gap-2">
                                                                    <span className="text-sm line-through text-gray-400">
                                                                        {formatCurrency(hist.preco_custo_anterior)}
                                                                    </span>
                                                                    <span className="text-sm font-bold text-gray-900 dark:text-white">
                                                                        {formatCurrency(hist.preco_custo_novo)}
                                                                    </span>
                                                                    {variacaoCusto !== 0 && (
                                                                        <span className={`text-xs font-semibold ${
                                                                            variacaoCusto > 0 
                                                                                ? 'text-red-600 dark:text-red-400' 
                                                                                : 'text-green-600 dark:text-green-400'
                                                                        }`}>
                                                                            {variacaoCusto > 0 ? '+' : ''}{formatCurrency(variacaoCusto)}
                                                                        </span>
                                                                    )}
                                                                </div>
                                                            </div>
                                                            
                                                            {/* Venda */}
                                                            <div>
                                                                <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Preço de Venda</p>
                                                                <div className="flex items-center gap-2">
                                                                    <span className="text-sm line-through text-gray-400">
                                                                        {formatCurrency(hist.preco_venda_anterior)}
                                                                    </span>
                                                                    <span className="text-sm font-bold text-gray-900 dark:text-white">
                                                                        {formatCurrency(hist.preco_venda_novo)}
                                                                    </span>
                                                                    {variacaoVenda !== 0 && (
                                                                        <span className={`text-xs font-semibold ${
                                                                            variacaoVenda > 0 
                                                                                ? 'text-green-600 dark:text-green-400' 
                                                                                : 'text-red-600 dark:text-red-400'
                                                                        }`}>
                                                                            {variacaoVenda > 0 ? '+' : ''}{formatCurrency(variacaoVenda)}
                                                                        </span>
                                                                    )}
                                                                </div>
                                                            </div>
                                                            
                                                            {/* Margem */}
                                                            <div>
                                                                <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Margem de Lucro</p>
                                                                <div className="flex items-center gap-2">
                                                                    <span className="text-sm line-through text-gray-400">
                                                                        {hist.margem_anterior.toFixed(1)}%
                                                                    </span>
                                                                    <span className="text-sm font-bold text-gray-900 dark:text-white">
                                                                        {hist.margem_nova.toFixed(1)}%
                                                                    </span>
                                                                    {variacaoMargemPct !== 0 && (
                                                                        <span className={`text-xs font-semibold ${
                                                                            variacaoMargemPct > 0 
                                                                                ? 'text-green-600 dark:text-green-400' 
                                                                                : 'text-red-600 dark:text-red-400'
                                                                        }`}>
                                                                            {variacaoMargemPct > 0 ? '+' : ''}{variacaoMargemPct.toFixed(1)}pp
                                                                        </span>
                                                                    )}
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Tab: Fornecedor */}
                            {activeTab === 'fornecedor' && (
                                <div className="space-y-6">
                                    {!produto.fornecedor_id ? (
                                        <div className="text-center py-12">
                                            <AlertTriangle className="w-16 h-16 text-orange-400 mx-auto mb-4" />
                                            <p className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                                                Produto sem fornecedor cadastrado
                                            </p>
                                            <p className="text-sm text-gray-600 dark:text-gray-400">
                                                Cadastre um fornecedor para este produto para melhor controle de estoque
                                            </p>
                                        </div>
                                    ) : fornecedorInfo ? (
                                        <div className="space-y-4">
                                            {/* Informações do Fornecedor */}
                                            <div className="bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-lg p-6 border border-blue-200 dark:border-blue-800">
                                                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                                                    {fornecedorInfo.nome || fornecedorInfo.razao_social}
                                                </h3>
                                                <div className="grid grid-cols-2 gap-4">
                                                    <div>
                                                        <p className="text-sm text-gray-600 dark:text-gray-400">CNPJ</p>
                                                        <p className="text-base font-semibold text-gray-900 dark:text-white">
                                                            {fornecedorInfo.cnpj || 'Não informado'}
                                                        </p>
                                                    </div>
                                                    <div>
                                                        <p className="text-sm text-gray-600 dark:text-gray-400">Telefone</p>
                                                        <p className="text-base font-semibold text-gray-900 dark:text-white">
                                                            {fornecedorInfo.telefone || 'Não informado'}
                                                        </p>
                                                    </div>
                                                    <div>
                                                        <p className="text-sm text-gray-600 dark:text-gray-400">Email</p>
                                                        <p className="text-base font-semibold text-gray-900 dark:text-white">
                                                            {fornecedorInfo.email || 'Não informado'}
                                                        </p>
                                                    </div>
                                                    <div>
                                                        <p className="text-sm text-gray-600 dark:text-gray-400">Cidade/Estado</p>
                                                        <p className="text-base font-semibold text-gray-900 dark:text-white">
                                                            {fornecedorInfo.cidade && fornecedorInfo.estado 
                                                                ? `${fornecedorInfo.cidade}/${fornecedorInfo.estado}`
                                                                : 'Não informado'
                                                            }
                                                        </p>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Histórico de Compras */}
                                            <div className="bg-gray-50 dark:bg-gray-750 rounded-lg p-6">
                                                <h3 className="text-lg font-bold text-gray-800 dark:text-white mb-4">
                                                    Histórico de Compras deste Produto
                                                </h3>
                                                <div className="text-center py-8">
                                                    <Package className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
                                                    <p className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">
                                                        Histórico de Compras em Desenvolvimento
                                                    </p>
                                                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                                                        Em breve você poderá visualizar:
                                                    </p>
                                                    <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-2 max-w-md mx-auto text-left">
                                                        <li className="flex items-center gap-2">
                                                            <span className="text-blue-600">✓</span>
                                                            Histórico completo de pedidos de compra
                                                        </li>
                                                        <li className="flex items-center gap-2">
                                                            <span className="text-blue-600">✓</span>
                                                            Evolução de preços de custo ao longo do tempo
                                                        </li>
                                                        <li className="flex items-center gap-2">
                                                            <span className="text-blue-600">✓</span>
                                                            Tempo médio de entrega do fornecedor
                                                        </li>
                                                        <li className="flex items-center gap-2">
                                                            <span className="text-blue-600">✓</span>
                                                            Análise de confiabilidade e pontualidade
                                                        </li>
                                                    </ul>
                                                </div>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="flex justify-center items-center h-64">
                                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500"></div>
                                        </div>
                                    )}
                                </div>
                            )}
                        </>
                    )}
                </div>

                {/* Footer */}
                <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-4 bg-gray-50 dark:bg-gray-750 flex justify-end">
                    <button
                        onClick={onClose}
                        className="px-6 py-2.5 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-white rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
                    >
                        Fechar
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ProductHistoryModal;
