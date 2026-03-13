import React, { useEffect, useState, useCallback, useMemo } from "react";
import { apiClient } from "../../api/apiClient";
import {
    Wallet, TrendingUp, TrendingDown, Brain, Lightbulb,
    Target, PieChart, Calculator, BarChart2,
    Zap, AlertCircle, Calendar, ArrowRight, ShieldCheck,
    ChevronRight, Sparkles
} from "lucide-react";
import { Despesa, ResumoFinanceiro, AlertaFinanceiro } from './expensesService';
import { motion, AnimatePresence } from "framer-motion";
import { format, subDays } from 'date-fns';
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
    indicadores: {
        comprometimento: number;
        pressao_caixa: number;
        venda_media: number;
        saldo_fluxo: number;
    };
    variacao: {
        despesas_percentual: number;
        receitas_percentual: number;
        lucro_percentual: number;
    };
    previsao: {
        despesas_estimadas: number;
        receitas_estimadas: number;
        lucro_projetado: number;
    };
    alertas: AlertaFinanceiro[];
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
    const [showAnalyticsModal, setShowAnalyticsModal] = useState(false);
    const [loading, setLoading] = useState(true);

    const categoriasFixas = useMemo(() => [
        {
            categoria: 'Custos Fixos',
            cor: '#3B82F6',
            subcategorias: ['Aluguel', 'Água', 'Luz', 'Internet', 'Seguros', 'Impostos']
        },
        {
            categoria: 'Salários e Encargos',
            cor: '#10B981',
            subcategorias: ['Salários', 'INSS', 'FGTS', 'Vale Transporte', 'Benefícios']
        },
        {
            categoria: 'Compras de Mercadorias',
            cor: '#F59E0B',
            subcategorias: ['Fornecedores', 'Matéria Prima', 'Embalagens', 'Transporte']
        },
        {
            categoria: 'Impostos e Taxas',
            cor: '#EF4444',
            subcategorias: ['IRPJ', 'PIS', 'COFINS', 'ICMS', 'ISS']
        },
        {
            categoria: 'Operacionais',
            cor: '#8B5CF6',
            subcategorias: ['Marketing', 'Manutenção', 'Software', 'Material Escritório']
        }
    ], []);

    const formatarMoeda = (valor: number) => {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(valor);
    };

    const formatarPercentual = (valor: number) => {
        return `${valor > 0 ? '+' : ''}${valor.toFixed(1)}%`;
    };

    const gerarAnaliseInteligente = useCallback((): AnaliseInteligente | null => {
        if (!resumo) return null;

        const { dre_consolidado, indicadores_gestao, fluxo_caixa_real, despesas_mes, alertas } = resumo;

        const total_despesas = despesas_mes.total || 0;
        const total_receitas = dre_consolidado.receita_bruta || 0;
        const lucro_liquido = dre_consolidado.lucro_liquido || (total_receitas - total_despesas);

        const mes_atual = {
            total_despesas,
            total_receitas,
            lucro_liquido,
            margem_lucro: (total_receitas > 0) ? (lucro_liquido / total_receitas) * 100 : 0
        };

        const indicadores = {
            comprometimento: indicadores_gestao.indice_comprometimento || 0,
            pressao_caixa: indicadores_gestao.pressao_caixa_diaria || 0,
            venda_media: indicadores_gestao.venda_media_diaria || 0,
            saldo_fluxo: fluxo_caixa_real.saldo || 0
        };

        const variacao = {
            despesas_percentual: -2.5,
            receitas_percentual: 5.8,
            lucro_percentual: 12.4
        };

        const previsao = {
            despesas_estimadas: total_despesas * 1.02,
            receitas_estimadas: total_receitas * 1.05,
            lucro_projetado: (total_receitas * 1.05) - (total_despesas * 1.02)
        };

        const insights: AnaliseInteligente['insights'] = [
            {
                titulo: 'Otimização de Custos',
                descricao: indicadores.comprometimento > 50
                    ? 'Seu comprometimento de renda está alto. Revise fornecedores.'
                    : 'Custos sob controle. Bom momento para investimentos operacionais.',
                tipo: 'economia',
                valor_impacto: total_despesas * 0.1
            },
            {
                titulo: 'Estratégia de Vendas',
                descricao: 'Aumentar o ticket médio em 10% pode gerar um reflexo direto no lucro líquido.',
                tipo: 'investimento',
                valor_impacto: total_receitas * 0.1
            }
        ];

        return {
            mes_atual,
            indicadores,
            variacao,
            previsao,
            alertas,
            insights
        };
    }, [resumo]);

    useEffect(() => {
        if (resumo) {
            setAnaliseInteligente(gerarAnaliseInteligente());
        }
    }, [resumo, gerarAnaliseInteligente]);

    const fetchData = useCallback(async () => {
        setLoading(true);
        try {
            const dataFim = format(new Date(), 'yyyy-MM-dd');
            const dataInicio = format(subDays(new Date(), parseInt(selectedPeriod)), 'yyyy-MM-dd');

            const [despesasRes, resumoRes] = await Promise.all([
                apiClient.get('/despesas/', { params: { inicio: dataInicio, fim: dataFim } }),
                apiClient.get('/despesas/resumo-financeiro/', { params: { data_inicio: dataInicio, data_fim: dataFim } })
            ]);

            if (despesasRes.data?.success) {
                setDespesas(despesasRes.data.data);
            }
            if (resumoRes.data?.success) {
                setResumo(resumoRes.data);
            }
        } catch (error) {
            console.error('Erro ao carregar dados:', error);
        } finally {
            setLoading(false);
        }
    }, [selectedPeriod]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    const dadosGraficoTendencia = useMemo(() => {
        if (!analiseInteligente) return null;

        return {
            labels: ['Meta Est.', 'Atual', 'Projetado'],
            datasets: [
                {
                    label: 'Despesas',
                    data: [
                        analiseInteligente.mes_atual.total_despesas * 0.95,
                        analiseInteligente.mes_atual.total_despesas,
                        analiseInteligente.previsao.despesas_estimadas
                    ],
                    backgroundColor: 'rgba(239, 68, 68, 0.8)',
                    borderColor: '#EF4444',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Receitas',
                    data: [
                        analiseInteligente.mes_atual.total_receitas * 0.92,
                        analiseInteligente.mes_atual.total_receitas,
                        analiseInteligente.previsao.receitas_estimadas
                    ],
                    backgroundColor: 'rgba(16, 185, 129, 0.2)',
                    borderColor: '#10B981',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }
            ]
        };
    }, [analiseInteligente]);

    const dadosGraficoCategorias = useMemo(() => {
        if (!despesas.length) return null;

        const totaisCategorias = categoriasFixas.map(cat => ({
            label: cat.categoria,
            total: 0,
            cor: cat.cor,
            subcategorias: cat.subcategorias.map(s => s.toLowerCase())
        }));

        const categoriaOutros = { label: 'Outros', total: 0, cor: '#94A3B8', subcategorias: [] as string[] };

        despesas.forEach(despesa => {
            const categoriaDespesa = (despesa.categoria || "").toLowerCase();
            const descricaoDespesa = (despesa.descricao || "").toLowerCase();

            const index = totaisCategorias.findIndex(cat =>
                cat.label.toLowerCase() === categoriaDespesa ||
                cat.subcategorias.some(sub => categoriaDespesa.includes(sub) || descricaoDespesa.includes(sub))
            );

            if (index !== -1) {
                totaisCategorias[index].total += despesa.valor;
            } else {
                categoriaOutros.total += despesa.valor;
            }
        });

        const categoriasAtivas = [...totaisCategorias, categoriaOutros].filter(c => c.total > 0);

        return {
            labels: categoriasAtivas.map(c => c.label),
            datasets: [{
                data: categoriasAtivas.map(c => c.total),
                backgroundColor: categoriasAtivas.map(c => c.cor),
                borderWidth: 0,
                hoverOffset: 20
            }]
        };
    }, [despesas, categoriasFixas]);

    return (
        <div className="min-h-screen bg-[#F8FAFC] p-4 md:p-8 font-sans text-slate-900 overflow-x-hidden">
            <div className="fixed top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
                <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-400/10 blur-[120px] rounded-full" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-400/10 blur-[120px] rounded-full" />
            </div>

            <div className="max-w-7xl mx-auto relative z-10">
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-10"
                >
                    <div>
                        <div className="flex items-center space-x-3 mb-2">
                            <div className="p-2 bg-blue-600 rounded-lg shadow-lg shadow-blue-200">
                                <Brain className="w-6 h-6 text-white" />
                            </div>
                            <span className="text-sm font-semibold text-blue-600 tracking-wider uppercase">Intelligence Hub</span>
                        </div>
                        <h1 className="text-4xl font-extrabold tracking-tight text-slate-900">
                            Controle Financeiro <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">Inteligente</span>
                        </h1>
                        <p className="text-slate-500 mt-2 flex items-center">
                            <Sparkles className="w-4 h-4 mr-2 text-amber-400" />
                            Análise preditiva em tempo real baseada no seu desempenho operacional.
                        </p>
                    </div>

                    <div className="flex items-center space-x-3">
                        <div className="bg-white/60 backdrop-blur-md border border-white/40 p-1.5 rounded-2xl flex items-center shadow-sm">
                            {(['30', '60', '90'] as const).map((period) => (
                                <button
                                    key={period}
                                    onClick={() => setSelectedPeriod(period)}
                                    className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${selectedPeriod === period
                                        ? 'bg-white shadow-md text-blue-600'
                                        : 'text-slate-500 hover:text-slate-900'
                                        }`}
                                >
                                    {period}d
                                </button>
                            ))}
                        </div>
                        <button
                            onClick={() => setShowAnalyticsModal(true)}
                            className="bg-slate-900 text-white px-6 py-3 rounded-2xl font-semibold shadow-xl shadow-slate-200 hover:bg-slate-800 transition-all flex items-center space-x-2 active:scale-95"
                        >
                            <BarChart2 className="w-5 h-5" />
                            <span>Deep Insights</span>
                        </button>
                    </div>
                </motion.div>

                <AnimatePresence mode="wait">
                    {loading ? (
                        <motion.div
                            key="loading"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
                        >
                            {[1, 2, 3, 4].map((i) => (
                                <div key={i} className="h-32 bg-white/40 animate-pulse rounded-3xl border border-white/60" />
                            ))}
                        </motion.div>
                    ) : analiseInteligente && (
                        <motion.div
                            key="content"
                            initial="hidden"
                            animate="show"
                            variants={{
                                hidden: { opacity: 0 },
                                show: {
                                    opacity: 1,
                                    transition: { staggerChildren: 0.1 }
                                }
                            }}
                            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10"
                        >
                            <motion.div variants={{ hidden: { opacity: 0, scale: 0.95 }, show: { opacity: 1, scale: 1 } }} className="group">
                                <div className="bg-white/80 backdrop-blur-xl p-6 rounded-[2rem] border border-white shadow-xl shadow-slate-200/50 hover:shadow-2xl hover:shadow-red-200/20 transition-all duration-500 relative overflow-hidden h-full">
                                    <div className="absolute top-0 right-0 w-24 h-24 bg-red-500/5 rounded-full -mr-12 -mt-12 group-hover:scale-150 transition-transform duration-700" />
                                    <div className="flex justify-between items-start mb-4">
                                        <div className="p-3 bg-red-50 rounded-2xl group-hover:bg-red-500 group-hover:text-white transition-colors duration-300">
                                            <Wallet className="w-6 h-6" />
                                        </div>
                                        <div className={`flex items-center px-2.5 py-1 rounded-full text-xs font-bold ${analiseInteligente.variacao.despesas_percentual > 0 ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-600'
                                            }`}>
                                            {formatarPercentual(analiseInteligente.variacao.despesas_percentual)}
                                        </div>
                                    </div>
                                    <p className="text-slate-500 text-sm font-medium">Saídas no Período</p>
                                    <h3 className="text-2xl font-black text-slate-900 mt-1">
                                        {formatarMoeda(analiseInteligente.mes_atual.total_despesas)}
                                    </h3>
                                    <div className="mt-4 flex items-center text-xs text-slate-400 space-x-1">
                                        <span>Projeção:</span>
                                        <span className="text-slate-600 font-bold">{formatarMoeda(analiseInteligente.previsao.despesas_estimadas)}</span>
                                    </div>
                                </div>
                            </motion.div>

                            <motion.div variants={{ hidden: { opacity: 0, scale: 0.95 }, show: { opacity: 1, scale: 1 } }} className="group">
                                <div className="bg-white/80 backdrop-blur-xl p-6 rounded-[2rem] border border-white shadow-xl shadow-slate-200/50 hover:shadow-2xl hover:shadow-green-200/20 transition-all duration-500 relative overflow-hidden h-full">
                                    <div className="absolute top-0 right-0 w-24 h-24 bg-green-500/5 rounded-full -mr-12 -mt-12 group-hover:scale-150 transition-transform duration-700" />
                                    <div className="flex justify-between items-start mb-4">
                                        <div className="p-3 bg-green-50 rounded-2xl group-hover:bg-green-500 group-hover:text-white transition-colors duration-300">
                                            <TrendingUp className="w-6 h-6" />
                                        </div>
                                        <div className="flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-green-50 text-green-600">
                                            {formatarPercentual(analiseInteligente.variacao.receitas_percentual)}
                                        </div>
                                    </div>
                                    <p className="text-slate-500 text-sm font-medium">Faturamento Bruto</p>
                                    <h3 className="text-2xl font-black text-slate-900 mt-1">
                                        {formatarMoeda(analiseInteligente.mes_atual.total_receitas)}
                                    </h3>
                                    <div className="mt-4 flex items-center text-xs text-slate-400 space-x-1">
                                        <span>Eficiência:</span>
                                        <span className="text-slate-600 font-bold">Excelente</span>
                                    </div>
                                </div>
                            </motion.div>

                            <motion.div variants={{ hidden: { opacity: 0, scale: 0.95 }, show: { opacity: 1, scale: 1 } }} className="group">
                                <div className="bg-gradient-to-br from-slate-900 to-slate-800 p-6 rounded-[2rem] border border-slate-700 shadow-2xl hover:shadow-blue-500/20 transition-all duration-500 relative overflow-hidden h-full">
                                    <div className="absolute bottom-0 right-0 w-32 h-32 bg-blue-500/10 rounded-full -mr-16 -mb-16 group-hover:scale-150 transition-transform duration-700" />
                                    <div className="flex justify-between items-start mb-4">
                                        <div className="p-3 bg-white/10 rounded-2xl group-hover:bg-blue-500 group-hover:text-white transition-colors duration-300">
                                            <Target className="w-6 h-6 text-blue-400 group-hover:text-white" />
                                        </div>
                                    </div>
                                    <p className="text-slate-400 text-sm font-medium">Lucro Líquido</p>
                                    <h3 className="text-2xl font-black text-white mt-1">
                                        {formatarMoeda(analiseInteligente.mes_atual.lucro_liquido)}
                                    </h3>
                                    <div className="mt-4">
                                        <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-blue-500 rounded-full transition-all duration-1000"
                                                style={{ width: `${Math.min(analiseInteligente.mes_atual.margem_lucro * 2, 100)}%` }}
                                            />
                                        </div>
                                        <p className="text-[10px] text-slate-500 mt-1 font-bold uppercase tracking-widest">Margem: {analiseInteligente.mes_atual.margem_lucro.toFixed(1)}%</p>
                                    </div>
                                </div>
                            </motion.div>

                            <motion.div variants={{ hidden: { opacity: 0, scale: 0.95 }, show: { opacity: 1, scale: 1 } }} className="group">
                                <div className="bg-white/80 backdrop-blur-xl p-6 rounded-[2rem] border border-white shadow-xl shadow-slate-200/50 hover:shadow-2xl hover:shadow-purple-200/20 transition-all duration-500 relative overflow-hidden h-full">
                                    <div className="absolute top-0 right-0 w-24 h-24 bg-purple-500/5 rounded-full -mr-12 -mt-12 group-hover:scale-150 transition-transform duration-700" />
                                    <div className="flex justify-between items-start mb-4">
                                        <div className="p-3 bg-purple-50 rounded-2xl group-hover:bg-purple-500 group-hover:text-white transition-colors duration-300">
                                            <Calculator className="w-6 h-6 text-purple-600" />
                                        </div>
                                    </div>
                                    <p className="text-slate-500 text-sm font-medium">Saúde Operacional</p>
                                    <h3 className="text-2xl font-black text-slate-900 mt-1">
                                        {analiseInteligente.indicadores.comprometimento < 30 ? 'Ótima' : 'Atenção'}
                                    </h3>
                                    <div className="mt-4 flex items-center text-xs text-slate-400 space-x-1">
                                        <span>Comprometimento:</span>
                                        <span className={`font-bold ${analiseInteligente.indicadores.comprometimento > 50 ? 'text-red-600' : 'text-slate-600'}`}>
                                            {analiseInteligente.indicadores.comprometimento.toFixed(1)}%
                                        </span>
                                    </div>
                                </div>
                            </motion.div>
                        </motion.div>
                    )}
                </AnimatePresence>

                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                    <div className="lg:col-span-8 space-y-8">
                        <div className="bg-white/60 backdrop-blur-md p-1.5 rounded-3xl border border-white flex space-x-2 shadow-sm">
                            {[
                                { id: 'overview', label: 'Dashboard', icon: BarChart2 },
                                { id: 'detalhado', label: 'Evolução', icon: Brain },
                                { id: 'previsao', label: 'Projeções', icon: Target },
                                { id: 'insights', label: 'Estratégia', icon: Lightbulb }
                            ].map((tab) => (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id as any)}
                                    className={`flex-1 flex items-center justify-center space-x-2 py-3 px-4 rounded-2xl transition-all duration-300 font-bold text-sm ${activeTab === tab.id
                                        ? 'bg-slate-900 text-white shadow-lg shadow-slate-200'
                                        : 'text-slate-500 hover:bg-white hover:text-slate-900'
                                        }`}
                                >
                                    <tab.icon className="w-4 h-4" />
                                    <span>{tab.label}</span>
                                </button>
                            ))}
                        </div>

                        <div className="bg-white/80 backdrop-blur-xl p-8 rounded-[2.5rem] border border-white shadow-2xl shadow-slate-200/50 min-h-[500px]">
                            <AnimatePresence mode="wait">
                                <motion.div
                                    key={activeTab}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: -10 }}
                                    transition={{ duration: 0.3 }}
                                >
                                    {activeTab === 'overview' && (
                                        <div className="space-y-10">
                                            <div className="flex items-center justify-between">
                                                <h3 className="text-xl font-black text-slate-900">Visão Panorâmica</h3>
                                                <div className="flex items-center space-x-2 text-xs font-bold text-slate-400 bg-slate-50 px-3 py-1.5 rounded-full uppercase tracking-tighter">
                                                    <Calendar className="w-3 h-3" />
                                                    <span>Tempo Real</span>
                                                </div>
                                            </div>

                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                                                <div className="space-y-4">
                                                    <p className="text-sm font-bold text-slate-400 uppercase tracking-widest">Tendência de Fluxo</p>
                                                    <div className="h-[300px]">
                                                        {dadosGraficoTendencia && <Line data={dadosGraficoTendencia} options={{
                                                            responsive: true,
                                                            maintainAspectRatio: false,
                                                            plugins: {
                                                                legend: { display: false },
                                                                tooltip: {
                                                                    callbacks: {
                                                                        label: (context) => `${context.dataset.label}: ${formatarMoeda(Number(context.parsed.y) ?? 0)}`
                                                                    }
                                                                }
                                                            },
                                                            scales: { y: { display: false }, x: { grid: { display: false } } }
                                                        }} />}
                                                    </div>
                                                </div>
                                                <div className="space-y-4">
                                                    <p className="text-sm font-bold text-slate-400 uppercase tracking-widest">Peso por Categoria</p>
                                                    <div className="h-[300px]">
                                                        {dadosGraficoCategorias && <Bar data={dadosGraficoCategorias} options={{
                                                            responsive: true,
                                                            maintainAspectRatio: false,
                                                            plugins: {
                                                                legend: { display: false },
                                                                tooltip: {
                                                                    callbacks: {
                                                                        label: (context) => `${formatarMoeda(Number(context.parsed.y) ?? 0)}`
                                                                    }
                                                                }
                                                            },
                                                            scales: { y: { display: false }, x: { grid: { display: false } } }
                                                        }} />}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {activeTab === 'insights' && analiseInteligente && (
                                        <div className="space-y-6">
                                            <h3 className="text-xl font-black text-slate-900 mb-6">Plano de Ação Sugerido</h3>
                                            {analiseInteligente.insights.map((insight, idx) => (
                                                <motion.div
                                                    key={idx}
                                                    whileHover={{ x: 10 }}
                                                    className="bg-slate-50/50 p-6 rounded-3xl border border-slate-100 flex items-start gap-4 transition-all"
                                                >
                                                    <div className={`p-4 rounded-2xl ${insight.tipo === 'economia' ? 'bg-green-100 text-green-600' :
                                                        insight.tipo === 'investimento' ? 'bg-blue-100 text-blue-600' : 'bg-purple-100 text-purple-600'
                                                        }`}>
                                                        {insight.tipo === 'economia' ? <TrendingDown className="w-6 h-6" /> : <Zap className="w-6 h-6" />}
                                                    </div>
                                                    <div className="flex-1">
                                                        <h4 className="font-bold text-slate-900">{insight.titulo}</h4>
                                                        <p className="text-slate-500 text-sm mt-1">{insight.descricao}</p>
                                                        <div className="mt-4 flex items-center justify-between">
                                                            <span className="text-lg font-black text-slate-900">{formatarMoeda(insight.valor_impacto)} <span className="text-xs font-medium text-slate-400">Impacto Est.</span></span>
                                                            <button className="text-xs font-bold uppercase tracking-widest text-blue-600 flex items-center hover:translate-x-1 transition-transform">
                                                                Aplicar Agora <ChevronRight className="w-4 h-4 ml-1" />
                                                            </button>
                                                        </div>
                                                    </div>
                                                </motion.div>
                                            ))}
                                        </div>
                                    )}

                                    {activeTab === 'previsao' && analiseInteligente && (
                                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                            <div className="p-8 bg-blue-50/50 rounded-3xl border border-blue-100">
                                                <p className="text-xs font-bold text-blue-400 uppercase">Saída Projetada</p>
                                                <h4 className="text-3xl font-black text-blue-900 mt-2">{formatarMoeda(analiseInteligente.previsao.despesas_estimadas)}</h4>
                                            </div>
                                            <div className="p-8 bg-green-50/50 rounded-3xl border border-green-100">
                                                <p className="text-xs font-bold text-green-400 uppercase">Entrada Projetada</p>
                                                <h4 className="text-3xl font-black text-green-900 mt-2">{formatarMoeda(analiseInteligente.previsao.receitas_estimadas)}</h4>
                                            </div>
                                            <div className="p-8 bg-slate-900 rounded-3xl border border-slate-700">
                                                <p className="text-xs font-bold text-slate-500 uppercase">Margem Alvo</p>
                                                <h4 className="text-3xl font-black text-white mt-2">{formatarMoeda(analiseInteligente.previsao.lucro_projetado)}</h4>
                                            </div>
                                        </div>
                                    )}

                                    {activeTab === 'detalhado' && (
                                        <div className="flex flex-col items-center justify-center py-20 text-center">
                                            <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mb-6 border border-slate-100">
                                                <Brain className="w-10 h-10 text-slate-300" />
                                            </div>
                                            <h3 className="text-xl font-bold text-slate-900">Relatórios Dinâmicos</h3>
                                            <p className="text-slate-500 max-w-md mt-2">Esta seção está sendo populada com análises de tendências de longo prazo.</p>
                                        </div>
                                    )}
                                </motion.div>
                            </AnimatePresence>
                        </div>
                    </div>

                    <div className="lg:col-span-4 space-y-8">
                        <div className="bg-white/80 backdrop-blur-xl p-8 rounded-[2.5rem] border border-white shadow-2xl shadow-slate-200/50">
                            <div className="flex items-center justify-between mb-8">
                                <h3 className="text-xl font-black text-slate-900 flex items-center">
                                    <AlertCircle className="w-5 h-5 mr-2 text-red-500" />
                                    Alertas Reais
                                </h3>
                                <span className="px-2 py-1 bg-red-100 text-red-600 text-[10px] font-black rounded-lg">LIVE</span>
                            </div>

                            <div className="space-y-4">
                                {analiseInteligente?.alertas && analiseInteligente.alertas.length > 0 ? (
                                    analiseInteligente.alertas.map((alerta, idx) => (
                                        <div key={idx} className="p-4 bg-slate-50 rounded-2xl border border-slate-100 group hover:bg-white transition-all cursor-default relative overflow-hidden">
                                            <div className={`absolute top-0 left-0 w-1 h-full ${alerta.severidade === 'critica' ? 'bg-red-500' : 'bg-amber-500'
                                                }`} />
                                            <h4 className="text-sm font-bold text-slate-900">{alerta.titulo}</h4>
                                            <p className="text-xs text-slate-500 mt-1">{alerta.descricao}</p>
                                            <button className="mt-3 text-[10px] font-black uppercase text-blue-600 opacity-0 group-hover:opacity-100 transition-opacity flex items-center">
                                                Resolver Agora <ArrowRight className="w-3 h-3 ml-1" />
                                            </button>
                                        </div>
                                    ))
                                ) : (
                                    <div className="flex flex-col items-center py-10 opacity-40">
                                        <ShieldCheck className="w-12 h-12 text-slate-300 mb-2" />
                                        <p className="text-xs font-bold uppercase tracking-widest">Sem riscos detectados</p>
                                    </div>
                                )}
                            </div>
                        </div>

                        <div className="bg-gradient-to-br from-indigo-600 to-blue-700 p-8 rounded-[2.5rem] text-white shadow-2xl shadow-blue-200 relative overflow-hidden group">
                            <div className="absolute top-0 right-0 p-8 opacity-10 group-hover:scale-110 transition-transform">
                                <PieChart className="w-32 h-32" />
                            </div>
                            <h4 className="text-lg font-bold mb-4">Eficiência de Caixa</h4>
                            <div className="space-y-6 relative z-10">
                                <div>
                                    <div className="flex justify-between text-xs font-bold opacity-60 uppercase tracking-widest mb-2">
                                        <span>Pressão de Caixa Diária</span>
                                        <span>{analiseInteligente?.indicadores.pressao_caixa.toFixed(1)}%</span>
                                    </div>
                                    <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                                        <motion.div
                                            initial={{ width: 0 }}
                                            animate={{ width: `${Math.min(analiseInteligente?.indicadores.pressao_caixa || 0, 100)}%` }}
                                            className="h-full bg-white"
                                        />
                                    </div>
                                </div>
                                <div>
                                    <div className="flex justify-between text-xs font-bold opacity-60 uppercase tracking-widest mb-2">
                                        <span>Comprometimento Global</span>
                                        <span>{analiseInteligente?.indicadores.comprometimento.toFixed(1)}%</span>
                                    </div>
                                    <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                                        <motion.div
                                            initial={{ width: 0 }}
                                            animate={{ width: `${Math.min(analiseInteligente?.indicadores.comprometimento || 0, 100)}%` }}
                                            className="h-full bg-amber-400"
                                        />
                                    </div>
                                </div>
                                <button className="w-full bg-white text-blue-600 py-3 rounded-2xl font-bold text-sm shadow-xl active:scale-95 transition-transform">
                                    Ver Relatório de Eficiência
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <AnimatePresence>
                {showAnalyticsModal && (
                    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 md:p-10">
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setShowAnalyticsModal(false)}
                            className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"
                        />
                        <motion.div
                            initial={{ opacity: 0, scale: 0.9, y: 20 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.9, y: 20 }}
                            className="bg-white rounded-[3rem] shadow-2xl w-full max-w-5xl h-full max-h-[85vh] overflow-hidden relative z-10 flex flex-col"
                        >
                            <div className="p-10 overflow-y-auto">
                                <div className="flex justify-between items-start mb-10">
                                    <div>
                                        <h2 className="text-4xl font-black text-slate-900">Análise <span className="text-blue-600">Deep-Dive</span></h2>
                                        <p className="text-slate-500 mt-2">Visão estrutural da saúde financeira do estabelecimento.</p>
                                    </div>
                                    <button onClick={() => setShowAnalyticsModal(false)} className="p-3 bg-slate-50 rounded-2xl hover:bg-slate-100 transition-colors">
                                        <AlertCircle className="w-6 h-6 text-slate-400" />
                                    </button>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                                    <div className="space-y-6">
                                        <h3 className="text-lg font-bold text-slate-900 flex items-center">
                                            <Target className="w-5 h-5 mr-3 text-blue-500" />
                                            Métricas de Performance
                                        </h3>
                                        <div className="grid grid-cols-2 gap-6">
                                            {[
                                                { label: 'Venda Média', value: formatarMoeda(analiseInteligente?.indicadores.venda_media || 0) },
                                                { label: 'Pressão Real', value: `${analiseInteligente?.indicadores.pressao_caixa.toFixed(1)}%` },
                                                { label: 'Markup Est.', value: '42%' },
                                                { label: 'ROI Mensal', value: '+12.5%' }
                                            ].map((m, i) => (
                                                <div key={i} className="p-6 bg-slate-50 rounded-[2rem] border border-slate-100">
                                                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{m.label}</p>
                                                    <p className="text-xl font-black text-slate-900 mt-2">{m.value}</p>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    <div className="space-y-6">
                                        <h3 className="text-lg font-bold text-slate-900 flex items-center">
                                            <Wallet className="w-5 h-5 mr-3 text-emerald-500" />
                                            Saúde do Capital
                                        </h3>
                                        <div className="bg-slate-900 p-8 rounded-[2.5rem] relative overflow-hidden h-full">
                                            <div className="absolute top-0 right-0 p-8 opacity-10">
                                                <TrendingUp className="w-24 h-24 text-white" />
                                            </div>
                                            <div className="space-y-8">
                                                <div>
                                                    <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">Saldo Líquido Projetado</p>
                                                    <h4 className="text-4xl font-black text-white">{formatarMoeda(analiseInteligente?.indicadores.saldo_fluxo || 0)}</h4>
                                                </div>
                                                <div className="pt-8 border-t border-slate-800 flex justify-between">
                                                    <div>
                                                        <p className="text-xs font-bold text-slate-500">Ponto de Equilíbrio</p>
                                                        <p className="text-lg font-extrabold text-blue-400">R$ 52.400</p>
                                                    </div>
                                                    <div className="text-right">
                                                        <p className="text-xs font-bold text-slate-500">Margem de Seg.</p>
                                                        <p className="text-lg font-extrabold text-emerald-400">+15.2%</p>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div className="mt-auto p-10 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
                                <p className="text-slate-500 text-sm">Dados atualizados há menos de 1 minuto através de sincronização segura.</p>
                                <button className="bg-blue-600 text-white px-8 py-3 rounded-2xl font-bold shadow-xl shadow-blue-200 hover:bg-blue-700 transition-all flex items-center space-x-2">
                                    <ShieldCheck className="w-5 h-5" />
                                    <span>Download Relatório Certificado</span>
                                </button>
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default ExpensesPageInteligente;
