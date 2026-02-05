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

import { CorrelationDetailsModal } from './CorrelationDetailsModal';
import { RecommendationDetailsModal } from './RecommendationDetailsModal';

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
    explicacao?: string;
    acoes?: string[];
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
  const [expenseChartMode, setExpenseChartMode] = useState<'barras' | 'pizza'>('barras');
  const [selectedExpenseIndex, setSelectedExpenseIndex] = useState<number | null>(null);

  // Estados para Modal de Correlação
  const [selectedCorrelation, setSelectedCorrelation] = useState<any>(null);
  const [isCorrelationModalOpen, setIsCorrelationModalOpen] = useState(false);
  // Estados para Modal de Recomendação
  const [selectedRecommendation, setSelectedRecommendation] = useState<any>(null);
  const [isRecommendationModalOpen, setIsRecommendationModalOpen] = useState(false);

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
                <div className="bg-green-50 p-4 rounded-lg border-l-4 border-green-500">
                  <p className="text-sm font-bold text-green-900 mb-2">💡 O que é Margem Líquida?</p>
                  <p className="text-sm text-green-800 mb-3">
                    É o percentual de lucro que sobra depois de pagar TODOS os custos do seu mercadinho 
                    (produtos, funcionários, aluguel, luz, água, etc). 
                  </p>
                  <p className="text-sm text-green-800 font-semibold">
                    📊 Sua margem de {(mes?.margem_lucro || 0).toFixed(1)}% significa:
                  </p>
                  <p className="text-sm text-green-800">
                    A cada R$ 100 que você vende, R$ {(mes?.margem_lucro || 0).toFixed(0)} fica de lucro no seu bolso.
                  </p>
                </div>
                
                <div className="bg-white border-2 border-green-200 p-4 rounded-lg">
                  <p className="text-sm font-bold text-gray-900 mb-3">📈 Detalhamento Financeiro:</p>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-blue-50 p-3 rounded-lg">
                      <p className="text-xs text-blue-600 font-medium mb-1">Total Vendido</p>
                      <p className="text-lg font-bold text-blue-900">R$ {(mes?.total_vendas || 0).toLocaleString('pt-BR', { maximumFractionDigits: 0 })}</p>
                      <p className="text-xs text-blue-700 mt-1">Tudo que entrou</p>
                    </div>
                    <div className="bg-green-50 p-3 rounded-lg">
                      <p className="text-xs text-green-600 font-medium mb-1">Lucro Líquido</p>
                      <p className="text-lg font-bold text-green-900">R$ {(mes?.lucro_bruto || 0).toLocaleString('pt-BR', { maximumFractionDigits: 0 })}</p>
                      <p className="text-xs text-green-700 mt-1">O que sobrou</p>
                    </div>
                  </div>
                </div>

                <div className="bg-gradient-to-r from-yellow-50 to-orange-50 p-4 rounded-lg border border-yellow-300">
                  <p className="text-sm font-bold text-orange-900 mb-2">🎯 Como está sua margem?</p>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <span className={`w-3 h-3 rounded-full ${(mes?.margem_lucro || 0) >= 20 ? 'bg-green-500' : 'bg-gray-300'}`}></span>
                      <span className="text-sm text-gray-700">✅ Excelente: acima de 20% - Seu negócio está muito saudável!</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`w-3 h-3 rounded-full ${(mes?.margem_lucro || 0) >= 10 && (mes?.margem_lucro || 0) < 20 ? 'bg-yellow-500' : 'bg-gray-300'}`}></span>
                      <span className="text-sm text-gray-700">⚠️ Razoável: entre 10% e 20% - Dá para melhorar</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`w-3 h-3 rounded-full ${(mes?.margem_lucro || 0) < 10 ? 'bg-red-500' : 'bg-gray-300'}`}></span>
                      <span className="text-sm text-gray-700">🚨 Atenção: abaixo de 10% - Precisa melhorar urgente!</span>
                    </div>
                  </div>
                </div>

                <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                  <p className="text-sm font-bold text-blue-900 mb-2">💪 Como aumentar sua margem:</p>
                  <ul className="space-y-2 text-sm text-blue-800">
                    <li className="flex items-start gap-2">
                      <span className="text-blue-600 font-bold">1.</span>
                      <span>Negocie melhores preços com fornecedores (compre mais barato)</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-600 font-bold">2.</span>
                      <span>Reduza desperdícios e produtos vencidos</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-600 font-bold">3.</span>
                      <span>Foque em vender mais produtos da Classe A (os que dão mais lucro)</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-600 font-bold">4.</span>
                      <span>Controle bem as despesas (luz, água, salários)</span>
                    </li>
                  </ul>
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
                <div className="bg-blue-50 p-4 rounded-lg border-l-4 border-blue-500">
                  <p className="text-sm font-bold text-blue-900 mb-2">💡 O que é ROI (Retorno sobre Investimento)?</p>
                  <p className="text-sm text-blue-800 mb-3">
                    ROI mostra quanto dinheiro você GANHOU em relação ao que você INVESTIU comprando produtos para vender.
                    É como saber se o dinheiro que você gastou comprando mercadorias valeu a pena.
                  </p>
                  <p className="text-sm text-blue-800 font-semibold">
                    📊 Seu ROI de {(mes?.roi_mensal || 0).toFixed(1)}% significa:
                  </p>
                  <p className="text-sm text-blue-800">
                    Para cada R$ 100 que você gastou comprando produtos, você ganhou R$ {(mes?.roi_mensal || 0).toFixed(0)} de lucro.
                  </p>
                </div>

                <div className="bg-white border-2 border-blue-200 p-4 rounded-lg">
                  <p className="text-sm font-bold text-gray-900 mb-3">💰 Exemplo Prático:</p>
                  <div className="space-y-2 text-sm text-gray-700">
                    <div className="flex justify-between items-center p-2 bg-red-50 rounded">
                      <span>Você investiu (comprou produtos):</span>
                      <span className="font-bold text-red-700">- R$ {(mes?.investimentos || 0).toLocaleString('pt-BR', { maximumFractionDigits: 0 })}</span>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-green-50 rounded">
                      <span>Você ganhou de lucro:</span>
                      <span className="font-bold text-green-700">+ R$ {((mes?.investimentos || 0) * (mes?.roi_mensal || 0) / 100).toLocaleString('pt-BR', { maximumFractionDigits: 0 })}</span>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-blue-100 rounded border-2 border-blue-400">
                      <span className="font-bold">Retorno (ROI):</span>
                      <span className="font-bold text-blue-900">{(mes?.roi_mensal || 0).toFixed(1)}%</span>
                    </div>
                  </div>
                </div>

                <div className="bg-gradient-to-r from-purple-50 to-pink-50 p-4 rounded-lg border border-purple-300">
                  <p className="text-sm font-bold text-purple-900 mb-2">🏆 Produtos que mais deram retorno:</p>
                  <p className="text-xs text-purple-700 mb-3">Estes são os produtos que mais trouxeram lucro para você:</p>
                  <div className="space-y-2">
                    {analise_produtos?.produtos_estrela?.slice(0, 3).map((produto: any, idx: number) => (
                      <div key={produto.id} className="flex justify-between items-center p-2 bg-white rounded-lg shadow-sm">
                        <div className="flex items-center gap-2">
                          <span className="w-6 h-6 bg-purple-600 text-white rounded-full flex items-center justify-center text-xs font-bold">{idx + 1}</span>
                          <span className="text-sm text-gray-800 font-medium">{produto.nome}</span>
                        </div>
                        <span className="font-bold text-purple-700">R$ {produto.faturamento?.toFixed(0) || '0'}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-gradient-to-r from-yellow-50 to-orange-50 p-4 rounded-lg border border-yellow-300">
                  <p className="text-sm font-bold text-orange-900 mb-2">🎯 Seu ROI está bom?</p>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <span className={`w-3 h-3 rounded-full ${(mes?.roi_mensal || 0) >= 30 ? 'bg-green-500' : 'bg-gray-300'}`}></span>
                      <span className="text-sm text-gray-700">✅ Excelente: acima de 30% - Investimento muito bom!</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`w-3 h-3 rounded-full ${(mes?.roi_mensal || 0) >= 15 && (mes?.roi_mensal || 0) < 30 ? 'bg-yellow-500' : 'bg-gray-300'}`}></span>
                      <span className="text-sm text-gray-700">⚠️ Razoável: entre 15% e 30% - Está ok, mas pode melhorar</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`w-3 h-3 rounded-full ${(mes?.roi_mensal || 0) < 15 ? 'bg-red-500' : 'bg-gray-300'}`}></span>
                      <span className="text-sm text-gray-700">🚨 Baixo: abaixo de 15% - Precisa revisar os produtos!</span>
                    </div>
                  </div>
                </div>

                <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                  <p className="text-sm font-bold text-green-900 mb-2">💪 Como melhorar seu ROI:</p>
                  <ul className="space-y-2 text-sm text-green-800">
                    <li className="flex items-start gap-2">
                      <span className="text-green-600 font-bold">1.</span>
                      <span>Compre mais dos produtos que vendem rápido (Classe A)</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-green-600 font-bold">2.</span>
                      <span>Evite comprar muito de produtos que ficam parados (Classe C)</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-green-600 font-bold">3.</span>
                      <span>Negocie descontos maiores com fornecedores</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-green-600 font-bold">4.</span>
                      <span>Faça promoções para girar o estoque mais rápido</span>
                    </li>
                  </ul>
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
                <div className="bg-purple-50 p-4 rounded-lg border-l-4 border-purple-500">
                  <p className="text-sm font-bold text-purple-900 mb-2">💡 O que é Ticket Médio?</p>
                  <p className="text-sm text-purple-800 mb-3">
                    É o valor MÉDIO que cada cliente gasta quando vem ao seu mercadinho. 
                    Quanto maior o ticket médio, mais cada cliente compra por visita!
                  </p>
                  <p className="text-sm text-purple-800 font-semibold">
                    📊 Seu ticket médio de R$ {(hoje?.ticket_medio || 0).toFixed(2)} significa:
                  </p>
                  <p className="text-sm text-purple-800">
                    Em média, cada cliente que entra no seu mercado gasta R$ {(hoje?.ticket_medio || 0).toFixed(2)}.
                  </p>
                </div>

                <div className="bg-white border-2 border-purple-200 p-4 rounded-lg">
                  <p className="text-sm font-bold text-gray-900 mb-3">📊 Como calculamos:</p>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center p-2 bg-blue-50 rounded">
                      <span className="text-sm text-gray-700">Total vendido hoje:</span>
                      <span className="font-bold text-blue-900">R$ {(hoje?.total_vendas || 0).toLocaleString('pt-BR', { maximumFractionDigits: 0 })}</span>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-green-50 rounded">
                      <span className="text-sm text-gray-700">Clientes atendidos:</span>
                      <span className="font-bold text-green-900">{hoje?.clientes_atendidos || 0} pessoas</span>
                    </div>
                    <div className="border-t-2 border-gray-300 my-2"></div>
                    <div className="flex justify-between items-center p-2 bg-purple-100 rounded border-2 border-purple-400">
                      <span className="font-bold text-gray-900">Ticket Médio:</span>
                      <span className="font-bold text-purple-900">R$ {(hoje?.ticket_medio || 0).toFixed(2)}</span>
                    </div>
                    <p className="text-xs text-gray-600 text-center mt-2">
                      (Total vendido ÷ Número de clientes = Ticket Médio)
                    </p>
                  </div>
                </div>

                <div className="bg-gradient-to-r from-yellow-50 to-orange-50 p-4 rounded-lg border border-yellow-300">
                  <p className="text-sm font-bold text-orange-900 mb-2">🎯 Seu ticket médio está bom?</p>
                  <p className="text-xs text-orange-700 mb-3">Depende do tipo de mercadinho, mas veja uma referência:</p>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <span className={`w-3 h-3 rounded-full ${(hoje?.ticket_medio || 0) >= 50 ? 'bg-green-500' : 'bg-gray-300'}`}></span>
                      <span className="text-sm text-gray-700">✅ Muito bom: acima de R$ 50 por cliente</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`w-3 h-3 rounded-full ${(hoje?.ticket_medio || 0) >= 30 && (hoje?.ticket_medio || 0) < 50 ? 'bg-yellow-500' : 'bg-gray-300'}`}></span>
                      <span className="text-sm text-gray-700">⚠️ Razoável: entre R$ 30 e R$ 50</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`w-3 h-3 rounded-full ${(hoje?.ticket_medio || 0) < 30 ? 'bg-red-500' : 'bg-gray-300'}`}></span>
                      <span className="text-sm text-gray-700">🚨 Baixo: abaixo de R$ 30 - Precisa melhorar!</span>
                    </div>
                  </div>
                </div>

                <div className="bg-gradient-to-r from-pink-50 to-purple-50 p-4 rounded-lg border border-pink-300">
                  <p className="text-sm font-bold text-pink-900 mb-2">💪 Como aumentar o ticket médio:</p>
                  <p className="text-xs text-pink-700 mb-3">Faça seus clientes comprarem mais em cada visita:</p>
                  <ul className="space-y-2 text-sm text-pink-800">
                    <li className="flex items-start gap-2">
                      <span className="text-pink-600 font-bold">1.</span>
                      <div>
                        <p className="font-semibold">Crie combos e promoções</p>
                        <p className="text-xs text-pink-700">Ex: "Leve 3, pague 2" ou "Combo café + pão com desconto"</p>
                      </div>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-pink-600 font-bold">2.</span>
                      <div>
                        <p className="font-semibold">Sugira produtos complementares</p>
                        <p className="text-xs text-pink-700">Ex: Cliente comprou macarrão? Ofereça molho de tomate</p>
                      </div>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-pink-600 font-bold">3.</span>
                      <div>
                        <p className="font-semibold">Destaque produtos no caixa</p>
                        <p className="text-xs text-pink-700">Balas, chocolates, pilhas - coisas que o cliente compra por impulso</p>
                      </div>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-pink-600 font-bold">4.</span>
                      <div>
                        <p className="font-semibold">Organize bem as prateleiras</p>
                        <p className="text-xs text-pink-700">Produtos mais caros na altura dos olhos, produtos relacionados juntos</p>
                      </div>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-pink-600 font-bold">5.</span>
                      <div>
                        <p className="font-semibold">Ofereça produtos de qualidade</p>
                        <p className="text-xs text-pink-700">Tenha opções premium para quem quer gastar mais</p>
                      </div>
                    </li>
                  </ul>
                </div>

                <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                  <p className="text-sm font-bold text-blue-900 mb-2">💡 Exemplo Real:</p>
                  <p className="text-sm text-blue-800">
                    Se você aumentar o ticket médio de R$ {(hoje?.ticket_medio || 0).toFixed(2)} para 
                    R$ {((hoje?.ticket_medio || 0) * 1.2).toFixed(2)} (20% a mais), com {hoje?.clientes_atendidos || 0} clientes por dia, 
                    você faturaria <span className="font-bold text-blue-900">R$ {(((hoje?.ticket_medio || 0) * 1.2 * (hoje?.clientes_atendidos || 0)) - (hoje?.total_vendas || 0)).toLocaleString('pt-BR', { maximumFractionDigits: 0 })} A MAIS por dia!</span>
                  </p>
                  <p className="text-xs text-blue-700 mt-2">
                    Isso dá <span className="font-bold">R$ {(((hoje?.ticket_medio || 0) * 1.2 * (hoje?.clientes_atendidos || 0)) - (hoje?.total_vendas || 0) * 30).toLocaleString('pt-BR', { maximumFractionDigits: 0 })} a mais por mês!</span>
                  </p>
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
                <div className="bg-orange-50 p-4 rounded-lg border-l-4 border-orange-500">
                  <p className="text-sm font-bold text-orange-900 mb-2">💡 O que é Ponto de Equilíbrio?</p>
                  <p className="text-sm text-orange-800 mb-3">
                    É o valor MÍNIMO que você precisa vender para NÃO TER PREJUÍZO. 
                    É quando o dinheiro que entra é igual ao dinheiro que sai.
                  </p>
                  <p className="text-sm text-orange-800 font-semibold mb-2">
                    📊 Seu ponto de equilíbrio é R$ {(analise_financeira.indicadores?.ponto_equilibrio || 0).toLocaleString('pt-BR', { maximumFractionDigits: 0 })}
                  </p>
                  <div className="space-y-2 text-sm text-orange-800">
                    <p>✅ Se vender MAIS que isso: <span className="font-bold text-green-700">VOCÊ LUCRA!</span></p>
                    <p>❌ Se vender MENOS que isso: <span className="font-bold text-red-700">VOCÊ TEM PREJUÍZO!</span></p>
                  </div>
                </div>

                <div className="bg-white border-2 border-orange-200 p-4 rounded-lg">
                  <p className="text-sm font-bold text-gray-900 mb-3">📊 Situação Atual do Seu Mercadinho:</p>
                  <div className="space-y-3">
                    <div className="p-3 bg-blue-50 rounded-lg">
                      <p className="text-xs text-blue-600 font-medium mb-1">Quanto você vendeu este mês:</p>
                      <p className="text-xl font-bold text-blue-900">R$ {(mes?.total_vendas || 0).toLocaleString('pt-BR', { maximumFractionDigits: 0 })}</p>
                    </div>
                    <div className="p-3 bg-red-50 rounded-lg">
                      <p className="text-xs text-red-600 font-medium mb-1">Quanto você gastou (despesas):</p>
                      <p className="text-xl font-bold text-red-900">R$ {(mes?.total_despesas || 0).toLocaleString('pt-BR', { maximumFractionDigits: 0 })}</p>
                    </div>
                    <div className="p-3 bg-orange-50 rounded-lg border-2 border-orange-400">
                      <p className="text-xs text-orange-600 font-medium mb-1">Ponto de Equilíbrio (mínimo para não ter prejuízo):</p>
                      <p className="text-xl font-bold text-orange-900">R$ {(analise_financeira.indicadores?.ponto_equilibrio || 0).toLocaleString('pt-BR', { maximumFractionDigits: 0 })}</p>
                    </div>
                    <div className="p-3 bg-green-50 rounded-lg border-2 border-green-400">
                      <p className="text-xs text-green-600 font-medium mb-1">Quanto você está acima do ponto de equilíbrio:</p>
                      <p className="text-xl font-bold text-green-900">
                        {((mes?.total_vendas || 0) / (analise_financeira.indicadores?.ponto_equilibrio || 1) * 100).toFixed(0)}%
                      </p>
                      <p className="text-xs text-green-700 mt-1">
                        Você vendeu R$ {((mes?.total_vendas || 0) - (analise_financeira.indicadores?.ponto_equilibrio || 0)).toLocaleString('pt-BR', { maximumFractionDigits: 0 })} a mais que o mínimo!
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-4 rounded-lg border border-green-300">
                  <p className="text-sm font-bold text-green-900 mb-2">✅ Margem de Segurança: {(analise_financeira.indicadores?.margem_seguranca || 0).toFixed(1)}%</p>
                  <p className="text-sm text-green-800 mb-3">
                    A margem de segurança mostra o quanto você pode "perder" de vendas antes de começar a ter prejuízo.
                  </p>
                  <p className="text-sm text-green-800 font-semibold">
                    📊 O que significa {(analise_financeira.indicadores?.margem_seguranca || 0).toFixed(1)}%?
                  </p>
                  <p className="text-sm text-green-800">
                    Suas vendas podem cair até {(analise_financeira.indicadores?.margem_seguranca || 0).toFixed(1)}% 
                    (R$ {((mes?.total_vendas || 0) * (analise_financeira.indicadores?.margem_seguranca || 0) / 100).toLocaleString('pt-BR', { maximumFractionDigits: 0 })}) 
                    que você ainda não terá prejuízo!
                  </p>
                </div>

                <div className="bg-gradient-to-r from-yellow-50 to-orange-50 p-4 rounded-lg border border-yellow-300">
                  <p className="text-sm font-bold text-orange-900 mb-2">🎯 Sua margem de segurança está boa?</p>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <span className={`w-3 h-3 rounded-full ${(analise_financeira.indicadores?.margem_seguranca || 0) >= 30 ? 'bg-green-500' : 'bg-gray-300'}`}></span>
                      <span className="text-sm text-gray-700">✅ Excelente: acima de 30% - Muito seguro!</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`w-3 h-3 rounded-full ${(analise_financeira.indicadores?.margem_seguranca || 0) >= 15 && (analise_financeira.indicadores?.margem_seguranca || 0) < 30 ? 'bg-yellow-500' : 'bg-gray-300'}`}></span>
                      <span className="text-sm text-gray-700">⚠️ Razoável: entre 15% e 30% - Está ok</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`w-3 h-3 rounded-full ${(analise_financeira.indicadores?.margem_seguranca || 0) < 15 ? 'bg-red-500' : 'bg-gray-300'}`}></span>
                      <span className="text-sm text-gray-700">🚨 Baixa: abaixo de 15% - Cuidado! Pouca margem de erro</span>
                    </div>
                  </div>
                </div>

                <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                  <p className="text-sm font-bold text-blue-900 mb-2">💪 Como melhorar seu ponto de equilíbrio:</p>
                  <p className="text-xs text-blue-700 mb-3">Você pode baixar o ponto de equilíbrio (precisar vender menos) de 2 formas:</p>
                  <div className="space-y-3">
                    <div className="bg-white p-3 rounded-lg border-l-4 border-blue-500">
                      <p className="text-sm font-bold text-blue-900 mb-1">1️⃣ REDUZIR DESPESAS FIXAS</p>
                      <ul className="text-sm text-blue-800 space-y-1 ml-4">
                        <li>• Negocie aluguel mais barato</li>
                        <li>• Economize energia (troque lâmpadas, desligue equipamentos)</li>
                        <li>• Reduza desperdícios</li>
                        <li>• Renegocie contratos (internet, telefone)</li>
                      </ul>
                    </div>
                    <div className="bg-white p-3 rounded-lg border-l-4 border-green-500">
                      <p className="text-sm font-bold text-green-900 mb-1">2️⃣ AUMENTAR A MARGEM DE LUCRO</p>
                      <ul className="text-sm text-green-800 space-y-1 ml-4">
                        <li>• Negocie melhores preços com fornecedores</li>
                        <li>• Venda mais produtos de margem alta</li>
                        <li>• Reduza produtos que dão pouco lucro</li>
                        <li>• Ajuste preços quando necessário</li>
                      </ul>
                    </div>
                  </div>
                </div>

                <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
                  <p className="text-sm font-bold text-purple-900 mb-2">💡 Exemplo Prático:</p>
                  <p className="text-sm text-purple-800">
                    Se você conseguir reduzir suas despesas em R$ 500 por mês, seu ponto de equilíbrio vai baixar! 
                    Isso significa que você vai precisar vender MENOS para não ter prejuízo, e vai lucrar MAIS!
                  </p>
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
                        content={({ payload, label }) => {
                          if (payload && payload.length > 0) {
                            const produto = payload[0].payload;
                            return (
                              <div className="bg-white p-4 shadow-2xl rounded-lg border-2 border-gray-300 max-w-sm">
                                <p className="font-bold text-gray-900 text-base mb-3">{label}</p>
                                <div className="space-y-2">
                                  <div className="flex justify-between items-center">
                                    <span className="text-sm text-gray-600">Faturamento:</span>
                                    <span className="font-bold text-green-700 text-lg">
                                      R$ {payload?.[0]?.value?.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                    </span>
                                  </div>
                                  <div className="flex justify-between items-center">
                                    <span className="text-sm text-gray-600">Classificação:</span>
                                    <span className={`font-bold text-lg px-3 py-1 rounded-full`} 
                                          style={{ 
                                            backgroundColor: getABCColor(produto?.classificacao) + '20',
                                            color: getABCColor(produto?.classificacao)
                                          }}>
                                      Classe {produto?.classificacao}
                                    </span>
                                  </div>
                                  <div className="flex justify-between items-center">
                                    <span className="text-sm text-gray-600">Margem de lucro:</span>
                                    <span className="font-bold text-blue-700">{(produto?.margem || 0).toFixed(1)}%</span>
                                  </div>
                                  <div className="flex justify-between items-center">
                                    <span className="text-sm text-gray-600">Quantidade vendida:</span>
                                    <span className="font-bold text-purple-700">{produto?.quantidade_vendida} un.</span>
                                  </div>
                                </div>
                                <div className="mt-3 pt-3 border-t border-gray-200">
                                  <p className="text-xs font-semibold text-gray-700 mb-1">
                                    💡 {produto?.classificacao === 'A' ? 'Produto CAMPEÃO! Nunca deixe faltar.' :
                                        produto?.classificacao === 'B' ? 'Produto intermediário. Mantenha estoque moderado.' :
                                        'Produto lento. Considere reduzir estoque.'}
                                  </p>
                                </div>
                              </div>
                            );
                          }
                          return null;
                        }}
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
                {/* EXPLICAÇÃO DA CURVA ABC */}
                <div className="bg-gradient-to-br from-indigo-50 to-purple-50 p-6 rounded-xl border-2 border-indigo-300">
                  <h3 className="font-bold text-gray-900 mb-3 text-lg">� O que é a Curva ABC?</h3>
                  <p className="text-sm text-gray-700 mb-4">
                    A Curva ABC (também chamada de Regra 80/20 ou Princípio de Pareto) divide seus produtos em 3 grupos 
                    de acordo com quanto dinheiro eles trazem para você:
                  </p>
                  <div className="space-y-4">
                    <div className="bg-white p-4 rounded-lg border-l-4 border-green-500">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center">
                          <span className="text-white font-bold">A</span>
                        </div>
                        <p className="font-bold text-green-900 text-base">Classe A - Seus CAMPEÕES 🏆</p>
                      </div>
                      <p className="text-sm text-gray-700 mb-2">
                        São apenas 20% dos seus produtos, mas trazem {analise_produtos.curva_abc.resumo.A.percentual.toFixed(0)}% do seu faturamento!
                      </p>
                      <p className="text-sm text-green-800 font-semibold">
                        💡 O que fazer: NUNCA deixe faltar! Compre sempre, negocie bons preços, destaque na loja.
                      </p>
                    </div>

                    <div className="bg-white p-4 rounded-lg border-l-4 border-yellow-500">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="w-8 h-8 rounded-full bg-yellow-500 flex items-center justify-center">
                          <span className="text-white font-bold">B</span>
                        </div>
                        <p className="font-bold text-yellow-900 text-base">Classe B - Os INTERMEDIÁRIOS ⚖️</p>
                      </div>
                      <p className="text-sm text-gray-700 mb-2">
                        São 30% dos produtos e trazem {analise_produtos?.curva_abc?.resumo?.B?.percentual?.toFixed(0) || 0}% do faturamento.
                      </p>
                      <p className="text-sm text-yellow-800 font-semibold">
                        💡 O que fazer: Mantenha estoque moderado. Fique de olho para não virar Classe C.
                      </p>
                    </div>

                    <div className="bg-white p-4 rounded-lg border-l-4 border-red-500">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="w-8 h-8 rounded-full bg-red-500 flex items-center justify-center">
                          <span className="text-white font-bold">C</span>
                        </div>
                        <p className="font-bold text-red-900 text-base">Classe C - Os LENTOS 🐌</p>
                      </div>
                      <p className="text-sm text-gray-700 mb-2">
                        São 50% dos produtos (metade do seu estoque!), mas trazem apenas {analise_produtos?.curva_abc?.resumo?.C?.percentual?.toFixed(0) || 0}% do faturamento.
                      </p>
                      <p className="text-sm text-red-800 font-semibold">
                        💡 O que fazer: Compre menos! Faça promoções para girar. Considere tirar alguns da loja.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-6 rounded-xl border border-blue-200">
                  <h3 className="font-bold text-gray-900 mb-4">📊 Interpretação da Curva ABC</h3>
                  <div className="space-y-3">
                    <div className="flex items-center gap-3">
                      <div className="w-3 h-3 rounded-full bg-green-500"></div>
                      <div>
                        <p className="font-semibold text-gray-900">Classe A ({analise_produtos.curva_abc.resumo.A.quantidade} produtos)</p>
                        <p className="text-sm text-gray-600">Responsáveis por {analise_produtos.curva_abc.resumo.A.percentual.toFixed(1)}% do faturamento</p>
                        {analise_produtos.curva_abc.resumo.A.margem_media !== undefined && (
                          <p className="text-xs text-green-700 font-semibold">Margem média: {analise_produtos.curva_abc.resumo.A.margem_media.toFixed(1)}%</p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                      <div>
                        <p className="font-semibold text-gray-900">Classe B ({analise_produtos?.curva_abc?.resumo?.B?.quantidade || 0} produtos)</p>
                        <p className="text-sm text-gray-600">Responsáveis por {analise_produtos?.curva_abc?.resumo?.B?.percentual?.toFixed(1) || 0}% do faturamento</p>
                        {analise_produtos?.curva_abc?.resumo?.B?.margem_media !== undefined && (
                          <p className="text-xs text-yellow-700 font-semibold">Margem média: {analise_produtos.curva_abc.resumo.B.margem_media.toFixed(1)}%</p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-3 h-3 rounded-full bg-red-500"></div>
                      <div>
                        <p className="font-semibold text-gray-900">Classe C ({analise_produtos?.curva_abc?.resumo?.C?.quantidade || 0} produtos)</p>
                        <p className="text-sm text-gray-600">Responsáveis por {analise_produtos?.curva_abc?.resumo?.C?.percentual?.toFixed(1) || 0}% do faturamento</p>
                        {analise_produtos?.curva_abc?.resumo?.C?.margem_media !== undefined && (
                          <p className="text-xs text-red-700 font-semibold">Margem média: {analise_produtos.curva_abc.resumo.C.margem_media.toFixed(1)}%</p>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  {analise_produtos?.curva_abc?.pareto_80_20 && (
                    <div className="mt-4 p-3 bg-green-100 rounded-lg border border-green-300">
                      <p className="text-sm text-green-900 font-semibold">
                        ✅ Lei de Pareto Confirmada! 
                      </p>
                      <p className="text-xs text-green-800 mt-1">
                        Seus produtos seguem a regra 80/20: poucos produtos (Classe A) geram a maior parte do faturamento.
                        Isso é NORMAL e esperado!
                      </p>
                    </div>
                  )}
                </div>

                {/* TOP 5 PRODUTOS DA CLASSE A */}
                <div className="border-2 border-green-300 rounded-xl p-4 bg-gradient-to-br from-green-50 to-emerald-50">
                  <h4 className="font-bold text-gray-900 mb-3 text-lg">🏆 Top 5 Produtos Classe A</h4>
                  <p className="text-sm text-gray-700 mb-4">
                    Estes são seus produtos MAIS IMPORTANTES! Cuide bem deles:
                  </p>
                  <div className="space-y-3">
                    {analise_produtos?.curva_abc?.produtos
                      ?.filter(p => p.classificacao === 'A')
                      ?.slice(0, 5)
                      ?.map((produto, idx) => (
                        <div
                          key={produto.id}
                          className="flex items-center justify-between p-4 hover:bg-white rounded-lg cursor-pointer transition-all shadow-sm border border-green-200"
                        >
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-600 text-white rounded-full flex items-center justify-center font-bold text-lg shadow-md">
                              {idx + 1}
                            </div>
                            <div>
                              <p className="font-bold text-gray-900">{produto.nome}</p>
                              <div className="flex gap-3 mt-1">
                                <span className="text-xs text-gray-600">Margem: <span className="font-semibold text-green-700">{produto.margem.toFixed(1)}%</span></span>
                                <span className="text-xs text-gray-600">Vendidos: <span className="font-semibold">{produto.quantidade_vendida}</span></span>
                              </div>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="font-bold text-green-700 text-lg">R$ {produto.faturamento.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
                            <p className="text-xs text-gray-600">Faturamento</p>
                          </div>
                        </div>
                      ))}
                  </div>
                  <div className="mt-4 p-3 bg-yellow-50 rounded-lg border border-yellow-300">
                    <p className="text-sm text-yellow-900 font-semibold">
                      ⚠️ ATENÇÃO: Se qualquer um destes produtos faltar, você perde MUITO dinheiro!
                    </p>
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
            {/* BANNER EXPLICATIVO */}
            <div className="mb-6 bg-gradient-to-r from-purple-50 to-pink-50 p-5 rounded-xl border-2 border-purple-300">
              <h3 className="font-bold text-purple-900 mb-3 text-lg">📚 O que é Análise Temporal?</h3>
              <p className="text-sm text-purple-800 mb-3">
                A Análise Temporal mostra como suas vendas se comportam ao longo do TEMPO. 
                Isso ajuda você a entender padrões, prever o futuro e tomar decisões melhores!
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="bg-white p-3 rounded-lg border-l-4 border-purple-500">
                  <p className="font-bold text-purple-900 text-sm mb-1">📈 Tendência</p>
                  <p className="text-xs text-gray-700">Suas vendas estão subindo ou caindo? Veja a direção do seu negócio.</p>
                </div>
                <div className="bg-white p-3 rounded-lg border-l-4 border-indigo-500">
                  <p className="font-bold text-indigo-900 text-sm mb-1">📅 Sazonalidade</p>
                  <p className="text-xs text-gray-700">Descubra em quais dias/meses você vende mais ou menos.</p>
                </div>
                <div className="bg-white p-3 rounded-lg border-l-4 border-green-500">
                  <p className="font-bold text-green-900 text-sm mb-1">🔮 Previsões</p>
                  <p className="text-xs text-gray-700">Veja quanto você deve vender nos próximos dias para se preparar!</p>
                </div>
              </div>
            </div>

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
                          content={({ payload, label }) => {
                            if (payload && payload.length > 0) {
                              return (
                                <div className="bg-white p-4 shadow-2xl rounded-lg border-2 border-purple-300 max-w-xs">
                                  <p className="font-bold text-purple-900 text-base mb-3">📅 {label}</p>
                                  <div className="space-y-2">
                                    {payload?.map((entry, index) => (
                                      <div key={index} className="flex justify-between items-center">
                                        <span className="text-sm font-medium" style={{ color: entry.color }}>
                                          {entry.name}:
                                        </span>
                                        <span className="font-bold text-lg" style={{ color: entry.color }}>
                                          R$ {entry.value?.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                        </span>
                                      </div>
                                    ))}
                                  </div>
                                  {payload.length > 1 && payload[0].value && payload[1].value && (
                                    <div className="mt-3 pt-3 border-t border-gray-200">
                                      <p className="text-xs text-gray-600">
                                        {payload[1].value > payload[0].value ? 
                                          '📈 Previsão acima do realizado' : 
                                          payload[1].value < payload[0].value ?
                                          '📉 Previsão abaixo do realizado' :
                                          '➡️ Previsão igual ao realizado'}
                                      </p>
                                    </div>
                                  )}
                                </div>
                              );
                            }
                            return null;
                          }}
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
                  <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-lg border-2 border-purple-300 shadow-sm">
                    <p className="text-xs text-purple-600 font-bold mb-2">📊 TENDÊNCIA</p>
                    <p className={`text-2xl font-bold mb-1 ${analise_temporal.tendencia_vendas?.length > 1 && (analise_temporal.tendencia_vendas[analise_temporal.tendencia_vendas.length - 1]?.vendas || 0) > (analise_temporal.tendencia_vendas[analise_temporal.tendencia_vendas.length - 2]?.vendas || 0) ? 'text-green-600' : 'text-red-600'}`}>
                      {analise_temporal.tendencia_vendas?.length > 1 && (analise_temporal.tendencia_vendas[analise_temporal.tendencia_vendas.length - 1]?.vendas || 0) > (analise_temporal.tendencia_vendas[analise_temporal.tendencia_vendas.length - 2]?.vendas || 0) ? '📈' : '📉'}
                    </p>
                    <p className={`text-sm font-semibold ${analise_temporal.tendencia_vendas?.length > 1 && (analise_temporal.tendencia_vendas[analise_temporal.tendencia_vendas.length - 1]?.vendas || 0) > (analise_temporal.tendencia_vendas[analise_temporal.tendencia_vendas.length - 2]?.vendas || 0) ? 'text-green-700' : 'text-red-700'}`}>
                      {analise_temporal.tendencia_vendas?.length > 1 && (analise_temporal.tendencia_vendas[analise_temporal.tendencia_vendas.length - 1]?.vendas || 0) > (analise_temporal.tendencia_vendas[analise_temporal.tendencia_vendas.length - 2]?.vendas || 0) ? 'Crescendo' : 'Caindo'}
                    </p>
                    <p className="text-xs text-purple-700 mt-2">
                      {analise_temporal.tendencia_vendas?.length > 1 && (analise_temporal.tendencia_vendas[analise_temporal.tendencia_vendas.length - 1]?.vendas || 0) > (analise_temporal.tendencia_vendas[analise_temporal.tendencia_vendas.length - 2]?.vendas || 0) ? 
                        '✅ Suas vendas estão subindo!' : 
                        '⚠️ Suas vendas estão caindo'}
                    </p>
                  </div>
                  <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg border-2 border-blue-300 shadow-sm">
                    <p className="text-xs text-blue-600 font-bold mb-2">📅 MÉDIA 7 DIAS</p>
                    <p className="text-2xl font-bold text-blue-900 mb-1">
                      R$ {(analise_temporal.tendencia_vendas?.slice(-7).reduce((acc, curr) => acc + (curr.vendas || 0), 0) / Math.max(1, Math.min(7, analise_temporal.tendencia_vendas?.length || 0)))?.toLocaleString('pt-BR', { maximumFractionDigits: 0 }) || '0'}
                    </p>
                    <p className="text-sm font-semibold text-blue-700">Por dia</p>
                    <p className="text-xs text-blue-700 mt-2">
                      Média dos últimos 7 dias
                    </p>
                  </div>
                  <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg border-2 border-green-300 shadow-sm">
                    <p className="text-xs text-green-600 font-bold mb-2">🔮 PREVISÃO AMANHÃ</p>
                    <p className="text-2xl font-bold text-green-900 mb-1">
                      R$ {(analise_temporal.previsao_proxima_semana[0]?.previsao || 0).toLocaleString('pt-BR', { maximumFractionDigits: 0 })}
                    </p>
                    <p className="text-sm font-semibold text-green-700">Esperado</p>
                    <p className="text-xs text-green-700 mt-2">
                      Prepare-se para este valor!
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
            {/* BANNER EXPLICATIVO */}
            <div className="mb-6 bg-gradient-to-r from-green-50 to-emerald-50 p-5 rounded-xl border-2 border-green-300">
              <h3 className="font-bold text-green-900 mb-3 text-lg">📚 O que é Análise Financeira?</h3>
              <p className="text-sm text-green-800 mb-3">
                A Análise Financeira mostra para onde está indo o seu dinheiro e quanto você está lucrando de verdade.
                É como um "raio-X" da saúde financeira do seu mercadinho!
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="bg-white p-3 rounded-lg border-l-4 border-red-500">
                  <p className="font-bold text-red-900 text-sm mb-1">💸 Despesas</p>
                  <p className="text-xs text-gray-700">
                    Veja quanto você gasta com cada tipo de despesa (aluguel, luz, salários, etc). 
                    Descubra onde pode economizar!
                  </p>
                </div>
                <div className="bg-white p-3 rounded-lg border-l-4 border-green-500">
                  <p className="font-bold text-green-900 text-sm mb-1">💰 Margens</p>
                  <p className="text-xs text-gray-700">
                    Entenda quanto você lucra de verdade depois de pagar tudo. 
                    Quanto maior a margem, melhor!
                  </p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* GRÁFICO DE COLUNAS: DISTRIBUIÇÃO DE DESPESAS */}
              <div className="bg-gradient-to-br from-gray-50 to-white p-6 rounded-xl border border-gray-200">
                <div className="mb-4 bg-blue-50 p-4 rounded-lg border-l-4 border-blue-500">
                  <p className="text-sm font-bold text-blue-900 mb-2">💡 Como ler este gráfico:</p>
                  <ul className="text-sm text-blue-800 space-y-1">
                    <li>• Cada barra mostra um tipo de despesa</li>
                    <li>• Quanto MAIOR a barra, mais você gasta com aquilo</li>
                    <li>• O número (%) mostra quanto aquela despesa representa do total</li>
                    <li>• Clique em uma barra para destacá-la e ver mais detalhes</li>
                  </ul>
                </div>
                
                <h3 className="font-bold text-gray-900 mb-6 text-lg">📊 Distribuição de Despesas</h3>
                <div className="flex items-center justify-between mb-3">
                  <div className="text-sm text-gray-600">
                    Ordenado por valor (maior para menor)
                  </div>
                  <div className="flex gap-2">
                    <button
                      className={`px-3 py-1 rounded-lg ${expenseChartMode === 'barras' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'} hover:bg-blue-500 hover:text-white transition-colors`}
                      onClick={() => setExpenseChartMode('barras')}
                    >
                      📊 Barras
                    </button>
                    <button
                      className={`px-3 py-1 rounded-lg ${expenseChartMode === 'pizza' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'} hover:bg-blue-500 hover:text-white transition-colors`}
                      onClick={() => setExpenseChartMode('pizza')}
                    >
                      🥧 Pizza
                    </button>
                  </div>
                </div>
                <div className="h-[320px]">
                  {analise_financeira?.despesas_detalhadas && analise_financeira.despesas_detalhadas.length > 0 ? (
                    expenseChartMode === 'barras' ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                          data={[...analise_financeira.despesas_detalhadas].sort((a, b) => b.valor - a.valor)}
                          layout="vertical"
                          margin={{ left: 80, right: 20, top: 10, bottom: 10 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
                          <XAxis
                            type="number"
                            tickFormatter={(v) => `R$ ${Number(v).toLocaleString('pt-BR')}`}
                          />
                          <YAxis
                            type="category"
                            dataKey="tipo"
                            width={80}
                          />
                          <Tooltip
                            content={({ active, payload }) => {
                              if (active && payload && payload.length) {
                                const d = payload[0].payload;
                                return (
                                  <div className="bg-white p-4 shadow-2xl rounded-lg border-2 border-gray-300 max-w-xs">
                                    <p className="font-bold text-gray-900 text-base mb-2">{d.tipo}</p>
                                    <div className="space-y-2">
                                      <div className="flex justify-between items-center">
                                        <span className="text-sm text-gray-600">Valor gasto:</span>
                                        <span className="font-bold text-red-700">R$ {d.valor.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                                      </div>
                                      <div className="flex justify-between items-center">
                                        <span className="text-sm text-gray-600">% do total:</span>
                                        <span className="font-bold text-blue-700">{d.percentual.toFixed(1)}%</span>
                                      </div>
                                      <div className="flex justify-between items-center">
                                        <span className="text-sm text-gray-600">Impacto no lucro:</span>
                                        <span className="font-bold text-orange-700">{d.impacto_lucro.toFixed(1)}%</span>
                                      </div>
                                    </div>
                                    <div className="mt-3 pt-3 border-t border-gray-200">
                                      <p className="text-sm font-semibold text-gray-700 mb-1">
                                        Tendência: {d.tendencia === 'alta' ? '📈 Aumentando' : d.tendencia === 'baixa' ? '📉 Diminuindo' : '➡️ Estável'}
                                      </p>
                                      <p className="text-xs text-gray-600">
                                        {d.tendencia === 'alta' ? '⚠️ Esta despesa está crescendo. Fique atento!' : 
                                         d.tendencia === 'baixa' ? '✅ Ótimo! Esta despesa está diminuindo.' : 
                                         '✓ Esta despesa está controlada.'}
                                      </p>
                                    </div>
                                  </div>
                                );
                              }
                              return null;
                            }}
                          />
                          <Bar
                            dataKey="valor"
                            name="Valor"
                            onClick={(data, index) => setSelectedExpenseIndex(selectedExpenseIndex === index ? null : index)}
                          >
                            {[...analise_financeira.despesas_detalhadas]
                              .sort((a, b) => b.valor - a.valor)
                              .map((entry, index) => (
                                <Cell
                                  key={`cell-bar-${index}`}
                                  fill={getDistinctColor(index)}
                                  opacity={selectedExpenseIndex === null || selectedExpenseIndex === index ? 1 : 0.35}
                                />
                              ))}
                            <LabelList
                              dataKey="percentual"
                              formatter={(v: number) => `${v.toFixed(1)}%`}
                              position="right"
                              style={{ fill: '#374151', fontSize: 11, fontWeight: 600 }}
                            />
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    ) : (
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
                                  <div className="bg-white p-4 shadow-2xl rounded-lg border-2 border-gray-300 z-50 max-w-xs">
                                    <p className="font-bold text-gray-900 text-base mb-2">{data.tipo}</p>
                                    <div className="space-y-2">
                                      <div className="flex justify-between items-center">
                                        <span className="text-sm text-gray-600">Valor gasto:</span>
                                        <span className="font-bold text-red-700">R$ {data.valor.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                                      </div>
                                      <div className="flex justify-between items-center">
                                        <span className="text-sm text-gray-600">% do total:</span>
                                        <span className="font-bold text-blue-700">{data.percentual.toFixed(1)}%</span>
                                      </div>
                                      <div className="flex justify-between items-center">
                                        <span className="text-sm text-gray-600">Impacto no lucro:</span>
                                        <span className="font-bold text-orange-700">{data.impacto_lucro.toFixed(1)}%</span>
                                      </div>
                                    </div>
                                    <div className="mt-3 pt-3 border-t border-gray-200">
                                      <p className="text-sm font-semibold text-gray-700 mb-1">
                                        Tendência: {data.tendencia === 'alta' ? '📈 Aumentando' : data.tendencia === 'baixa' ? '📉 Diminuindo' : '➡️ Estável'}
                                      </p>
                                      <p className="text-xs text-gray-600">
                                        {data.tendencia === 'alta' ? '⚠️ Esta despesa está crescendo. Fique atento!' : 
                                         data.tendencia === 'baixa' ? '✅ Ótimo! Esta despesa está diminuindo.' : 
                                         '✓ Esta despesa está controlada.'}
                                      </p>
                                    </div>
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
                    )
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
                {selectedExpenseIndex !== null && analise_financeira?.despesas_detalhadas?.length > 0 && (
                  <div className="mt-4 p-4 bg-indigo-50 rounded-lg border border-indigo-200">
                    <p className="text-sm text-indigo-900 font-semibold mb-1">Detalhe destacado</p>
                    {(() => {
                      const d = [...analise_financeira.despesas_detalhadas].sort((a, b) => b.valor - a.valor)[selectedExpenseIndex!];
                      return (
                        <div className="text-sm text-indigo-800">
                          <span className="font-bold">{d.tipo}</span>: R$ {d.valor.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} • {d.percentual.toFixed(1)}% • Impacto no lucro: {d.impacto_lucro.toFixed(1)}% • Tendência: {d.tendencia === 'alta' ? '📈 Alta' : d.tendencia === 'baixa' ? '📉 Baixa' : '➡️ Estável'}
                        </div>
                      );
                    })()}
                  </div>
                )}
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
                    <div 
                      key={idx} 
                      className="bg-gray-900/50 p-4 rounded-lg hover:bg-gray-900 transition-all cursor-pointer group border border-transparent hover:border-gray-700"
                      onClick={() => {
                        setSelectedCorrelation(corr);
                        setIsCorrelationModalOpen(true);
                      }}
                    >
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-gray-300 font-medium group-hover:text-white transition-colors">{corr.variavel1} × {corr.variavel2}</span>
                        <span className={`px-3 py-1 rounded-full text-sm font-bold ${Math.abs(corr.correlacao) > 0.7 ? 'bg-red-500/20 text-red-300' :
                            Math.abs(corr.correlacao) > 0.4 ? 'bg-yellow-500/20 text-yellow-300' :
                              'bg-green-500/20 text-green-300'
                          }`}>
                          r = {corr.correlacao.toFixed(2)}
                        </span>
                      </div>
                      <p className="text-gray-400 text-sm mb-2 group-hover:text-gray-300">{corr.insight}</p>
                      <div className="flex justify-between text-xs text-gray-500">
                        <span>Significância: p = {corr.significancia.toFixed(3)}</span>
                        <span>{Math.abs(corr.correlacao) > 0.7 ? '🔴 Forte' : Math.abs(corr.correlacao) > 0.4 ? '🟡 Moderada' : '🟢 Fraca'}</span>
                      </div>
                      <div className="mt-2 text-center text-xs text-blue-400 opacity-0 group-hover:opacity-100 transition-opacity font-medium">
                        Clique para ver análise detalhada
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
                      <div
                        key={idx}
                        className="bg-black/30 p-4 rounded-lg hover:bg-black/40 transition-all cursor-pointer group border border-transparent hover:border-purple-700/40"
                        onClick={() => {
                          setSelectedRecommendation(rec);
                          setIsRecommendationModalOpen(true);
                        }}
                      >
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
                        <div className="flex items-center gap-3">
                          <span className="text-gray-400 text-sm">Impacto:</span>
                          <div className="flex-1 h-2 bg-white/10 rounded-full overflow-hidden">
                            <div
                              className="h-2 bg-green-400 rounded-full transition-all"
                              style={{ width: `${Math.min(100, Math.max(0, rec.impacto_esperado))}%` }}
                            />
                          </div>
                          <span className="text-green-300 text-sm font-bold">+{(typeof rec.impacto_esperado === 'number' ? rec.impacto_esperado.toFixed(1) : '0.0')}%</span>
                        </div>
                        {Array.isArray(rec.acoes_detalhadas) && rec.acoes_detalhadas.length > 0 && (
                          <div className="mt-3 text-xs text-gray-400">
                            <span className="font-semibold text-gray-300">Passos:</span> {rec.acoes_detalhadas[0]}
                          </div>
                        )}
                        <div className="mt-2 text-center text-xs text-blue-400 opacity-0 group-hover:opacity-100 transition-opacity font-medium">
                          Clique para ver gráficos e plano de ação detalhado
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

      {/* MODAL DE CORRELAÇÃO */}
      <CorrelationDetailsModal 
        isOpen={isCorrelationModalOpen} 
        onClose={() => setIsCorrelationModalOpen(false)} 
        correlation={selectedCorrelation} 
      />
       {/* MODAL DE RECOMENDAÇÃO */}
       <RecommendationDetailsModal
         isOpen={isRecommendationModalOpen}
         onClose={() => setIsRecommendationModalOpen(false)}
         recommendation={selectedRecommendation}
       />
    </div>
  );
};

export default DashboardPage;
