import React, { useEffect, useState, useCallback, useMemo } from "react";
import { apiClient } from "../../api/apiClient";
import {
    Wallet, TrendingUp, TrendingDown, Brain, Lightbulb,
    Target, DollarSign, PieChart, Users,
    Building, ShoppingCart, Package, Calculator, BarChart2,
    Zap, AlertCircle
} from "lucide-react";
import { Despesa, ResumoFinanceiro } from './expensesService';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
    ArcElement,
    PointElement,
    LineElement,
    Filler
} from 'chart.js';
import { Bar, Line } from 'react-chartjs-2';

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
    ArcElement,
    PointElement,
    LineElement,
    Filler
);

interface AnaliseInteligente {
    mes_atual: {
        total_despesas: number;
        total_receitas: number;
        lucro_liquido: number;
        margem_lucro: number;
    };
    mes_anterior: {
        total_despesas: number;
        total_receitas: number;
        lucro_liquido: number;
        margem_lucro: number;
    };
    variacao: {
        despesas_percentual: number;
        receitas_percentual: number;
        lucro_percentual: number;
    };
    previsao_proximo_mes: {
        despesas_estimadas: number;
        receitas_estimadas: number;
        lucro_projetado: number;
    };
    alertas_inteligentes: Array<{
        tipo: 'oportunidade' | 'risco' | 'atencao';
        mensagem: string;
        impacto: number;
        acao_recomendada: string;
    }>;
    insights: Array<{
        titulo: string;
        descricao: string;
        tipo: 'economia' | 'investimento' | 'otimizacao';
        valor_impacto: number;
    }>;
}

