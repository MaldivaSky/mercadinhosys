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
  Tooltip, ResponsiveContainer, LineChart, Line, Cell
} from 'recharts';

// API Client
import { apiClient } from '../../api/apiClient';

// TIPOS CIENT├ìFICOS
type ProdutoPrevisao = {
  produto_nome?: string;
  nome?: string;
  estoque_atual: number;
  demanda_diaria_prevista: number;
  risco_ruptura?: boolean;
  margem_lucro?: number;
  custo_estoque?: number;
  giro_estoque?: number;
  classifica├º├úo_abc?: string;
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
  estoque_atual: number;
  margem: number;
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
  correla├º├Áes: Array<{
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
      
      console.log('­ƒöì Backend Response:', response.data);
      
      // ­ƒöÑ MAPEAR ESTRUTURA DO BACKEND PARA O FORMATO ESPERADO PELO FRONTEND
      const backendData = response.data.data;
      
      // Calcular despesas totais
      const totalDespesas = Array.isArray(backendData?.expenses) 
        ? backendData.expenses.reduce((sum: number, exp: any) => sum + (exp.valor || 0), 0) 
        : 0;
      
      // Calcular lucro bruto
      const totalVendas = backendData?.summary?.revenue?.value || 0;
      const custoEstoque = backendData?.inventory?.custo_total || 0;
      const lucroBruto = totalVendas - totalDespesas;
      
      // Calcular margem de lucro
      const margemLucro = totalVendas > 0 ? (lucroBruto / totalVendas) * 100 : 0;
      
      // Calcular ROI
      const roiMensal = custoEstoque > 0 ? (lucroBruto / custoEstoque) * 100 : 0;
      
      // Mapear produtos da curva ABC para produtos_estrela
      const produtosEstrela = backendData?.produtos_estrela || backendData?.abc?.produtos
        ?.filter((p: any) => p.classificacao === 'A')
        ?.slice(0, 10)
        ?.map((p: any) => ({
          id: p.id,
          nome: p.nome,
          classificacao: p.classificacao || 'A',
          margem: p.margem || 0,
          market_share: p.market_share || 0,
          total_vendido: p.total_vendido || p.quantidade_vendida || 0,
          custo_unitario: p.custo_unitario || p.preco_custo || 0,
          preco_venda: p.preco_venda || 0,
          lucro_total: p.lucro_total || p.faturamento || 0,
          roi: p.roi || 0,
          elasticidade: p.elasticidade || 0,
          faturamento: p.faturamento || 0,
          quantidade_vendida: p.quantidade_vendida || p.total_vendido || 0
        })) || [];
      
      // ­ƒöÑ FOR├çAR GERA├ç├âO DE PRODUTOS LENTOS SEMPRE
      let produtosLentos = [];
      
      // Sempre gerar produtos lentos a partir da Classe C
      if (backendData?.abc?.produtos && backendData.abc.produtos.length > 0) {
        const produtosClasseC = backendData.abc.produtos
          .filter((p: any) => p.classificacao === 'C')
          .sort((a: any, b: any) => (a.quantidade_vendida || 0) - (b.quantidade_vendida || 0))
          .slice(0, 10);
        
        produtosLentos = produtosClasseC.map((p: any) => ({
          id: p.id,
          nome: p.nome,
          quantidade: p.quantidade_vendida || 0,
          total_vendido: p.faturamento || 0,
          dias_estoque: 0,
          giro_estoque: p.quantidade_vendida > 0 ? (p.faturamento / p.quantidade_vendida) : 0,
          custo_parado: (p.preco_custo || 0) * (p.quantidade_vendida || 0),
          perda_mensal: 0,
          classificacao: 'C',
          margem: p.margem || 0
        }));
      }
      
      // Se o backend retornou produtos lentos, usar eles
      if (backendData?.produtos_lentos && backendData.produtos_lentos.length > 0) {
        produtosLentos = backendData.produtos_lentos;
      }
      
      // Mapear previs├úo de demanda
      const previsaoDemanda = backendData?.previsao_demanda || [];
      
      // Mapear timeseries para formato correto
      const timeseriesFormatted = Array.isArray(backendData?.timeseries)
        ? backendData.timeseries.map((item: any) => ({
            data: item.data || item.date || '',
            vendas: item.total || item.vendas || 0,
            quantidade: item.quantidade || 0,
            ticket_medio: item.ticket_medio || 0,
            previsao: null
          }))
        : [];
      
      // ­ƒöÑ GERAR SAZONALIDADE a partir do trend
      const sazonalidadeData = [];
      if (backendData?.trend?.best_day && backendData?.trend?.worst_day) {
        const melhorDia = backendData.trend.best_day;
        const piorDia = backendData.trend.worst_day;
        const variacaoSemanal = melhorDia.avg_sales > 0 
          ? ((melhorDia.avg_sales - piorDia.avg_sales) / piorDia.avg_sales) * 100 
          : 0;
        
        sazonalidadeData.push({
          periodo: "Padr├úo Semanal",
          variacao: variacaoSemanal,
          descricao: `Melhor dia: ${melhorDia.day} (R$ ${melhorDia.avg_sales.toFixed(0)}). Pior dia: ${piorDia.day} (R$ ${piorDia.avg_sales.toFixed(0)})`
        });
      }
      
      if (backendData?.trend?.trend) {
        const trendText = backendData.trend.trend === 'up' ? 'Crescimento' : 
                         backendData.trend.trend === 'down' ? 'Queda' : 'Est├ível';
        const growthPercent = backendData.trend.growth_percent || 0;
        
        sazonalidadeData.push({
          periodo: "Tend├¬ncia Geral",
          variacao: growthPercent,
          descricao: `${trendText} de ${Math.abs(growthPercent).toFixed(1)}% no per├¡odo analisado`
        });
      }
      
      // ­ƒöÑ GERAR COMPARA├ç├âO MENSAL a partir do timeseries
      const comparacaoMensal = [];
      if (Array.isArray(backendData?.timeseries) && backendData.timeseries.length >= 30) {
        // Agrupar por m├¬s
        const vendasPorMes: Record<string, number[]> = {};
        backendData.timeseries.forEach((item: any) => {
          if (item.data && item.total) {
            const mesAno = item.data.substring(0, 7); // "2026-02"
            if (!vendasPorMes[mesAno]) vendasPorMes[mesAno] = [];
            vendasPorMes[mesAno].push(item.total);
          }
        });
        
        // Calcular totais por m├¬s
        const meses = Object.keys(vendasPorMes).sort();
        const mesesNomes = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
        
        for (let i = 0; i < meses.length; i++) {
          const mesAtual = meses[i];
          const totalAtual = vendasPorMes[mesAtual].reduce((a, b) => a + b, 0);
          const mesAnterior = i > 0 ? meses[i - 1] : null;
          const totalAnterior = mesAnterior ? vendasPorMes[mesAnterior].reduce((a, b) => a + b, 0) : totalAtual;
          
          const crescimento = totalAnterior > 0 ? ((totalAtual - totalAnterior) / totalAnterior) * 100 : 0;
          const mesNumero = parseInt(mesAtual.split('-')[1]);
          const mesNome = mesesNomes[mesNumero - 1];
          
          comparacaoMensal.push({
            mes: mesNome,
            vendas: totalAtual,
            meta: totalAtual * 1.1, // Meta = 10% acima das vendas
            crescimento: crescimento
          });
        }
      }
      
      // Mapear forecast CORRETAMENTE
      const forecastFormatted = Array.isArray(backendData?.forecast)
        ? backendData.forecast.map((item: any, idx: number) => ({
            dia: item.data || `Dia ${idx + 1}`,
            previsao: item.valor_previsto || item.value || item.previsao || 0,
            intervalo_confianca: item.confianca === 'alta' ? 3.0 : item.confianca === 'media' ? 5.0 : 10.0
          }))
        : [];
      
      const mappedData = {
        ...response.data,
        data: {
          hoje: {
            data: new Date().toISOString(),
            total_vendas: totalVendas,
            quantidade_vendas: backendData?.summary?.revenue?.sample_size || 0,
            ticket_medio: backendData?.summary?.avg_ticket?.value || 0,
            clientes_atendidos: backendData?.summary?.unique_customers || 0,
            crescimento_vs_ontem: backendData?.summary?.growth?.value || 0,
            meta_atingida: 0,
            vendas_por_forma_pagamento: {},
            custo_vendas: custoEstoque,
            lucro_liquido: lucroBruto,
            margem_diaria: margemLucro
          },
          mes: {
            total_vendas: totalVendas,
            total_despesas: totalDespesas,
            lucro_bruto: lucroBruto,
            margem_lucro: margemLucro,
            crescimento_mensal: backendData?.summary?.growth?.value || 0,
            despesas_por_tipo: {},
            custo_produtos_vendidos: custoEstoque,
            investimentos: custoEstoque,
            roi_mensal: roiMensal
          },
          analise_produtos: {
            curva_abc: backendData?.abc || { produtos: [], resumo: { A: { quantidade: 0, faturamento_total: 0, percentual: 0 }, B: { quantidade: 0, faturamento_total: 0, percentual: 0 }, C: { quantidade: 0, faturamento_total: 0, percentual: 0 } }, pareto_80_20: false },
            produtos_estrela: produtosEstrela,
            produtos_lentos: produtosLentos,
            previsao_demanda: previsaoDemanda,
            produtos_margem: []
          },
          analise_financeira: {
            despesas_detalhadas: backendData?.expenses || [],
            investimentos: {
              marketing: 0,
              estoque: custoEstoque,
              infraestrutura: 0,
              total: custoEstoque,
              roi_esperado: roiMensal
            },
            margens: {
              bruta: margemLucro,
              operacional: margemLucro * 0.8,
              liquida: margemLucro,
              contribuicao: margemLucro * 1.2
            },
            indicadores: {
              ponto_equilibrio: totalDespesas,
              margem_seguranca: totalVendas > 0 ? ((totalVendas - totalDespesas) / totalVendas) * 100 : 0,
              alavancagem_operacional: 1.5,
              ebitda: lucroBruto
            }
          },
          analise_temporal: {
            vendas_por_hora: [],
            vendas_por_categoria: [],
            tendencia_vendas: timeseriesFormatted,
            sazonalidade: sazonalidadeData,
            comparacao_meses: comparacaoMensal,
            previsao_proxima_semana: forecastFormatted
          },
          insights_cientificos: {
            correla├º├Áes: backendData?.correlations || [],
            anomalias: backendData?.anomalies || [],
            previsoes: backendData?.previsao_demanda || [],
            recomendacoes_otimizacao: (backendData?.recomendacoes && backendData.recomendacoes.length > 0) 
              ? backendData.recomendacoes.map((rec: any) => ({
                  area: rec.tipo || rec.area || 'Geral',
                  acao: rec.mensagem || rec.acao || '',
                  impacto_esperado: rec.impacto_esperado || 10,
                  complexidade: rec.complexidade || 'media'
                }))
              : [
                  {
                    area: 'Estoque',
                    acao: 'Revisar produtos com baixo giro e considerar promo├º├Áes para liberar capital',
                    impacto_esperado: 15,
                    complexidade: 'baixa'
                  },
                  {
                    area: 'Vendas',
                    acao: 'Focar nos produtos Classe A que representam 80% do faturamento',
                    impacto_esperado: 25,
                    complexidade: 'baixa'
                  },
                  {
                    area: 'Margem',
                    acao: 'Analisar produtos com margem abaixo de 20% e ajustar precifica├º├úo',
                    impacto_esperado: 18,
                    complexidade: 'media'
                  }
                ]
          },
          alertas_cientificos: []
        }
      };
      
      console.log('Ô£à Mapped Data:', mappedData);
      console.log('­ƒöì Backend Raw Data:', backendData);
      console.log('­ƒöì Produtos Lentos (backend):', backendData?.produtos_lentos);
      console.log('­ƒöì Produtos Lentos (mapped):', produtosLentos);
      console.log('­ƒöì Recomenda├º├Áes (backend):', backendData?.recomendacoes);
      console.log('­ƒöì Sazonalidade:', sazonalidadeData);
      console.log('­ƒöì Compara├º├úo Mensal:', comparacaoMensal);
      console.log('­ƒöì ABC Analysis:', backendData?.abc);
      setData(mappedData);
    } catch (err) {
      console.error('ÔØî Dashboard Error:', err);
      setError('Erro ao carregar dados cient├¡ficos');
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

  // FILTRAR PRODUTOS DA CURVA ABC BASEADO NA SELE├ç├âO
  const produtosFiltrados = useMemo(() => {
    if (!data?.data?.analise_produtos?.curva_abc?.produtos) return [];
    
    const todosProdutos = data.data.analise_produtos.curva_abc.produtos;
    
    if (selectedABC === 'all') {
      // Quando "TODOS" est├í selecionado, pegar uma AMOSTRA de cada classe
      const produtosA = todosProdutos.filter((p: any) => p.classificacao === 'A');
      const produtosB = todosProdutos.filter((p: any) => p.classificacao === 'B');
      const produtosC = todosProdutos.filter((p: any) => p.classificacao === 'C');
      
      // Pegar 5 de cada classe para mostrar diversidade
      const amostraA = produtosA.slice(0, 5);
      const amostraB = produtosB.slice(0, 5);
      const amostraC = produtosC.slice(0, 5);
      
      // Combinar as amostras
      return [...amostraA, ...amostraB, ...amostraC];
    }
    
    return todosProdutos.filter(
      (p: any) => p.classificacao === selectedABC
    );
  }, [data?.data?.analise_produtos?.curva_abc?.produtos, selectedABC]);

  if (loading) return (
    <div className="flex items-center justify-center h-screen">
      <div className="text-center">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-4 text-lg font-semibold text-gray-700">Carregando An├ílise Cient├¡fica...</p>
        <p className="text-gray-500">Processando dados estat├¡sticos e modelos preditivos</p>
      </div>
    </div>
  );

  if (error || !data) return (
    <div className="p-8 bg-red-50 rounded-xl">
      <div className="flex items-center gap-3 text-red-700 mb-4">
        <AlertTriangle className="w-8 h-8" />
        <h2 className="text-2xl font-bold">Erro na An├ílise Cient├¡fica</h2>
      </div>
      <p className="text-red-600 mb-4">{error || 'Dados n├úo dispon├¡veis'}</p>
      <button onClick={loadDashboard} className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2">
        <RefreshCw className="w-4 h-4" />
        Tentar Novamente
      </button>
    </div>
  );

  const { hoje, mes, analise_produtos, analise_financeira, insights_cientificos = {
    correla├º├Áes: [],
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
      {/* HEADER CIENT├ìFICO */}
      <div className="mb-6">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-3xl md:text-4xl font-bold text-gray-900">Dashboard Executivo</h1>
            <p className="text-gray-600 mt-1">
              An├ílise completa do seu neg├│cio ÔÇó {new Date().toLocaleDateString('pt-BR')}
            </p>
          </div>
          <div className="flex gap-3">
            <select
              className="px-4 py-2 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 font-medium"
              value={viewMode}
              onChange={(e) => setViewMode(e.target.value as any)}
            >
              <option value="visao-geral">­ƒôè Vis├úo Geral</option>
              <option value="detalhado">­ƒôê An├ílise Detalhada</option>
              <option value="cientifico">­ƒö¼ Modo Avan├ºado</option>
            </select>
            <button onClick={loadDashboard} className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2 transition-colors">
              <RefreshCw className="w-4 h-4" />
              Atualizar
            </button>
          </div>
        </div>
      </div>

      {/* KPIs PRINCIPAIS - SIMPLIFICADOS */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {[
          {
            title: 'Faturamento',
            value: `R$ ${(mes?.total_vendas || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`,
            change: hoje?.crescimento_vs_ontem || 0,
            icon: DollarIcon,
            color: 'from-green-500 to-emerald-600',
            subtitle: `${mes?.margem_lucro?.toFixed(1) || 0}% de margem`
          },
          {
            title: 'Lucro L├¡quido',
            value: `R$ ${(mes?.lucro_bruto || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`,
            change: 5.2,
            icon: TrendingUpFill,
            color: 'from-blue-500 to-cyan-600',
            subtitle: `ROI: ${(mes?.roi_mensal || 0).toFixed(1)}%`
          },
          {
            title: 'Ticket M├®dio',
            value: `R$ ${(hoje?.ticket_medio || 0).toFixed(2)}`,
            change: 8.7,
            icon: TrendingUp,
            color: 'from-purple-500 to-pink-600',
            subtitle: `${hoje?.clientes_atendidos || 0} clientes`
          },
          {
            title: 'Despesas',
            value: `R$ ${(mes?.total_despesas || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`,
            change: -2.3,
            icon: AlertCircle,
            color: 'from-orange-500 to-red-600',
            subtitle: `${(((mes?.total_despesas || 0) / (mes?.total_vendas || 1)) * 100).toFixed(1)}% do faturamento`
          }
        ].map((kpi, idx) => (
          <div
            key={idx}
            className={`bg-gradient-to-br ${kpi.color} rounded-xl shadow-lg p-6 text-white transform transition-all duration-300 hover:scale-105 hover:shadow-xl`}
          >
            <div className="flex justify-between items-start mb-4">
              <kpi.icon className="w-8 h-8 opacity-80" />
              <div className={`flex items-center px-2 py-1 rounded-full text-xs font-bold ${kpi.change >= 0 ? 'bg-white/20' : 'bg-black/20'}`}>
                {kpi.change >= 0 ? <ArrowUpRight className="w-3 h-3 mr-1" /> : <ArrowDownRight className="w-3 h-3 mr-1" />}
                {Math.abs(kpi.change).toFixed(1)}%
              </div>
            </div>
            
            <p className="text-sm opacity-80 mb-1">{kpi.title}</p>
            <p className="text-3xl font-bold mb-2">{kpi.value}</p>
            <p className="text-sm opacity-90">{kpi.subtitle}</p>
          </div>
        ))}
      </div>

      {/* SE├ç├âO PRINCIPAL: CURVA ABC COM GR├üFICO DE PARETO */}
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
              <p className="text-gray-600">An├ílise 80/20 dos produtos ÔÇó {analise_produtos?.curva_abc?.pareto_80_20 ? 'Ô£à Lei de Pareto Confirmada' : 'ÔÜá´©Å Distribui├º├úo At├¡pica'}</p>
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
            {produtosFiltrados.length > 0 ? (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* GR├üFICO DE PARETO */}
              <div className="lg:col-span-2">
                <div className="h-[400px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={produtosFiltrados.slice(0, 15)}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="nome" angle={-45} textAnchor="end" height={80} />
                      <YAxis />
                      <Tooltip
                        content={({ payload, label }) => (
                          <div className="bg-white p-4 shadow-xl rounded-lg border border-gray-200">
                            <p className="font-bold text-gray-900">{label}</p>
                            <p className="text-sm text-gray-600">Faturamento: R$ {payload?.[0]?.value?.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
                            <p className="text-sm text-gray-600">Classifica├º├úo: <span className={`font-bold`} style={{ color: getABCColor(payload?.[0]?.payload?.classificacao) }}>{payload?.[0]?.payload?.classificacao}</span></p>
                            <p className="text-sm text-gray-600">Margem: {(payload?.[0]?.payload?.margem || 0).toFixed(1)}%</p>
                            <p className="text-sm text-gray-600">Qtd Vendida: {payload?.[0]?.payload?.quantidade_vendida}</p>
                            <p className="text-sm text-gray-600">% Acumulado: {(payload?.[0]?.payload?.percentual_acumulado || 0).toFixed(1)}%</p>
                          </div>
                        )}
                      />
                      <Bar
                        dataKey="faturamento"
                        name="Faturamento"
                      >
                        {produtosFiltrados.slice(0, 15).map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={getABCColor(entry.classificacao)} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <div className="flex justify-center gap-6 mt-6">
                  {Object.entries(analise_produtos?.curva_abc?.resumo || {}).map(([classe, dados]) => (
                    <div key={classe} className="text-center">
                      <div className={`w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-2 ${classe === 'A' ? 'bg-green-100' : classe === 'B' ? 'bg-yellow-100' : 'bg-red-100'}`}>
                        <span className={`text-2xl font-bold ${classe === 'A' ? 'text-green-600' : classe === 'B' ? 'text-yellow-600' : 'text-red-600'}`}>
                          {classe}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600">{dados.quantidade} produtos</p>
                      <p className="text-lg font-bold text-gray-900">{(dados?.percentual || 0).toFixed(1)}% do faturamento</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* LEGENDA E DETALHES */}
              <div className="space-y-6">
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-6 rounded-xl border border-blue-200">
                  <h3 className="font-bold text-gray-900 mb-4">­ƒôè Interpreta├º├úo da Curva ABC</h3>
                  <div className="space-y-3">
                    <div className="flex items-center gap-3">
                      <div className="w-3 h-3 rounded-full bg-green-500"></div>
                      <div>
                        <p className="font-semibold text-gray-900">Classe A (20% dos produtos)</p>
                        <p className="text-sm text-gray-600">Respons├íveis por {analise_produtos?.curva_abc?.resumo?.A?.percentual?.toFixed(1) || 0}% do faturamento</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                      <div>
                        <p className="font-semibold text-gray-900">Classe B (30% dos produtos)</p>
                        <p className="text-sm text-gray-600">Respons├íveis por {analise_produtos?.curva_abc?.resumo?.B?.percentual?.toFixed(1) || 0}% do faturamento</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-3 h-3 rounded-full bg-red-500"></div>
                      <div>
                        <p className="font-semibold text-gray-900">Classe C (50% dos produtos)</p>
                        <p className="text-sm text-gray-600">Respons├íveis por {analise_produtos?.curva_abc?.resumo?.C?.percentual?.toFixed(1) || 0}% do faturamento</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* TOP 5 PRODUTOS DA CLASSE SELECIONADA */}
                <div className="border border-gray-200 rounded-xl p-4">
                  <h4 className="font-bold text-gray-900 mb-3">
                    ­ƒÅå Top Produtos {selectedABC === 'all' ? 'Geral' : `Classe ${selectedABC}`}
                  </h4>
                  <div className="space-y-3">
                    {produtosFiltrados
                      ?.slice(0, 5)
                      ?.map((produto, idx) => (
                        <div
                          key={produto.id}
                          className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg cursor-pointer transition-colors"
                        >
                          <div className="flex items-center gap-3">
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${
                              produto.classificacao === 'A' ? 'bg-green-100 text-green-800' :
                              produto.classificacao === 'B' ? 'bg-yellow-100 text-yellow-800' :
                              'bg-red-100 text-red-800'
                            }`}>
                              {idx + 1}
                            </div>
                            <div>
                              <p className="font-medium text-gray-900">{produto.nome}</p>
                              <p className="text-xs text-gray-500">
                                Classe {produto.classificacao} ÔÇó Margem: {produto.margem.toFixed(1)}%
                              </p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className={`font-bold ${
                              produto.classificacao === 'A' ? 'text-green-600' :
                              produto.classificacao === 'B' ? 'text-yellow-600' :
                              'text-red-600'
                            }`}>
                              R$ {(produto?.faturamento || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            </p>
                            <p className="text-xs text-gray-500">{produto?.quantidade_vendida || 0} unidades</p>
                          </div>
                        </div>
                      ))}
                  </div>
                </div>
              </div>
            </div>
            ) : (
              <div className="flex items-center justify-center h-64">
                <div className="text-center">
                  <ChartBar className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-600 font-medium mb-2">
                    Nenhum produto encontrado na Classe {selectedABC}
                  </p>
                  <p className="text-gray-500 text-sm">
                    {selectedABC === 'C' 
                      ? 'Parab├®ns! Voc├¬ n├úo tem produtos de baixo desempenho (Classe C).'
                      : 'Selecione outra classe para visualizar os produtos.'}
                  </p>
                  <button
                    onClick={() => setSelectedABC('all')}
                    className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    Ver Todos os Produtos
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
      )}

      {/* SE├ç├âO: AN├üLISE TEMPORAL - TEND├èNCIA DE VENDAS */}
      {(viewMode === 'detalhado' || viewMode === 'cientifico') && (
      <div className="bg-white rounded-2xl shadow-xl mb-8 overflow-hidden border border-gray-200">
        <div
          className="p-6 border-b border-gray-200 flex justify-between items-center cursor-pointer hover:bg-gray-50"
          onClick={() => toggleCard('analise-temporal')}
        >
          <div className="flex items-center gap-3">
            <TrendingUp className="w-8 h-8 text-purple-600" />
            <div>
              <h2 className="text-2xl font-bold text-gray-900">An├ílise Temporal de Vendas</h2>
              <p className="text-gray-600">Tend├¬ncia ÔÇó Sazonalidade ÔÇó Previs├Áes ÔÇó Evolu├º├úo Mensal</p>
            </div>
          </div>
          <ChevronDown className={`w-6 h-6 text-gray-500 transform transition-transform ${expandedCards['analise-temporal'] ? 'rotate-180' : ''}`} />
        </div>

        {expandedCards['analise-temporal'] && (
          <div className="p-6 animate-fadeIn">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* GR├üFICO DE LINHA: EVOLU├ç├âO DAS VENDAS */}
              <div className="bg-gradient-to-br from-purple-50 to-white p-6 rounded-xl border border-purple-200">
                <h3 className="font-bold text-gray-900 mb-6 text-lg flex items-center gap-2">
                  <LineChartIcon className="w-5 h-5 text-purple-600" />
                  Evolu├º├úo das Vendas (30 dias)
                </h3>
                <div className="h-[300px]">
                  {analise_temporal?.tendencia_vendas?.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={analise_temporal?.tendencia_vendas || []}>
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
                          name="Vendas Di├írias"
                        />
                        <Line
                          type="monotone"
                          dataKey="previsao"
                          stroke="#ef4444"
                          strokeWidth={2}
                          strokeDasharray="5 5"
                          dot={false}
                          name="Previs├úo"
                          connectNulls={false}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex items-center justify-center h-full">
                      <div className="text-center">
                        <LineChartIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                        <p className="text-gray-500">Dados de tend├¬ncia n├úo dispon├¡veis</p>
                      </div>
                    </div>
                  )}
                </div>
                <div className="mt-4 grid grid-cols-3 gap-4 text-center">
                  <div className="bg-purple-50 p-3 rounded-lg">
                    <p className="text-sm text-purple-600 font-medium">Tend├¬ncia</p>
                    <p className={`text-lg font-bold ${analise_temporal?.tendencia_vendas?.length > 1 && (analise_temporal?.tendencia_vendas[analise_temporal?.tendencia_vendas.length - 1]?.vendas || 0) > (analise_temporal?.tendencia_vendas[analise_temporal?.tendencia_vendas.length - 2]?.vendas || 0) ? 'text-green-600' : 'text-red-600'}`}>
                      {analise_temporal?.tendencia_vendas?.length > 1 && (analise_temporal?.tendencia_vendas[analise_temporal?.tendencia_vendas.length - 1]?.vendas || 0) > (analise_temporal?.tendencia_vendas[analise_temporal?.tendencia_vendas.length - 2]?.vendas || 0) ? '­ƒôê Crescendo' : '­ƒôë Caindo'}
                    </p>
                  </div>
                  <div className="bg-blue-50 p-3 rounded-lg">
                    <p className="text-sm text-blue-600 font-medium">M├®dia 7 dias</p>
                    <p className="text-lg font-bold text-blue-700">
                      R$ {(analise_temporal?.tendencia_vendas?.slice(-7).reduce((acc, curr) => acc + (curr.vendas || 0), 0) / Math.max(1, Math.min(7, analise_temporal?.tendencia_vendas?.length || 0)))?.toLocaleString('pt-BR', { maximumFractionDigits: 0 }) || '0'}
                    </p>
                  </div>
                  <div className="bg-green-50 p-3 rounded-lg">
                    <p className="text-sm text-green-600 font-medium">Previs├úo Amanh├ú</p>
                    <p className="text-lg font-bold text-green-700">
                      R$ {(analise_temporal?.previsao_proxima_semana?.[0]?.previsao || 0).toLocaleString('pt-BR', { maximumFractionDigits: 0 })}
                    </p>
                  </div>
                </div>
              </div>

              {/* M├ëTRICAS DE SAZONALIDADE E PREVIS├òES */}
              <div className="space-y-6">
                {/* SAZONALIDADE */}
                <div className="bg-gradient-to-r from-indigo-50 to-purple-50 p-6 rounded-xl border border-indigo-200">
                  <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                    <Calendar className="w-5 h-5 text-indigo-600" />
                    Padr├Áes Sazonais
                  </h3>
                  <div className="space-y-3">
                    {analise_temporal?.sazonalidade && analise_temporal?.sazonalidade.length > 0 ? (
                      analise_temporal?.sazonalidade.map((padrao, idx) => (
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
                        <p className="text-gray-500">Dados insuficientes para an├ílise sazonal</p>
                        <p className="text-sm text-gray-400 mt-1">Necess├írio pelo menos 3 meses de hist├│rico</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* PREVIS├âO PR├ôXIMA SEMANA */}
                <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-6 rounded-xl border border-green-200">
                  <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                    <TargetIcon className="w-5 h-5 text-green-600" />
                    Previs├úo Pr├│xima Semana
                  </h3>
                  <div className="space-y-3">
                    {analise_temporal?.previsao_proxima_semana && analise_temporal?.previsao_proxima_semana.length > 0 ? (
                      analise_temporal?.previsao_proxima_semana.map((prev, idx) => (
                        <div key={idx} className="bg-white/70 p-4 rounded-lg">
                          <div className="flex justify-between items-center">
                            <span className="font-medium text-gray-900">{prev?.dia || `Dia ${idx + 1}`}</span>
                            <div className="text-right">
                              <p className="font-bold text-green-700">R$ {(prev?.previsao || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
                              <p className="text-xs text-gray-500">┬▒{prev?.intervalo_confianca?.toFixed(1) || '5.0'}%</p>
                            </div>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="bg-white/70 p-6 rounded-lg text-center">
                        <TargetIcon className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                        <p className="text-gray-500">Previs├Áes n├úo dispon├¡veis</p>
                        <p className="text-sm text-gray-400 mt-1">Necess├írio mais dados hist├│ricos</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* COMPARA├ç├âO MENSAL */}
                <div className="bg-gradient-to-r from-orange-50 to-red-50 p-6 rounded-xl border border-orange-200">
                  <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                    <LucideBarChart className="w-5 h-5 text-orange-600" />
                    Compara├º├úo Mensal
                  </h3>
                  <div className="space-y-3">
                    {analise_temporal?.comparacao_meses && analise_temporal?.comparacao_meses.length > 0 ? (
                      analise_temporal?.comparacao_meses.map((comp, idx) => (
                        <div key={idx} className="bg-white/70 p-4 rounded-lg">
                          <div className="flex justify-between items-center mb-2">
                            <span className="font-medium text-gray-900">{comp.mes}</span>
                            <span className={`px-2 py-1 rounded-full text-xs font-bold ${comp.crescimento > 0 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                              {comp.crescimento > 0 ? '+' : ''}{comp.crescimento.toFixed(1)}%
                            </span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-600">Vendas: R$ {(comp?.vendas || 0).toLocaleString('pt-BR')}</span>
                            <span className="text-gray-600">Meta: R$ {(comp?.meta || 0).toLocaleString('pt-BR')}</span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="bg-white/70 p-6 rounded-lg text-center">
                        <LucideBarChart className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                        <p className="text-gray-500">Compara├º├úo mensal n├úo dispon├¡vel</p>
                        <p className="text-sm text-gray-400 mt-1">Necess├írio pelo menos 2 meses de dados</p>
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

      {/* SE├ç├âO: AN├üLISE FINANCEIRA DETALHADA */}
      {(viewMode === 'detalhado' || viewMode === 'cientifico') && (
      <div className="bg-white rounded-2xl shadow-xl mb-8 overflow-hidden border border-gray-200">
        <div
          className="p-6 border-b border-gray-200 flex justify-between items-center cursor-pointer hover:bg-gray-50"
          onClick={() => toggleCard('analise-financeira')}
        >
          <div className="flex items-center gap-3">
            <DollarIcon className="w-8 h-8 text-green-600" />
            <div>
              <h2 className="text-2xl font-bold text-gray-900">An├ílise Financeira Cient├¡fica</h2>
              <p className="text-gray-600">Despesas vs Lucro ÔÇó Margens ÔÇó Indicadores de Performance</p>
            </div>
          </div>
          <ChevronDown className={`w-6 h-6 text-gray-500 transform transition-transform ${expandedCards['analise-financeira'] ? 'rotate-180' : ''}`} />
        </div>

        {expandedCards['analise-financeira'] && (
          <div className="p-6 animate-fadeIn">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* GR├üFICO DE COLUNAS: DISTRIBUI├ç├âO DE DESPESAS */}
              <div className="bg-gradient-to-br from-gray-50 to-white p-6 rounded-xl border border-gray-200">
                <h3 className="font-bold text-gray-900 mb-6 text-lg">­ƒôè Distribui├º├úo de Despesas</h3>
                <div className="h-[300px]">
                  {analise_financeira?.despesas_detalhadas && analise_financeira?.despesas_detalhadas.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={analise_financeira?.despesas_detalhadas}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                        <XAxis 
                          dataKey="tipo" 
                          angle={-45} 
                          textAnchor="end" 
                          height={80}
                          tick={{ fontSize: 12 }}
                        />
                        <YAxis tick={{ fontSize: 12 }} />
                        <Tooltip
                          content={({ payload }) => (
                            <div className="bg-white p-4 shadow-xl rounded-lg border border-gray-200">
                              <p className="font-bold text-gray-900">{payload?.[0]?.payload?.tipo}</p>
                              <p className="text-gray-600">Valor: R$ {payload?.[0]?.value?.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
                              <p className="text-gray-600">Percentual: {payload?.[0]?.payload?.percentual?.toFixed(1)}%</p>
                              <p className="text-gray-600">Impacto no Lucro: {payload?.[0]?.payload?.impacto_lucro?.toFixed(1)}%</p>
                              <p className="text-sm text-gray-500 mt-2">
                                Tend├¬ncia: {payload?.[0]?.payload?.tendencia === 'alta' ? '­ƒôê Alta' : payload?.[0]?.payload?.tendencia === 'baixa' ? '­ƒôë Baixa' : 'Ô×í´©Å Est├ível'}
                              </p>
                            </div>
                          )}
                        />
                        <Bar dataKey="valor" name="Valor da Despesa">
                          {analise_financeira?.despesas_detalhadas?.map((entry, index) => (
                            <Cell 
                              key={`cell-${index}`} 
                              fill={COLORS[index % COLORS.length]}
                              className="cursor-pointer hover:opacity-80 transition-opacity"
                            />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex items-center justify-center h-full">
                      <div className="text-center">
                        <DollarIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                        <p className="text-gray-600 font-medium mb-2">Nenhuma despesa registrada no per├¡odo</p>
                        <p className="text-gray-500 text-sm">As despesas aparecer├úo aqui quando forem cadastradas no sistema</p>
                        <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                          <p className="text-sm text-blue-800">
                            ­ƒÆí <strong>Dica:</strong> Cadastre despesas para visualizar a distribui├º├úo e an├ílise financeira completa
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

              {/* M├ëTRICAS DE MARGEM */}
              <div className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  {Object.entries(analise_financeira?.margens || {}).map(([nome, valor]) => (
                    <div key={nome} className="bg-white border border-gray-200 rounded-xl p-4 hover:shadow-md transition-shadow">
                      <p className="text-sm text-gray-600 font-medium mb-2">
                        {nome === 'bruta' ? 'Margem Bruta' :
                          nome === 'operacional' ? 'Margem Operacional' :
                            nome === 'liquida' ? 'Margem L├¡quida' : 'Margem Contribui├º├úo'}
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

                {/* INDICADORES AVAN├çADOS */}
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-6 rounded-xl border border-blue-200">
                  <h4 className="font-bold text-gray-900 mb-4">­ƒôê Indicadores Financeiros</h4>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-700">Ponto de Equil├¡brio</span>
                      <span className="font-bold text-blue-600">{(analise_financeira?.indicadores?.ponto_equilibrio || 0).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-700">Margem de Seguran├ºa</span>
                      <span className="font-bold text-green-600">{(analise_financeira?.indicadores?.margem_seguranca || 0).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-700">Alavancagem Operacional</span>
                      <span className="font-bold text-purple-600">{(analise_financeira?.indicadores?.alavancagem_operacional || 0).toFixed(2)}x</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-700">EBITDA</span>
                      <span className="font-bold text-green-700">R$ {(analise_financeira?.indicadores?.ebitda || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
      )}

      {/* SE├ç├âO: INSIGHTS CIENT├ìFICOS */}
      {viewMode === 'cientifico' && (
      <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl shadow-2xl overflow-hidden mb-8">
        <div
          className="p-6 border-b border-gray-700 flex justify-between items-center cursor-pointer hover:bg-gray-800/50"
          onClick={() => toggleCard('insights')}
        >
          <div className="flex items-center gap-3">
            <Brain className="w-8 h-8 text-cyan-400" />
            <div>
              <h2 className="text-2xl font-bold text-white">­ƒºá Insights Cient├¡ficos</h2>
              <p className="text-gray-300">Correla├º├Áes ÔÇó Anomalias ÔÇó Previs├Áes ÔÇó Recomenda├º├Áes de Otimiza├º├úo</p>
            </div>
          </div>
          <ChevronDown className={`w-6 h-6 text-gray-400 transform transition-transform ${expandedCards['insights'] ? 'rotate-180' : ''}`} />
        </div>

        {expandedCards['insights'] && (
          <div className="p-6 animate-fadeIn">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* CORRELA├ç├òES */}
              <div className="bg-gray-800/50 rounded-xl p-6 backdrop-blur-sm">
                <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                  <GitMerge className="w-5 h-5" />
                  Correla├º├Áes Estat├¡sticas
                </h3>
                <div className="space-y-4">
                  {(insights_cientificos?.correla├º├Áes || []).map((corr, idx) => (
                    <div key={idx} className="bg-gray-900/50 p-4 rounded-lg hover:bg-gray-900 transition-colors">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-gray-300 font-medium">{corr.variavel1} ├ù {corr.variavel2}</span>
                        <span className={`px-3 py-1 rounded-full text-sm font-bold ${Math.abs(corr.correlacao) > 0.7 ? 'bg-red-500/20 text-red-300' :
                            Math.abs(corr.correlacao) > 0.4 ? 'bg-yellow-500/20 text-yellow-300' :
                              'bg-green-500/20 text-green-300'
                          }`}>
                          r = {corr.correlacao.toFixed(2)}
                        </span>
                      </div>
                      <p className="text-gray-400 text-sm mb-2">{corr.insight}</p>
                      <div className="flex justify-between text-xs text-gray-500">
                        <span>Signific├óncia: p = {corr.significancia.toFixed(3)}</span>
                        <span>{Math.abs(corr.correlacao) > 0.7 ? '­ƒö┤ Forte' : Math.abs(corr.correlacao) > 0.4 ? '­ƒƒí Moderada' : '­ƒƒó Fraca'}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* PREVIS├òES E RECOMENDA├ç├òES */}
              <div className="space-y-6">
                <div className="bg-gradient-to-r from-blue-900/30 to-cyan-900/30 rounded-xl p-6">
                  <h3 className="text-xl font-bold text-white mb-6">­ƒö« Previs├Áes (Pr├│ximos 30 dias)</h3>
                  <div className="space-y-4">
                    {(insights_cientificos?.previsoes || []).map((prev, idx) => (
                      <div key={idx} className="bg-black/30 p-4 rounded-lg">
                        <div className="flex justify-between items-center mb-3">
                          <span className="text-gray-300 font-medium">{prev.variavel}</span>
                          <span className="px-3 py-1 bg-blue-500/20 text-blue-300 rounded-full text-sm">
                            {prev.confianca.toFixed(1)}% confian├ºa
                          </span>
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="text-center">
                            <p className="text-sm text-gray-400">Atual</p>
                            <p className="text-xl font-bold text-white">R$ {(prev?.valor_atual || 0).toLocaleString('pt-BR')}</p>
                          </div>
                          <ArrowUpRight className="w-6 h-6 text-green-400" />
                          <div className="text-center">
                            <p className="text-sm text-gray-400">Previs├úo</p>
                            <p className="text-xl font-bold text-green-400">R$ {(prev?.previsao_30d || 0).toLocaleString('pt-BR')}</p>
                          </div>
                        </div>
                        <div className="mt-3 text-xs text-gray-400">
                          Intervalo: R$ {prev.intervalo_confianca[0].toLocaleString('pt-BR')} - R$ {prev.intervalo_confianca[1].toLocaleString('pt-BR')}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* RECOMENDA├ç├òES DE OTIMIZA├ç├âO */}
                <div className="bg-gradient-to-r from-purple-900/30 to-pink-900/30 rounded-xl p-6">
                  <h3 className="text-xl font-bold text-white mb-6">­ƒÜÇ Recomenda├º├Áes de Otimiza├º├úo</h3>
                  <div className="space-y-4">
                    {(insights_cientificos?.recomendacoes_otimizacao || []).map((rec, idx) => (
                      <div key={idx} className="bg-black/30 p-4 rounded-lg hover:bg-black/40 transition-colors cursor-pointer">
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-gray-300 font-medium">{rec.area}</span>
                          <span className={`px-3 py-1 rounded-full text-xs font-bold ${rec.complexidade === 'baixa' ? 'bg-green-500/30 text-green-300' :
                              rec.complexidade === 'media' ? 'bg-yellow-500/30 text-yellow-300' :
                                'bg-red-500/30 text-red-300'
                            }`}>
                            {rec.complexidade === 'baixa' ? '­ƒƒó F├ícil' : rec.complexidade === 'media' ? '­ƒƒí M├®dio' : '­ƒö┤ Complexo'}
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

      {/* SE├ç├âO: PRODUTOS ESTRAT├ëGICOS */}
      {viewMode === 'cientifico' && (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* PRODUTOS ESTRELA */}
        <div className="bg-gradient-to-br from-yellow-50 to-orange-50 rounded-2xl shadow-xl p-6 border border-yellow-200">
          <div className="flex items-center gap-3 mb-6">
            <Star className="w-8 h-8 text-yellow-600" />
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Ô¡É Produtos Estrela</h2>
              <p className="text-gray-600">Alta margem + Alta participa├º├úo + Alta rentabilidade</p>
            </div>
          </div>
          <div className="space-y-4">
            {analise_produtos?.produtos_estrela?.map((produto, idx) => (
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
                    <p className="text-sm text-gray-600">Ticket M├®dio</p>
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
              <h2 className="text-2xl font-bold text-gray-900">ÔÜá´©Å Produtos Lentos</h2>
              <p className="text-gray-600">Baixo giro + Alto custo de estoque + Oportunidade de melhoria</p>
            </div>
          </div>
          <div className="space-y-4">
            {analise_produtos?.produtos_lentos?.length > 0 ? (
              analise_produtos?.produtos_lentos?.map((produto, idx) => (
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
                        <p className="text-sm text-gray-600">Vendeu apenas {produto.quantidade} unidades</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-xl font-bold text-red-600">{produto.giro_estoque?.toFixed(2) || '0.00'}x</p>
                      <p className="text-sm text-gray-600">Giro</p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-3 mt-3">
                    <div className="bg-red-50 p-3 rounded-lg">
                      <p className="text-xs text-red-600 font-medium">Estoque Atual</p>
                      <p className="text-lg font-bold text-red-700">{produto.estoque_atual || 0} un</p>
                    </div>
                    <div className="bg-orange-50 p-3 rounded-lg">
                      <p className="text-xs text-orange-600 font-medium">Dias de Estoque</p>
                      <p className="text-lg font-bold text-orange-700">{produto.dias_estoque < 999 ? `${produto.dias_estoque} dias` : 'Ôê×'}</p>
                    </div>
                    <div className="bg-yellow-50 p-3 rounded-lg">
                      <p className="text-xs text-yellow-600 font-medium">Capital Parado</p>
                      <p className="text-lg font-bold text-yellow-700">R$ {(produto.custo_parado || 0).toFixed(2)}</p>
                    </div>
                    <div className="bg-pink-50 p-3 rounded-lg">
                      <p className="text-xs text-pink-600 font-medium">Perda Mensal</p>
                      <p className="text-lg font-bold text-pink-700">R$ {(produto.perda_mensal || 0).toFixed(2)}</p>
                    </div>
                  </div>
                  
                  <div className="mt-3 pt-3 border-t border-red-200">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Faturamento Total:</span>
                      <span className="font-bold text-gray-900">R$ {(produto.total_vendido || 0).toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-sm mt-1">
                      <span className="text-gray-600">Margem:</span>
                      <span className="font-bold text-green-600">{(produto.margem || 0).toFixed(1)}%</span>
                    </div>
                  </div>
                  
                  <div className="mt-3 bg-red-50 p-3 rounded-lg">
                    <p className="text-xs font-bold text-red-800 mb-1">­ƒÆí Recomenda├º├úo:</p>
                    <p className="text-xs text-red-700">
                      {produto.giro_estoque < 0.5 
                        ? 'Considere promo├º├úo agressiva ou descontinuar produto'
                        : produto.giro_estoque < 1.0
                        ? 'Fa├ºa promo├º├úo para acelerar vendas'
                        : 'Reduza reposi├º├úo e monitore de perto'}
                    </p>
                  </div>
                </div>
              ))
            ) : (
              <div className="bg-white/80 backdrop-blur-sm rounded-xl p-8 text-center border border-red-100">
                <Package className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 font-medium">Nenhum produto lento identificado</p>
                <p className="text-gray-500 text-sm">Todos os produtos est├úo com bom desempenho!</p>
              </div>
            )}
          </div>
        </div>
      </div>
      )}

      {/* SE├ç├âO: PREVIS├âO DE DEMANDA */}
      {viewMode === 'cientifico' && (
      <div className="bg-gradient-to-br from-purple-50 to-indigo-50 rounded-2xl shadow-xl p-6 mb-8 border border-purple-200">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-3">
          <Target className="w-8 h-8 text-purple-600" />
          ­ƒôè Previs├úo de Demanda Inteligente
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {analise_produtos?.previsao_demanda?.map((previsao, idx) => {
            // Calcular dias at├® acabar o estoque
            const estoqueAtual = previsao.estoque_atual || 0;
            const demandaDiaria = previsao.demanda_diaria_prevista || 0;
            const diasAteAcabar = demandaDiaria > 0 ? Math.floor(estoqueAtual / demandaDiaria) : 999;
            const riscoRuptura = diasAteAcabar < 7;
            
            return (
            <div key={idx} className={`bg-white/80 backdrop-blur-sm rounded-xl p-6 border ${riscoRuptura ? 'border-red-300 bg-red-50/50' : 'border-purple-100'}`}>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-gray-900">{previsao.nome || previsao.produto_nome || previsao.variavel}</h3>
                <div className="flex items-center gap-2">
                  {riscoRuptura && (
                    <span className="px-3 py-1 rounded-full text-xs font-bold bg-red-100 text-red-800">
                      ÔÜá´©Å Risco Ruptura
                    </span>
                  )}
                  <span className={`px-3 py-1 rounded-full text-xs font-bold ${previsao.confianca > 80 ? 'bg-green-100 text-green-800' : previsao.confianca > 60 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'}`}>
                    {previsao.confianca?.toFixed(0) || 75}% confian├ºa
                  </span>
                </div>
              </div>

              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Estoque Atual</span>
                  <span className={`font-bold ${riscoRuptura ? 'text-red-600' : 'text-gray-900'}`}>
                    {estoqueAtual} unidades
                  </span>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Demanda Di├íria</span>
                  <span className="font-bold text-purple-600">{demandaDiaria.toFixed(1)} un/dia</span>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Dias at├® Acabar</span>
                  <div className="flex items-center gap-2">
                    <span className={`font-bold text-xl ${diasAteAcabar < 7 ? 'text-red-600' : diasAteAcabar < 14 ? 'text-yellow-600' : 'text-green-600'}`}>
                      {diasAteAcabar < 999 ? `${diasAteAcabar} dias` : 'Ôê×'}
                    </span>
                    {diasAteAcabar < 7 && <AlertTriangle className="w-5 h-5 text-red-500" />}
                  </div>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Margem de Lucro</span>
                  <span className="font-bold text-green-600">{(previsao.margem_lucro || 0).toFixed(1)}%</span>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Classifica├º├úo ABC</span>
                  <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                    previsao.classifica├º├úo_abc === 'A' ? 'bg-green-100 text-green-800' :
                    previsao.classifica├º├úo_abc === 'B' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    Classe {previsao.classifica├º├úo_abc || 'C'}
                  </span>
                </div>

                {riscoRuptura && (
                  <div className="pt-4 border-t border-red-200 bg-red-50 p-3 rounded-lg">
                    <p className="text-sm font-bold text-red-800 mb-1">­ƒÜ¿ A├º├úo Urgente Necess├íria!</p>
                    <p className="text-xs text-red-700">
                      Estoque acabar├í em {diasAteAcabar} dias. Fa├ºa reposi├º├úo imediatamente para evitar ruptura.
                    </p>
                  </div>
                )}

                <div className="pt-4 border-t border-purple-200">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Previs├úo Vendas 30d</span>
                    <span className="font-bold text-purple-600">
                      R$ {(previsao.previsao_30d || 0).toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                    </span>
                  </div>
                </div>
              </div>
            </div>
            );
          })}
        </div>
      </div>
      )}
    </div>
  );
};

export default DashboardPage;
