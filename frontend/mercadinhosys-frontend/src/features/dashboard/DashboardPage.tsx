// @ts-nocheck
import React, { useState, useEffect, useMemo } from 'react';
import {
  TrendingUp, Package, AlertTriangle, Star, Calendar, Target,
  ArrowUpRight, ArrowDownRight, ChevronDown, Cpu, Brain, Database,
  DollarSign as DollarIcon, Target as TargetIcon, AlertCircle,
  TrendingUp as TrendingUpFill, GitMerge, ChartBar, BarChart as LucideBarChart,
  LineChart as LineChartIcon, RefreshCw
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, LineChart, Line, Cell, LabelList,
  PieChart, Pie, Legend
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
    A: { quantidade: number; faturamento_total: number; percentual: number; margem_media?: number };
    B: { quantidade: number; faturamento_total: number; percentual: number; margem_media?: number };
    C: { quantidade: number; faturamento_total: number; percentual: number; margem_media?: number };
    TODOS?: { quantidade: number; faturamento_total: number; percentual: number; margem_media?: number };
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

const getDistinctColor = (index: number) => {
  const hue = (index * 137.508) % 360;
  return `hsl(${hue}, 70%, 50%)`;
};

const DashboardPage: React.FC = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedCards, setExpandedCards] = useState<Record<string, boolean>>({
    'curva-abc': true,
    'analise-financeira': true,
    'analise-temporal': true,
    'insights': true
  });
  const [selectedABC, setSelectedABC] = useState<'A' | 'B' | 'C' | 'all'>('all');
  const [viewMode, setViewMode] = useState<'visao-geral' | 'detalhado' | 'cientifico'>('cientifico');
  const [hoveredKPI, setHoveredKPI] = useState<number | null>(null);
  const [expandedKPI, setExpandedKPI] = useState<number | null>(null);

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

  // FILTRAR PRODUTOS DA CURVA ABC BASEADO NA SELEÇÃO
  const produtosFiltrados = useMemo(() => {
    if (!data?.data?.analise_produtos?.curva_abc?.produtos) return [];
    
    if (selectedABC === 'all') {
      return data.data.analise_produtos.curva_abc.produtos;
    }
    
    return data.data.analise_produtos.curva_abc.produtos.filter(
      (p: any) => p.classificacao === selectedABC
    );
  }, [data?.data?.analise_produtos?.curva_abc?.produtos, selectedABC]);

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

  const { hoje, mes, analise_produtos, analise_financeira, insights_cientificos = {
    correlações: [],
    anomalias: [],
    previsoes: [],
    recomendacoes_otimizacao: []
  }, analise_temporal = {
    tendencia_vendas: [],
    sazonalidade: [],
    comparacao_meses: [],
    previsao_proxima_semana: []
  } } = data.data;

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
              className="px-4 py-2 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 font-medium"
              value={viewMode}
              onChange={(e) => setViewMode(e.target.value as any)}
            >
              <option value="visao-geral">📊 Visão Geral</option>
              <option value="detalhado">📈 Análise Detalhada</option>
              <option value="cientifico">🧬 Modo Científico</option>
            </select>
            <button onClick={loadDashboard} className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2">
              <RefreshCw className="w-4 h-4" />
              Atualizar Modelos
            </button>
          </div>
        </div>
      </div>

      {/* DESCRIÇÃO DO MODO SELECIONADO */}
      {viewMode === 'visao-geral' && (
        <div className="mb-6 p-4 bg-blue-50 border-l-4 border-blue-500 rounded-r-lg">
          <p className="text-blue-900 font-medium">
            📊 <strong>Visão Geral:</strong> Visualização simplificada com apenas os KPIs principais para acompanhamento rápido.
          </p>
        </div>
      )}
      {viewMode === 'detalhado' && (
        <div className="mb-6 p-4 bg-purple-50 border-l-4 border-purple-500 rounded-r-lg">
          <p className="text-purple-900 font-medium">
            📈 <strong>Análise Detalhada:</strong> KPIs + Curva ABC + Análise Temporal + Análise Financeira para decisões estratégicas.
          </p>
        </div>
      )}
      {viewMode === 'cientifico' && (
        <div className="mb-6 p-4 bg-green-50 border-l-4 border-green-500 rounded-r-lg">
          <p className="text-green-900 font-medium">
            🧬 <strong>Modo Científico:</strong> Visualização completa com insights científicos, correlações, previsões e recomendações de otimização.
          </p>
        </div>
      )}

      {/* KPIs PRINCIPAIS COM TOOLTIPS E EXPLICAÇÕES */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {[
          {
            title: 'Margem Líquida',
            tooltip: 'Percentual de lucro sobre as vendas. Quanto maior, melhor a rentabilidade.',
            value: `${(mes?.margem_lucro || 0).toFixed(1)}%`,
            change: hoje.crescimento_vs_ontem,
            icon: TrendingUpFill,
            color: 'bg-gradient-to-r from-green-500 to-emerald-600',
            details: `Lucro: R$ ${(mes?.lucro_bruto || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
            explanation: `De cada R$ 100 em vendas, R$ ${(mes?.margem_lucro || 0).toFixed(0)} é lucro`,
            expandedContent: (
              <div className="space-y-3">
                <div className="bg-green-50 p-3 rounded-lg">
                  <p className="text-sm font-semibold text-green-900 mb-1">💡 O que isso significa?</p>
                  <p className="text-sm text-green-800">
                    A margem líquida mostra quanto sobra de lucro depois de pagar todos os custos. 
                    Uma margem de {(mes?.margem_lucro || 0).toFixed(1)}% significa que você está lucrando 
                    R$ {(mes?.margem_lucro || 0).toFixed(0)} para cada R$ 100 vendidos.
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="bg-gray-50 p-2 rounded">
                    <p className="text-gray-600">Total Vendas</p>
                    <p className="font-bold text-gray-900">R$ {(mes?.total_vendas || 0).toLocaleString('pt-BR', { maximumFractionDigits: 0 })}</p>
                  </div>
                  <div className="bg-gray-50 p-2 rounded">
                    <p className="text-gray-600">Lucro Líquido</p>
                    <p className="font-bold text-green-600">R$ {(mes?.lucro_bruto || 0).toLocaleString('pt-BR', { maximumFractionDigits: 0 })}</p>
                  </div>
                </div>
                <div className="text-xs text-gray-500 italic">
                  ✅ Margem saudável: acima de 20% | ⚠️ Atenção: abaixo de 10%
                </div>
              </div>
            )
          },
          {
            title: 'ROI Mensal',
            tooltip: 'Retorno sobre Investimento. Mostra quanto você ganhou em relação ao que investiu em estoque.',
            value: `${(mes?.roi_mensal || 0).toFixed(1)}%`,
            change: 5.2,
            icon: TrendingUp,
            color: 'bg-gradient-to-r from-blue-500 to-cyan-600',
            details: `Investido: R$ ${(mes?.investimentos || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
            explanation: `Para cada R$ 100 investidos, você ganhou R$ ${(mes?.roi_mensal || 0).toFixed(0)}`,
            expandedContent: (
              <div className="space-y-3">
                <div className="bg-blue-50 p-3 rounded-lg">
                  <p className="text-sm font-semibold text-blue-900 mb-1">💡 O que isso significa?</p>
                  <p className="text-sm text-blue-800">
                    O ROI mostra o retorno do seu investimento em estoque. Um ROI de {(mes?.roi_mensal || 0).toFixed(1)}% 
                    significa que para cada R$ 100 investidos em produtos, você ganhou R$ {(mes?.roi_mensal || 0).toFixed(0)} de lucro.
                  </p>
                </div>
                <div className="bg-gradient-to-r from-blue-50 to-cyan-50 p-3 rounded-lg">
                  <p className="text-sm font-semibold text-blue-900 mb-2">🏆 Produtos que mais contribuíram:</p>
                  <div className="space-y-2">
                    {analise_produtos?.produtos_estrela?.slice(0, 3).map((produto: any, idx: number) => (
                      <div key={produto.id} className="flex justify-between items-center text-sm">
                        <span className="text-blue-800 truncate flex-1">{idx + 1}. {produto.nome}</span>
                        <span className="font-bold text-blue-600 ml-2">R$ {produto.faturamento.toFixed(0)}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="text-xs text-gray-500 italic">
                  ✅ ROI excelente: acima de 30% | ⚠️ Atenção: abaixo de 10%
                </div>
              </div>
            )
          },
          {
            title: 'Ticket Médio',
            tooltip: 'Valor médio que cada cliente gasta por compra. Quanto maior, melhor.',
            value: `R$ ${(hoje?.ticket_medio || 0).toFixed(2)}`,
            change: 8.7,
            icon: DollarIcon,
            color: 'bg-gradient-to-r from-purple-500 to-pink-600',
            details: `${hoje?.clientes_atendidos || 0} clientes hoje`,
            explanation: `Cada cliente gastou em média R$ ${(hoje?.ticket_medio || 0).toFixed(2)}`,
            expandedContent: (
              <div className="space-y-3">
                <div className="bg-purple-50 p-3 rounded-lg">
                  <p className="text-sm font-semibold text-purple-900 mb-1">💡 O que isso significa?</p>
                  <p className="text-sm text-purple-800">
                    O ticket médio mostra quanto cada cliente gasta por compra. Um ticket de R$ {(hoje?.ticket_medio || 0).toFixed(2)} 
                    indica que, em média, cada cliente compra esse valor por visita.
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="bg-gray-50 p-2 rounded">
                    <p className="text-gray-600">Clientes Hoje</p>
                    <p className="font-bold text-gray-900">{hoje?.clientes_atendidos || 0}</p>
                  </div>
                  <div className="bg-gray-50 p-2 rounded">
                    <p className="text-gray-600">Total Vendas</p>
                    <p className="font-bold text-purple-600">R$ {(hoje?.total_vendas || 0).toLocaleString('pt-BR', { maximumFractionDigits: 0 })}</p>
                  </div>
                </div>
                <div className="bg-gradient-to-r from-purple-50 to-pink-50 p-3 rounded-lg">
                  <p className="text-xs font-semibold text-purple-900 mb-1">💡 Como aumentar o ticket médio?</p>
                  <ul className="text-xs text-purple-800 space-y-1">
                    <li>• Ofereça combos e promoções</li>
                    <li>• Sugira produtos complementares</li>
                    <li>• Destaque produtos premium</li>
                  </ul>
                </div>
              </div>
            )
          },
          {
            title: 'Ponto de Equilíbrio',
            tooltip: 'Quanto você precisa vender para cobrir todos os custos. Abaixo disso, você tem prejuízo.',
            value: `R$ ${(analise_financeira.indicadores?.ponto_equilibrio || 0).toLocaleString('pt-BR', { maximumFractionDigits: 0 })}`,
            change: -2.3,
            icon: TargetIcon,
            color: 'bg-gradient-to-r from-orange-500 to-red-600',
            details: `Margem de Segurança: ${(analise_financeira.indicadores?.margem_seguranca || 0).toFixed(1)}%`,
            explanation: `Você precisa vender R$ ${(analise_financeira.indicadores?.ponto_equilibrio || 0).toLocaleString('pt-BR', { maximumFractionDigits: 0 })} para não ter prejuízo`,
            expandedContent: (
              <div className="space-y-3">
                <div className="bg-orange-50 p-3 rounded-lg">
                  <p className="text-sm font-semibold text-orange-900 mb-1">💡 O que isso significa?</p>
                  <p className="text-sm text-orange-800">
                    O ponto de equilíbrio é o valor mínimo que você precisa vender para cobrir todos os custos 
                    (produtos, despesas, salários, etc). Abaixo de R$ {(analise_financeira.indicadores?.ponto_equilibrio || 0).toLocaleString('pt-BR', { maximumFractionDigits: 0 })}, 
                    você tem prejuízo. Acima disso, você lucra!
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="bg-gray-50 p-2 rounded">
                    <p className="text-gray-600">Vendas Atuais</p>
                    <p className="font-bold text-gray-900">R$ {(mes?.total_vendas || 0).toLocaleString('pt-BR', { maximumFractionDigits: 0 })}</p>
                  </div>
                  <div className="bg-gray-50 p-2 rounded">
                    <p className="text-gray-600">Total Despesas</p>
                    <p className="font-bold text-red-600">R$ {(mes?.total_despesas || 0).toLocaleString('pt-BR', { maximumFractionDigits: 0 })}</p>
                  </div>
                </div>
                <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-3 rounded-lg">
                  <p className="text-sm font-semibold text-green-900 mb-1">✅ Situação Atual</p>
                  <p className="text-sm text-green-800">
                    Você está {((mes?.total_vendas || 0) / (analise_financeira.indicadores?.ponto_equilibrio || 1) * 100).toFixed(0)}% 
                    acima do ponto de equilíbrio. Margem de segurança: {(analise_financeira.indicadores?.margem_seguranca || 0).toFixed(1)}%
                  </p>
                </div>
                <div className="text-xs text-gray-500 italic">
                  ✅ Seguro: margem acima de 20% | ⚠️ Atenção: margem abaixo de 10%
                </div>
              </div>
            )
          }
        ].map((kpi, idx) => (
          <div
            key={idx}
            className="bg-white rounded-2xl shadow-xl p-6 transform transition-all duration-300 hover:scale-105 hover:shadow-2xl cursor-pointer border border-gray-200 relative"
            onMouseEnter={() => setHoveredKPI(idx)}
            onMouseLeave={() => setHoveredKPI(null)}
            onClick={() => setExpandedKPI(expandedKPI === idx ? null : idx)}
          >
            {/* Tooltip on hover */}
            {hoveredKPI === idx && (
              <div className="absolute -top-2 left-1/2 transform -translate-x-1/2 -translate-y-full bg-gray-900 text-white text-xs rounded-lg px-3 py-2 z-10 w-64 shadow-xl">
                <div className="relative">
                  {kpi.tooltip}
                  <div className="absolute -bottom-2 left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
                </div>
              </div>
            )}

            <div className="flex justify-between items-start mb-4">
              <div className={`${kpi.color} p-3 rounded-xl shadow-lg`}>
                <kpi.icon className="w-6 h-6 text-white" />
              </div>
              <div className={`flex items-center px-3 py-1 rounded-full text-sm font-semibold ${kpi.change >= 0 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                {kpi.change >= 0 ? <ArrowUpRight className="w-4 h-4 mr-1" /> : <ArrowDownRight className="w-4 h-4 mr-1" />}
                {Math.abs(kpi.change).toFixed(1)}%
              </div>
            </div>
            
            <div className="flex items-center gap-2 mb-2">
              <h3 className="text-gray-500 text-sm font-medium">{kpi.title}</h3>
              <AlertCircle className="w-4 h-4 text-gray-400" />
            </div>
            
            <p className="text-3xl font-bold text-gray-900 mb-2">{kpi.value}</p>
            <p className="text-gray-600 text-sm mb-3">{kpi.details}</p>
            
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-3 rounded-lg mb-3">
              <p className="text-xs text-blue-900 font-medium">{kpi.explanation}</p>
            </div>

            {/* Expanded content */}
            {expandedKPI === idx && (
              <div className="mt-4 pt-4 border-t border-gray-200 animate-fadeIn">
                {kpi.expandedContent}
              </div>
            )}

            <div className="mt-4 pt-4 border-t border-gray-100">
              <div className="flex justify-between items-center text-xs">
                <span className="text-gray-500">
                  {expandedKPI === idx ? 'Clique para recolher' : 'Clique para mais detalhes'}
                </span>
                <span className={`font-semibold ${kpi.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {kpi.change >= 0 ? 'Acima da meta' : 'Abaixo da meta'}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* SEÇÃO PRINCIPAL: CURVA ABC COM GRÁFICO DE PARETO */}
      {(viewMode === 'detalhado' || viewMode === 'cientifico') && (
      <div className="bg-white rounded-2xl shadow-xl mb-8 overflow-hidden border border-gray-200">
        <div
          className="p-6 border-b border-gray-200 flex justify-between items-center cursor-pointer hover:bg-gray-50"
          onClick={() => toggleCard('curva-abc')}
        >
          <div className="flex items-center gap-3">
            <ChartBar className="w-8 h-8 text-blue-600" />
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Curva ABC de Pareto</h2>
              <p className="text-gray-600">Análise 80/20 dos produtos • {analise_produtos?.curva_abc?.pareto_80_20 ? '✅ Lei de Pareto Confirmada' : '⚠️ Distribuição Atípica'}</p>
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

        {expandedCards['curva-abc'] && analise_produtos?.curva_abc && (
          <div className="p-6 animate-fadeIn">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* GRÁFICO DE PARETO */}
              <div className="lg:col-span-2">
                <div className="h-[400px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={produtosFiltrados.slice(0, 15)}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="nome" angle={-45} textAnchor="end" height={80} />
                      <YAxis yAxisId="left" />
                      <YAxis yAxisId="right" orientation="right" />
                      <Tooltip
                        content={({ payload, label }) => (
                          <div className="bg-white p-4 shadow-xl rounded-lg border border-gray-200">
                            <p className="font-bold text-gray-900">{label}</p>
                            <p className="text-sm text-gray-600">Faturamento: R$ {payload?.[0]?.value?.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
                            <p className="text-sm text-gray-600">Classificação: <span className={`font-bold`} style={{ color: getABCColor(payload?.[0]?.payload?.classificacao) }}>{payload?.[0]?.payload?.classificacao}</span></p>
                            <p className="text-sm text-gray-600">Margem: {(payload?.[0]?.payload?.margem || 0).toFixed(1)}%</p>
                            <p className="text-sm text-gray-600">Qtd Vendida: {payload?.[0]?.payload?.quantidade_vendida}</p>
                          </div>
                        )}
                      />
                      <Bar
                        yAxisId="left"
                        dataKey="faturamento"
                        name="Faturamento"
                      >
                        {produtosFiltrados.slice(0, 15).map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={getABCColor(entry.classificacao)} />
                        ))}
                        <LabelList 
                          dataKey="margem" 
                          position="top" 
                          formatter={(val: number) => `${val.toFixed(1)}%`}
                          style={{ fill: '#4B5563', fontSize: '11px', fontWeight: 'bold' }}
                        />
                      </Bar>
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
                <div className="flex justify-center gap-6 mt-6 flex-wrap">
                  {Object.entries(analise_produtos?.curva_abc?.resumo || {}).map(([classe, dados]) => {
                    const getColors = (cls: string) => {
                      switch(cls) {
                        case 'A': return { bg: 'bg-green-100', text: 'text-green-600' };
                        case 'B': return { bg: 'bg-yellow-100', text: 'text-yellow-600' };
                        case 'C': return { bg: 'bg-red-100', text: 'text-red-600' };
                        default: return { bg: 'bg-blue-100', text: 'text-blue-600' };
                      }
                    };
                    const colors = getColors(classe);
                    return (
                      <div key={classe} className="text-center p-2 rounded-lg hover:bg-gray-50 transition-colors">
                        <div className={`w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-2 ${colors.bg}`}>
                          <span className={`text-xl font-bold ${colors.text}`}>
                            {classe === 'TODOS' ? 'ALL' : classe}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600">{dados.quantidade} itens</p>
                        <p className="text-sm font-bold text-gray-900">{(dados?.percentual || 0).toFixed(1)}% Fat.</p>
                        {dados.margem_media !== undefined && (
                          <p className="text-xs font-semibold text-gray-500 mt-1">
                            Margem: <span className={colors.text}>{dados.margem_media.toFixed(1)}%</span>
                          </p>
                        )}
                      </div>
                    );
                  })}
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
                        <p className="text-sm text-gray-600">Responsáveis por {analise_produtos?.curva_abc?.resumo?.B?.percentual?.toFixed(1) || 0}% do faturamento</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-3 h-3 rounded-full bg-red-500"></div>
                      <div>
                        <p className="font-semibold text-gray-900">Classe C (50% dos produtos)</p>
                        <p className="text-sm text-gray-600">Responsáveis por {analise_produtos?.curva_abc?.resumo?.C?.percentual?.toFixed(1) || 0}% do faturamento</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* TOP 5 PRODUTOS DA CLASSE A */}
                <div className="border border-gray-200 rounded-xl p-4">
                  <h4 className="font-bold text-gray-900 mb-3">🏆 Top Produtos Classe A</h4>
                  <div className="space-y-3">
                    {analise_produtos?.curva_abc?.produtos
                      ?.filter(p => p.classificacao === 'A')
                      ?.slice(0, 5)
                      ?.map((produto, idx) => (
                        <div
                          key={produto.id}
                          className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg cursor-pointer transition-colors"
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
      )}

      {/* SEÇÃO: ANÁLISE TEMPORAL - TENDÊNCIA DE VENDAS */}
      {(viewMode === 'detalhado' || viewMode === 'cientifico') && (
      <div className="bg-white rounded-2xl shadow-xl mb-8 overflow-hidden border border-gray-200">
        <div
          className="p-6 border-b border-gray-200 flex justify-between items-center cursor-pointer hover:bg-gray-50"
          onClick={() => toggleCard('analise-temporal')}
        >
          <div className="flex items-center gap-3">
            <TrendingUp className="w-8 h-8 text-purple-600" />
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Análise Temporal de Vendas</h2>
              <p className="text-gray-600">Tendência • Sazonalidade • Previsões • Evolução Mensal</p>
            </div>
          </div>
          <ChevronDown className={`w-6 h-6 text-gray-500 transform transition-transform ${expandedCards['analise-temporal'] ? 'rotate-180' : ''}`} />
        </div>

        {expandedCards['analise-temporal'] && (
          <div className="p-6 animate-fadeIn">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* GRÁFICO DE LINHA: EVOLUÇÃO DAS VENDAS */}
              <div className="bg-gradient-to-br from-purple-50 to-white p-6 rounded-xl border border-purple-200">
                <h3 className="font-bold text-gray-900 mb-6 text-lg flex items-center gap-2">
                  <LineChartIcon className="w-5 h-5 text-purple-600" />
                  Evolução das Vendas (30 dias)
                </h3>
                <div className="h-[300px]">
                  {analise_temporal?.tendencia_vendas?.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={analise_temporal.tendencia_vendas}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                        <XAxis
                          dataKey="data"
                          tick={{ fontSize: 12 }}
                          angle={-45}
                          textAnchor="end"
                          height={60}
                        />
                        <YAxis tick={{ fontSize: 12 }} />
                        <Tooltip
                          content={({ payload, label }) => (
                            <div className="bg-white p-4 shadow-xl rounded-lg border border-gray-200">
                              <p className="font-bold text-gray-900">{label}</p>
                              {payload?.map((entry, index) => (
                                <p key={index} className="text-sm" style={{ color: entry.color }}>
                                  {entry.name}: R$ {entry.value?.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                </p>
                              ))}
                            </div>
                          )}
                        />
                        <Line
                          type="monotone"
                          dataKey="vendas"
                          stroke="#8b5cf6"
                          strokeWidth={3}
                          dot={{ fill: '#8b5cf6', strokeWidth: 2, r: 4 }}
                          name="Vendas Diárias"
                        />
                        <Line
                          type="monotone"
                          dataKey="previsao"
                          stroke="#ef4444"
                          strokeWidth={2}
                          strokeDasharray="5 5"
                          dot={false}
                          name="Previsão"
                          connectNulls={false}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex items-center justify-center h-full">
                      <div className="text-center">
                        <LineChartIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                        <p className="text-gray-500">Dados de tendência não disponíveis</p>
                      </div>
                    </div>
                  )}
                </div>
                <div className="mt-4 grid grid-cols-3 gap-4 text-center">
                  <div className="bg-purple-50 p-3 rounded-lg">
                    <p className="text-sm text-purple-600 font-medium">Tendência</p>
                    <p className={`text-lg font-bold ${analise_temporal.tendencia_vendas?.length > 1 && (analise_temporal.tendencia_vendas[analise_temporal.tendencia_vendas.length - 1]?.vendas || 0) > (analise_temporal.tendencia_vendas[analise_temporal.tendencia_vendas.length - 2]?.vendas || 0) ? 'text-green-600' : 'text-red-600'}`}>
                      {analise_temporal.tendencia_vendas?.length > 1 && (analise_temporal.tendencia_vendas[analise_temporal.tendencia_vendas.length - 1]?.vendas || 0) > (analise_temporal.tendencia_vendas[analise_temporal.tendencia_vendas.length - 2]?.vendas || 0) ? '📈 Crescendo' : '📉 Caindo'}
                    </p>
                  </div>
                  <div className="bg-blue-50 p-3 rounded-lg">
                    <p className="text-sm text-blue-600 font-medium">Média 7 dias</p>
                    <p className="text-lg font-bold text-blue-700">
                      R$ {(analise_temporal.tendencia_vendas?.slice(-7).reduce((acc, curr) => acc + (curr.vendas || 0), 0) / Math.max(1, Math.min(7, analise_temporal.tendencia_vendas?.length || 0)))?.toLocaleString('pt-BR', { maximumFractionDigits: 0 }) || '0'}
                    </p>
                  </div>
                  <div className="bg-green-50 p-3 rounded-lg">
                    <p className="text-sm text-green-600 font-medium">Previsão Amanhã</p>
                    <p className="text-lg font-bold text-green-700">
                      R$ {(analise_temporal.previsao_proxima_semana[0]?.previsao || 0).toLocaleString('pt-BR', { maximumFractionDigits: 0 })}
                    </p>
                  </div>
                </div>
              </div>

              {/* MÉTRICAS DE SAZONALIDADE E PREVISÕES */}
              <div className="space-y-6">
                {/* SAZONALIDADE */}
                <div className="bg-gradient-to-r from-indigo-50 to-purple-50 p-6 rounded-xl border border-indigo-200">
                  <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                    <Calendar className="w-5 h-5 text-indigo-600" />
                    Padrões Sazonais
                  </h3>
                  <div className="space-y-3">
                    {analise_temporal.sazonalidade && analise_temporal.sazonalidade.length > 0 ? (
                      analise_temporal.sazonalidade.map((padrao, idx) => (
                        <div key={idx} className="bg-white/70 p-4 rounded-lg">
                          <div className="flex justify-between items-center mb-2">
                            <span className="font-medium text-gray-900">{padrao.periodo}</span>
                            <span className={`px-2 py-1 rounded-full text-xs font-bold ${padrao.variacao > 0 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                              {padrao.variacao > 0 ? '+' : ''}{padrao.variacao.toFixed(1)}%
                            </span>
                          </div>
                          <p className="text-sm text-gray-600">{padrao.descricao}</p>
                        </div>
                      ))
                    ) : (
                      <div className="bg-white/70 p-6 rounded-lg text-center">
                        <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                        <p className="text-gray-500">Dados insuficientes para análise sazonal</p>
                        <p className="text-sm text-gray-400 mt-1">Necessário pelo menos 3 meses de histórico</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* PREVISÃO PRÓXIMA SEMANA */}
                <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-6 rounded-xl border border-green-200">
                  <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                    <TargetIcon className="w-5 h-5 text-green-600" />
                    Previsão Próxima Semana
                  </h3>
                  <div className="space-y-3">
                    {analise_temporal.previsao_proxima_semana && analise_temporal.previsao_proxima_semana.length > 0 ? (
                      analise_temporal.previsao_proxima_semana.map((prev, idx) => (
                        <div key={idx} className="bg-white/70 p-4 rounded-lg">
                          <div className="flex justify-between items-center">
                            <span className="font-medium text-gray-900">{prev.dia}</span>
                            <div className="text-right">
                              <p className="font-bold text-green-700">R$ {prev.previsao.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
                              <p className="text-xs text-gray-500">±{prev.intervalo_confianca?.toFixed(1) || '5.0'}%</p>
                            </div>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="bg-white/70 p-6 rounded-lg text-center">
                        <TargetIcon className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                        <p className="text-gray-500">Previsões não disponíveis</p>
                        <p className="text-sm text-gray-400 mt-1">Necessário mais dados históricos</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* COMPARAÇÃO MENSAL */}
                <div className="bg-gradient-to-r from-orange-50 to-red-50 p-6 rounded-xl border border-orange-200">
                  <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                    <LucideBarChart className="w-5 h-5 text-orange-600" />
                    Comparação Mensal
                  </h3>
                  <div className="space-y-3">
                    {analise_temporal.comparacao_meses && analise_temporal.comparacao_meses.length > 0 ? (
                      analise_temporal.comparacao_meses.map((comp, idx) => (
                        <div key={idx} className="bg-white/70 p-4 rounded-lg">
                          <div className="flex justify-between items-center mb-2">
                            <span className="font-medium text-gray-900">{comp.mes}</span>
                            <span className={`px-2 py-1 rounded-full text-xs font-bold ${comp.crescimento > 0 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                              {comp.crescimento > 0 ? '+' : ''}{comp.crescimento.toFixed(1)}%
                            </span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-600">Vendas: R$ {comp.vendas.toLocaleString('pt-BR')}</span>
                            <span className="text-gray-600">Meta: R$ {comp.meta.toLocaleString('pt-BR')}</span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="bg-white/70 p-6 rounded-lg text-center">
                        <LucideBarChart className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                        <p className="text-gray-500">Comparação mensal não disponível</p>
                        <p className="text-sm text-gray-400 mt-1">Necessário pelo menos 2 meses de dados</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
      )}

      {/* SEÇÃO: ANÁLISE FINANCEIRA DETALHADA */}
      {(viewMode === 'detalhado' || viewMode === 'cientifico') && (
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
              {/* GRÁFICO DE COLUNAS: DISTRIBUIÇÃO DE DESPESAS */}
              <div className="bg-gradient-to-br from-gray-50 to-white p-6 rounded-xl border border-gray-200">
                <h3 className="font-bold text-gray-900 mb-6 text-lg">📊 Distribuição de Despesas</h3>
                <div className="h-[300px]">
                  {analise_financeira?.despesas_detalhadas && analise_financeira.despesas_detalhadas.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={analise_financeira.despesas_detalhadas}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
                            const RADIAN = Math.PI / 180;
                            const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
                            const x = cx + radius * Math.cos(-midAngle * RADIAN);
                            const y = cy + radius * Math.sin(-midAngle * RADIAN);
                            return percent > 0.05 ? (
                              <text x={x} y={y} fill="white" textAnchor={x > cx ? 'start' : 'end'} dominantBaseline="central" fontSize={12} fontWeight="bold">
                                {`${(percent * 100).toFixed(0)}%`}
                              </text>
                            ) : null;
                          }}
                          outerRadius={100}
                          fill="#8884d8"
                          dataKey="valor"
                          nameKey="tipo"
                        >
                          {analise_financeira.despesas_detalhadas.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={getDistinctColor(index)} />
                          ))}
                        </Pie>
                        <Tooltip
                          content={({ active, payload }) => {
                            if (active && payload && payload.length) {
                              const data = payload[0].payload;
                              return (
                                <div className="bg-white p-4 shadow-xl rounded-lg border border-gray-200 z-50">
                                  <p className="font-bold text-gray-900">{data.tipo}</p>
                                  <p className="text-gray-600">Valor: R$ {data.valor.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
                                  <p className="text-gray-600">Percentual: {data.percentual.toFixed(1)}%</p>
                                  <p className="text-gray-600">Impacto no Lucro: {data.impacto_lucro.toFixed(1)}%</p>
                                  <p className="text-sm text-gray-500 mt-2">
                                    Tendência: {data.tendencia === 'alta' ? '📈 Alta' : data.tendencia === 'baixa' ? '📉 Baixa' : '➡️ Estável'}
                                  </p>
                                </div>
                              );
                            }
                            return null;
                          }}
                        />
                        <Legend 
                          layout="vertical" 
                          verticalAlign="middle" 
                          align="right"
                          wrapperStyle={{ fontSize: '12px' }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex items-center justify-center h-full">
                      <div className="text-center">
                        <DollarIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                        <p className="text-gray-600 font-medium mb-2">Nenhuma despesa registrada no período</p>
                        <p className="text-gray-500 text-sm">As despesas aparecerão aqui quando forem cadastradas no sistema</p>
                        <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                          <p className="text-sm text-blue-800">
                            💡 <strong>Dica:</strong> Cadastre despesas para visualizar a distribuição e análise financeira completa
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
                <div className="grid grid-cols-2 gap-4 mt-6">
                  <div className="bg-green-50 p-4 rounded-lg">
                    <p className="text-sm text-green-800 font-medium">Lucro Bruto</p>
                    <p className="text-2xl font-bold text-green-700">R$ {(mes?.lucro_bruto || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
                    <p className="text-sm text-green-600">Margem: {(mes?.margem_lucro || 0).toFixed(1)}%</p>
                  </div>
                  <div className="bg-red-50 p-4 rounded-lg">
                    <p className="text-sm text-red-800 font-medium">Despesas Totais</p>
                    <p className="text-2xl font-bold text-red-700">R$ {(mes?.total_despesas || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
                    <p className="text-sm text-red-600">{(((mes?.total_despesas || 0) / (mes?.total_vendas || 1)) * 100).toFixed(1)}% das vendas</p>
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
                      <span className="font-bold text-blue-600">{(analise_financeira.indicadores?.ponto_equilibrio || 0).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-700">Margem de Segurança</span>
                      <span className="font-bold text-green-600">{(analise_financeira.indicadores?.margem_seguranca || 0).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-700">Alavancagem Operacional</span>
                      <span className="font-bold text-purple-600">{(analise_financeira.indicadores?.alavancagem_operacional || 0).toFixed(2)}x</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-700">EBITDA</span>
                      <span className="font-bold text-green-700">R$ {(analise_financeira.indicadores?.ebitda || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
      )}

      {/* SEÇÃO: INSIGHTS CIENTÍFICOS */}
      {viewMode === 'cientifico' && (
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
                  {(insights_cientificos.correlações || []).map((corr, idx) => (
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
                    {(insights_cientificos.previsoes || []).map((prev, idx) => (
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
                    {(insights_cientificos.recomendacoes_otimizacao || []).map((rec, idx) => (
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
                          <span className="text-green-400 font-bold">+{(typeof rec.impacto_esperado === 'number' ? rec.impacto_esperado.toFixed(1) : '0.0')}%</span>
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
      )}

      {/* SEÇÃO: PRODUTOS ESTRATÉGICOS */}
      {viewMode === 'cientifico' && (
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
                      <p className="text-sm text-gray-600">Faturamento: <span className="font-bold text-green-600">R$ {produto.faturamento.toFixed(2)}</span></p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-yellow-600">{produto.quantidade_vendida}</p>
                    <p className="text-sm text-gray-600">Vendas</p>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <p className="text-sm text-gray-600">Faturamento</p>
                    <p className="text-lg font-bold text-gray-900">R$ {produto.faturamento.toFixed(2)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Quantidade</p>
                    <p className="text-lg font-bold text-blue-600">{produto.quantidade_vendida}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Ticket Médio</p>
                    <p className="text-lg font-bold text-purple-600">R$ {(produto.faturamento / produto.quantidade_vendida).toFixed(2)}</p>
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
            {analise_produtos.produtos_lentos.length > 0 ? (
              analise_produtos.produtos_lentos.map((produto, idx) => (
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
                        <p className="text-sm text-gray-600">Produto com baixo desempenho</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-xl font-bold text-red-600">Revisar</p>
                      <p className="text-sm text-gray-600">estratégia</p>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="bg-white/80 backdrop-blur-sm rounded-xl p-8 text-center border border-red-100">
                <Package className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 font-medium">Nenhum produto lento identificado</p>
                <p className="text-gray-500 text-sm">Todos os produtos estão com bom desempenho!</p>
              </div>
            )}
          </div>
        </div>
      </div>
      )}

      {/* SEÇÃO: PREVISÃO DE DEMANDA */}
      {viewMode === 'cientifico' && (
      <div className="bg-gradient-to-br from-purple-50 to-indigo-50 rounded-2xl shadow-xl p-6 mb-8 border border-purple-200">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-3">
          <Target className="w-8 h-8 text-purple-600" />
          📊 Previsão de Demanda Inteligente
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {analise_produtos.previsao_demanda.map((previsao, idx) => (
            <div key={idx} className="bg-white/80 backdrop-blur-sm rounded-xl p-6 border border-purple-100">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-gray-900">{previsao.variavel}</h3>
                <div className="flex items-center gap-2">
                  <span className={`px-3 py-1 rounded-full text-xs font-bold ${previsao.confianca > 80 ? 'bg-green-100 text-green-800' : previsao.confianca > 60 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'}`}>
                    {previsao.confianca.toFixed(0)}% confiança
                  </span>
                </div>
              </div>

              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Valor Atual</span>
                  <span className="font-bold text-gray-900">R$ {previsao.valor_atual.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Previsão 30 dias</span>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-purple-600">R$ {previsao.previsao_30d.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                    <TrendingUp className={`w-4 h-4 ${previsao.previsao_30d > previsao.valor_atual ? 'text-green-500' : 'text-red-500'}`} />
                  </div>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Intervalo de Confiança</span>
                  <span className="text-sm text-gray-700">
                    R$ {previsao.intervalo_confianca[0].toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 })} - R$ {previsao.intervalo_confianca[1].toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                  </span>
                </div>

                <div className="pt-4 border-t border-purple-200">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Crescimento Projetado</span>
                    <span className={`font-bold ${previsao.previsao_30d > previsao.valor_atual ? 'text-green-600' : 'text-red-600'}`}>
                      {(((previsao.previsao_30d - previsao.valor_atual) / previsao.valor_atual) * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
      )}
    </div>
  );
};

export default DashboardPage;