const ExpensesPageInteligente: React.FC = () => {
    const [despesas, setDespesas] = useState<Despesa[]>([]);
    const [resumo, setResumo] = useState<ResumoFinanceiro | null>(null);
    const [analiseInteligente, setAnaliseInteligente] = useState<AnaliseInteligente | null>(null);
    const [activeTab, setActiveTab] = useState<'overview' | 'detalhado' | 'previsao' | 'insights'>('overview');
    const [selectedPeriod, setSelectedPeriod] = useState<'30' | '60' | '90'>('30');

    // Categorias inteligentes com IA
    const categoriasFixas = [
        {
            categoria: 'Custos Fixos',
            icone: Building,
            cor: '#3B82F6',
            subcategorias: ['Aluguel', 'Água', 'Luz', 'Internet', 'Seguros', 'Impostos']
        },
        {
            categoria: 'Salários e Encargos',
            icone: Users,
            cor: '#10B981',
            subcategorias: ['Salários', 'INSS', 'FGTS', 'Vale Transporte', 'Benefícios']
        },
        {
            categoria: 'Compras de Mercadorias',
            icone: ShoppingCart,
            cor: '#F59E0B',
            subcategorias: ['Fornecedores', 'Matéria Prima', 'Embalagens', 'Transporte']
        },
        {
            categoria: 'Fio Terra',
            icone: DollarSign,
            cor: '#EF4444',
            subcategorias: ['IRPJ', 'PIS', 'COFINS', 'ICMS', 'ISS']
        },
        {
            categoria: 'Operacionais',
            icone: Package,
            cor: '#8B5CF6',
            subcategorias: ['Marketing', 'Manutenção', 'Software', 'Material Escritório']
        }
    ];

    const formatarMoeda = (valor: number) => {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(valor);
    };

    const formatarPercentual = (valor: number) => {
        return `${valor > 0 ? '+' : ''}${valor.toFixed(1)}%`;
    };

    // Simulação de análise inteligente (em produção, viria da API)
    const gerarAnaliseInteligente = useCallback(() => {
        if (!resumo) return null;

        const mes_atual = {
            total_despesas: resumo.total_despesas || 0,
            total_receitas: resumo.total_receitas || 0,
            lucro_liquido: (resumo.total_receitas || 0) - (resumo.total_despesas || 0),
            margem_lucro: ((resumo.total_receitas || 0) > 0) 
                ? (((resumo.total_receitas || 0) - (resumo.total_despesas || 0)) / (resumo.total_receitas || 0)) * 100 
                : 0
        };

        const mes_anterior = {
            total_despesas: (resumo.total_despesas || 0) * 0.9,
            total_receitas: (resumo.total_receitas || 0) * 0.85,
            lucro_liquido: ((resumo.total_receitas || 0) * 0.85) - ((resumo.total_despesas || 0) * 0.9),
            margem_lucro: 15.5
        };

        const variacao = {
            despesas_percentual: ((mes_atual.total_despesas - mes_anterior.total_despesas) / mes_anterior.total_despesas) * 100,
            receitas_percentual: ((mes_atual.total_receitas - mes_anterior.total_receitas) / mes_anterior.total_receitas) * 100,
            lucro_percentual: ((mes_atual.lucro_liquido - mes_anterior.lucro_liquido) / Math.abs(mes_anterior.lucro_liquido)) * 100
        };

        const previsao_proximo_mes = {
            despesas_estimadas: mes_atual.total_despesas * 1.05,
            receitas_estimadas: mes_atual.total_receitas * 1.08,
            lucro_projetado: (mes_atual.total_receitas * 1.08) - (mes_atual.total_despesas * 1.05)
        };

        const alertas_inteligentes = [
            {
                tipo: 'oportunidade',
                mensagem: 'Suas despesas com fornecedores aumentaram 15%. Negocie melhores condições!',
                impacto: mes_atual.total_despesas * 0.15,
                acao_recomendada: 'Entrar em contato com fornecedores para renegociar prazos e preços'
            },
            {
                tipo: 'risco',
                mensagem: 'Margem de lucro caiu 5% este mês. Analise custos fixos.',
                impacto: Math.abs(mes_atual.margem_lucro - mes_anterior.margem_lucro),
                acao_recomendada: 'Revisar contratos de aluguel e serviços essenciais'
            },
            {
                tipo: 'atencao',
                mensagem: 'Fio terra representa 8% do faturamento. Considere planejamento tributário.',
                impacto: mes_atual.total_despesas * 0.08,
                acao_recomendada: 'Consultar contador para otimização fiscal'
            }
        ];

        const insights = [
            {
                titulo: 'Oportunidade de Economia',
                descricao: 'Reduzindo despesas operacionais em 10% você economiza R$ 2.500/mês',
                tipo: 'economia' as const,
                valor_impacto: 2500
            },
            {
                titulo: 'Investimento Recomendado',
                descricao: 'Automatizar gestão pode aumentar eficiência em 25%',
                tipo: 'investimento' as const,
                valor_impacto: 5000
            },
            {
                titulo: 'Otimização de Estoque',
                descricao: 'Giro de estoque otimizado pode liberar R$ 8.000 em capital',
                tipo: 'otimizacao' as const,
                valor_impacto: 8000
            }
        ];

        return {
            mes_atual,
            mes_anterior,
            variacao,
            previsao_proximo_mes,
            alertas_inteligentes,
            insights
        };
    }, [resumo]);

    useEffect(() => {
        setAnaliseInteligente(gerarAnaliseInteligente());
    }, [gerarAnaliseInteligente]);

    const fetchData = useCallback(async () => {
        try {
            const [despesasRes, resumoRes] = await Promise.all([
                apiClient.get('/despesas/'),
                apiClient.get('/despesas/resumo')
            ]);

            if (despesasRes.data?.success) {
                setDespesas(despesasRes.data.despesas);
            }
            if (resumoRes.data?.success) {
                setResumo(resumoRes.data.resumo);
            }
        } catch (error) {
            console.error('Erro ao carregar dados:', error);
        }
    }, []);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    const dadosGraficoTendencia = useMemo(() => {
        if (!analiseInteligente) return null;

        return {
            labels: ['Mês Anterior', 'Mês Atual', 'Previsão Próximo Mês'],
            datasets: [
                {
                    label: 'Despesas',
                    data: [
                        analiseInteligente.mes_anterior.total_despesas,
                        analiseInteligente.mes_atual.total_despesas,
                        analiseInteligente.previsao_proximo_mes.despesas_estimadas
                    ],
                    backgroundColor: '#EF4444',
                    borderColor: '#EF4444',
                },
                {
                    label: 'Receitas',
                    data: [
                        analiseInteligente.mes_anterior.total_receitas,
                        analiseInteligente.mes_atual.total_receitas,
                        analiseInteligente.previsao_proximo_mes.receitas_estimadas
                    ],
                    backgroundColor: '#10B981',
                    borderColor: '#10B981',
                }
            ]
        };
    }, [analiseInteligente]);

    const dadosGraficoCategorias = useMemo(() => {
        if (!resumo?.despesas_por_categoria) return null;

        const categorias = Object.entries(resumo.despesas_por_categoria).map(([categoria, dados]) => ({
            categoria,
            total: dados.total,
            quantidade: dados.quantidade || 1
        }));

        return {
            labels: categorias.map(c => c.categoria),
            datasets: [{
                data: categorias.map(c => c.total),
                backgroundColor: [
                    '#3B82F6', '#10B981', '#F59E0B', 
                    '#EF4444', '#8B5CF6', '#F97316'
                ],
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        };
    }, [resumo]);

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6">
            <div className="max-w-7xl mx-auto">
                {/* Header Inteligente */}
                <div className="bg-white rounded-2xl shadow-lg p-8 mb-8 border border-gray-100">
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900 flex items-center">
                                <Brain className="w-8 h-8 text-blue-600 mr-3" />
                                Centro de Controle Financeiro Inteligente
                            </h1>
                            <p className="text-gray-600 mt-2">
                                Análise preditiva e recomendações para otimizar seu negócio
                            </p>
                        </div>
                        <div className="flex items-center space-x-4">
                            <select
                                value={selectedPeriod}
                                onChange={(e) => setSelectedPeriod(e.target.value as any)}
                                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            >
                                <option value="30">Últimos 30 dias</option>
                                <option value="60">Últimos 60 dias</option>
                                <option value="90">Últimos 90 dias</option>
                            </select>
                            <button
                                onClick={() => setShowAnalyticsModal(true)}
                                className="flex items-center space-x-2 px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-all transform hover:scale-105"
                            >
                                <BarChart2 className="w-5 h-5" />
                                <span>Análise Profunda</span>
                            </button>
                        </div>
                    </div>
                </div>

                {/* Cards Principais com IA */}
                {analiseInteligente && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                        <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-red-500">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm font-medium text-gray-600">Despesas do Mês</p>
                                    <p className="text-2xl font-bold text-gray-900">
                                        {formatarMoeda(analiseInteligente.mes_atual.total_despesas)}
                                    </p>
                                    <div className="flex items-center mt-2">
                                        {analiseInteligente.variacao.despesas_percentual > 0 ? (
                                            <TrendingUp className="w-4 h-4 text-red-500 mr-1" />
                                        ) : (
                                            <TrendingDown className="w-4 h-4 text-green-500 mr-1" />
                                        )}
                                        <span className={`text-sm font-medium ${
                                            analiseInteligente.variacao.despesas_percentual > 0 ? 'text-red-500' : 'text-green-500'
                                        }`}>
                                            {formatarPercentual(analiseInteligente.variacao.despesas_percentual)}
                                        </span>
                                    </div>
                                </div>
                                <div className="p-3 bg-red-100 rounded-lg">
                                    <Wallet className="w-6 h-6 text-red-600" />
                                </div>
                            </div>
                        </div>

                        <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-green-500">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm font-medium text-gray-600">Receitas do Mês</p>
                                    <p className="text-2xl font-bold text-gray-900">
                                        {formatarMoeda(analiseInteligente.mes_atual.total_receitas)}
                                    </p>
                                    <div className="flex items-center mt-2">
                                        {analiseInteligente.variacao.receitas_percentual > 0 ? (
                                            <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
                                        ) : (
                                            <TrendingDown className="w-4 h-4 text-red-500 mr-1" />
                                        )}
                                        <span className={`text-sm font-medium ${
                                            analiseInteligente.variacao.receitas_percentual > 0 ? 'text-green-500' : 'text-red-500'
                                        }`}>
                                            {formatarPercentual(analiseInteligente.variacao.receitas_percentual)}
                                        </span>
                                    </div>
                                </div>
                                <div className="p-3 bg-green-100 rounded-lg">
                                    <TrendingUp className="w-6 h-6 text-green-600" />
                                </div>
                            </div>
                        </div>

                        <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-blue-500">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm font-medium text-gray-600">Lucro Líquido</p>
                                    <p className="text-2xl font-bold text-gray-900">
                                        {formatarMoeda(analiseInteligente.mes_atual.lucro_liquido)}
                                    </p>
                                    <div className="flex items-center mt-2">
                                        {analiseInteligente.variacao.lucro_percentual > 0 ? (
                                            <TrendingUp className="w-4 h-4 text-blue-500 mr-1" />
                                        ) : (
                                            <TrendingDown className="w-4 h-4 text-red-500 mr-1" />
                                        )}
                                        <span className={`text-sm font-medium ${
                                            analiseInteligente.variacao.lucro_percentual > 0 ? 'text-blue-500' : 'text-red-500'
                                        }`}>
                                            {formatarPercentual(analiseInteligente.variacao.lucro_percentual)}
                                        </span>
                                    </div>
                                </div>
                                <div className="p-3 bg-blue-100 rounded-lg">
                                    <Target className="w-6 h-6 text-blue-600" />
                                </div>
                            </div>
                        </div>

                        <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-purple-500">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm font-medium text-gray-600">Margem de Lucro</p>
                                    <p className="text-2xl font-bold text-gray-900">
                                        {analiseInteligente.mes_atual.margem_lucro.toFixed(1)}%
                                    </p>
                                    <div className="flex items-center mt-2">
                                        <Calculator className="w-4 h-4 text-purple-500 mr-1" />
                                        <span className="text-sm font-medium text-purple-500">
                                            Meta: 25%
                                        </span>
                                    </div>
                                </div>
                                <div className="p-3 bg-purple-100 rounded-lg">
                                    <PieChart className="w-6 h-6 text-purple-600" />
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Alertas Inteligentes */}
                {analiseInteligente && (
                    <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
                        <h2 className="text-xl font-bold text-gray-900 mb-6 flex items-center">
                            <Lightbulb className="w-6 h-6 text-yellow-500 mr-2" />
                            Recomendações Inteligentes
                        </h2>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            {analiseInteligente.alertas_inteligentes.map((alerta, index) => (
                                <div
                                    key={index}
                                    className={`p-4 rounded-lg border-l-4 ${
                                        alerta.tipo === 'oportunidade' ? 'bg-green-50 border-green-500' :
                                        alerta.tipo === 'risco' ? 'bg-red-50 border-red-500' :
                                        'bg-yellow-50 border-yellow-500'
                                    }`}
                                >
                                    <div className="flex items-start">
                                        <div className="flex-shrink-0">
                                            {alerta.tipo === 'oportunidade' && <TrendingUp className="w-5 h-5 text-green-600" />}
                                            {alerta.tipo === 'risco' && <AlertCircle className="w-5 h-5 text-red-600" />}
                                            {alerta.tipo === 'atencao' && <Zap className="w-5 h-5 text-yellow-600" />}
                                        </div>
                                        <div className="ml-3 flex-1">
                                            <h3 className="font-semibold text-gray-900 mb-1">
                                                {alerta.tipo === 'oportunidade' ? 'Oportunidade' :
                                                 alerta.tipo === 'risco' ? 'Risco' : 'Atenção'}
                                            </h3>
                                            <p className="text-sm text-gray-700 mb-2">{alerta.mensagem}</p>
                                            <div className="flex items-center justify-between">
                                                <span className="text-sm font-medium text-gray-600">
                                                    Impacto: {formatarMoeda(alerta.impacto)}
                                                </span>
                                                <button className="text-sm text-blue-600 hover:text-blue-800 font-medium">
                                                    Ver Ação →
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Tabs de Análise */}
                <div className="bg-white rounded-xl shadow-lg">
                    <div className="border-b border-gray-200">
                        <nav className="flex space-x-8 px-6">
                            {[
                                { id: 'overview', label: 'Visão Geral', icon: BarChart2 },
                                { id: 'detalhado', label: 'Análise Detalhada', icon: Brain },
                                { id: 'previsao', label: 'Previsões', icon: Target },
                                { id: 'insights', label: 'Insights', icon: Lightbulb }
                            ].map((tab) => (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id as any)}
                                    className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                                        activeTab === tab.id
                                            ? 'border-blue-500 text-blue-600'
                                            : 'border-transparent text-gray-500 hover:text-gray-700'
                                    }`}
                                >
                                    <tab.icon className="w-4 h-4" />
                                    <span>{tab.label}</span>
                                </button>
                            ))}
                        </nav>
                    </div>

                    <div className="p-6">
                        {activeTab === 'overview' && (
                            <div className="space-y-8">
                                {/* Gráfico de Tendência */}
                                {dadosGraficoTendencia && (
                                    <div>
                                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Tendência Financeira</h3>
                                        <div className="bg-gray-50 rounded-lg p-4">
                                            <Line data={dadosGraficoTendencia} options={{
                                                responsive: true,
                                                plugins: {
                                                    legend: { position: 'top' },
                                                    tooltip: {
                                                        callbacks: {
                                                            label: (context) => `${context.dataset.label}: ${formatarMoeda(context.parsed.y)}`
                                                        }
                                                    }
                                                }
                                            }} />
                                        </div>
                                    </div>
                                )}

                                {/* Gráfico de Categorias */}
                                {dadosGraficoCategorias && (
                                    <div>
                                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Despesas por Categoria</h3>
                                        <div className="bg-gray-50 rounded-lg p-4">
                                            <Bar data={dadosGraficoCategorias} options={{
                                                responsive: true,
                                                plugins: {
                                                    legend: { display: false },
                                                    tooltip: {
                                                        callbacks: {
                                                            label: (context) => `${formatarMoeda(context.parsed.y)}`
                                                        }
                                                    }
                                                }
                                            }} />
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        {activeTab === 'detalhado' && (
                            <div className="text-center py-12">
                                <Brain className="w-16 h-16 text-blue-600 mx-auto mb-4" />
                                <h3 className="text-xl font-semibold text-gray-900 mb-2">Análise Detalhada com IA</h3>
                                <p className="text-gray-600 mb-6">
                                    Análise avançada de padrões, anomalias e oportunidades de otimização
                                </p>
                                <button className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                                    Gerar Relatório Completo
                                </button>
                            </div>
                        )}

                        {activeTab === 'previsao' && analiseInteligente && (
                            <div className="space-y-6">
                                <h3 className="text-lg font-semibold text-gray-900">Previsão para o Próximo Mês</h3>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                    <div className="bg-blue-50 rounded-lg p-4">
                                        <h4 className="font-medium text-blue-900 mb-2">Despesas Estimadas</h4>
                                        <p className="text-2xl font-bold text-blue-900">
                                            {formatarMoeda(analiseInteligente.previsao_proximo_mes.despesas_estimadas)}
                                        </p>
                                    </div>
                                    <div className="bg-green-50 rounded-lg p-4">
                                        <h4 className="font-medium text-green-900 mb-2">Receitas Estimadas</h4>
                                        <p className="text-2xl font-bold text-green-900">
                                            {formatarMoeda(analiseInteligente.previsao_proximo_mes.receitas_estimadas)}
                                        </p>
                                    </div>
                                    <div className="bg-purple-50 rounded-lg p-4">
                                        <h4 className="font-medium text-purple-900 mb-2">Lucro Projetado</h4>
                                        <p className="text-2xl font-bold text-purple-900">
                                            {formatarMoeda(analiseInteligente.previsao_proximo_mes.lucro_projetado)}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeTab === 'insights' && analiseInteligente && (
                            <div className="space-y-6">
                                <h3 className="text-lg font-semibold text-gray-900">Insights Estratégicos</h3>
                                <div className="space-y-4">
                                    {analiseInteligente.insights.map((insight, index) => (
                                        <div key={index} className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-6 border border-blue-200">
                                            <div className="flex items-start">
                                                <div className="flex-shrink-0">
                                                    {insight.tipo === 'economia' && <TrendingDown className="w-6 h-6 text-green-600" />}
                                                    {insight.tipo === 'investimento' && <Target className="w-6 h-6 text-blue-600" />}
                                                    {insight.tipo === 'otimizacao' && <Zap className="w-6 h-6 text-purple-600" />}
                                                </div>
                                                <div className="ml-4 flex-1">
                                                    <h4 className="font-semibold text-gray-900 mb-2">{insight.titulo}</h4>
                                                    <p className="text-gray-700 mb-3">{insight.descricao}</p>
                                                    <div className="flex items-center justify-between">
                                                        <span className="text-lg font-bold text-blue-600">
                                                            {formatarMoeda(insight.valor_impacto)}
                                                        </span>
                                                        <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm">
                                                            Implementar
                                                        </button>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ExpensesPageInteligente;
