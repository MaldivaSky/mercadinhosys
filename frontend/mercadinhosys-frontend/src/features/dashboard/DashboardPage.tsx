import React, { useState, useEffect, useMemo } from 'react';
import {
  TrendingUp, TrendingDown, ShoppingCart, Users, Package,
  CreditCard, DollarSign, BarChart as LucideBarChart, AlertTriangle,
  Clock, Star, Calendar, Zap, Target, Award, Activity, Percent,
  ArrowUpRight, ArrowDownRight, Filter, PieChart as PieChartIcon,
  LineChart as LineChartIcon, RefreshCw, ChevronDown, ChevronUp,
  Layers, Cpu, Brain, Database, Server, TrendingUp as TrendingUpIcon,
  Eye, EyeOff, MoreVertical, Settings, DollarSign as DollarIcon,
  Wallet, TrendingDown as TrendingDownIcon, Box, ChartBar,
  Target as TargetIcon, AlertCircle, TrendingUp as TrendingUpFill
} from 'lucide-react';
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, LineChart, Line, AreaChart, Area,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from 'recharts';

// API Client
import { apiClient } from '../../api/apiClient';

// TIPOS CIENTÍFICOS
type ProdutoPrevisao = {
  produto_nome?: string;
  nome?: string;
  estoque_atual: number;
  demanda_diaria_prevista: number;
  risco_ruptura?: boolean;
  margem_lucro?: number;
  custo_estoque?: number;
  giro_estoque?: number;
  classificação_abc?: string;
};

interface ProdutoEstrela {
  id: number;
  nome: string;
  classificacao: string;
  margem: number;
  market_share: number;
  total_vendido: number;
  custo_unitario: number;
  preco_venda: number;
  lucro_total: number;
  roi: number;
  elasticidade: number;
}

interface ProdutoLento {
  id: number;
  nome: string;
  quantidade: number;
  total_vendido: number;
  dias_estoque: number;
  giro_estoque: number;
  custo_parado: number;
  perda_mensal: number;
}

interface CurvaABC {
  classificacao: string;
  produtos: Array<{
    id: number;
    nome: string;
    faturamento: number;
    percentual_acumulado: number;
    classificacao: 'A' | 'B' | 'C';
    quantidade_vendida: number;
    margem: number;
  }>;
  resumo: {
    A: { quantidade: number; faturamento_total: number; percentual: number };
    B: { quantidade: number; faturamento_total: number; percentual: number };
    C: { quantidade: number; faturamento_total: number; percentual: number };
  };
  pareto_80_20: boolean;
}

interface AnaliseFinanceira {
  despesas_detalhadas: Array<{
    tipo: string;
    valor: number;
    percentual: number;
    impacto_lucro: number;
    tendencia: 'alta' | 'baixa' | 'estavel';
  }>;
  investimentos: {
    marketing: number;
    estoque: number;
    infraestrutura: number;
    total: number;
    roi_esperado: number;
  };
  margens: {
    bruta: number;
    operacional: number;
    liquida: number;
    contribuicao: number;
  };
  indicadores: {
    ponto_equilibrio: number;
    margem_seguranca: number;
    alavancagem_operacional: number;
    ebitda: number;
  };
}

interface InsightsCientificos {
  correlações: Array<{
    variavel1: string;
    variavel2: string;
    correlacao: number;
    significancia: number;
    insight: string;
  }>;
  anomalias: Array<{
    tipo: string;
    descricao: string;
    impacto: number;
    causa_provavel: string;
  }>;
  previsoes: Array<{
    variavel: string;
    valor_atual: number;
    previsao_30d: number;
    confianca: number;
    intervalo_confianca: [number, number];
  }>;
  recomendacoes_otimizacao: Array<{
    area: string;
    acao: string;
    impacto_esperado: number;
    complexidade: 'baixa' | 'media' | 'alta';
  }>;
}

interface DashboardData {
  success: boolean;
  usuario: {
    nome: string;
    role: string;
    acesso_avancado: boolean;
  };
  data: {
    hoje: {
      data: string;
      total_vendas: number;
      quantidade_vendas: number;
      ticket_medio: number;
      clientes_atendidos: number;
      crescimento_vs_ontem: number;
      meta_atingida: number;
      vendas_por_forma_pagamento: Record<string, number>;
      custo_vendas: number;
      lucro_liquido: number;
      margem_diaria: number;
    };
    mes: {
      total_vendas: number;
      total_despesas: number;
      lucro_bruto: number;
      margem_lucro: number;
      crescimento_mensal: number;
      despesas_por_tipo: Record<string, number>;
      custo_produtos_vendidos: number;
      investimentos: number;
      roi_mensal: number;
    };
    analise_produtos: {
      curva_abc: CurvaABC;
      produtos_estrela: ProdutoEstrela[];
      produtos_lentos: ProdutoLento[];
      previsao_demanda: ProdutoPrevisao[];
      produtos_margem: Array<{
        id: number;
        nome: string;
        margem_lucro: number;
        preco_venda: number;
        custo_unitario: number;
        quantidade_vendida: number;
        elasticidade_preco: number;
      }>;
    };
    analise_financeira: AnaliseFinanceira;
    analise_temporal: {
      vendas_por_hora: Array<{
        hora: number;
        quantidade: number;
        total: number;
        lucro: number;
        margem: number;
      }>;
      vendas_por_categoria: Array<{
        categoria: string;
        total: number;
        lucro: number;
        margem: number;
        share: number;
      }>;
      tendencia_vendas: Array<{
        data: string;
        total: number;
        previsao: number;
        intervalo_min: number;
        intervalo_max: number;
      }>;
    };
    insights_cientificos: InsightsCientificos;
    alertas_cientificos: Array<{
      tipo: 'anomalia' | 'tendencia' | 'oportunidade' | 'risco';
      titulo: string;
      descricao: string;
      gravidade: number;
      variaveis_envolvidas: string[];
      acao_recomendada: string;
    }>;
  };
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

const DashboardPage: React.FC = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedCards, setExpandedCards] = useState<Record<string, boolean>>({
    'curva-abc': true,
    'analise-financeira': true,
    'insights': true
  });
  const [selectedABC, setSelectedABC] = useState<'A' | 'B' | 'C' | 'all'>('all');
  const [viewMode, setViewMode] = useState<'visao-geral' | 'detalhado' | 'cientifico'>('cientifico');
  const [hoveredProduct, setHoveredProduct] = useState<number | null>(null);
  const [selectedMetric, setSelectedMetric] = useState<'margem' | 'faturamento' | 'giro'>('margem');

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/dashboard/cientifico');
      setData(response.data);
    } catch (err) {
      setError('Erro ao carregar dados científicos');
    } finally {
      setLoading(false);
    }
  };

  const toggleCard = (cardId: string) => {
    setExpandedCards(prev => ({
      ...prev,
      [cardId]: !prev[cardId]
    }));
  };

  const getABCColor = (classificacao: 'A' | 'B' | 'C') => {
    switch (classificacao) {
      case 'A': return '#10B981';
      case 'B': return '#F59E0B';
      case 'C': return '#EF4444';
      default: return '#6B7280';
    }
  };

  const calculateROIColor = (roi: number) => {
    if (roi >= 30) return '#10B981';
    if (roi >= 10) return '#F59E0B';
    return '#EF4444';
  };

  if (loading) return (
    <div className="flex items-center justify-center h-screen">
      <div className="text-center">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-4 text-lg font-semibold text-gray-700">Carregando Análise Científica...</p>
        <p className="text-gray-500">Processando dados estatísticos e modelos preditivos</p>
      </div>
    </div>
  );

  if (error || !data) return (
    <div className="p-8 bg-red-50 rounded-xl">
      <div className="flex items-center gap-3 text-red-700 mb-4">
        <AlertTriangle className="w-8 h-8" />
        <h2 className="text-2xl font-bold">Erro na Análise Científica</h2>
      </div>
      <p className="text-red-600 mb-4">{error || 'Dados não disponíveis'}</p>
      <button onClick={loadDashboard} className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2">
        <RefreshCw className="w-4 h-4" />
        Tentar Novamente
      </button>
    </div>
  );

  const { hoje, mes, analise_produtos, analise_financeira, analise_temporal, insights_cientificos } = data.data;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 p-4 md:p-6">
      {/* HEADER CIENTÍFICO */}
      <div className="mb-8">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Brain className="w-10 h-10 text-blue-600" />
              <h1 className="text-3xl md:text-4xl font-bold text-gray-900">Dashboard de Ciência de Dados</h1>
            </div>
            <p className="text-gray-600">
              Análises estatísticas, modelos preditivos e otimização baseada em dados
            </p>
            <div className="flex items-center gap-4 mt-3">
              <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                <Cpu className="w-4 h-4 inline mr-1" />
                Modelos Ativos: 12
              </span>
              <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                <Database className="w-4 h-4 inline mr-1" />
                {new Date().toLocaleDateString('pt-BR')}
              </span>
            </div>
          </div>
          <div className="flex gap-3">
            <select
              className="px-4 py-2 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              value={viewMode}
              onChange={(e) => setViewMode(e.target.value as any)}
            >
              <option value="visao-geral">Visão Geral</option>
              <option value="detalhado">Análise Detalhada</option>
              <option value="cientifico">Modo Científico</option>
            </select>
            <button onClick={loadDashboard} className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2">
              <RefreshCw className="w-4 h-4" />
              Atualizar Modelos
            </button>
          </div>
        </div>
      </div>

      {/* KPIs PRINCIPAIS COM ANIMAÇÃO */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {[
          {
            title: 'Margem Líquida',
            value: `${mes.margem_lucro.toFixed(1)}%`,
            change: hoje.crescimento_vs_ontem,
            icon: TrendingUpFill,
            color: 'bg-gradient-to-r from-green-500 to-emerald-600',
            details: `Lucro: R$ ${mes.lucro_bruto.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
          },
          {
            title: 'ROI Mensal',
            value: `${mes.roi_mensal.toFixed(1)}%`,
            change: 5.2,
            icon: TrendingUp,
            color: 'bg-gradient-to-r from-blue-500 to-cyan-600',
            details: `Investido: R$ ${mes.investimentos.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
          },
          {
            title: 'Ticket Médio',
            value: `R$ ${hoje.ticket_medio.toFixed(2)}`,
            change: 8.7,
            icon: DollarIcon,
            color: 'bg-gradient-to-r from-purple-500 to-pink-600',
            details: `${hoje.clientes_atendidos} clientes atendidos`
          },
          {
            title: 'Ponto de Equilíbrio',
            value: `${analise_financeira.indicadores.ponto_equilibrio.toFixed(1)}%`,
            change: -2.3,
            icon: TargetIcon,
            color: 'bg-gradient-to-r from-orange-500 to-red-600',
            details: `Margem de Segurança: ${analise_financeira.indicadores.margem_seguranca.toFixed(1)}%`
          }
        ].map((kpi, idx) => (
          <div
            key={idx}
            className="bg-white rounded-2xl shadow-xl p-6 transform transition-all duration-300 hover:scale-105 hover:shadow-2xl cursor-pointer border border-gray-200"
            onMouseEnter={() => { }}
            onMouseLeave={() => { }}
          >
            <div className="flex justify-between items-start mb-4">
              <div className={`${kpi.color} p-3 rounded-xl shadow-lg`}>
                <kpi.icon className="w-6 h-6 text-white" />
              </div>
              <div className={`flex items-center px-3 py-1 rounded-full text-sm font-semibold ${kpi.change >= 0 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                {kpi.change >= 0 ? <ArrowUpRight className="w-4 h-4 mr-1" /> : <ArrowDownRight className="w-4 h-4 mr-1" />}
                {Math.abs(kpi.change).toFixed(1)}%
              </div>
            </div>
            <h3 className="text-gray-500 text-sm font-medium mb-2">{kpi.title}</h3>
            <p className="text-3xl font-bold text-gray-900 mb-2">{kpi.value}</p>
            <p className="text-gray-600 text-sm">{kpi.details}</p>
            <div className="mt-4 pt-4 border-t border-gray-100">
              <div className="flex justify-between text-xs text-gray-500">
                <span>Performance</span>
                <span className={`font-semibold ${kpi.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {kpi.change >= 0 ? 'Acima da meta' : 'Abaixo da meta'}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* SEÇÃO PRINCIPAL: CURVA ABC COM GRÁFICO DE PARETO */}
      <div className="bg-white rounded-2xl shadow-xl mb-8 overflow-hidden border border-gray-200">
        <div
          className="p-6 border-b border-gray-200 flex justify-between items-center cursor-pointer hover:bg-gray-50"
          onClick={() => toggleCard('curva-abc')}
        >
          <div className="flex items-center gap-3">
            <ChartBar className="w-8 h-8 text-blue-600" />
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Curva ABC de Pareto</h2>
              <p className="text-gray-600">Análise 80/20 dos produtos • {analise_produtos.curva_abc.pareto_80_20 ? '✅ Lei de Pareto Confirmada' : '⚠️ Distribuição Atípica'}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex space-x-1">
              <button
                className={`px-4 py-2 rounded-lg ${selectedABC === 'all' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'}`}
                onClick={(e) => { e.stopPropagation(); setSelectedABC('all'); }}
              >
                Todos
              </button>
              <button
                className={`px-4 py-2 rounded-lg ${selectedABC === 'A' ? 'bg-green-600 text-white' : 'bg-gray-100 text-gray-700'}`}
                onClick={(e) => { e.stopPropagation(); setSelectedABC('A'); }}
              >
                Classe A
              </button>
              <button
                className={`px-4 py-2 rounded-lg ${selectedABC === 'B' ? 'bg-yellow-600 text-white' : 'bg-gray-100 text-gray-700'}`}
                onClick={(e) => { e.stopPropagation(); setSelectedABC('B'); }}
              >
                Classe B
              </button>
              <button
                className={`px-4 py-2 rounded-lg ${selectedABC === 'C' ? 'bg-red-600 text-white' : 'bg-gray-100 text-gray-700'}`}
                onClick={(e) => { e.stopPropagation(); setSelectedABC('C'); }}
              >
                Classe C
              </button>
            </div>
            <ChevronDown className={`w-6 h-6 text-gray-500 transform transition-transform ${expandedCards['curva-abc'] ? 'rotate-180' : ''}`} />
          </div>
        </div>

        {expandedCards['curva-abc'] && (
          <div className="p-6 animate-fadeIn">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* GRÁFICO DE PARETO */}
              <div className="lg:col-span-2">
                <div className="h-[400px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={analise_produtos.curva_abc.produtos.slice(0, 15)}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="nome" angle={-45} textAnchor="end" height={80} />
                      <YAxis yAxisId="left" />
                      <YAxis yAxisId="right" orientation="right" />
                      <Tooltip
                        content={({ payload, label }) => (
                          <div className="bg-white p-4 shadow-xl rounded-lg border border-gray-200">
                            <p className="font-bold text-gray-900">{label}</p>
                            <p className="text-sm text-gray-600">Faturamento: R$ {payload?.[0]?.value?.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
                            <p className="text-sm text-gray-600">Classificação: <span className={`font-bold ${getABCColor(payload?.[1]?.payload?.classificacao)}`}>{payload?.[1]?.payload?.classificacao}</span></p>
                            <p className="text-sm text-gray-600">Margem: {payload?.[1]?.payload?.margem.toFixed(1)}%</p>
                          </div>
                        )}
                      />
                      <Bar
                        yAxisId="left"
                        dataKey="faturamento"
                        fill="#8884d8"
                        name="Faturamento"
                        onMouseEnter={(data, index) => setHoveredProduct(data.id)}
                        onMouseLeave={() => setHoveredProduct(null)}
                      />
                      <Line
                        yAxisId="right"
                        type="monotone"
                        dataKey="percentual_acumulado"
                        stroke="#ff7300"
                        strokeWidth={3}
                        dot={false}
                        name="% Acumulado"
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <div className="flex justify-center gap-6 mt-6">
                  {Object.entries(analise_produtos.curva_abc.resumo).map(([classe, dados]) => (
                    <div key={classe} className="text-center">
                      <div className={`w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-2 ${classe === 'A' ? 'bg-green-100' : classe === 'B' ? 'bg-yellow-100' : 'bg-red-100'}`}>
                        <span className={`text-2xl font-bold ${classe === 'A' ? 'text-green-600' : classe === 'B' ? 'text-yellow-600' : 'text-red-600'}`}>
                          {classe}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600">{dados.quantidade} produtos</p>
                      <p className="text-lg font-bold text-gray-900">{dados.percentual.toFixed(1)}% do faturamento</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* LEGENDA E DETALHES */}
              <div className="space-y-6">
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-6 rounded-xl border border-blue-200">
                  <h3 className="font-bold text-gray-900 mb-4">📊 Interpretação da Curva ABC</h3>
                  <div className="space-y-3">
                    <div className="flex items-center gap-3">
                      <div className="w-3 h-3 rounded-full bg-green-500"></div>
                      <div>
                        <p className="font-semibold text-gray-900">Classe A (20% dos produtos)</p>
                        <p className="text-sm text-gray-600">Responsáveis por {analise_produtos.curva_abc.resumo.A.percentual.toFixed(1)}% do faturamento</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                      <div>
                        <p className="font-semibold text-gray-900">Classe B (30% dos produtos)</p>
                        <p className="text-sm text-gray-600">Responsáveis por {analise_produtos.curva_abc.resumo.B.percentual.toFixed(1)}% do faturamento</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-3 h-3 rounded-full bg-red-500"></div>
                      <div>
                        <p className="font-semibold text-gray-900">Classe C (50% dos produtos)</p>
                        <p className="text-sm text-gray-600">Responsáveis por {analise_produtos.curva_abc.resumo.C.percentual.toFixed(1)}% do faturamento</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* TOP 5 PRODUTOS DA CLASSE A */}
                <div className="border border-gray-200 rounded-xl p-4">
                  <h4 className="font-bold text-gray-900 mb-3">🏆 Top Produtos Classe A</h4>
                  <div className="space-y-3">
                    {analise_produtos.curva_abc.produtos
                      .filter(p => p.classificacao === 'A')
                      .slice(0, 5)
                      .map((produto, idx) => (
                        <div
                          key={produto.id}
                          className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg cursor-pointer transition-colors"
                          onMouseEnter={() => setHoveredProduct(produto.id)}
                          onMouseLeave={() => setHoveredProduct(null)}
                        >
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 bg-green-100 text-green-800 rounded-full flex items-center justify-center font-bold">
                              {idx + 1}
                            </div>
                            <div>
                              <p className="font-medium text-gray-900">{produto.nome}</p>
                              <p className="text-xs text-gray-500">Margem: {produto.margem.toFixed(1)}%</p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="font-bold text-green-600">R$ {produto.faturamento.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
                            <p className="text-xs text-gray-500">{produto.quantidade_vendida} unidades</p>
                          </div>
                        </div>
                      ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* SEÇÃO: ANÁLISE FINANCEIRA DETALHADA */}
      <div className="bg-white rounded-2xl shadow-xl mb-8 overflow-hidden border border-gray-200">
        <div
          className="p-6 border-b border-gray-200 flex justify-between items-center cursor-pointer hover:bg-gray-50"
          onClick={() => toggleCard('analise-financeira')}
        >
          <div className="flex items-center gap-3">
            <DollarIcon className="w-8 h-8 text-green-600" />
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Análise Financeira Científica</h2>
              <p className="text-gray-600">Despesas vs Lucro • Margens • Indicadores de Performance</p>
            </div>
          </div>
          <ChevronDown className={`w-6 h-6 text-gray-500 transform transition-transform ${expandedCards['analise-financeira'] ? 'rotate-180' : ''}`} />
        </div>

        {expandedCards['analise-financeira'] && (
          <div className="p-6 animate-fadeIn">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* GRÁFICO DE PIZZA: DISTRIBUIÇÃO DE DESPESAS */}
              <div className="bg-gradient-to-br from-gray-50 to-white p-6 rounded-xl border border-gray-200">
                <h3 className="font-bold text-gray-900 mb-6 text-lg">🥧 Distribuição de Despesas</h3>
                <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={analise_financeira.despesas_detalhadas}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                        outerRadius={100}
                        fill="#8884d8"
                        dataKey="valor"
                      >
                        {analise_financeira.despesas_detalhadas.map((entry, index) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={COLORS[index % COLORS.length]}
                            className="cursor-pointer hover:opacity-80 transition-opacity"
                          />
                        ))}
                      </Pie>
                      <Tooltip
                        content={({ payload }) => (
                          <div className="bg-white p-4 shadow-xl rounded-lg border border-gray-200">
                            <p className="font-bold text-gray-900">{payload?.[0]?.payload?.tipo}</p>
                            <p className="text-gray-600">Valor: R$ {payload?.[0]?.value?.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
                            <p className="text-gray-600">Percentual: {payload?.[0]?.payload?.percentual.toFixed(1)}%</p>
                            <p className="text-gray-600">Impacto no Lucro: {payload?.[0]?.payload?.impacto_lucro.toFixed(1)}%</p>
                          </div>
                        )}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="grid grid-cols-2 gap-4 mt-6">
                  <div className="bg-green-50 p-4 rounded-lg">
                    <p className="text-sm text-green-800 font-medium">Lucro Bruto</p>
                    <p className="text-2xl font-bold text-green-700">R$ {mes.lucro_bruto.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
                    <p className="text-sm text-green-600">Margem: {mes.margem_lucro.toFixed(1)}%</p>
                  </div>
                  <div className="bg-red-50 p-4 rounded-lg">
                    <p className="text-sm text-red-800 font-medium">Despesas Totais</p>
                    <p className="text-2xl font-bold text-red-700">R$ {mes.total_despesas.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
                    <p className="text-sm text-red-600">{((mes.total_despesas / mes.total_vendas) * 100).toFixed(1)}% das vendas</p>
                  </div>
                </div>
              </div>

              {/* MÉTRICAS DE MARGEM */}
              <div className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  {Object.entries(analise_financeira.margens).map(([nome, valor]) => (
                    <div key={nome} className="bg-white border border-gray-200 rounded-xl p-4 hover:shadow-md transition-shadow">
                      <p className="text-sm text-gray-600 font-medium mb-2">
                        {nome === 'bruta' ? 'Margem Bruta' :
                          nome === 'operacional' ? 'Margem Operacional' :
                            nome === 'liquida' ? 'Margem Líquida' : 'Margem Contribuição'}
                      </p>
                      <p className={`text-3xl font-bold ${valor >= 20 ? 'text-green-600' : valor >= 10 ? 'text-yellow-600' : 'text-red-600'}`}>
                        {valor.toFixed(1)}%
                      </p>
                      <div className="mt-2">
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${valor >= 20 ? 'bg-green-500' : valor >= 10 ? 'bg-yellow-500' : 'bg-red-500'}`}
                            style={{ width: `${Math.min(valor, 100)}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* INDICADORES AVANÇADOS */}
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-6 rounded-xl border border-blue-200">
                  <h4 className="font-bold text-gray-900 mb-4">📈 Indicadores Financeiros</h4>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-700">Ponto de Equilíbrio</span>
                      <span className="font-bold text-blue-600">{analise_financeira.indicadores.ponto_equilibrio.toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-700">Margem de Segurança</span>
                      <span className="font-bold text-green-600">{analise_financeira.indicadores.margem_seguranca.toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-700">Alavancagem Operacional</span>
                      <span className="font-bold text-purple-600">{analise_financeira.indicadores.alavancagem_operacional.toFixed(2)}x</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-700">EBITDA</span>
                      <span className="font-bold text-green-700">R$ {analise_financeira.indicadores.ebitda.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* SEÇÃO: INSIGHTS CIENTÍFICOS */}
      <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl shadow-2xl overflow-hidden mb-8">
        <div
          className="p-6 border-b border-gray-700 flex justify-between items-center cursor-pointer hover:bg-gray-800/50"
          onClick={() => toggleCard('insights')}
        >
          <div className="flex items-center gap-3">
            <Brain className="w-8 h-8 text-cyan-400" />
            <div>
              <h2 className="text-2xl font-bold text-white">🧠 Insights Científicos</h2>
              <p className="text-gray-300">Correlações • Anomalias • Previsões • Recomendações de Otimização</p>
            </div>
          </div>
          <ChevronDown className={`w-6 h-6 text-gray-400 transform transition-transform ${expandedCards['insights'] ? 'rotate-180' : ''}`} />
        </div>

        {expandedCards['insights'] && (
          <div className="p-6 animate-fadeIn">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* CORRELAÇÕES */}
              <div className="bg-gray-800/50 rounded-xl p-6 backdrop-blur-sm">
                <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                  <GitMerge className="w-5 h-5" />
                  Correlações Estatísticas
                </h3>
                <div className="space-y-4">
                  {insights_cientificos.correlações.map((corr, idx) => (
                    <div key={idx} className="bg-gray-900/50 p-4 rounded-lg hover:bg-gray-900 transition-colors">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-gray-300 font-medium">{corr.variavel1} × {corr.variavel2}</span>
                        <span className={`px-3 py-1 rounded-full text-sm font-bold ${Math.abs(corr.correlacao) > 0.7 ? 'bg-red-500/20 text-red-300' :
                            Math.abs(corr.correlacao) > 0.4 ? 'bg-yellow-500/20 text-yellow-300' :
                              'bg-green-500/20 text-green-300'
                          }`}>
                          r = {corr.correlacao.toFixed(2)}
                        </span>
                      </div>
                      <p className="text-gray-400 text-sm mb-2">{corr.insight}</p>
                      <div className="flex justify-between text-xs text-gray-500">
                        <span>Significância: p = {corr.significancia.toFixed(3)}</span>
                        <span>{Math.abs(corr.correlacao) > 0.7 ? '🔴 Forte' : Math.abs(corr.correlacao) > 0.4 ? '🟡 Moderada' : '🟢 Fraca'}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* PREVISÕES E RECOMENDAÇÕES */}
              <div className="space-y-6">
                <div className="bg-gradient-to-r from-blue-900/30 to-cyan-900/30 rounded-xl p-6">
                  <h3 className="text-xl font-bold text-white mb-6">🔮 Previsões (Próximos 30 dias)</h3>
                  <div className="space-y-4">
                    {insights_cientificos.previsoes.map((prev, idx) => (
                      <div key={idx} className="bg-black/30 p-4 rounded-lg">
                        <div className="flex justify-between items-center mb-3">
                          <span className="text-gray-300 font-medium">{prev.variavel}</span>
                          <span className="px-3 py-1 bg-blue-500/20 text-blue-300 rounded-full text-sm">
                            {prev.confianca.toFixed(1)}% confiança
                          </span>
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="text-center">
                            <p className="text-sm text-gray-400">Atual</p>
                            <p className="text-xl font-bold text-white">R$ {prev.valor_atual.toLocaleString('pt-BR')}</p>
                          </div>
                          <ArrowUpRight className="w-6 h-6 text-green-400" />
                          <div className="text-center">
                            <p className="text-sm text-gray-400">Previsão</p>
                            <p className="text-xl font-bold text-green-400">R$ {prev.previsao_30d.toLocaleString('pt-BR')}</p>
                          </div>
                        </div>
                        <div className="mt-3 text-xs text-gray-400">
                          Intervalo: R$ {prev.intervalo_confianca[0].toLocaleString('pt-BR')} - R$ {prev.intervalo_confianca[1].toLocaleString('pt-BR')}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* RECOMENDAÇÕES DE OTIMIZAÇÃO */}
                <div className="bg-gradient-to-r from-purple-900/30 to-pink-900/30 rounded-xl p-6">
                  <h3 className="text-xl font-bold text-white mb-6">🚀 Recomendações de Otimização</h3>
                  <div className="space-y-4">
                    {insights_cientificos.recomendacoes_otimizacao.map((rec, idx) => (
                      <div key={idx} className="bg-black/30 p-4 rounded-lg hover:bg-black/40 transition-colors cursor-pointer">
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-gray-300 font-medium">{rec.area}</span>
                          <span className={`px-3 py-1 rounded-full text-xs font-bold ${rec.complexidade === 'baixa' ? 'bg-green-500/30 text-green-300' :
                              rec.complexidade === 'media' ? 'bg-yellow-500/30 text-yellow-300' :
                                'bg-red-500/30 text-red-300'
                            }`}>
                            {rec.complexidade === 'baixa' ? '🟢 Fácil' : rec.complexidade === 'media' ? '🟡 Médio' : '🔴 Complexo'}
                          </span>
                        </div>
                        <p className="text-gray-300 mb-3">{rec.acao}</p>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-400">Impacto Esperado:</span>
                          <span className="text-green-400 font-bold">+{rec.impacto_esperado.toFixed(1)}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* SEÇÃO: PRODUTOS ESTRATÉGICOS */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* PRODUTOS ESTRELA */}
        <div className="bg-gradient-to-br from-yellow-50 to-orange-50 rounded-2xl shadow-xl p-6 border border-yellow-200">
          <div className="flex items-center gap-3 mb-6">
            <Star className="w-8 h-8 text-yellow-600" />
            <div>
              <h2 className="text-2xl font-bold text-gray-900">⭐ Produtos Estrela</h2>
              <p className="text-gray-600">Alta margem + Alta participação + Alta rentabilidade</p>
            </div>
          </div>
          <div className="space-y-4">
            {analise_produtos.produtos_estrela.map((produto, idx) => (
              <div
                key={produto.id}
                className="bg-white/80 backdrop-blur-sm rounded-xl p-4 hover:shadow-lg transition-all duration-300 hover:scale-[1.02] cursor-pointer border border-yellow-100"
              >
                <div className="flex justify-between items-center mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gradient-to-r from-yellow-500 to-orange-500 rounded-lg flex items-center justify-center">
                      <Star className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <p className="font-bold text-gray-900">{produto.nome}</p>
                      <p className="text-sm text-gray-600">ROI: <span className={`font-bold ${calculateROIColor(produto.roi)}`}>{produto.roi.toFixed(1)}%</span></p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-yellow-600">{produto.margem.toFixed(1)}%</p>
                    <p className="text-sm text-gray-600">Margem</p>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <p className="text-sm text-gray-600">Market Share</p>
                    <p className="text-lg font-bold text-gray-900">{produto.market_share.toFixed(1)}%</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Elasticidade</p>
                    <p className={`text-lg font-bold ${produto.elasticidade > 1 ? 'text-green-600' : 'text-red-600'}`}>
                      {produto.elasticidade.toFixed(2)}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Lucro Total</p>
                    <p className="text-lg font-bold text-green-600">R$ {produto.lucro_total.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* PRODUTOS LENTOS */}
        <div className="bg-gradient-to-br from-red-50 to-pink-50 rounded-2xl shadow-xl p-6 border border-red-200">
          <div className="flex items-center gap-3 mb-6">
            <AlertTriangle className="w-8 h-8 text-red-600" />
            <div>
              <h2 className="text-2xl font-bold text-gray-900">⚠️ Produtos Lentos</h2>
              <p className="text-gray-600">Baixo giro + Alto custo de estoque + Oportunidade de melhoria</p>
            </div>
          </div>
          <div className="space-y-4">
            {analise_produtos.produtos_lentos.map((produto, idx) => (
              <div
                key={produto.id}
                className="bg-white/80 backdrop-blur-sm rounded-xl p-4 hover:shadow-lg transition-all duration-300 hover:scale-[1.02] cursor-pointer border border-red-100"
              >
                <div className="flex justify-between items-center mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gradient-to-r from-red-500 to-pink-500 rounded-lg flex items-center justify-center">
                      <Package className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <p className="font-bold text-gray-900">{produto.nome}</p>
                      <p className="text-sm text-gray-600">{produto.quantidade} unidades paradas</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xl font-bold text-red-600">{produto.dias_estoque} dias</p>
                    <p className="text-sm text-gray-600">em estoque</p>
                  </div>
                </div>
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-600">Giro do Estoque</span>
                      <span className="font-bold text-red-600">{produto.giro_estoque.toFixed(1)}x/ano</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="h-2 rounded-full bg-gradient-to-r from-red-500 to-pink-500"
                        style={{ width: `${Math.min(produto.giro_estoque * 10, 100)}%` }}
                      ></div>
                    </div>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Custo Parado</span>
                    <span className="font-bold text-red-700">R$ {produto.custo_parado.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Perda Mensal Estimada</span>
                    <span className="font-bold text-red-800">R$ {produto.perda_mensal.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* SEÇÃO: PREVISÃO DE DEMANDA */}
      <div className="bg-gradient-to-br from-purple-50 to-indigo-50 rounded-2xl shadow-xl p-6 mb-8 border border-purple-200">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-3">
          <Target className="w-8 h-8 text-purple-600" />
          📊 Previsão de Demanda Inteligente
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b-2 border-purple-200">
                <th className="text-left py-3 px-4 text-sm font-bold text-gray-700">Produto</th>
                <th className="text-center py-3 px-4 text-sm font-bold text-gray-700">Estoque Atual</th>
                <th className="text-center py-3 px-4 text-sm font-bold text-gray-700">Demanda/Dia</th>
                <th className="text-center py-3 px-4 text-sm font-bold text-gray-700">Dias Restantes</th>
                <th className="text-center py-3 px-4 text-sm font-bold text-gray-700">Classificação ABC</th>
                <th className="text-center py-3 px-4 text-sm font-bold text-gray-700">Giro Estoque</th>
                <th className="text-center py-3 px-4 text-sm font-bold text-gray-700">Ação Recomendada</th>
              </tr>
            </thead>
            <tbody>
              {analise_produtos.previsao_demanda.map((produto, idx) => {
                const diasRestantes = produto.demanda_diaria_prevista > 0
                  ? produto.estoque_atual / produto.demanda_diaria_prevista
                  : 999;
                const isCritico = diasRestantes < 3;
                const isAtencao = diasRestantes < 7;

                return (
                  <tr key={idx} className={`border-b border-purple-100 hover:bg-white/50 ${isCritico ? 'bg-red-50' : isAtencao ? 'bg-yellow-50' : ''}`}>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-3">
                        <div className={`w-3 h-3 rounded-full ${getABCColor(produto.classificação_abc as any)}`}></div>
                        <span className="font-medium text-gray-900">{produto.nome || produto.produto_nome}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-center font-semibold text-gray-800">{produto.estoque_atual}</td>
                    <td className="py-3 px-4 text-center">
                      <div className="inline-flex items-center gap-2">
                        <span className="font-bold text-blue-600">{produto.demanda_diaria_prevista.toFixed(1)}</span>
                        <TrendingUp className="w-4 h-4 text-green-500" />
                      </div>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span className={`font-bold ${isCritico ? 'text-red-600' : isAtencao ? 'text-yellow-600' : 'text-green-600'}`}>
                        {diasRestantes < 999 ? Math.floor(diasRestantes) : '∞'} dias
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span className={`px-3 py-1 rounded-full text-xs font-bold ${getABCColor(produto.classificação_abc as any)}`} style={{
                        backgroundColor: `${getABCColor(produto.classificação_abc as any)}20`,
                        color: getABCColor(produto.classificação_abc as any)
                      }}>
                        Classe {produto.classificação_abc}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <div className="flex items-center justify-center gap-2">
                        <div className="w-20 bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${(produto.giro_estoque || 0) > 10 ? 'bg-green-500' : (produto.giro_estoque || 0) > 5 ? 'bg-yellow-500' : 'bg-red-500'}`}
                            style={{ width: `${Math.min((produto.giro_estoque || 0) * 10, 100)}%` }}
                          ></div>
                        </div>
                        <span className="text-sm font-medium text-gray-700">{(produto.giro_estoque || 0).toFixed(1)}x</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-center">
                      {isCritico ? (
                        <span className="px-3 py-2 bg-red-100 text-red-700 rounded-lg text-sm font-bold animate-pulse">
                          🚨 URGENTE - COMPRAR AGORA
                        </span>
                      ) : isAtencao ? (
                        <span className="px-3 py-2 bg-yellow-100 text-yellow-700 rounded-lg text-sm font-bold">
                          ⚠️ Programar Compra
                        </span>
                      ) : (
                        <span className="px-3 py-2 bg-green-100 text-green-700 rounded-lg text-sm font-bold">
                          ✓ Estoque OK
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;