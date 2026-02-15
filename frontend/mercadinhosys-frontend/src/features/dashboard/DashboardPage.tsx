// @ts-nocheck
import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  TrendingUp, Package, AlertTriangle, Star, Calendar, Target,
  ArrowUpRight, ArrowDownRight, ChevronDown, Cpu, Brain, Database,
  DollarSign as DollarIcon, Target as TargetIcon, AlertCircle,
  TrendingUp as TrendingUpFill, GitMerge, ChartBar, BarChart as LucideBarChart,
  LineChart as LineChartIcon, RefreshCw, X, Clock, Lightbulb, Users
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, LineChart, Line, Cell, AreaChart, Area, Legend
} from 'recharts';

// API Client
import { apiClient } from '../../api/apiClient';

// 🔥 RESTAURADO: Importar modais
import {
  AnomalyDetailsModal,
  CorrelationDetailsModal,
  RecommendationDetailsModal,
  ProdutoEstrelaModal,
  ProdutoLentoModal
} from './components/modals';

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

// 🔥 NOVO: Interface para Métricas de RH
interface RHMetrics {
  total_beneficios_mensal: number;
  total_salarios: number;
  custo_folha_estimado: number;
  funcionarios_ativos: number;
  total_entradas_periodo: number;
  total_atrasos_qtd: number;
  taxa_pontualidade: number;
  total_minutos_atraso: number;
  minutos_extras_estimados: number;
  custo_extras_estimado: number;
  turnover_rate?: number;
  admissoes_periodo?: number;
  demissoes_periodo?: number;
  evolution_turnover?: Array<{ mes: string; admissoes: number; demissoes: number; ausencias?: number; atrasos?: number; horas_extras?: number }>;
  benefits_breakdown?: Array<{ name: string; value: number }>;
  top_overtime_employees?: Array<{ nome: string; horas: number; custo_estimado: number }>;
  team_status_today?: Array<{ nome: string; cargo: string; status: string; ultimo_registro: string }>;
  recent_points?: Array<{ data: string; hora: string; tipo: string; funcionario: string }>;
  daily_ponto_summary?: Array<{ data: string; funcionario: string; entrada: string; saida: string; minutos_atraso: number; minutos_extras: number }>;
  overtime_trend?: Array<{ data: string; minutos_extras: number; custo_extras: number }>;
  atrasos_por_funcionario_mes?: Array<{ funcionario_id: number; nome: string; cargo: string; atrasos_qtd: number; minutos_atraso: number }>;
  horas_extras_por_funcionario_mes?: Array<{ funcionario_id: number; nome: string; cargo: string; minutos_extras: number; custo_extras: number }>;
  faltas_por_funcionario_mes?: Array<{ funcionario_id: number; nome: string; cargo: string; faltas: number; dias_uteis: number; dias_presenca: number }>;
  banco_horas_por_funcionario_mes?: Array<{ funcionario_id: number; nome: string; cargo: string; saldo_minutos: number; valor_hora_extra: number; horas_trabalhadas_minutos: number; horas_esperadas_minutos: number }>;
  espelho_pagamento_mes?: Array<{ funcionario_id: number; nome: string; cargo: string; salario_base: number; beneficios: number; horas_extras_horas: number; custo_horas_extras: number; atrasos_minutos: number; faltas: number; banco_horas_saldo_horas: number; total_estimado: number }>;
  resumo_mes?: { inicio: string | null; fim: string | null; dias_uteis: number; total_atrasos_minutos: number; total_atrasos_qtd: number; total_extras_minutos: number; total_faltas: number };
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
      produtos_por_hora: Record<number, Array<{
        produto_id: number;
        produto_nome: string;
        quantidade_vendida: number;
        faturamento: number;
      }>>;
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
    rh?: RHMetrics; // 🔥 NOVO: Dados de RH
  };
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
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
  const [viewMode, setViewMode] = useState<'visao-geral' | 'detalhado' | 'avancado' | 'rh'>('visao-geral'); // 🔥 Inicia em Visão Geral
  const [hoveredKPI, setHoveredKPI] = useState<number | null>(null);
  const [expandedKPI, setExpandedKPI] = useState<number | null>(null);

  // 🔥 NOVO: Filtro de período
  const [periodoDias, setPeriodoDias] = useState<number>(30);
  const [modoFiltro, setModoFiltro] = useState<'rapido' | 'personalizado'>('rapido');
  const [dataInicio, setDataInicio] = useState<string>('');
  const [dataFim, setDataFim] = useState<string>('');

  // 🔥 NOVO: Modal de KPI com gráfico
  const [kpiModalAberto, setKpiModalAberto] = useState<string | null>(null);
  const [visualizacaoModal, setVisualizacaoModal] = useState<'dias' | 'meses'>('dias');
  const [dadosHistoricoKPI, setDadosHistoricoKPI] = useState<any>(null);

  // 🔥 RESTAURADO: Estados para controlar modais
  const [selectedAnomaly, setSelectedAnomaly] = useState<any>(null);
  const [selectedCorrelation, setSelectedCorrelation] = useState<any>(null);
  const [selectedProduct, setSelectedProduct] = useState<any>(null);
  const [selectedRecommendation, setSelectedRecommendation] = useState<any>(null);

  // 🔥 NOVO: Estados para modais de análises avançadas
  const [modalProdutoEstrela, setModalProdutoEstrela] = useState<any>(null);
  const [modalProdutoLento, setModalProdutoLento] = useState<any>(null);
  const [modalAfinidade, setModalAfinidade] = useState<any>(null);
  const [modalMatrizHorario, setModalMatrizHorario] = useState<any>(null);
  const [modalComportamentoHora, setModalComportamentoHora] = useState<any>(null);

  const [rhFuncionarios, setRhFuncionarios] = useState<any[]>([]);
  const [rhPontoLoading, setRhPontoLoading] = useState(false);
  const [rhPontoError, setRhPontoError] = useState<string | null>(null);
  const [rhPontoFiltroFuncionarioId, setRhPontoFiltroFuncionarioId] = useState<string>('');
  const [rhPontoFiltroInicio, setRhPontoFiltroInicio] = useState<string>('');
  const [rhPontoFiltroFim, setRhPontoFiltroFim] = useState<string>('');
  const [rhPontoPage, setRhPontoPage] = useState<number>(1);
  const [rhPontoPerPage, setRhPontoPerPage] = useState<number>(25);
  const [rhPontoTotal, setRhPontoTotal] = useState<number>(0);
  const [rhPontoPages, setRhPontoPages] = useState<number>(1);
  const [rhPontoItems, setRhPontoItems] = useState<any[]>([]);

  useEffect(() => {
    loadDashboard();
  }, [periodoDias]); // 🔥 Recarregar quando período mudar

  const loadRhSupportData = async () => {
    try {
      setRhPontoError(null);
      const resp = await apiClient.get('/funcionarios', {
        params: { simples: true, por_pagina: 200, incluir_estatisticas: false },
      });
      const items = resp?.data?.data || resp?.data?.funcionarios || resp?.data || [];
      setRhFuncionarios(Array.isArray(items) ? items : []);
    } catch (e: any) {
      setRhFuncionarios([]);
    }
  };

  const loadRhPontoHistorico = async (page = 1) => {
    try {
      setRhPontoLoading(true);
      setRhPontoError(null);
      const params: any = { page, per_page: rhPontoPerPage };
      if (rhPontoFiltroInicio) params.data_inicio = rhPontoFiltroInicio;
      if (rhPontoFiltroFim) params.data_fim = rhPontoFiltroFim;
      if (rhPontoFiltroFuncionarioId) params.funcionario_id = Number(rhPontoFiltroFuncionarioId);
      const resp = await apiClient.get('/dashboard/rh/ponto/historico', { params });
      const d = resp?.data?.data;
      setRhPontoItems(d?.items || []);
      setRhPontoPage(d?.page || page);
      setRhPontoPerPage(d?.per_page || rhPontoPerPage);
      setRhPontoTotal(d?.total || 0);
      setRhPontoPages(d?.pages || 1);
    } catch (e: any) {
      setRhPontoItems([]);
      setRhPontoTotal(0);
      setRhPontoPages(1);
      setRhPontoError(e?.response?.data?.message || e?.message || 'Erro ao carregar histórico de ponto');
    } finally {
      setRhPontoLoading(false);
    }
  };

  useEffect(() => {
    if (viewMode === 'rh') {
      loadRhSupportData();
      loadRhPontoHistorico(1);
    }
  }, [viewMode]);

  // 🔥 NOVO: Aplicar filtro personalizado
  const aplicarFiltroPersonalizado = () => {
    if (!dataInicio || !dataFim) {
      alert('Por favor, selecione data de início e fim');
      return;
    }

    const inicio = new Date(dataInicio);
    const fim = new Date(dataFim);
    const diffTime = Math.abs(fim.getTime() - inicio.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    setPeriodoDias(diffDays);
    loadDashboard();
  };

  const loadDashboard = async () => {
    try {
      setLoading(true);

      // 🔥 NOVO: Se o usuário filtrou datas específicas, enviar essas datas
      let url = `/dashboard/cientifico?days=${periodoDias}`;

      if (dataInicio && dataFim) {
        // Enviar datas específicas para o backend respeitar o filtro
        url = `/dashboard/cientifico?start_date=${dataInicio}T00:00:00&end_date=${dataFim}T23:59:59`;
        console.log(`� Carregando dashboard com datas específicas: ${dataInicio} a ${dataFim}`);
      } else {
        console.log(`🔍 Carregando dashboard com período de ${periodoDias} dias`);
      }

      const response = await apiClient.get(url, { timeout: 60000 });

      console.log('🔍 Backend Response:', response.data);
      console.log('📊 Período retornado pelo backend:', response.data?.metadata?.period_days);

      // 🔥 MAPEAR ESTRUTURA DO BACKEND PARA O FORMATO ESPERADO PELO FRONTEND
      const backendData = response.data.data;
      const financials = backendData?.financials || {};

      // 🔥 CORREÇÃO: Usar dados financeiros pré-calculados pelo backend (Unica Fonte de Verdade)
      const totalVendas = financials.revenue || backendData?.summary?.revenue?.value || 0;
      const cogs = financials.cogs || 0; // Custo das Mercadorias Vendidas (Real)
      const totalDespesas = financials.expenses || backendData?.total_despesas || 0;

      const lucroBruto = financials.gross_profit || (totalVendas - cogs);
      const lucroLiquido = financials.net_profit || (lucroBruto - totalDespesas);

      const margemLucro = financials.net_margin || (totalVendas > 0 ? (lucroLiquido / totalVendas) * 100 : 0);
      const roiMensal = financials.roi || 0;

      // Valor do estoque (Ativo) - Diferente de COGS (Despesa)
      const valorEstoqueAtivo = backendData?.inventory?.custo_total || 0;
      const custoEstoque = valorEstoqueAtivo; // Alias para compatibilidade com restante do código

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
          quantidade_vendida: p.quantidade_vendida || p.total_vendido || 0,
          ultima_compra: p.ultima_compra || null
        })) || [];

      // 🔥 FORÇAR GERAÇÃO DE PRODUTOS LENTOS SEMPRE
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

      // Mapear previsão de demanda
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

      // 🔥 GERAR SAZONALIDADE a partir do trend
      const sazonalidadeData = [];
      if (backendData?.trend?.best_day && backendData?.trend?.worst_day) {
        const melhorDia = backendData.trend.best_day;
        const piorDia = backendData.trend.worst_day;
        const variacaoSemanal = melhorDia.avg_sales > 0
          ? ((melhorDia.avg_sales - piorDia.avg_sales) / piorDia.avg_sales) * 100
          : 0;

        sazonalidadeData.push({
          periodo: "Padrão Semanal",
          variacao: variacaoSemanal,
          descricao: `Melhor dia: ${melhorDia.day} (R$ ${melhorDia.avg_sales.toFixed(0)}). Pior dia: ${piorDia.day} (R$ ${piorDia.avg_sales.toFixed(0)})`
        });
      }

      if (backendData?.trend?.trend) {
        const trendText = backendData.trend.trend === 'up' ? 'Crescimento' :
          backendData.trend.trend === 'down' ? 'Queda' : 'Estável';
        const growthPercent = backendData.trend.growth_percent || 0;

        sazonalidadeData.push({
          periodo: "Tendência Geral",
          variacao: growthPercent,
          descricao: `${trendText} de ${Math.abs(growthPercent).toFixed(1)}% no período analisado`
        });
      }

      // 🔥 GERAR COMPARAÇÃO MENSAL a partir do timeseries
      const comparacaoMensal = [];
      if (Array.isArray(backendData?.timeseries) && backendData.timeseries.length >= 30) {
        // Agrupar por mês
        const vendasPorMes: Record<string, number[]> = {};
        backendData.timeseries.forEach((item: any) => {
          if (item.data && item.total) {
            const mesAno = item.data.substring(0, 7); // "2026-02"
            if (!vendasPorMes[mesAno]) vendasPorMes[mesAno] = [];
            vendasPorMes[mesAno].push(item.total);
          }
        });

        // Calcular totais por mês
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
            crescimento_vs_ontem: backendData?.summary?.growth_period?.value ?? backendData?.summary?.growth?.value ?? 0,
            meta_atingida: 0,
            vendas_por_forma_pagamento: {},
            custo_vendas: cogs, // 🔥 CORRIGIDO: Usar CMV (Custo das Mercadorias Vendidas)
            lucro_liquido: lucroLiquido,
            margem_diaria: margemLucro
          },
          mes: {
            total_vendas: totalVendas,
            total_despesas: totalDespesas,
            lucro_bruto: lucroBruto,
            lucro_liquido: lucroLiquido,
            margem_lucro: margemLucro,
            crescimento_mensal: backendData?.summary?.growth_period?.value ?? backendData?.summary?.growth?.value ?? 0,
            despesas_por_tipo: {},
            custo_produtos_vendidos: cogs, // 🔥 CORRIGIDO: Usar CMV
            investimentos: valorEstoqueAtivo, // 🔥 Manter valor do estoque como investimento (Ativo)
            roi_mensal: roiMensal
          },
          rh: backendData?.rh, // 🔥 NOVO: Dados de RH mapeados
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
              margem_seguranca: totalVendas > 0 ? ((lucroLiquido / totalVendas) * 100) : 0,  // 🔥 CORRIGIDO: Usar lucroLiquido
              alavancagem_operacional: 1.5,
              ebitda: lucroBruto
            }
          },
          analise_temporal: {
            vendas_por_hora: (backendData?.sales_by_hour || []).map((h: any) => ({
              hora: h.hora || 0,
              quantidade: h.qtd || h.quantidade || 0,
              total: h.total || 0,
              lucro: h.lucro || 0,
              margem: h.margem || 0
            })),  // 🔥 CORREÇÃO: Mapear corretamente com valores padrão
            produtos_por_hora: (() => {
              // 🔥 CORREÇÃO: Transformar lista em Record<hora, produtos[]>
              const topProducts = backendData?.top_products_by_hour || [];
              if (!Array.isArray(topProducts)) return {};

              // Se for array simples, agrupar por hora (ou retornar vazio se não tiver hora)
              const grouped: Record<number, any[]> = {};
              topProducts.forEach((p: any) => {
                const hora = p.hora || 0;
                if (!grouped[hora]) grouped[hora] = [];
                grouped[hora].push(p);
              });
              return grouped;
            })(),  // 🔥 NOVO: Produtos por horário
            padroes_temporais_clientes: (() => {
              // 🔥 CORREÇÃO: Backend retorna lista simples, frontend espera objeto com perfis_temporais
              const patterns = backendData?.customer_temporal_patterns || [];
              if (!Array.isArray(patterns)) return {};

              // Transformar lista em objeto com estrutura esperada
              return {
                perfis_temporais: {}  // Vazio por enquanto, já que backend não retorna perfis
              };
            })(),  // 🔥 NOVO
            concentracao_horaria: backendData?.hourly_concentration || {},  // 🔥 NOVO
            matriz_produto_horario: backendData?.product_hour_matrix || { matrix: [], products: [], hours: [] },  // 🔥 NOVO
            afinidade_cliente_produto: backendData?.customer_product_affinity || [],  // 🔥 NOVO
            comportamento_clientes_horario: backendData?.hourly_customer_behavior || { comportamento_por_hora: [], total_horas_analisadas: 0 },  // 🔥 NOVO
            vendas_por_categoria: [],
            tendencia_vendas: timeseriesFormatted,
            sazonalidade: sazonalidadeData,
            comparacao_meses: comparacaoMensal,
            previsao_proxima_semana: forecastFormatted
          },
          insights_cientificos: {
            correlações: backendData?.correlations || [],
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
                  acao: 'Revisar produtos com baixo giro e considerar promoções para liberar capital',
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
                  acao: 'Analisar produtos com margem abaixo de 20% e ajustar precificação',
                  impacto_esperado: 18,
                  complexidade: 'media'
                }
              ]
          },
          alertas_cientificos: []
        }
      };

      console.log('✅ Mapped Data:', mappedData);
      console.log('🔍 Backend Raw Data:', backendData);
      console.log('🔍 Timeseries:', backendData?.timeseries);
      console.log('🔍 Timeseries Formatted:', timeseriesFormatted);
      console.log('🔍 Sales by Hour:', backendData?.sales_by_hour);
      console.log('🔍 Produtos Lentos (backend):', backendData?.produtos_lentos);
      console.log('🔍 Produtos Lentos (mapped):', produtosLentos);
      console.log('🔍 Recomendações (backend):', backendData?.recomendacoes);
      console.log('🔍 Sazonalidade:', sazonalidadeData);
      console.log('🔍 Comparação Mensal:', comparacaoMensal);
      console.log('🔍 ABC Analysis:', backendData?.abc);
      console.log('🔍 Analise Temporal Mapeada:', mappedData.data.analise_temporal);
      console.log('🔍 Correlações:', backendData?.correlations);
      console.log('🔍 Insights Científicos:', mappedData.data.insights_cientificos);
      setData(mappedData);
    } catch (err: unknown) {
      console.error('❌ Dashboard Error:', err);
      const e = err as { code?: string; message?: string };
      const isNetworkError =
        e?.code === 'ERR_NETWORK' ||
        e?.message?.includes('ECONNREFUSED') ||
        e?.message?.includes('Network Error');
      setError(
        isNetworkError
          ? 'Backend indisponível. Inicie o servidor Flask na porta 5000.'
          : 'Erro ao carregar dados científicos'
      );
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

    const todosProdutos = data.data.analise_produtos.curva_abc.produtos;

    if (selectedABC === 'all') {
      // Quando "TODOS" está selecionado, pegar uma AMOSTRA de cada classe
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
    <div className="flex items-center justify-center h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      <div className="text-center">
        <div className="relative">
          <div className="animate-spin rounded-full h-20 w-20 border-b-4 border-blue-600 mx-auto"></div>
          <Brain className="w-10 h-10 text-blue-600 absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
        </div>
        <p className="mt-6 text-xl font-semibold text-gray-700">Carregando Dashboard...</p>
        <p className="text-gray-500 mt-2">Analisando dados dos últimos {periodoDias} dias</p>
        <div className="mt-4 flex items-center justify-center gap-2">
          <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
          <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
          <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
        </div>
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

  const { hoje, mes, rh, analise_produtos, analise_financeira, insights_cientificos = {
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
      <div className="mb-6">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-3xl md:text-4xl font-bold text-gray-900">Dashboard Executivo</h1>
            <p className="text-gray-600 mt-1">
              Análise completa do seu negócio • {new Date().toLocaleDateString('pt-BR')}
            </p>
          </div>
          <div className="flex flex-col sm:flex-row gap-3">

            <button
              onClick={loadDashboard}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              Atualizar
            </button>
          </div>
        </div>
      </div>

      {/* 🔥 NOVO: FILTROS DE PERÍODO E VISUALIZAÇÃO - ACIMA DAS ANÁLISES */}
      <div className="bg-white rounded-xl shadow-lg p-6 mb-6 border border-gray-200">
        <div className="flex flex-col gap-6">
          {/* SELETOR DE MODO DE FILTRO */}
          <div className="flex gap-4 border-b border-gray-200 pb-4">
            <button
              onClick={() => setModoFiltro('rapido')}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${modoFiltro === 'rapido'
                ? 'bg-blue-600 text-white shadow-lg'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
            >
              ⚡ Filtro Rápido
            </button>
            <button
              onClick={() => setModoFiltro('personalizado')}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${modoFiltro === 'personalizado'
                ? 'bg-blue-600 text-white shadow-lg'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
            >
              📅 Período Personalizado
            </button>
          </div>

          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            {/* FILTRO RÁPIDO */}
            {modoFiltro === 'rapido' && (
              <div className="flex-1">
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  📅 Período de Análise
                </label>
                <div className="flex gap-2 flex-wrap">
                  {[
                    { dias: 7, label: '7 dias', desc: 'Última semana' },
                    { dias: 15, label: '15 dias', desc: 'Últimas 2 semanas' },
                    { dias: 30, label: '30 dias', desc: 'Último mês' },
                    { dias: 60, label: '60 dias', desc: 'Últimos 2 meses' },
                    { dias: 90, label: '90 dias', desc: 'Último trimestre' },
                    { dias: 180, label: '6 meses', desc: 'Último semestre' },
                    { dias: 365, label: '1 ano', desc: 'Último ano' }
                  ].map((periodo) => (
                    <button
                      key={periodo.dias}
                      onClick={() => setPeriodoDias(periodo.dias)}
                      disabled={loading}
                      className={`px-4 py-2 rounded-lg font-medium transition-all ${periodoDias === periodo.dias
                        ? 'bg-blue-600 text-white shadow-lg scale-105 ring-2 ring-blue-300'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200 hover:scale-102'
                        } ${loading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                      title={periodo.desc}
                    >
                      {periodo.label}
                    </button>
                  ))}
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  📊 Analisando dados dos últimos <strong className="text-blue-600">{periodoDias} dias</strong>
                  {loading && <span className="ml-2 text-blue-600 animate-pulse">• Carregando...</span>}
                </p>
              </div>
            )}

            {/* FILTRO PERSONALIZADO */}
            {modoFiltro === 'personalizado' && (
              <div className="flex-1">
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  📅 Selecione o Período Personalizado
                </label>
                <div className="flex gap-4 items-end flex-wrap">
                  <div className="flex-1 min-w-[200px]">
                    <label className="block text-xs text-gray-600 mb-1">Data Início</label>
                    <input
                      type="date"
                      value={dataInicio}
                      onChange={(e) => setDataInicio(e.target.value)}
                      max={new Date().toISOString().split('T')[0]}
                      className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div className="flex-1 min-w-[200px]">
                    <label className="block text-xs text-gray-600 mb-1">Data Fim</label>
                    <input
                      type="date"
                      value={dataFim}
                      onChange={(e) => setDataFim(e.target.value)}
                      max={new Date().toISOString().split('T')[0]}
                      min={dataInicio}
                      className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <button
                    onClick={aplicarFiltroPersonalizado}
                    disabled={loading || !dataInicio || !dataFim}
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-all"
                  >
                    Aplicar Filtro
                  </button>
                </div>
                {dataInicio && dataFim && (
                  <p className="text-xs text-gray-500 mt-2">
                    📊 Período selecionado: <strong className="text-blue-600">
                      {new Date(dataInicio).toLocaleDateString('pt-BR')} até {new Date(dataFim).toLocaleDateString('pt-BR')}
                    </strong>
                    {loading && <span className="ml-2 text-blue-600 animate-pulse">• Carregando...</span>}
                  </p>
                )}
              </div>
            )}

            {/* FILTRO DE MODO DE VISUALIZAÇÃO */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                👁️ Modo de Visualização
              </label>
              <select
                className="px-4 py-2 bg-white border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 font-medium"
                value={viewMode}
                onChange={(e) => {
                  const val = e.target.value;
                  if (val === 'rh') {
                    navigate('/rh');
                  } else {
                    setViewMode(val as any);
                  }
                }}
              >
                <option value="visao-geral">📊 Visão Geral</option>
                <option value="detalhado">📈 Análise Detalhada</option>
                <option value="avancado">🔬 Análise Avançada</option>
                <option value="rh">👥 Análise de RH</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* KPIs PRINCIPAIS - COM INDICADOR DE PERÍODO */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {[
          {
            title: 'Faturamento',
            periodo: `Últimos ${periodoDias} dias`,
            value: `R$ ${(mes?.total_vendas || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`,
            change: mes?.crescimento_mensal || 0,
            icon: DollarIcon,
            color: 'from-green-500 to-emerald-600',
            subtitle: `${mes?.margem_lucro?.toFixed(1) || 0}% de margem`,
            key: `faturamento-${periodoDias}` // 🔥 Key única para forçar re-render
          },
          {
            title: 'Lucro Líquido',
            periodo: `Últimos ${periodoDias} dias`,
            value: `R$ ${(mes?.lucro_bruto || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`,
            change: mes?.crescimento_mensal || 0,
            icon: TrendingUpFill,
            color: 'from-blue-500 to-cyan-600',
            subtitle: `ROI: ${(mes?.roi_mensal || 0).toFixed(1)}%`,
            key: `lucro-${periodoDias}` // 🔥 Key única para forçar re-render
          },
          {
            title: 'Ticket Médio',
            periodo: `Últimos ${periodoDias} dias`,
            value: `R$ ${(hoje?.ticket_medio || 0).toFixed(2)}`,
            change: hoje?.crescimento_vs_ontem || 0,
            icon: TrendingUp,
            color: 'from-purple-500 to-pink-600',
            subtitle: `${hoje?.clientes_atendidos || 0} clientes`,
            key: `ticket-${periodoDias}` // 🔥 Key única para forçar re-render
          },
          {
            title: 'Despesas',
            periodo: `Últimos ${periodoDias} dias`,
            value: `R$ ${(mes?.total_despesas || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`,
            change: mes?.crescimento_mensal || 0,
            icon: AlertCircle,
            color: 'from-orange-500 to-red-600',
            subtitle: `${(((mes?.total_despesas || 0) / (mes?.total_vendas || 1)) * 100).toFixed(1)}% do faturamento`,
            key: `despesas-${periodoDias}` // 🔥 Key única para forçar re-render
          }
        ].map((kpi, idx) => (
          <div
            key={kpi.key} // 🔥 Usar key única baseada no período
            onClick={() => setKpiModalAberto(kpi.title)} // 🔥 Abrir modal ao clicar
            className={`bg-gradient-to-br ${kpi.color} rounded-xl shadow-lg p-6 text-white transform transition-all duration-300 hover:scale-105 hover:shadow-xl animate-fadeIn cursor-pointer`}
            title="Clique para ver histórico detalhado"
          >
            <div className="flex justify-between items-start mb-2">
              <kpi.icon className="w-8 h-8 opacity-80" />
              <div className={`flex items-center px-2 py-1 rounded-full text-xs font-bold ${kpi.change >= 0 ? 'bg-white/20' : 'bg-black/20'}`}>
                {kpi.change >= 0 ? <ArrowUpRight className="w-3 h-3 mr-1" /> : <ArrowDownRight className="w-3 h-3 mr-1" />}
                {Math.abs(kpi.change).toFixed(1)}%
              </div>
            </div>

            <p className="text-xs opacity-70 mb-1">📅 {kpi.periodo}</p>
            <p className="text-sm opacity-80 mb-1">{kpi.title}</p>
            <p className="text-3xl font-bold mb-2">{kpi.value}</p>
            <p className="text-sm opacity-90">{kpi.subtitle}</p>
          </div>
        ))}
      </div>

      {/* 🔥 NOVO: RESUMO EXECUTIVO - VISÃO GERAL */}
      {viewMode === 'visao-geral' && (
        <div className="space-y-6">
          {/* Indicador de Modo Ativo */}
          <div className="bg-gradient-to-r from-blue-500 to-indigo-600 rounded-xl shadow-lg p-4 text-white">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
                  <TargetIcon className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-lg font-bold">📊 Visão Geral Ativa</h3>
                  <p className="text-sm text-blue-100">Resumo executivo dos principais indicadores</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm text-blue-100">Período</p>
                <p className="text-lg font-bold">{periodoDias} dias</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-200">
            <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-3">
              <TargetIcon className="w-8 h-8 text-blue-600" />
              📊 Resumo Executivo - Últimos {periodoDias} dias
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Desempenho Financeiro */}
              <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl p-6 border border-green-200">
                <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <DollarIcon className="w-5 h-5 text-green-600" />
                  Desempenho Financeiro
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-700">Faturamento Total:</span>
                    <span className="font-bold text-green-600">R$ {(mes?.total_vendas || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-700">Lucro Líquido:</span>
                    <span className="font-bold text-blue-600">R$ {(mes?.lucro_bruto || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-700">Margem de Lucro:</span>
                    <span className="font-bold text-purple-600">{mes?.margem_lucro?.toFixed(1) || 0}%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-700">ROI:</span>
                    <span className="font-bold text-orange-600">{(mes?.roi_mensal || 0).toFixed(1)}%</span>
                  </div>
                </div>
              </div>

              {/* Produtos e Estoque */}
              <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-xl p-6 border border-blue-200">
                <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <Package className="w-5 h-5 text-blue-600" />
                  Produtos e Estoque
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-700">Produtos Estrela (Classe A):</span>
                    <span className="font-bold text-green-600">{analise_produtos?.produtos_estrela?.length || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-700">Produtos Lentos (Classe C):</span>
                    <span className="font-bold text-red-600">{analise_produtos?.produtos_lentos?.length || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-700">Total de Produtos ABC:</span>
                    <span className="font-bold text-blue-600">{analise_produtos?.curva_abc?.produtos?.length || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-700">Ticket Médio:</span>
                    <span className="font-bold text-purple-600">R$ {(hoje?.ticket_medio || 0).toFixed(2)}</span>
                  </div>
                </div>
              </div>

              {/* Insights Rápidos */}
              <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-6 border border-purple-200 md:col-span-2">
                <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <Brain className="w-5 h-5 text-purple-600" />
                  💡 Insights Rápidos
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-white/80 p-4 rounded-lg">
                    <p className="text-sm text-gray-600 mb-1">Crescimento</p>
                    {mes?.crescimento_mensal != null && mes.crescimento_mensal !== 0 ? (
                      <p className={`text-2xl font-bold ${mes.crescimento_mensal >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {mes.crescimento_mensal >= 0 ? '+' : ''}{mes.crescimento_mensal.toFixed(1)}%
                      </p>
                    ) : mes?.crescimento_mensal === 0 ? (
                      <p className="text-2xl font-bold text-gray-500">0.0%</p>
                    ) : (
                      <p className="text-2xl font-bold text-gray-400">--</p>
                    )}
                    <p className="text-xs text-gray-500 mt-1">vs período anterior</p>
                  </div>
                  <div className="bg-white/80 p-4 rounded-lg">
                    <p className="text-sm text-gray-600 mb-1">Clientes Atendidos</p>
                    <p className="text-2xl font-bold text-blue-600">{hoje?.clientes_atendidos || 0}</p>
                    <p className="text-xs text-gray-500 mt-1">no período</p>
                  </div>
                  <div className="bg-white/80 p-4 rounded-lg">
                    <p className="text-sm text-gray-600 mb-1">Despesas / Faturamento</p>
                    <p className="text-2xl font-bold text-orange-600">
                      {(((mes?.total_despesas || 0) / (mes?.total_vendas || 1)) * 100).toFixed(1)}%
                    </p>
                    <p className="text-xs text-gray-500 mt-1">índice de eficiência</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-800">
                💡 <strong>Dica:</strong> Para análises mais detalhadas, selecione <strong>"Análise Detalhada"</strong> ou <strong>"Análise Avançada"</strong> nos filtros acima.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* 🔥 INDICADOR DE MODO: ANÁLISE DETALHADA */}
      {viewMode === 'detalhado' && (
        <div className="bg-gradient-to-r from-purple-500 to-pink-600 rounded-xl shadow-lg p-4 text-white mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
                <ChartBar className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-lg font-bold">📈 Análise Detalhada Ativa</h3>
                <p className="text-sm text-purple-100">Curva ABC, Tendências e Análise Financeira</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm text-purple-100">Período</p>
              <p className="text-lg font-bold">{periodoDias} dias</p>
            </div>
          </div>
        </div>
      )}

      {/* 🔥 INDICADOR DE MODO: ANÁLISE AVANÇADA */}
      {viewMode === 'avancado' && (
        <div className="bg-gradient-to-r from-cyan-500 to-blue-600 rounded-xl shadow-lg p-4 text-white mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
                <Brain className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-lg font-bold">🔬 Análise Avançada Ativa</h3>
                <p className="text-sm text-cyan-100">Insights Científicos, Correlações e Previsões</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm text-cyan-100">Período</p>
              <p className="text-lg font-bold">{periodoDias} dias</p>
            </div>
          </div>
        </div>
      )}

      {/* SEÇÃO PRINCIPAL: CURVA ABC COM GRÁFICO DE PARETO */}
      {viewMode === 'detalhado' && (
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
              {produtosFiltrados.length > 0 ? (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                  {/* GRÁFICO DE PARETO */}
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
                                <p className="text-sm text-gray-600">Classificação: <span className={`font-bold`} style={{ color: getABCColor(payload?.[0]?.payload?.classificacao) }}>{payload?.[0]?.payload?.classificacao}</span></p>
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
                      <h3 className="font-bold text-gray-900 mb-4">📊 Interpretação da Curva ABC</h3>
                      <div className="space-y-3">
                        <div className="flex items-center gap-3">
                          <div className="w-3 h-3 rounded-full bg-green-500"></div>
                          <div>
                            <p className="font-semibold text-gray-900">Classe A (20% dos produtos)</p>
                            <p className="text-sm text-gray-600">Responsáveis por {analise_produtos?.curva_abc?.resumo?.A?.percentual?.toFixed(1) || 0}% do faturamento</p>
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

                    {/* TOP 5 PRODUTOS DA CLASSE SELECIONADA */}
                    <div className="border border-gray-200 rounded-xl p-4">
                      <h4 className="font-bold text-gray-900 mb-3">
                        🏆 Top Produtos {selectedABC === 'all' ? 'Geral' : `Classe ${selectedABC}`}
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
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${produto.classificacao === 'A' ? 'bg-green-100 text-green-800' :
                                  produto.classificacao === 'B' ? 'bg-yellow-100 text-yellow-800' :
                                    'bg-red-100 text-red-800'
                                  }`}>
                                  {idx + 1}
                                </div>
                                <div>
                                  <p className="font-medium text-gray-900">{produto.nome}</p>
                                  <p className="text-xs text-gray-500">
                                    Classe {produto.classificacao} • Margem: {produto.margem.toFixed(1)}%
                                  </p>
                                </div>
                              </div>
                              <div className="text-right">
                                <p className={`font-bold ${produto.classificacao === 'A' ? 'text-green-600' :
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
                        ? 'Parabéns! Você não tem produtos de baixo desempenho (Classe C).'
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

      {/* SEÇÃO: ANÁLISE TEMPORAL - TENDÊNCIA DE VENDAS */}
      {viewMode === 'detalhado' && (
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
                <div className="bg-gradient-to-br from-purple-50 to-white p-6 rounded-xl border border-purple-200 lg:col-span-2">
                  <h3 className="font-bold text-gray-900 mb-6 text-lg flex items-center gap-2">
                    <LineChartIcon className="w-5 h-5 text-purple-600" />
                    Evolução das Vendas (30 dias)
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
                      <p className={`text-lg font-bold ${analise_temporal?.tendencia_vendas?.length > 1 && (analise_temporal?.tendencia_vendas[analise_temporal?.tendencia_vendas.length - 1]?.vendas || 0) > (analise_temporal?.tendencia_vendas[analise_temporal?.tendencia_vendas.length - 2]?.vendas || 0) ? 'text-green-600' : 'text-red-600'}`}>
                        {analise_temporal?.tendencia_vendas?.length > 1 && (analise_temporal?.tendencia_vendas[analise_temporal?.tendencia_vendas.length - 1]?.vendas || 0) > (analise_temporal?.tendencia_vendas[analise_temporal?.tendencia_vendas.length - 2]?.vendas || 0) ? '📈 Alta' : '📉 Baixa'}
                      </p>
                    </div>
                    <div className="bg-blue-50 p-3 rounded-lg">
                      <p className="text-sm text-blue-600 font-medium">Média 7 dias</p>
                      <p className="text-lg font-bold text-blue-700">
                        R$ {(analise_temporal?.tendencia_vendas?.slice(-7).reduce((acc, curr) => acc + (curr.vendas || 0), 0) / Math.max(1, Math.min(7, analise_temporal?.tendencia_vendas?.length || 0)))?.toLocaleString('pt-BR', { maximumFractionDigits: 0 }) || '0'}
                      </p>
                    </div>
                    <div className="bg-green-50 p-3 rounded-lg">
                      <p className="text-sm text-green-600 font-medium">Previsão Amanhã</p>
                      <p className="text-lg font-bold text-green-700">
                        R$ {(analise_temporal?.previsao_proxima_semana?.[0]?.previsao || 0).toLocaleString('pt-BR', { maximumFractionDigits: 0 })}
                      </p>
                    </div>
                  </div>
                </div>

                {/* 🔥 MOVIDO: COMPARAÇÃO MENSAL - AGORA ABAIXO DO GRÁFICO */}
                <div className="bg-gradient-to-r from-orange-50 to-red-50 p-6 rounded-xl border border-orange-200 lg:col-span-2">
                  <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                    <LucideBarChart className="w-5 h-5 text-orange-600" />
                    Comparação Mensal
                  </h3>
                  <div className="space-y-3">
                    {analise_temporal?.comparacao_meses && analise_temporal?.comparacao_meses.length > 0 ? (
                      analise_temporal?.comparacao_meses.map((comp, idx) => (
                        <div key={`mes-${comp.mes || idx}`} className="bg-white/70 p-4 rounded-lg">
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
                        <p className="text-gray-500">Comparação mensal não disponível</p>
                        <p className="text-sm text-gray-400 mt-1">Necessário pelo menos 2 meses de dados</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 🔥 NOVO: SEÇÃO DE ANÁLISE DE VENDAS POR HORÁRIO */}
      {viewMode === 'detalhado' && (
        <div className="bg-white rounded-2xl shadow-xl mb-8 overflow-hidden border border-gray-200">
          <div className="p-6 border-b border-gray-200 bg-gradient-to-r from-indigo-50 to-purple-50">
            <div className="flex items-center gap-3">
              <Clock className="w-8 h-8 text-indigo-600" />
              <div>
                <h2 className="text-2xl font-bold text-gray-900">⏰ Análise de Vendas por Horário</h2>
                <p className="text-gray-600">Identifique os melhores horários para vendas e otimize sua operação</p>
              </div>
            </div>
          </div>

          <div className="p-6">
            {analise_temporal?.vendas_por_hora && analise_temporal.vendas_por_hora.length > 0 ? (
              <div className="space-y-6">
                {/* Gráfico de Barras - Vendas por Hora */}
                <div className="bg-gradient-to-br from-gray-50 to-indigo-50 rounded-xl p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">📊 Volume de Vendas por Horário</h3>
                  <div className="h-[400px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={analise_temporal.vendas_por_hora}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                        <XAxis
                          dataKey="hora"
                          tick={{ fontSize: 12 }}
                          tickFormatter={(value) => `${value}h`}
                        />
                        <YAxis
                          yAxisId="left"
                          tick={{ fontSize: 12 }}
                          tickFormatter={(value) => `R$ ${(value / 1000).toFixed(0)}k`}
                        />
                        <YAxis
                          yAxisId="right"
                          orientation="right"
                          tick={{ fontSize: 12 }}
                        />
                        <Tooltip
                          content={({ payload, label }) => {
                            if (!payload || payload.length === 0) return null;
                            const data = payload[0]?.payload;
                            return (
                              <div className="bg-white dark:bg-slate-800 p-4 shadow-xl rounded-lg border-2 border-indigo-200">
                                <p className="font-bold text-gray-900 dark:text-gray-100 mb-2">
                                  🕐 {label}:00 - {label}:59
                                </p>
                                <div className="space-y-1">
                                  <p className="text-sm text-gray-700 dark:text-gray-300">
                                    💰 Faturamento: <span className="font-bold text-indigo-600">R$ {data?.total?.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</span>
                                  </p>
                                  <p className="text-sm text-gray-700 dark:text-gray-300">
                                    🛒 Vendas: <span className="font-bold text-purple-600">{data?.quantidade}</span>
                                  </p>
                                  <p className="text-sm text-gray-700 dark:text-gray-300">
                                    💵 Ticket Médio: <span className="font-bold text-green-600">R$ {(data?.total / data?.quantidade || 0).toFixed(2)}</span>
                                  </p>
                                  <p className="text-sm text-gray-700 dark:text-gray-300">
                                    📈 Margem: <span className="font-bold text-blue-600">{data?.margem?.toFixed(1)}%</span>
                                  </p>
                                </div>
                              </div>
                            );
                          }}
                        />
                        <Bar
                          yAxisId="left"
                          dataKey="total"
                          fill="#6366F1"
                          radius={[8, 8, 0, 0]}
                          name="Faturamento"
                        />
                        <Bar
                          yAxisId="right"
                          dataKey="quantidade"
                          fill="#A855F7"
                          radius={[8, 8, 0, 0]}
                          name="Quantidade"
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Insights Inteligentes */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {(() => {
                    // Calcular insights
                    const vendasPorHora = analise_temporal.vendas_por_hora;

                    // 🔥 DEFENSIVE: Verificar se há dados
                    if (!vendasPorHora || vendasPorHora.length === 0) {
                      return <div className="col-span-3 text-center text-gray-500">Sem dados de vendas por hora</div>;
                    }

                    const melhorHorario = vendasPorHora.reduce((max, h) => h.total > max.total ? h : max, vendasPorHora[0]);
                    const piorHorario = vendasPorHora.reduce((min, h) => h.total < min.total ? h : min, vendasPorHora[0]);
                    const totalVendas = vendasPorHora.reduce((sum, h) => sum + h.total, 0);
                    const mediaHoraria = totalVendas / vendasPorHora.length;
                    const horariosAcimaDaMedia = vendasPorHora.filter(h => h.total > mediaHoraria);

                    // 🔥 DEFENSIVE: Garantir que melhorHorario e piorHorario têm valores válidos
                    const melhorMargemSafe = melhorHorario?.margem ?? 0;
                    const piorTotalSafe = piorHorario?.total ?? 0;
                    const melhorTotalSafe = melhorHorario?.total ?? 1; // Evitar divisão por zero

                    return (
                      <>
                        {/* Melhor Horário */}
                        <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl p-6 border border-green-200">
                          <div className="flex items-center gap-3 mb-3">
                            <div className="w-12 h-12 bg-green-500 rounded-lg flex items-center justify-center">
                              <TrendingUp className="w-6 h-6 text-white" />
                            </div>
                            <div>
                              <p className="text-sm text-green-700 font-medium">🏆 Melhor Horário</p>
                              <p className="text-2xl font-bold text-green-900">{melhorHorario?.hora ?? 0}h</p>
                            </div>
                          </div>
                          <div className="space-y-1 text-sm">
                            <p className="text-gray-700">💰 R$ {(melhorHorario?.total ?? 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</p>
                            <p className="text-gray-700">🛒 {melhorHorario?.quantidade ?? 0} vendas</p>
                            <p className="text-gray-700">📈 {melhorMargemSafe.toFixed(1)}% margem</p>
                          </div>
                          <div className="mt-3 pt-3 border-t border-green-200">
                            <p className="text-xs text-green-700">
                              💡 <strong>Dica:</strong> Concentre promoções e equipe neste horário
                            </p>
                          </div>
                        </div>

                        {/* Horário Crítico */}
                        <div className="bg-gradient-to-br from-red-50 to-pink-50 rounded-xl p-6 border border-red-200">
                          <div className="flex items-center gap-3 mb-3">
                            <div className="w-12 h-12 bg-red-500 rounded-lg flex items-center justify-center">
                              <AlertTriangle className="w-6 h-6 text-white" />
                            </div>
                            <div>
                              <p className="text-sm text-red-700 font-medium">⚠️ Horário Crítico</p>
                              <p className="text-2xl font-bold text-red-900">{piorHorario?.hora ?? 0}h</p>
                            </div>
                          </div>
                          <div className="space-y-1 text-sm">
                            <p className="text-gray-700">💰 R$ {(piorHorario?.total ?? 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</p>
                            <p className="text-gray-700">🛒 {piorHorario?.quantidade ?? 0} vendas</p>
                            <p className="text-gray-700">📉 {((piorTotalSafe / melhorTotalSafe) * 100).toFixed(0)}% do melhor</p>
                          </div>
                          <div className="mt-3 pt-3 border-t border-red-200">
                            <p className="text-xs text-red-700">
                              💡 <strong>Dica:</strong> Avalie necessidade de equipe reduzida
                            </p>
                          </div>
                        </div>

                        {/* Horários de Pico */}
                        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-200">
                          <div className="flex items-center gap-3 mb-3">
                            <div className="w-12 h-12 bg-blue-500 rounded-lg flex items-center justify-center">
                              <TargetIcon className="w-6 h-6 text-white" />
                            </div>
                            <div>
                              <p className="text-sm text-blue-700 font-medium">🎯 Horários de Pico</p>
                              <p className="text-2xl font-bold text-blue-900">{horariosAcimaDaMedia.length}</p>
                            </div>
                          </div>
                          <div className="space-y-1 text-sm">
                            <p className="text-gray-700">📊 Média: R$ {mediaHoraria.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</p>
                            <p className="text-gray-700">⏰ Horários:</p>
                            <p className="text-gray-700 font-mono text-xs">
                              {horariosAcimaDaMedia.slice(0, 5).map(h => `${h.hora}h`).join(', ')}
                              {horariosAcimaDaMedia.length > 5 && '...'}
                            </p>
                          </div>
                          <div className="mt-3 pt-3 border-t border-blue-200">
                            <p className="text-xs text-blue-700">
                              💡 <strong>Dica:</strong> Foque recursos nos horários de pico
                            </p>
                          </div>
                        </div>
                      </>
                    );
                  })()}
                </div>

                {/* Recomendações Estratégicas */}
                <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl p-6 border border-purple-200">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <Lightbulb className="w-5 h-5 text-purple-600" />
                    💡 Recomendações Estratégicas
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-white/70 p-4 rounded-lg">
                      <p className="font-semibold text-purple-900 mb-2">👥 Gestão de Equipe</p>
                      <ul className="text-sm text-gray-700 space-y-1">
                        <li>• Escale mais funcionários nos horários de pico</li>
                        <li>• Reduza equipe nos horários de baixo movimento</li>
                        <li>• Planeje intervalos fora dos horários críticos</li>
                      </ul>
                    </div>
                    <div className="bg-white/70 p-4 rounded-lg">
                      <p className="font-semibold text-purple-900 mb-2">🎯 Estratégias de Vendas</p>
                      <ul className="text-sm text-gray-700 space-y-1">
                        <li>• Lance promoções nos horários de maior movimento</li>
                        <li>• Teste ofertas especiais em horários fracos</li>
                        <li>• Monitore ticket médio por horário</li>
                      </ul>
                    </div>
                  </div>
                </div>

                {/* 🔥 NOVO: Produtos Mais Vendidos por Horário */}
                {analise_temporal?.produtos_por_hora && Object.keys(analise_temporal.produtos_por_hora).length > 0 && (
                  <div className="bg-gradient-to-r from-cyan-50 to-blue-50 rounded-xl p-6 border border-cyan-200">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                      <Package className="w-5 h-5 text-cyan-600" />
                      🏆 Top Produtos por Horário
                    </h3>
                    <p className="text-sm text-gray-600 mb-4">
                      Descubra quais produtos vendem melhor em cada período do dia
                    </p>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-[600px] overflow-y-auto">
                      {Object.entries(analise_temporal.produtos_por_hora)
                        .sort(([horaA], [horaB]) => Number(horaA) - Number(horaB))
                        .filter(([hora, produtos]: [string, any]) => {
                          // 🔥 FILTER: Remover entradas vazias antes do map
                          const produtosArray = Array.isArray(produtos) ? produtos : [];
                          return produtosArray.length > 0;
                        })
                        .map(([hora, produtos]: [string, any]) => {
                          const produtosArray = Array.isArray(produtos) ? produtos : [];

                          return (
                            <div key={hora} className="bg-white/80 rounded-lg p-4 border border-cyan-100 hover:shadow-md transition-shadow">
                              <div className="flex items-center justify-between mb-3">
                                <h4 className="font-bold text-cyan-900 flex items-center gap-2">
                                  <Clock className="w-4 h-4" />
                                  {hora}h - {Number(hora) + 1}h
                                </h4>
                                <span className="text-xs bg-cyan-100 text-cyan-700 px-2 py-1 rounded-full">
                                  Top {produtosArray.length}
                                </span>
                              </div>

                              <div className="space-y-2">
                                {produtosArray.map((produto, idx) => (
                                  <div
                                    key={produto.produto_id}
                                    className="flex items-center justify-between p-2 bg-gradient-to-r from-cyan-50 to-blue-50 rounded-lg hover:from-cyan-100 hover:to-blue-100 transition-colors"
                                  >
                                    <div className="flex items-center gap-2 flex-1 min-w-0">
                                      <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${idx === 0 ? 'bg-yellow-400 text-yellow-900' :
                                        idx === 1 ? 'bg-gray-300 text-gray-700' :
                                          idx === 2 ? 'bg-orange-400 text-orange-900' :
                                            'bg-blue-100 text-blue-700'
                                        }`}>
                                        {idx + 1}
                                      </div>
                                      <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium text-gray-900 truncate" title={produto.produto_nome}>
                                          {produto.produto_nome}
                                        </p>
                                        <p className="text-xs text-gray-600">
                                          {produto.quantidade_vendida} un
                                        </p>
                                      </div>
                                    </div>
                                    <div className="text-right ml-2">
                                      <p className="text-sm font-bold text-cyan-700">
                                        R$ {produto.faturamento.toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                                      </p>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          );
                        })}
                    </div>

                    {/* Insights sobre produtos por horário */}
                    <div className="mt-6 bg-white/80 rounded-lg p-4 border border-cyan-100">
                      <h4 className="font-semibold text-cyan-900 mb-3 flex items-center gap-2">
                        <Lightbulb className="w-4 h-4" />
                        💡 Insights de Produtos por Horário
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm text-gray-700">
                        <div className="flex items-start gap-2">
                          <span className="text-cyan-600">•</span>
                          <p>Use esses dados para planejar o estoque e garantir disponibilidade nos horários de pico</p>
                        </div>
                        <div className="flex items-start gap-2">
                          <span className="text-cyan-600">•</span>
                          <p>Crie combos e promoções com os produtos mais vendidos em cada horário</p>
                        </div>
                        <div className="flex items-start gap-2">
                          <span className="text-cyan-600">•</span>
                          <p>Posicione produtos estrategicamente conforme o horário de maior demanda</p>
                        </div>
                        <div className="flex items-start gap-2">
                          <span className="text-cyan-600">•</span>
                          <p>Treine a equipe para sugerir os produtos certos no momento certo</p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-12">
                <Clock className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500 text-lg">Dados de vendas por horário não disponíveis</p>
                <p className="text-gray-400 text-sm mt-2">Necessário mais dados históricos para análise</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* SEÇÃO: ANÁLISE FINANCEIRA DETALHADA */}
      {viewMode === 'detalhado' && (
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
                                  Tendência: {payload?.[0]?.payload?.tendencia === 'alta' ? '📈 Alta' : payload?.[0]?.payload?.tendencia === 'baixa' ? '📉 Baixa' : '➡️ Estável'}
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
                    {Object.entries(analise_financeira?.margens || {}).map(([nome, valor]) => (
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
                        <span className="font-bold text-blue-600">{(analise_financeira?.indicadores?.ponto_equilibrio || 0).toFixed(1)}%</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-gray-700">Margem de Segurança</span>
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

      {/* SEÇÃO: INSIGHTS CIENTÍFICOS */}
      {viewMode === 'avancado' && (
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
                    {(insights_cientificos?.correlações || []).map((corr, idx) => (
                      <div
                        key={`corr-${corr.variavel1}-${corr.variavel2}-${idx}`}
                        className="bg-gray-900/50 p-4 rounded-lg hover:bg-gray-900 transition-colors cursor-pointer"
                        onClick={() => setSelectedCorrelation({
                          variavel1: corr.variavel1,
                          variavel2: corr.variavel2,
                          forca: corr.correlacao,
                          significancia: corr.significancia,
                          implicacoes: corr.insight
                        })}
                      >
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
                      {(insights_cientificos?.previsoes || []).map((prev, idx) => (
                        <div key={`prev-${prev.variavel}-${idx}`} className="bg-black/30 p-4 rounded-lg">
                          <div className="flex justify-between items-center mb-3">
                            <span className="text-gray-300 font-medium">{prev.variavel}</span>
                            <span className="px-3 py-1 bg-blue-500/20 text-blue-300 rounded-full text-sm">
                              {prev.confianca.toFixed(1)}% confiança
                            </span>
                          </div>
                          <div className="flex items-center gap-4">
                            <div className="text-center">
                              <p className="text-sm text-gray-400">Atual</p>
                              <p className="text-xl font-bold text-white">R$ {(prev?.valor_atual || 0).toLocaleString('pt-BR')}</p>
                            </div>
                            <ArrowUpRight className="w-6 h-6 text-green-400" />
                            <div className="text-center">
                              <p className="text-sm text-gray-400">Previsão</p>
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

                  {/* RECOMENDAÇÕES DE OTIMIZAÇÃO */}
                  <div className="bg-gradient-to-r from-purple-900/30 to-pink-900/30 rounded-xl p-6">
                    <h3 className="text-xl font-bold text-white mb-6">🚀 Recomendações de Otimização</h3>
                    <div className="space-y-4">
                      {(insights_cientificos?.recomendacoes_otimizacao || []).map((rec, idx) => (
                        <div
                          key={`rec-${rec.area}-${idx}`}
                          className="bg-black/30 p-4 rounded-lg hover:bg-black/40 transition-colors cursor-pointer"
                          onClick={() => setSelectedRecommendation({
                            tipo: 'oportunidade',
                            mensagem: rec.acao,
                            impacto_estimado: rec.impacto_esperado * 1000, // Converter % para valor estimado
                            acao_sugerida: rec.acao,
                            prazo_sugerido: rec.complexidade === 'baixa' ? '1-2 semanas' : rec.complexidade === 'media' ? '3-4 semanas' : '1-2 meses'
                          })}
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
      {viewMode === 'avancado' && (
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
              {analise_produtos?.produtos_estrela?.map((produto, idx) => (
                <div
                  key={produto.id}
                  className="bg-white/80 backdrop-blur-sm rounded-xl p-4 hover:shadow-lg transition-all duration-300 hover:scale-[1.02] cursor-pointer border border-yellow-100"
                  onClick={() => setModalProdutoEstrela(produto)}
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
              {analise_produtos?.produtos_lentos?.length > 0 ? (
                analise_produtos?.produtos_lentos?.map((produto, idx) => (
                  <div
                    key={produto.id}
                    className="bg-white/80 backdrop-blur-sm rounded-xl p-4 hover:shadow-lg transition-all duration-300 hover:scale-[1.02] cursor-pointer border border-red-100"
                    onClick={() => setModalProdutoLento(produto)}
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
                        <p className="text-lg font-bold text-orange-700">{produto.dias_estoque < 999 ? `${produto.dias_estoque} dias` : '∞'}</p>
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
                      <p className="text-xs font-bold text-red-800 mb-1">💡 Recomendação:</p>
                      <p className="text-xs text-red-700">
                        {produto.giro_estoque < 0.5
                          ? 'Considere promoção agressiva ou descontinuar produto'
                          : produto.giro_estoque < 1.0
                            ? 'Faça promoção para acelerar vendas'
                            : 'Reduza reposição e monitore de perto'}
                      </p>
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
      {viewMode === 'avancado' && (
        <div className="bg-gradient-to-br from-purple-50 to-indigo-50 rounded-2xl shadow-xl p-6 mb-8 border border-purple-200">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-3">
            <Target className="w-8 h-8 text-purple-600" />
            📊 Previsão de Demanda Inteligente
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {analise_produtos?.previsao_demanda?.map((previsao, idx) => {
              // Calcular dias até acabar o estoque
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
                          ⚠️ Risco Ruptura
                        </span>
                      )}
                      <span className={`px-3 py-1 rounded-full text-xs font-bold ${previsao.confianca > 80 ? 'bg-green-100 text-green-800' : previsao.confianca > 60 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'}`}>
                        {previsao.confianca?.toFixed(0) || 75}% confiança
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
                      <span className="text-gray-600">Demanda Diária</span>
                      <span className="font-bold text-purple-600">{demandaDiaria.toFixed(1)} un/dia</span>
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Dias até Acabar</span>
                      <div className="flex items-center gap-2">
                        <span className={`font-bold text-xl ${diasAteAcabar < 7 ? 'text-red-600' : diasAteAcabar < 14 ? 'text-yellow-600' : 'text-green-600'}`}>
                          {diasAteAcabar < 999 ? `${diasAteAcabar} dias` : '∞'}
                        </span>
                        {diasAteAcabar < 7 && <AlertTriangle className="w-5 h-5 text-red-500" />}
                      </div>
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Margem de Lucro</span>
                      <span className="font-bold text-green-600">{(previsao.margem_lucro || 0).toFixed(1)}%</span>
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Classificação ABC</span>
                      <span className={`px-2 py-1 rounded-full text-xs font-bold ${previsao.classificação_abc === 'A' ? 'bg-green-100 text-green-800' :
                        previsao.classificação_abc === 'B' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                        Classe {previsao.classificação_abc || 'C'}
                      </span>
                    </div>

                    {riscoRuptura && (
                      <div className="pt-4 border-t border-red-200 bg-red-50 p-3 rounded-lg">
                        <p className="text-sm font-bold text-red-800 mb-1">🚨 Ação Urgente Necessária!</p>
                        <p className="text-xs text-red-700">
                          Estoque acabará em {diasAteAcabar} dias. Faça reposição imediatamente para evitar ruptura.
                        </p>
                      </div>
                    )}

                    <div className="pt-4 border-t border-purple-200">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Previsão Vendas 30d</span>
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

      {/* 🔥 NOVO: ANÁLISE CIENTÍFICA DE PADRÕES TEMPORAIS */}
      {viewMode === 'avancado' && analise_temporal?.padroes_temporais_clientes && Object.keys(analise_temporal.padroes_temporais_clientes.perfis_temporais || {}).length > 0 && (
        <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-2xl shadow-xl p-6 mb-8 border border-indigo-200">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-3">
            <Clock className="w-8 h-8 text-indigo-600" />
            🕐 Análise Científica: Padrões Temporais de Clientes
          </h2>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Perfis Temporais */}
            {Object.entries(analise_temporal.padroes_temporais_clientes.perfis_temporais || {}).map(([perfil, clientes]: [string, any[]]) => {
              // 🔥 DEFENSIVE: Garantir que clientes é um array
              const clientesArray = Array.isArray(clientes) ? clientes : [];
              const totalGasto = clientesArray.reduce((sum, c) => sum + (c.total_gasto || 0), 0);
              const ticketMedio = clientesArray.length > 0 ? totalGasto / clientesArray.length : 0;

              const perfilConfig = {
                matutino: { icon: '🌅', color: 'from-yellow-50 to-orange-50', border: 'border-yellow-200', text: 'text-yellow-900', badge: 'bg-yellow-100 text-yellow-800' },
                vespertino: { icon: '☀️', color: 'from-blue-50 to-cyan-50', border: 'border-blue-200', text: 'text-blue-900', badge: 'bg-blue-100 text-blue-800' },
                noturno: { icon: '🌙', color: 'from-purple-50 to-indigo-50', border: 'border-purple-200', text: 'text-purple-900', badge: 'bg-purple-100 text-purple-800' }
              }[perfil] || { icon: '⏰', color: 'from-gray-50 to-gray-100', border: 'border-gray-200', text: 'text-gray-900', badge: 'bg-gray-100 text-gray-800' };

              return (
                <div key={perfil} className={`bg-gradient-to-br ${perfilConfig.color} rounded-xl p-6 border ${perfilConfig.border}`}>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className={`text-lg font-bold ${perfilConfig.text} flex items-center gap-2`}>
                      <span className="text-2xl">{perfilConfig.icon}</span>
                      {perfil.charAt(0).toUpperCase() + perfil.slice(1)}
                    </h3>
                    <span className={`px-3 py-1 rounded-full text-xs font-bold ${perfilConfig.badge}`}>
                      {clientes.length} clientes
                    </span>
                  </div>

                  <div className="space-y-3">
                    <div className="bg-white/70 p-3 rounded-lg">
                      <p className="text-xs text-gray-600 mb-1">Faturamento Total</p>
                      <p className={`text-xl font-bold ${perfilConfig.text}`}>
                        R$ {totalGasto.toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                      </p>
                    </div>

                    <div className="bg-white/70 p-3 rounded-lg">
                      <p className="text-xs text-gray-600 mb-1">Ticket Médio</p>
                      <p className={`text-xl font-bold ${perfilConfig.text}`}>
                        R$ {ticketMedio.toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                      </p>
                    </div>

                    <div className="bg-white/70 p-3 rounded-lg">
                      <p className="text-xs text-gray-600 mb-1">Top 3 Clientes</p>
                      <div className="space-y-1 mt-2">
                        {clientes
                          .sort((a, b) => (b.total_gasto || 0) - (a.total_gasto || 0))
                          .slice(0, 3)
                          .map((cliente, idx) => (
                            <div key={cliente.cliente_id} className="flex items-center justify-between text-xs">
                              <span className="truncate flex-1 mr-2">{idx + 1}. {cliente.cliente_nome}</span>
                              <span className="font-bold">R$ {(cliente.total_gasto || 0).toLocaleString('pt-BR', { maximumFractionDigits: 0 })}</span>
                            </div>
                          ))}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Insights Científicos */}
          <div className="mt-6 bg-white/80 rounded-xl p-6 border border-indigo-200">
            <h3 className="font-bold text-indigo-900 mb-4 flex items-center gap-2">
              <Brain className="w-5 h-5" />
              🧠 Insights Científicos sobre Comportamento Temporal
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div className="flex items-start gap-3 p-3 bg-indigo-50 rounded-lg">
                <span className="text-indigo-600 font-bold">•</span>
                <p className="text-gray-700">
                  <strong>Segmentação Temporal:</strong> Clientes têm preferências horárias distintas. Use isso para campanhas direcionadas.
                </p>
              </div>
              <div className="flex items-start gap-3 p-3 bg-purple-50 rounded-lg">
                <span className="text-purple-600 font-bold">•</span>
                <p className="text-gray-700">
                  <strong>Otimização de Estoque:</strong> Ajuste reposição baseado nos perfis temporais dominantes.
                </p>
              </div>
              <div className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg">
                <span className="text-blue-600 font-bold">•</span>
                <p className="text-gray-700">
                  <strong>Personalização:</strong> Envie ofertas nos horários preferidos de cada segmento para maior conversão.
                </p>
              </div>
              <div className="flex items-start gap-3 p-3 bg-cyan-50 rounded-lg">
                <span className="text-cyan-600 font-bold">•</span>
                <p className="text-gray-700">
                  <strong>Lifetime Value:</strong> Clientes noturnos tendem a ter maior ticket médio. Priorize retenção desse segmento.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 🔥 NOVO: MATRIZ DE CORRELAÇÃO PRODUTO × HORÁRIO */}
      {viewMode === 'avancado' && analise_temporal?.matriz_produto_horario && analise_temporal.matriz_produto_horario.matrix && analise_temporal.matriz_produto_horario.matrix.length > 0 && (
        <div className="bg-gradient-to-br from-teal-50 to-cyan-50 rounded-2xl shadow-xl p-6 mb-8 border border-teal-200">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-3">
            <GitMerge className="w-8 h-8 text-teal-600" />
            🔬 Matriz de Correlação: Produto × Horário
          </h2>

          <p className="text-gray-600 mb-6">
            Heatmap mostrando a força da relação entre produtos e horários. Percentuais indicam quanto cada horário contribui para as vendas totais do produto.
          </p>

          {/* Heatmap */}
          <div className="bg-white rounded-xl p-6 border border-teal-200 overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr>
                  <th className="p-2 text-left font-bold text-gray-900 sticky left-0 bg-white z-10">Produto</th>
                  {analise_temporal.matriz_produto_horario.hours.map((hora: number) => (
                    <th key={hora} className="p-2 text-center font-bold text-gray-700 min-w-[50px]">
                      {hora}h
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {analise_temporal.matriz_produto_horario.matrix.map((produto: any) => (
                  <tr key={produto.produto_id} className="border-t border-gray-100 hover:bg-teal-50">
                    <td className="p-2 font-semibold text-gray-900 sticky left-0 bg-white z-10 max-w-[200px] truncate" title={produto.produto_nome}>
                      {produto.produto_nome}
                    </td>
                    {analise_temporal.matriz_produto_horario.hours.map((hora: number) => {
                      const cell = produto.horas[hora];
                      const percentual = cell?.percentual || 0;

                      // Calcular cor baseada no percentual (0-100)
                      const getColor = (pct: number) => {
                        if (pct === 0) return 'bg-gray-50 text-gray-400';
                        if (pct < 2) return 'bg-blue-100 text-blue-700';
                        if (pct < 5) return 'bg-blue-200 text-blue-800';
                        if (pct < 10) return 'bg-blue-300 text-blue-900';
                        if (pct < 15) return 'bg-teal-400 text-teal-900';
                        if (pct < 20) return 'bg-green-400 text-green-900';
                        return 'bg-green-500 text-white font-bold';
                      };

                      return (
                        <td
                          key={hora}
                          className={`p-2 text-center ${getColor(percentual)} transition-all hover:scale-110 cursor-pointer`}
                          title={`${produto.produto_nome} às ${hora}h: ${percentual.toFixed(1)}% (${cell?.quantidade || 0} un, R$ ${(cell?.faturamento || 0).toFixed(0)})`}
                        >
                          {percentual > 0 ? percentual.toFixed(1) : '-'}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Legenda */}
          <div className="mt-6 bg-white rounded-xl p-4 border border-teal-200">
            <h4 className="font-semibold text-teal-900 mb-3">📊 Legenda de Intensidade</h4>
            <div className="flex items-center gap-2 flex-wrap text-xs">
              <div className="flex items-center gap-1">
                <div className="w-8 h-6 bg-gray-50 border border-gray-200 rounded"></div>
                <span>0%</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-8 h-6 bg-blue-100 rounded"></div>
                <span>{'<'}2%</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-8 h-6 bg-blue-200 rounded"></div>
                <span>2-5%</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-8 h-6 bg-blue-300 rounded"></div>
                <span>5-10%</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-8 h-6 bg-teal-400 rounded"></div>
                <span>10-15%</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-8 h-6 bg-green-400 rounded"></div>
                <span>15-20%</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-8 h-6 bg-green-500 rounded"></div>
                <span>{'>'}20%</span>
              </div>
            </div>
          </div>

          {/* Insights */}
          <div className="mt-6 bg-white/80 rounded-xl p-6 border border-teal-200">
            <h3 className="font-bold text-teal-900 mb-4 flex items-center gap-2">
              <Lightbulb className="w-5 h-5" />
              💡 Como Usar Esta Análise
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div className="flex items-start gap-3 p-3 bg-teal-50 rounded-lg">
                <span className="text-teal-600 font-bold">1.</span>
                <p className="text-gray-700">
                  <strong>Gestão de Estoque:</strong> Produtos com alta concentração em horários específicos precisam de reposição estratégica.
                </p>
              </div>
              <div className="flex items-start gap-3 p-3 bg-cyan-50 rounded-lg">
                <span className="text-cyan-600 font-bold">2.</span>
                <p className="text-gray-700">
                  <strong>Promoções Direcionadas:</strong> Lance ofertas nos horários de maior demanda de cada produto.
                </p>
              </div>
              <div className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg">
                <span className="text-blue-600 font-bold">3.</span>
                <p className="text-gray-700">
                  <strong>Layout da Loja:</strong> Posicione produtos em destaque conforme o horário de pico.
                </p>
              </div>
              <div className="flex items-start gap-3 p-3 bg-green-50 rounded-lg">
                <span className="text-green-600 font-bold">4.</span>
                <p className="text-gray-700">
                  <strong>Cross-Selling:</strong> Identifique produtos complementares vendidos no mesmo horário.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 🔥 NOVO: AFINIDADE CLIENTE × PRODUTO */}
      {viewMode === 'avancado' && analise_temporal?.afinidade_cliente_produto && analise_temporal.afinidade_cliente_produto.length > 0 && (
        <div className="bg-gradient-to-br from-amber-50 to-yellow-50 rounded-2xl shadow-xl p-6 mb-8 border border-amber-200">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-3">
            <Star className="w-8 h-8 text-amber-600" />
            ⭐ Análise de Afinidade: Cliente × Produto
          </h2>

          <p className="text-gray-600 mb-6">
            Identifica padrões de compra recorrentes. Clientes com alta afinidade por produtos específicos são alvos ideais para campanhas personalizadas.
          </p>

          {/* Top 20 Afinidades */}
          <div className="bg-white rounded-xl p-6 border border-amber-200">
            <h3 className="font-bold text-amber-900 mb-4">🎯 Top 20 Afinidades Cliente-Produto</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-[600px] overflow-y-auto">
              {analise_temporal.afinidade_cliente_produto.slice(0, 20).map((afinidade: any, idx: number) => (
                <div key={`${afinidade.cliente_id}-${afinidade.produto_id}`} className="bg-gradient-to-r from-amber-50 to-yellow-50 rounded-lg p-4 border border-amber-100 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${idx < 3 ? 'bg-amber-400 text-amber-900' : 'bg-amber-100 text-amber-700'
                          }`}>
                          {idx + 1}
                        </span>
                        <p className="font-bold text-gray-900 truncate" title={afinidade.cliente_nome}>
                          {afinidade.cliente_nome}
                        </p>
                      </div>
                      <p className="text-sm text-gray-700 truncate ml-8" title={afinidade.produto_nome}>
                        → {afinidade.produto_nome}
                      </p>
                    </div>
                    <div className="ml-2 text-right">
                      <p className="text-xs text-amber-700 font-semibold">Score</p>
                      <p className="text-lg font-bold text-amber-900">
                        {(afinidade.score_afinidade / 1000).toFixed(1)}k
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div className="bg-white/70 p-2 rounded">
                      <p className="text-gray-600">Compras</p>
                      <p className="font-bold text-gray-900">{afinidade.frequencia_compra}x</p>
                    </div>
                    <div className="bg-white/70 p-2 rounded">
                      <p className="text-gray-600">Quantidade</p>
                      <p className="font-bold text-gray-900">{afinidade.quantidade_total} un</p>
                    </div>
                    <div className="bg-white/70 p-2 rounded">
                      <p className="text-gray-600">Total</p>
                      <p className="font-bold text-gray-900">R$ {afinidade.faturamento_total.toFixed(0)}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Insights */}
          <div className="mt-6 bg-white/80 rounded-xl p-6 border border-amber-200">
            <h3 className="font-bold text-amber-900 mb-4 flex items-center gap-2">
              <Lightbulb className="w-5 h-5" />
              💡 Estratégias de Marketing Baseadas em Afinidade
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div className="flex items-start gap-3 p-3 bg-amber-50 rounded-lg">
                <span className="text-amber-600 font-bold">•</span>
                <p className="text-gray-700">
                  <strong>Campanhas Personalizadas:</strong> Envie ofertas dos produtos favoritos de cada cliente via WhatsApp.
                </p>
              </div>
              <div className="flex items-start gap-3 p-3 bg-yellow-50 rounded-lg">
                <span className="text-yellow-600 font-bold">•</span>
                <p className="text-gray-700">
                  <strong>Programa de Fidelidade:</strong> Recompense clientes com alta frequência de compra de produtos específicos.
                </p>
              </div>
              <div className="flex items-start gap-3 p-3 bg-orange-50 rounded-lg">
                <span className="text-orange-600 font-bold">•</span>
                <p className="text-gray-700">
                  <strong>Recomendações Inteligentes:</strong> Sugira produtos complementares baseado no histórico de afinidade.
                </p>
              </div>
              <div className="flex items-start gap-3 p-3 bg-red-50 rounded-lg">
                <span className="text-red-600 font-bold">•</span>
                <p className="text-gray-700">
                  <strong>Alerta de Ruptura:</strong> Notifique clientes VIP quando produtos favoritos estiverem em falta.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 🔥 NOVO: COMPORTAMENTO DE CLIENTES POR HORÁRIO */}
      {viewMode === 'avancado' && analise_temporal?.comportamento_clientes_horario && analise_temporal.comportamento_clientes_horario.comportamento_por_hora && analise_temporal.comportamento_clientes_horario.comportamento_por_hora.length > 0 && (
        <div className="bg-gradient-to-br from-violet-50 to-purple-50 rounded-2xl shadow-xl p-6 mb-8 border border-violet-200">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-3">
            <Clock className="w-8 h-8 text-violet-600" />
            👥 Comportamento de Clientes por Horário
          </h2>

          <p className="text-gray-600 mb-6">
            Análise detalhada do comportamento de compra dos clientes ao longo do dia. Identifique horários com maior valor por cliente e frequência de compra.
          </p>

          {/* Gráfico de Comportamento */}
          <div className="bg-white rounded-xl p-6 border border-violet-200 mb-6">
            <h3 className="font-bold text-violet-900 mb-4">📊 Métricas por Horário</h3>
            <div className="h-[400px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={analise_temporal.comportamento_clientes_horario.comportamento_por_hora}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                  <XAxis
                    dataKey="hora"
                    tick={{ fontSize: 12 }}
                    tickFormatter={(value) => `${value}h`}
                  />
                  <YAxis
                    yAxisId="left"
                    tick={{ fontSize: 12 }}
                    tickFormatter={(value) => `R$ ${value.toFixed(0)}`}
                  />
                  <YAxis
                    yAxisId="right"
                    orientation="right"
                    tick={{ fontSize: 12 }}
                  />
                  <Tooltip
                    content={({ payload, label }) => {
                      if (!payload || payload.length === 0) return null;
                      const data = payload[0]?.payload;
                      return (
                        <div className="bg-white dark:bg-slate-800 p-4 shadow-xl rounded-lg border-2 border-violet-200">
                          <p className="font-bold text-gray-900 dark:text-gray-100 mb-2">
                            🕐 {label}:00 - {label}:59
                          </p>
                          <div className="space-y-1 text-sm">
                            <p className="text-gray-700 dark:text-gray-300">
                              👥 Clientes Únicos: <span className="font-bold text-violet-600">{data?.clientes_unicos}</span>
                            </p>
                            <p className="text-gray-700 dark:text-gray-300">
                              💰 Ticket Médio: <span className="font-bold text-green-600">R$ {data?.ticket_medio?.toFixed(2)}</span>
                            </p>
                            <p className="text-gray-700 dark:text-gray-300">
                              🛒 Total Vendas: <span className="font-bold text-blue-600">{data?.total_vendas}</span>
                            </p>
                            <p className="text-gray-700 dark:text-gray-300">
                              📈 Frequência: <span className="font-bold text-purple-600">{data?.frequencia_media?.toFixed(2)} vendas/cliente</span>
                            </p>
                            <p className="text-gray-700 dark:text-gray-300">
                              💵 Valor/Cliente: <span className="font-bold text-orange-600">R$ {data?.valor_por_cliente?.toFixed(2)}</span>
                            </p>
                          </div>
                        </div>
                      );
                    }}
                  />
                  <Bar
                    yAxisId="left"
                    dataKey="ticket_medio"
                    fill="#8B5CF6"
                    radius={[8, 8, 0, 0]}
                    name="Ticket Médio"
                  />
                  <Bar
                    yAxisId="right"
                    dataKey="clientes_unicos"
                    fill="#EC4899"
                    radius={[8, 8, 0, 0]}
                    name="Clientes Únicos"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Tabela Detalhada */}
          <div className="bg-white rounded-xl p-6 border border-violet-200 overflow-x-auto">
            <h3 className="font-bold text-violet-900 mb-4">📋 Detalhamento por Horário</h3>
            <table className="w-full text-sm">
              <thead className="bg-violet-50">
                <tr>
                  <th className="p-3 text-left font-bold text-violet-900">Horário</th>
                  <th className="p-3 text-center font-bold text-violet-900">Clientes</th>
                  <th className="p-3 text-center font-bold text-violet-900">Vendas</th>
                  <th className="p-3 text-center font-bold text-violet-900">Ticket Médio</th>
                  <th className="p-3 text-center font-bold text-violet-900">Frequência</th>
                  <th className="p-3 text-center font-bold text-violet-900">Valor/Cliente</th>
                </tr>
              </thead>
              <tbody>
                {analise_temporal.comportamento_clientes_horario.comportamento_por_hora.map((hora: any) => (
                  <tr key={hora.hora} className="border-t border-violet-100 hover:bg-violet-50">
                    <td className="p-3 font-semibold text-gray-900">{hora.hora}h - {hora.hora + 1}h</td>
                    <td className="p-3 text-center text-violet-700 font-bold">{hora.clientes_unicos}</td>
                    <td className="p-3 text-center text-blue-700">{hora.total_vendas}</td>
                    <td className="p-3 text-center text-green-700 font-bold">R$ {hora.ticket_medio.toFixed(2)}</td>
                    <td className="p-3 text-center text-purple-700">{hora.frequencia_media.toFixed(2)}x</td>
                    <td className="p-3 text-center text-orange-700 font-bold">R$ {hora.valor_por_cliente.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Insights */}
          <div className="mt-6 bg-white/80 rounded-xl p-6 border border-violet-200">
            <h3 className="font-bold text-violet-900 mb-4 flex items-center gap-2">
              <Lightbulb className="w-5 h-5" />
              💡 Insights de Comportamento do Cliente
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div className="flex items-start gap-3 p-3 bg-violet-50 rounded-lg">
                <span className="text-violet-600 font-bold">•</span>
                <p className="text-gray-700">
                  <strong>Horários VIP:</strong> Horários com maior ticket médio indicam clientes de maior valor. Priorize atendimento premium.
                </p>
              </div>
              <div className="flex items-start gap-3 p-3 bg-purple-50 rounded-lg">
                <span className="text-purple-600 font-bold">•</span>
                <p className="text-gray-700">
                  <strong>Frequência de Compra:</strong> Alta frequência indica clientes fiéis. Crie programas de recompensa para esses horários.
                </p>
              </div>
              <div className="flex items-start gap-3 p-3 bg-pink-50 rounded-lg">
                <span className="text-pink-600 font-bold">•</span>
                <p className="text-gray-700">
                  <strong>Valor por Cliente:</strong> Métrica chave para calcular ROI de campanhas por horário.
                </p>
              </div>
              <div className="flex items-start gap-3 p-3 bg-fuchsia-50 rounded-lg">
                <span className="text-fuchsia-600 font-bold">•</span>
                <p className="text-gray-700">
                  <strong>Segmentação Temporal:</strong> Use esses dados para criar campanhas de marketing direcionadas por horário.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 🔥 NOVO: ANÁLISE DE CONCENTRAÇÃO DE FATURAMENTO */}
      {viewMode === 'avancado' && analise_temporal?.concentracao_horaria && (
        <div className="bg-gradient-to-br from-rose-50 to-pink-50 rounded-2xl shadow-xl p-6 mb-8 border border-rose-200">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-3">
            <TrendingUp className="w-8 h-8 text-rose-600" />
            📊 Análise de Concentração: Índice de Gini & Diversificação
          </h2>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
            {/* Índice de Gini */}
            <div className="bg-white rounded-xl p-6 border border-rose-200">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-bold text-rose-900">Índice de Gini</h3>
                <div className={`w-16 h-16 rounded-full flex items-center justify-center ${(analise_temporal.concentracao_horaria.gini_index || 0) > 0.7 ? 'bg-red-100' :
                  (analise_temporal.concentracao_horaria.gini_index || 0) > 0.4 ? 'bg-yellow-100' :
                    'bg-green-100'
                  }`}>
                  <span className={`text-2xl font-bold ${(analise_temporal.concentracao_horaria.gini_index || 0) > 0.7 ? 'text-red-700' :
                    (analise_temporal.concentracao_horaria.gini_index || 0) > 0.4 ? 'text-yellow-700' :
                      'text-green-700'
                    }`}>
                    {((analise_temporal.concentracao_horaria.gini_index || 0) * 100).toFixed(0)}
                  </span>
                </div>
              </div>
              <p className="text-sm text-gray-600 mb-2">
                Mede a desigualdade na distribuição de vendas ao longo do dia
              </p>
              <div className="bg-rose-50 p-3 rounded-lg">
                <p className="text-xs font-semibold text-rose-900 mb-1">Interpretação:</p>
                <p className="text-xs text-rose-700">
                  {(analise_temporal.concentracao_horaria.gini_index || 0) > 0.7
                    ? '🔴 Alta concentração - Vendas muito concentradas em poucos horários'
                    : (analise_temporal.concentracao_horaria.gini_index || 0) > 0.4
                      ? '🟡 Concentração moderada - Distribuição razoável'
                      : '🟢 Baixa concentração - Vendas bem distribuídas'}
                </p>
              </div>
            </div>

            {/* Taxa de Concentração */}
            <div className="bg-white rounded-xl p-6 border border-orange-200">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-bold text-orange-900">Concentração Top 3</h3>
                <div className="w-16 h-16 rounded-full bg-orange-100 flex items-center justify-center">
                  <span className="text-2xl font-bold text-orange-700">
                    {(analise_temporal.concentracao_horaria.concentration_top_3 || 0).toFixed(0)}%
                  </span>
                </div>
              </div>
              <p className="text-sm text-gray-600 mb-2">
                Percentual do faturamento nos 3 melhores horários
              </p>
              <div className="bg-orange-50 p-3 rounded-lg">
                <p className="text-xs font-semibold text-orange-900 mb-1">Análise:</p>
                <p className="text-xs text-orange-700">
                  {(analise_temporal.concentracao_horaria.concentration_top_3 || 0) > 60
                    ? 'Risco alto - Dependência excessiva de poucos horários'
                    : 'Distribuição saudável de vendas'}
                </p>
              </div>
            </div>

            {/* Score de Diversificação */}
            <div className="bg-white rounded-xl p-6 border border-green-200">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-bold text-green-900">Diversificação</h3>
                <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center">
                  <span className="text-2xl font-bold text-green-700">
                    {(analise_temporal.concentracao_horaria.diversification || 0).toFixed(0)}%
                  </span>
                </div>
              </div>
              <p className="text-sm text-gray-600 mb-2">
                Quão bem distribuídas estão as vendas ao longo do dia
              </p>
              <div className="bg-green-50 p-3 rounded-lg">
                <p className="text-xs font-semibold text-green-900 mb-1">Status:</p>
                <p className="text-xs text-green-700">
                  {(analise_temporal.concentracao_horaria.diversification || 0) > 60
                    ? '✅ Boa diversificação - Menor risco operacional'
                    : '⚠️ Baixa diversificação - Considere estratégias para outros horários'}
                </p>
              </div>
            </div>
          </div>

          {/* Top Horários */}
          <div className="bg-white rounded-xl p-6 border border-rose-200">
            <h3 className="font-bold text-rose-900 mb-4">🏆 Top 5 Horários por Faturamento</h3>
            <div className="space-y-3">
              {(analise_temporal.concentracao_horaria.top_hours || []).map((hora, idx) => (
                <div key={hora.hora} className="flex items-center gap-4 p-3 bg-gradient-to-r from-rose-50 to-pink-50 rounded-lg">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${idx === 0 ? 'bg-yellow-400 text-yellow-900' :
                    idx === 1 ? 'bg-gray-300 text-gray-700' :
                      idx === 2 ? 'bg-orange-400 text-orange-900' :
                        'bg-rose-100 text-rose-700'
                    }`}>
                    {idx + 1}
                  </div>
                  <div className="flex-1">
                    <p className="font-bold text-gray-900">{hora.hora}h - {hora.hora + 1}h</p>
                    <p className="text-sm text-gray-600">
                      R$ {hora.faturamento.toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-rose-600">{hora.percentual.toFixed(1)}%</p>
                    <p className="text-xs text-gray-500">do total</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Recomendações Estratégicas */}
          <div className="mt-6 bg-white/80 rounded-xl p-6 border border-rose-200">
            <h3 className="font-bold text-rose-900 mb-4 flex items-center gap-2">
              <Lightbulb className="w-5 h-5" />
              💡 Recomendações Estratégicas Baseadas em Dados
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div className="flex items-start gap-3 p-3 bg-rose-50 rounded-lg">
                <span className="text-rose-600 font-bold">1.</span>
                <p className="text-gray-700">
                  <strong>Redução de Risco:</strong> Se concentração {'>'} 60%, crie promoções para horários fracos e diversifique receita.
                </p>
              </div>
              <div className="flex items-start gap-3 p-3 bg-pink-50 rounded-lg">
                <span className="text-pink-600 font-bold">2.</span>
                <p className="text-gray-700">
                  <strong>Otimização de Recursos:</strong> Aloque equipe e estoque proporcionalmente à concentração de vendas.
                </p>
              </div>
              <div className="flex items-start gap-3 p-3 bg-purple-50 rounded-lg">
                <span className="text-purple-600 font-bold">3.</span>
                <p className="text-gray-700">
                  <strong>Expansão de Horários:</strong> Teste novos produtos/serviços em horários de baixa concentração.
                </p>
              </div>
              <div className="flex items-start gap-3 p-3 bg-orange-50 rounded-lg">
                <span className="text-orange-600 font-bold">4.</span>
                <p className="text-gray-700">
                  <strong>Monitoramento Contínuo:</strong> Acompanhe o índice de Gini mensalmente para detectar mudanças de padrão.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 🔥 NOVO: ANÁLISE TEMPORAL AVANÇADA - PENSANDO COMO O DONO DO MERCADO */}
      {viewMode === 'avancado' && data?.data && (
        <div className="space-y-8 mb-8">
          {/* SEÇÃO 1: FATURAMENTO POR PERÍODO DO DIA */}
          {data.data.period_analysis && Object.keys(data.data.period_analysis).length > 0 && (
            <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-2xl shadow-xl p-6 border border-blue-200">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-3">
                <Clock className="w-8 h-8 text-blue-600" />
                ⏰ Análise por Período do Dia (Manhã/Tarde/Noite)
              </h2>
              <p className="text-gray-600 mb-6">Como varia o faturamento ao longo do dia? Qual período é mais lucrativo?</p>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {Object.entries(data.data.period_analysis).map(([periodo, dados]: [string, any]) => {
                  const periodoNome = periodo === 'manha' ? '🌅 Manhã (6h-12h)' :
                    periodo === 'tarde' ? '☀️ Tarde (12h-18h)' :
                      '🌙 Noite (18h-24h)';
                  const percentualTotal = (dados.faturamento / Object.values(data.data.period_analysis as any).reduce((sum: number, p: any) => sum + p.faturamento, 0)) * 100;

                  return (
                    <div key={periodo} className="bg-white rounded-xl p-6 border border-blue-100 hover:shadow-lg transition-shadow">
                      <h3 className="text-lg font-bold text-gray-900 mb-4">{periodoNome}</h3>

                      <div className="space-y-3">
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600">Faturamento:</span>
                          <span className="text-2xl font-bold text-blue-600">R$ {dados.faturamento.toLocaleString('pt-BR', { minimumFractionDigits: 0 })}</span>
                        </div>

                        <div className="flex justify-between items-center">
                          <span className="text-gray-600">% do Total:</span>
                          <span className="text-xl font-bold text-blue-500">{percentualTotal.toFixed(1)}%</span>
                        </div>

                        <div className="flex justify-between items-center">
                          <span className="text-gray-600">Vendas:</span>
                          <span className="font-semibold text-gray-900">{dados.vendas}</span>
                        </div>

                        <div className="flex justify-between items-center">
                          <span className="text-gray-600">Ticket Médio:</span>
                          <span className="font-semibold text-gray-900">R$ {dados.ticket_medio.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</span>
                        </div>

                        <div className="flex justify-between items-center">
                          <span className="text-gray-600">Por Hora:</span>
                          <span className="font-semibold text-gray-900">R$ {dados.faturamento_por_hora.toLocaleString('pt-BR', { minimumFractionDigits: 0 })}</span>
                        </div>
                      </div>

                      <div className="mt-4 pt-4 border-t border-blue-100">
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{ width: `${percentualTotal}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* SEÇÃO 2: ANÁLISE POR DIA DA SEMANA */}
          {data.data.weekday_analysis && Object.keys(data.data.weekday_analysis).length > 0 && (
            <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl shadow-xl p-6 border border-green-200">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-3">
                <Calendar className="w-8 h-8 text-green-600" />
                📅 Análise por Dia da Semana
              </h2>
              <p className="text-gray-600 mb-6">Sexta e sábado vendem mais? Qual dia pedir mais estoque?</p>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {Object.entries(data.data.weekday_analysis).map(([dia, dados]: [string, any]) => {
                  const totalFat = Object.values(data.data.weekday_analysis as any).reduce((sum: number, d: any) => sum + d.faturamento, 0);
                  const percentual = (dados.faturamento / totalFat) * 100;
                  const isWeekend = dia === 'Sexta' || dia === 'Sábado' || dia === 'Domingo';

                  return (
                    <div key={dia} className={`rounded-xl p-4 border ${isWeekend ? 'bg-yellow-50 border-yellow-200' : 'bg-white border-green-100'} hover:shadow-lg transition-shadow`}>
                      <h4 className="font-bold text-gray-900 mb-3">{dia}</h4>

                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Faturamento:</span>
                          <span className="font-semibold">R$ {dados.faturamento.toLocaleString('pt-BR', { minimumFractionDigits: 0 })}</span>
                        </div>

                        <div className="flex justify-between">
                          <span className="text-gray-600">Vendas:</span>
                          <span className="font-semibold">{dados.vendas}</span>
                        </div>

                        <div className="flex justify-between">
                          <span className="text-gray-600">Ticket:</span>
                          <span className="font-semibold">R$ {dados.ticket_medio.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</span>
                        </div>

                        <div className="mt-2 pt-2 border-t border-gray-200">
                          <div className="flex justify-between items-center">
                            <span className="text-xs text-gray-500">% do total:</span>
                            <span className="font-bold text-green-600">{percentual.toFixed(1)}%</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* SEÇÃO 3: RECOMENDAÇÕES DE ESTOQUE POR HORA */}
          {data.data.product_hourly_recommendations && data.data.product_hourly_recommendations.length > 0 && (
            <div className="bg-gradient-to-br from-orange-50 to-red-50 rounded-2xl shadow-xl p-6 border border-orange-200">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-3">
                <Package className="w-8 h-8 text-orange-600" />
                📦 Recomendações de Estoque por Hora
              </h2>
              <p className="text-gray-600 mb-6">Aumentar pão amanhã? Caprichar em cerveja sexta/sábado?</p>

              <div className="space-y-4">
                {data.data.product_hourly_recommendations.slice(0, 8).map((rec, idx) => (
                  <div key={idx} className={`rounded-lg p-4 border-l-4 ${rec.prioridade === 'alta' ? 'bg-red-50 border-red-500' :
                    rec.prioridade === 'media' ? 'bg-yellow-50 border-yellow-500' :
                      'bg-green-50 border-green-500'
                    }`}>
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h4 className="font-bold text-gray-900">{rec.produto}</h4>
                        <p className="text-sm text-gray-600">{rec.categoria} • {rec.periodo}</p>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-xs font-bold ${rec.prioridade === 'alta' ? 'bg-red-200 text-red-800' :
                        rec.prioridade === 'media' ? 'bg-yellow-200 text-yellow-800' :
                          'bg-green-200 text-green-800'
                        }`}>
                        {rec.prioridade === 'alta' ? '🔴 Alta' : rec.prioridade === 'media' ? '🟡 Média' : '🟢 Baixa'}
                      </span>
                    </div>

                    <p className="text-sm text-gray-700 mb-3">{rec.recomendacao}</p>

                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Qtd/Dia:</span>
                        <p className="font-bold text-gray-900">{rec.quantidade_vendida} un</p>
                      </div>
                      <div>
                        <span className="text-gray-600">Faturamento:</span>
                        <p className="font-bold text-gray-900">R$ {rec.faturamento.toLocaleString('pt-BR', { minimumFractionDigits: 0 })}</p>
                      </div>
                      <div>
                        <span className="text-gray-600">Frequência:</span>
                        <p className="font-bold text-gray-900">{rec.frequencia}x</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 🔥 NOVO: PAINEL DE RH */}
      {viewMode === 'rh' && rh && (
        <div className="space-y-6">
          {/* Cabeçalho RH */}
          <div className="bg-white rounded-xl shadow-lg p-6 border border-purple-200">
            <h2 className="text-2xl font-bold text-gray-900 mb-2 flex items-center gap-3">
              <Users className="w-8 h-8 text-purple-600" />
              Recursos Humanos & Departamento Pessoal
            </h2>
            <p className="text-gray-600">
              Visão consolidada de custos de folha, benefícios, assiduidade e horas extras.
            </p>
          </div>

          {/* Cards de KPI */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 gap-6">
            {/* Custo Total Estimado */}
            <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100 hover:shadow-lg transition-shadow">
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-purple-100 rounded-lg">
                  <DollarIcon className="w-6 h-6 text-purple-600" />
                </div>
                <span className="px-3 py-1 bg-purple-50 text-purple-700 text-xs font-bold rounded-full">Mensal</span>
              </div>
              <p className="text-gray-500 text-sm font-medium">Custo Total Folha (Est.)</p>
              <h3 className="text-2xl font-bold text-gray-900 mt-1">
                R$ {rh.custo_folha_estimado.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
              </h3>
              <p className="text-xs text-gray-400 mt-2">Salários + Benefícios + Extras</p>
            </div>

            {/* Funcionários Ativos */}
            <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100 hover:shadow-lg transition-shadow">
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-blue-100 rounded-lg">
                  <Users className="w-6 h-6 text-blue-600" />
                </div>
                <span className="px-3 py-1 bg-green-50 text-green-700 text-xs font-bold rounded-full">Ativos</span>
              </div>
              <p className="text-gray-500 text-sm font-medium">Colaboradores</p>
              <h3 className="text-2xl font-bold text-gray-900 mt-1">
                {rh.funcionarios_ativos}
              </h3>
              <p className="text-xs text-gray-400 mt-2">Registrados no sistema</p>
            </div>

            {/* Pontualidade */}
            <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100 hover:shadow-lg transition-shadow">
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-green-100 rounded-lg">
                  <Clock className="w-6 h-6 text-green-600" />
                </div>
                <span className={`px-3 py-1 text-xs font-bold rounded-full ${rh.taxa_pontualidade > 90 ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
                  }`}>
                  {rh.taxa_pontualidade}%
                </span>
              </div>
              <p className="text-gray-500 text-sm font-medium">Taxa de Pontualidade</p>
              <h3 className="text-2xl font-bold text-gray-900 mt-1">
                {rh.taxa_pontualidade}%
              </h3>
              <p className="text-xs text-gray-400 mt-2">{rh.total_atrasos_qtd} atrasos registrados</p>
            </div>

            {/* Horas Extras */}
            <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100 hover:shadow-lg transition-shadow">
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-orange-100 rounded-lg">
                  <AlertCircle className="w-6 h-6 text-orange-600" />
                </div>
                <span className="px-3 py-1 bg-orange-50 text-orange-700 text-xs font-bold rounded-full">Estimado</span>
              </div>
              <p className="text-gray-500 text-sm font-medium">Horas Extras (Custo)</p>
              <h3 className="text-2xl font-bold text-gray-900 mt-1">
                R$ {rh.custo_extras_estimado.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
              </h3>
              <p className="text-xs text-gray-400 mt-2">~{(rh.minutos_extras_estimados / 60).toFixed(1)} horas adicionais</p>
            </div>

            {/* Rotatividade (Turnover) */}
            <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100 hover:shadow-lg transition-shadow">
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-red-100 rounded-lg">
                  <TrendingUp className="w-6 h-6 text-red-600" />
                </div>
                <span className={`px-3 py-1 text-xs font-bold rounded-full ${(rh.turnover_rate || 0) > 5 ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'
                  }`}>
                  {(rh.turnover_rate || 0) > 5 ? 'Alto' : 'Normal'}
                </span>
              </div>
              <p className="text-gray-500 text-sm font-medium">Rotatividade (Turnover)</p>
              <h3 className="text-2xl font-bold text-gray-900 mt-1">
                {(rh.turnover_rate || 0).toFixed(1)}%
              </h3>
              <p className="text-xs text-gray-400 mt-2">
                +{rh.admissoes_periodo || 0} Adm. / -{rh.demissoes_periodo || 0} Dem.
              </p>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
            <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
              <ChartBar className="w-5 h-5 text-gray-500" />
              Resumo Mensal (RH)
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-xs text-gray-500 font-medium uppercase">Atrasos (min)</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{rh.resumo_mes?.total_atrasos_minutos || 0}</p>
                <p className="text-xs text-gray-400 mt-1">{rh.resumo_mes?.total_atrasos_qtd || 0} ocorrências</p>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-xs text-gray-500 font-medium uppercase">Horas Extras (h)</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{(((rh.resumo_mes?.total_extras_minutos || 0) / 60)).toFixed(1)}</p>
                <p className="text-xs text-gray-400 mt-1">{rh.resumo_mes?.total_extras_minutos || 0} min</p>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-xs text-gray-500 font-medium uppercase">Faltas (qtd)</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{rh.resumo_mes?.total_faltas || 0}</p>
                <p className="text-xs text-gray-400 mt-1">{rh.resumo_mes?.dias_uteis || 0} dias úteis (base)</p>
              </div>
              <div className="p-4 bg-purple-50 rounded-lg border border-purple-100">
                <p className="text-xs text-purple-600 font-medium uppercase">Período</p>
                <p className="text-sm font-bold text-purple-900 mt-2">
                  {rh.resumo_mes?.inicio ? new Date(rh.resumo_mes.inicio).toLocaleDateString('pt-BR') : '-'} — {rh.resumo_mes?.fim ? new Date(rh.resumo_mes.fim).toLocaleDateString('pt-BR') : '-'}
                </p>
                <p className="text-xs text-purple-700 mt-2">Mês corrente (acumulado)</p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
              <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-red-500" />
                Atrasos por Funcionário (Mês)
              </h3>
              <div className="overflow-x-auto max-h-[320px] overflow-y-auto">
                <table className="w-full text-sm text-left">
                  <thead className="bg-gray-50 text-gray-600 font-medium sticky top-0">
                    <tr>
                      <th className="px-4 py-3 rounded-l-lg">Funcionário</th>
                      <th className="px-4 py-3">Cargo</th>
                      <th className="px-4 py-3">Ocorrências</th>
                      <th className="px-4 py-3 rounded-r-lg text-right">Minutos</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {rh.atrasos_por_funcionario_mes && rh.atrasos_por_funcionario_mes.length > 0 ? (
                      rh.atrasos_por_funcionario_mes.map((row, idx) => (
                        <tr key={`atraso-${row.funcionario_id}-${idx}`} className="hover:bg-gray-50 transition-colors">
                          <td className="px-4 py-3 font-medium text-gray-900">{row.nome}</td>
                          <td className="px-4 py-3 text-gray-600">{row.cargo}</td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-1 text-xs font-bold rounded-full ${row.atrasos_qtd > 0 ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
                              {row.atrasos_qtd}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-right font-bold text-gray-900">{row.minutos_atraso}m</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={4} className="px-4 py-8 text-center text-gray-400">Sem dados de atrasos no mês</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
              <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-orange-500" />
                Horas Extras por Funcionário (Mês)
              </h3>
              <div className="overflow-x-auto max-h-[320px] overflow-y-auto">
                <table className="w-full text-sm text-left">
                  <thead className="bg-gray-50 text-gray-600 font-medium sticky top-0">
                    <tr>
                      <th className="px-4 py-3 rounded-l-lg">Funcionário</th>
                      <th className="px-4 py-3">Cargo</th>
                      <th className="px-4 py-3">Horas</th>
                      <th className="px-4 py-3 rounded-r-lg text-right">Custo Est.</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {rh.horas_extras_por_funcionario_mes && rh.horas_extras_por_funcionario_mes.length > 0 ? (
                      rh.horas_extras_por_funcionario_mes.map((row, idx) => (
                        <tr key={`extras-${row.funcionario_id}-${idx}`} className="hover:bg-gray-50 transition-colors">
                          <td className="px-4 py-3 font-medium text-gray-900">{row.nome}</td>
                          <td className="px-4 py-3 text-gray-600">{row.cargo}</td>
                          <td className="px-4 py-3 font-bold text-orange-600">{(row.minutos_extras / 60).toFixed(1)}h</td>
                          <td className="px-4 py-3 text-right font-bold text-gray-900">R$ {row.custo_extras.toFixed(2)}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={4} className="px-4 py-8 text-center text-gray-400">Sem horas extras no mês</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
              <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-yellow-600" />
                Faltas por Funcionário (Mês)
              </h3>
              <div className="overflow-x-auto max-h-[320px] overflow-y-auto">
                <table className="w-full text-sm text-left">
                  <thead className="bg-gray-50 text-gray-600 font-medium sticky top-0">
                    <tr>
                      <th className="px-4 py-3 rounded-l-lg">Funcionário</th>
                      <th className="px-4 py-3">Cargo</th>
                      <th className="px-4 py-3">Presença</th>
                      <th className="px-4 py-3 rounded-r-lg text-right">Faltas</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {rh.faltas_por_funcionario_mes && rh.faltas_por_funcionario_mes.length > 0 ? (
                      rh.faltas_por_funcionario_mes.map((row, idx) => (
                        <tr key={`faltas-${row.funcionario_id}-${idx}`} className="hover:bg-gray-50 transition-colors">
                          <td className="px-4 py-3 font-medium text-gray-900">{row.nome}</td>
                          <td className="px-4 py-3 text-gray-600">{row.cargo}</td>
                          <td className="px-4 py-3 text-gray-900">{row.dias_presenca}/{row.dias_uteis}</td>
                          <td className="px-4 py-3 text-right font-bold text-gray-900">{row.faltas}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={4} className="px-4 py-8 text-center text-gray-400">Sem dados de faltas</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
              <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                <GitMerge className="w-5 h-5 text-blue-600" />
                Banco de Horas (Mês)
              </h3>
              <div className="overflow-x-auto max-h-[320px] overflow-y-auto">
                <table className="w-full text-sm text-left">
                  <thead className="bg-gray-50 text-gray-600 font-medium sticky top-0">
                    <tr>
                      <th className="px-4 py-3 rounded-l-lg">Funcionário</th>
                      <th className="px-4 py-3">Cargo</th>
                      <th className="px-4 py-3">Saldo</th>
                      <th className="px-4 py-3 rounded-r-lg text-right">Valor Acum.</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {rh.banco_horas_por_funcionario_mes && rh.banco_horas_por_funcionario_mes.length > 0 ? (
                      rh.banco_horas_por_funcionario_mes.map((row, idx) => (
                        <tr key={`banco-${row.funcionario_id}-${idx}`} className="hover:bg-gray-50 transition-colors">
                          <td className="px-4 py-3 font-medium text-gray-900">{row.nome}</td>
                          <td className="px-4 py-3 text-gray-600">{row.cargo}</td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-1 text-xs font-bold rounded-full ${row.saldo_minutos > 0 ? 'bg-green-100 text-green-700' : row.saldo_minutos < 0 ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-700'}`}>
                              {(row.saldo_minutos / 60).toFixed(1)}h
                            </span>
                          </td>
                          <td className="px-4 py-3 text-right font-bold text-gray-900">R$ {row.valor_hora_extra.toFixed(2)}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={4} className="px-4 py-8 text-center text-gray-400">Banco de horas não calculado/registrado</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
            <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
              <DollarIcon className="w-5 h-5 text-purple-600" />
              Espelho de Pagamento (Estimado - Mês)
            </h3>
            <div className="overflow-x-auto max-h-[380px] overflow-y-auto">
              <table className="w-full text-sm text-left">
                <thead className="bg-gray-50 text-gray-600 font-medium sticky top-0">
                  <tr>
                    <th className="px-4 py-3 rounded-l-lg">Funcionário</th>
                    <th className="px-4 py-3">Salário</th>
                    <th className="px-4 py-3">Benefícios</th>
                    <th className="px-4 py-3">Extras</th>
                    <th className="px-4 py-3">Faltas</th>
                    <th className="px-4 py-3">Atraso</th>
                    <th className="px-4 py-3 rounded-r-lg text-right">Total Est.</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {rh.espelho_pagamento_mes && rh.espelho_pagamento_mes.length > 0 ? (
                    rh.espelho_pagamento_mes.map((row, idx) => (
                      <tr key={idx} className="hover:bg-gray-50 transition-colors">
                        <td className="px-4 py-3">
                          <p className="font-medium text-gray-900">{row.nome}</p>
                          <p className="text-xs text-gray-500">{row.cargo}</p>
                        </td>
                        <td className="px-4 py-3 text-gray-900">R$ {row.salario_base.toFixed(2)}</td>
                        <td className="px-4 py-3 text-gray-900">R$ {row.beneficios.toFixed(2)}</td>
                        <td className="px-4 py-3 text-gray-900">{row.horas_extras_horas.toFixed(1)}h / R$ {row.custo_horas_extras.toFixed(2)}</td>
                        <td className="px-4 py-3 text-gray-900">{row.faltas}</td>
                        <td className="px-4 py-3 text-gray-900">{row.atrasos_minutos}m</td>
                        <td className="px-4 py-3 text-right font-bold text-gray-900">R$ {row.total_estimado.toFixed(2)}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={7} className="px-4 py-10 text-center text-gray-400">Sem dados para espelho de pagamento</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Detalhamento Avançado RH */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Gráfico de Evolução de Turnover */}
            <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
              <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-gray-500" />
                Histórico de Admissões, Demissões, Ausências, Atrasos e Horas Extras
              </h3>
              <div className="h-[400px]">
                {rh.evolution_turnover && rh.evolution_turnover.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={rh.evolution_turnover}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="mes" tick={{ fontSize: 12 }} />
                      <YAxis tick={{ fontSize: 12 }} />
                      <Tooltip
                        contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                      />
                      <Legend />
                      <Bar dataKey="admissoes" name="Admissões" fill="#10B981" />
                      <Bar dataKey="demissoes" name="Demissões" fill="#EF4444" />
                      <Bar dataKey="ausencias" name="Ausências" fill="#F59E0B" />
                      <Bar dataKey="atrasos" name="Atrasos" fill="#8B5CF6" />
                      <Bar dataKey="horas_extras" name="H. Extras" fill="#06B6D4" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-full flex items-center justify-center text-gray-400">
                    Sem dados históricos suficientes
                  </div>
                )}
              </div>
            </div>

            {/* Top Funcionários com Horas Extras */}
            <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
              <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-orange-500" />
                Top Horas Extras (Custo Estimado)
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="bg-gray-50 text-gray-600 font-medium">
                    <tr>
                      <th className="px-4 py-3 rounded-l-lg">Colaborador</th>
                      <th className="px-4 py-3">Horas Extras</th>
                      <th className="px-4 py-3 rounded-r-lg text-right">Custo Est.</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {rh.top_overtime_employees && rh.top_overtime_employees.length > 0 ? (
                      rh.top_overtime_employees.map((func, idx) => (
                        <tr key={idx} className="hover:bg-gray-50 transition-colors">
                          <td className="px-4 py-3 font-medium text-gray-900">{func.nome}</td>
                          <td className="px-4 py-3 text-orange-600 font-bold">{func.horas}h</td>
                          <td className="px-4 py-3 text-right font-bold text-gray-900">
                            R$ {func.custo_estimado.toFixed(2)}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={3} className="px-4 py-8 text-center text-gray-400">
                          Nenhum registro de hora extra no período
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Gráficos de Composição Financeira RH */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Composição de Custos */}
            <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100 lg:col-span-1">
              <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                <DollarIcon className="w-5 h-5 text-gray-500" />
                Composição de Custos
              </h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-gray-700 font-medium">Salários Base</span>
                  <span className="font-bold text-gray-900">R$ {rh.total_salarios.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-gray-700 font-medium">Benefícios (VR/VA/VT)</span>
                  <span className="font-bold text-gray-900">R$ {rh.total_beneficios_mensal.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-orange-50 rounded-lg border border-orange-100">
                  <span className="text-orange-800 font-medium">Horas Extras (Est.)</span>
                  <span className="font-bold text-orange-900">R$ {rh.custo_extras_estimado.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</span>
                </div>
                <div className="pt-4 border-t border-gray-200 flex justify-between items-center">
                  <span className="text-lg font-bold text-gray-900">Total</span>
                  <span className="text-xl font-bold text-purple-700">R$ {rh.custo_folha_estimado.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</span>
                </div>
              </div>
            </div>

            {/* Distribuição de Benefícios */}
            <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100 lg:col-span-2">
              <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                <Target className="w-5 h-5 text-gray-500" />
                Distribuição de Benefícios
              </h3>
              <div className="h-[250px]">
                {rh.benefits_breakdown && rh.benefits_breakdown.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={rh.benefits_breakdown} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f0f0f0" />
                      <XAxis type="number" tickFormatter={(value) => `R$${value}`} />
                      <YAxis dataKey="name" type="category" width={100} tick={{ fontSize: 12 }} />
                      <Tooltip cursor={{ fill: 'transparent' }} formatter={(value: number) => [`R$ ${value.toFixed(2)}`, 'Custo']} />
                      <Bar dataKey="value" fill="#8884d8" radius={[0, 4, 4, 0]}>
                        {rh.benefits_breakdown.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-full flex items-center justify-center text-gray-400">
                    Sem dados de benefícios detalhados
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
              <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                <LineChartIcon className="w-5 h-5 text-gray-500" />
                Tendência de Horas Extras (14 dias)
              </h3>
              <div className="h-[280px]">
                {rh.overtime_trend && rh.overtime_trend.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={rh.overtime_trend} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="data" tick={{ fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip formatter={(value: number, name: string) => {
                        if (name === 'custo_extras') return [`R$ ${value.toFixed(2)}`, 'Custo'];
                        if (name === 'minutos_extras') return [`${(value / 60).toFixed(1)}h`, 'Horas'];
                        return [value, name];
                      }} />
                      <Line type="monotone" dataKey="minutos_extras" stroke="#F97316" strokeWidth={2} dot={false} />
                      <Line type="monotone" dataKey="custo_extras" stroke="#8B5CF6" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-full flex items-center justify-center text-gray-400">
                    Sem dados de horas extras no período
                  </div>
                )}
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
              <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                <Clock className="w-5 h-5 text-gray-500" />
                Resumo Diário de Ponto (7 dias)
              </h3>
              <div className="overflow-x-auto max-h-[280px] overflow-y-auto">
                <table className="w-full text-sm text-left">
                  <thead className="bg-gray-50 text-gray-600 font-medium sticky top-0">
                    <tr>
                      <th className="px-4 py-3 rounded-l-lg">Data</th>
                      <th className="px-4 py-3">Funcionário</th>
                      <th className="px-4 py-3">Entrada</th>
                      <th className="px-4 py-3">Saída</th>
                      <th className="px-4 py-3">Atraso</th>
                      <th className="px-4 py-3 rounded-r-lg">Extras</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {rh.daily_ponto_summary && rh.daily_ponto_summary.length > 0 ? (
                      rh.daily_ponto_summary.map((row, idx) => (
                        <tr key={idx} className="hover:bg-gray-50 transition-colors">
                          <td className="px-4 py-3 font-medium text-gray-900">
                            {new Date(row.data).toLocaleDateString('pt-BR')}
                          </td>
                          <td className="px-4 py-3 text-gray-900">{row.funcionario}</td>
                          <td className="px-4 py-3 text-gray-900">{row.entrada}</td>
                          <td className="px-4 py-3 text-gray-900">{row.saida}</td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-1 text-xs font-bold rounded-full ${row.minutos_atraso > 0 ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
                              {row.minutos_atraso > 0 ? `${row.minutos_atraso}m` : '0m'}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-1 text-xs font-bold rounded-full ${row.minutos_extras > 0 ? 'bg-orange-100 text-orange-700' : 'bg-gray-100 text-gray-700'}`}>
                              {row.minutos_extras > 0 ? `${(row.minutos_extras / 60).toFixed(1)}h` : '0h'}
                            </span>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={6} className="px-4 py-8 text-center text-gray-400">
                          Sem registros suficientes para o resumo diário
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Indicadores de Assiduidade */}
            <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
              <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                <Clock className="w-5 h-5 text-gray-500" />
                Assiduidade e Pontualidade
              </h3>
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="p-4 bg-blue-50 rounded-lg text-center">
                  <p className="text-2xl font-bold text-blue-700">{rh.total_entradas_periodo}</p>
                  <p className="text-xs text-blue-600 font-medium uppercase mt-1">Registros de Entrada</p>
                </div>
                <div className="p-4 bg-red-50 rounded-lg text-center">
                  <p className="text-2xl font-bold text-red-700">{rh.total_atrasos_qtd}</p>
                  <p className="text-xs text-red-600 font-medium uppercase mt-1">Atrasos</p>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex justify-between text-sm mb-1">
                  <span className="font-medium text-gray-700">Taxa de Pontualidade</span>
                  <span className="font-bold text-gray-900">{rh.taxa_pontualidade}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div
                    className={`h-2.5 rounded-full ${rh.taxa_pontualidade > 90 ? 'bg-green-500' : rh.taxa_pontualidade > 80 ? 'bg-yellow-500' : 'bg-red-500'}`}
                    style={{ width: `${rh.taxa_pontualidade}%` }}
                  ></div>
                </div>
                <p className="text-xs text-gray-500 mt-2 text-center">
                  Total acumulado de atrasos: <strong>{rh.total_minutos_atraso} minutos</strong> neste período.
                </p>
              </div>

              <div className="mt-4 p-4 bg-purple-50 rounded-lg border border-purple-100">
                <div className="flex gap-3">
                  <Lightbulb className="w-5 h-5 text-purple-600 flex-shrink-0" />
                  <div>
                    <h4 className="font-bold text-purple-900 text-sm">Dica de Gestão</h4>
                    <p className="text-xs text-purple-800 mt-1">
                      Acompanhe os atrasos recorrentes. O custo de horas extras pode ser reduzido ajustando escalas ou compensando horas.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Status da Equipe (Hoje) */}
            <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
              <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                <Users className="w-5 h-5 text-blue-500" />
                Status da Equipe (Hoje)
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="bg-gray-50 text-gray-600 font-medium">
                    <tr>
                      <th className="px-4 py-3 rounded-l-lg">Colaborador</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3 rounded-r-lg text-right">Último Registro</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {rh.team_status_today && rh.team_status_today.length > 0 ? (
                      rh.team_status_today.map((func, idx) => (
                        <tr key={idx} className="hover:bg-gray-50 transition-colors">
                          <td className="px-4 py-3">
                            <p className="font-medium text-gray-900">{func.nome}</p>
                            <p className="text-xs text-gray-500">{func.cargo}</p>
                          </td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-1 text-xs font-bold rounded-full ${func.status === 'Em Trabalho' ? 'bg-green-100 text-green-700' :
                              func.status === 'Almoço' ? 'bg-yellow-100 text-yellow-700' :
                                func.status === 'Saiu' ? 'bg-gray-100 text-gray-700' :
                                  'bg-red-100 text-red-700'
                              }`}>
                              {func.status}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-right font-medium text-gray-900">
                            {func.ultimo_registro}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={3} className="px-4 py-8 text-center text-gray-400">
                          Nenhuma atividade registrada hoje
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Últimos Registros de Ponto */}
          <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
            <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Clock className="w-5 h-5 text-gray-500" />
              Últimos Registros de Ponto (Listagem)
            </h3>
            <div className="overflow-x-auto max-h-[300px] overflow-y-auto">
              <table className="w-full text-sm text-left">
                <thead className="bg-gray-50 text-gray-600 font-medium sticky top-0">
                  <tr>
                    <th className="px-4 py-3 rounded-l-lg">Data</th>
                    <th className="px-4 py-3">Hora</th>
                    <th className="px-4 py-3">Funcionário</th>
                    <th className="px-4 py-3 rounded-r-lg">Tipo</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {rh.recent_points && rh.recent_points.length > 0 ? (
                    rh.recent_points.map((ponto, idx) => (
                      <tr key={idx} className="hover:bg-gray-50 transition-colors">
                        <td className="px-4 py-3 font-medium text-gray-900">{ponto.data}</td>
                        <td className="px-4 py-3 text-gray-900">{ponto.hora}</td>
                        <td className="px-4 py-3 text-gray-900">{ponto.funcionario}</td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-1 text-xs font-bold rounded-full ${ponto.tipo === 'entrada' ? 'bg-green-100 text-green-700' :
                            ponto.tipo === 'saida' ? 'bg-red-100 text-red-700' :
                              'bg-yellow-100 text-yellow-700'
                            }`}>
                            {ponto.tipo === 'entrada' ? 'Entrada' :
                              ponto.tipo === 'saida' ? 'Saída' :
                                ponto.tipo === 'saida_almoco' ? 'Saída Almoço' :
                                  ponto.tipo === 'retorno_almoco' ? 'Retorno Almoço' : ponto.tipo}
                          </span>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={4} className="px-4 py-8 text-center text-gray-400">
                        Nenhum registro de ponto encontrado
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* 🔥 NOVO: MODAL DE PRODUTO ESTRELA COM PLANO DE AÇÃO */}
      {modalProdutoEstrela && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto shadow-2xl">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gradient-to-r from-yellow-50 to-orange-50">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-gradient-to-r from-yellow-500 to-orange-500 rounded-lg flex items-center justify-center">
                  <Star className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">⭐ {modalProdutoEstrela.nome}</h2>
                  <p className="text-sm text-gray-600">Produto Estrela - Alta Performance</p>
                </div>
              </div>
              <button
                onClick={() => setModalProdutoEstrela(null)}
                className="p-2 hover:bg-white rounded-lg transition-colors"
              >
                <X className="w-6 h-6 text-gray-600" />
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Métricas Principais */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl p-4 border border-green-200">
                  <p className="text-sm text-green-700 mb-1">💰 Preço de Venda</p>
                  <p className="text-2xl font-bold text-green-900">
                    R$ {(modalProdutoEstrela.faturamento / modalProdutoEstrela.quantidade_vendida).toFixed(2)}
                  </p>
                </div>
                <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-xl p-4 border border-blue-200">
                  <p className="text-sm text-blue-700 mb-1">📦 Custo Unitário</p>
                  <p className="text-2xl font-bold text-blue-900">
                    R$ {modalProdutoEstrela.custo_unitario.toFixed(2)}
                  </p>
                </div>
                <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-4 border border-purple-200">
                  <p className="text-sm text-purple-700 mb-1">📈 Margem de Lucro</p>
                  <p className="text-2xl font-bold text-purple-900">
                    {modalProdutoEstrela.margem.toFixed(1)}%
                  </p>
                </div>
                <div className="bg-gradient-to-br from-orange-50 to-red-50 rounded-xl p-4 border border-orange-200">
                  <p className="text-sm text-orange-700 mb-1">🎯 Vendas (30d)</p>
                  <p className="text-2xl font-bold text-orange-900">
                    {modalProdutoEstrela.quantidade_vendida} un
                  </p>
                </div>
              </div>

              {/* Análise Financeira */}
              <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl p-6 border border-green-200">
                <h3 className="font-bold text-green-900 mb-4 flex items-center gap-2">
                  <DollarIcon className="w-5 h-5" />
                  💵 Análise Financeira Detalhada
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-white/70 p-4 rounded-lg">
                    <p className="text-sm text-gray-600 mb-1">Faturamento Total</p>
                    <p className="text-xl font-bold text-green-700">R$ {modalProdutoEstrela.faturamento.toFixed(2)}</p>
                  </div>
                  <div className="bg-white/70 p-4 rounded-lg">
                    <p className="text-sm text-gray-600 mb-1">Lucro Total</p>
                    <p className="text-xl font-bold text-blue-700">
                      R$ {(modalProdutoEstrela.faturamento - (modalProdutoEstrela.custo_unitario * modalProdutoEstrela.quantidade_vendida)).toFixed(2)}
                    </p>
                  </div>
                  <div className="bg-white/70 p-4 rounded-lg">
                    <p className="text-sm text-gray-600 mb-1">Lucro por Unidade</p>
                    <p className="text-xl font-bold text-purple-700">
                      R$ {((modalProdutoEstrela.faturamento / modalProdutoEstrela.quantidade_vendida) - modalProdutoEstrela.custo_unitario).toFixed(2)}
                    </p>
                  </div>
                </div>
              </div>

              {/* Plano de Ação */}
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-200">
                <h3 className="font-bold text-blue-900 mb-4 flex items-center gap-2">
                  <Target className="w-5 h-5" />
                  🎯 Plano de Ação Estratégico
                </h3>
                <div className="space-y-3">
                  <div className="bg-white/70 p-4 rounded-lg">
                    <p className="font-semibold text-blue-900 mb-2">1. Gestão de Estoque</p>
                    <p className="text-sm text-gray-700 mb-2">
                      • <strong>Demanda Diária:</strong> {(modalProdutoEstrela.quantidade_vendida / periodoDias).toFixed(1)} unidades/dia
                    </p>
                    <p className="text-sm text-gray-700 mb-2">
                      • <strong>Estoque Recomendado:</strong> {Math.ceil((modalProdutoEstrela.quantidade_vendida / periodoDias) * 15)} unidades (15 dias)
                    </p>
                    <p className="text-sm text-gray-700">
                      • <strong>Ponto de Reposição:</strong> {Math.ceil((modalProdutoEstrela.quantidade_vendida / periodoDias) * 7)} unidades (7 dias)
                    </p>
                  </div>

                  <div className="bg-white/70 p-4 rounded-lg">
                    <p className="font-semibold text-green-900 mb-2">2. Estratégia de Precificação</p>
                    <p className="text-sm text-gray-700 mb-2">
                      • <strong>Margem Atual:</strong> {modalProdutoEstrela.margem.toFixed(1)}% - {modalProdutoEstrela.margem > 30 ? '✅ Excelente' : modalProdutoEstrela.margem > 20 ? '✅ Boa' : '⚠️ Revisar'}
                    </p>
                    <p className="text-sm text-gray-700 mb-2">
                      • <strong>Potencial de Aumento:</strong> Teste aumentar 5-10% e monitore vendas
                    </p>
                    <p className="text-sm text-gray-700">
                      • <strong>Combos Sugeridos:</strong> Crie kits com produtos complementares
                    </p>
                  </div>

                  <div className="bg-white/70 p-4 rounded-lg">
                    <p className="font-semibold text-purple-900 mb-2">3. Marketing e Exposição</p>
                    <p className="text-sm text-gray-700 mb-2">
                      • <strong>Posicionamento:</strong> Coloque em local de destaque (altura dos olhos)
                    </p>
                    <p className="text-sm text-gray-700 mb-2">
                      • <strong>Promoções:</strong> "Leve 3, Pague 2" para aumentar volume
                    </p>
                    <p className="text-sm text-gray-700">
                      • <strong>Comunicação:</strong> Destaque como "Mais Vendido" ou "Favorito dos Clientes"
                    </p>
                  </div>

                  <div className="bg-white/70 p-4 rounded-lg">
                    <p className="font-semibold text-orange-900 mb-2">4. Análise de Fornecedor</p>
                    <p className="text-sm text-gray-700 mb-2">
                      • <strong>Negociação:</strong> Com alto volume, negocie desconto de 5-10%
                    </p>
                    <p className="text-sm text-gray-700 mb-2">
                      • <strong>Pagamento:</strong> Solicite prazo maior (30-45 dias)
                    </p>
                    <p className="text-sm text-gray-700">
                      • <strong>Alternativas:</strong> Pesquise 2-3 fornecedores para comparar
                    </p>
                  </div>
                </div>
              </div>

              {/* Projeções */}
              <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl p-6 border border-purple-200">
                <h3 className="font-bold text-purple-900 mb-4 flex items-center gap-2">
                  <TrendingUp className="w-5 h-5" />
                  📊 Projeções e Metas
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-white/70 p-4 rounded-lg">
                    <p className="text-sm text-gray-600 mb-2">Projeção Próximos 30 Dias</p>
                    <p className="text-xl font-bold text-purple-700">
                      {modalProdutoEstrela.quantidade_vendida} unidades
                    </p>
                    <p className="text-sm text-gray-600 mt-1">
                      Faturamento: R$ {modalProdutoEstrela.faturamento.toFixed(2)}
                    </p>
                  </div>
                  <div className="bg-white/70 p-4 rounded-lg">
                    <p className="text-sm text-gray-600 mb-2">Meta de Crescimento (+10%)</p>
                    <p className="text-xl font-bold text-green-700">
                      {Math.ceil(modalProdutoEstrela.quantidade_vendida * 1.1)} unidades
                    </p>
                    <p className="text-sm text-gray-600 mt-1">
                      Faturamento: R$ {(modalProdutoEstrela.faturamento * 1.1).toFixed(2)}
                    </p>
                  </div>
                </div>
              </div>

              {/* Alertas */}
              <div className="bg-gradient-to-r from-yellow-50 to-amber-50 rounded-xl p-6 border border-yellow-200">
                <h3 className="font-bold text-yellow-900 mb-4 flex items-center gap-2">
                  <AlertCircle className="w-5 h-5" />
                  ⚠️ Alertas e Cuidados
                </h3>
                <div className="space-y-2 text-sm text-gray-700">
                  <p>• <strong>Ruptura de Estoque:</strong> Nunca deixe faltar! Perda de vendas e clientes.</p>
                  <p>• <strong>Validade:</strong> Se perecível, monitore prazo de validade rigorosamente.</p>
                  <p>• <strong>Concorrência:</strong> Acompanhe preços dos concorrentes semanalmente.</p>
                  <p>• <strong>Sazonalidade:</strong> Produto pode ter variação sazonal - ajuste estoque.</p>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="flex justify-end gap-3 p-6 border-t border-gray-200 bg-gray-50">
              <button
                onClick={() => setModalProdutoEstrela(null)}
                className="px-6 py-2 bg-white text-gray-700 rounded-lg hover:bg-gray-100 transition-colors font-medium border border-gray-300"
              >
                Fechar
              </button>
              <button
                onClick={() => {
                  alert('Funcionalidade de impressão em desenvolvimento');
                }}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                📄 Imprimir Plano
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 🔥 NOVO: MODAL DE PRODUTO LENTO COM ESTRATÉGIAS DE LIQUIDAÇÃO */}
      {modalProdutoLento && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto shadow-2xl">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gradient-to-r from-red-50 to-pink-50">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-gradient-to-r from-red-500 to-pink-500 rounded-lg flex items-center justify-center">
                  <AlertTriangle className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">⚠️ {modalProdutoLento.nome}</h2>
                  <p className="text-sm text-gray-600">Produto Lento - Requer Ação Imediata</p>
                </div>
              </div>
              <button
                onClick={() => setModalProdutoLento(null)}
                className="p-2 hover:bg-white rounded-lg transition-colors"
              >
                <X className="w-6 h-6 text-gray-600" />
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Diagnóstico do Problema */}
              <div className="bg-gradient-to-r from-red-50 to-pink-50 rounded-xl p-6 border border-red-200">
                <h3 className="font-bold text-red-900 mb-4 flex items-center gap-2">
                  <AlertCircle className="w-5 h-5" />
                  🔍 Diagnóstico do Problema
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-white/70 p-4 rounded-lg">
                    <p className="text-sm text-gray-600 mb-1">Estoque Parado</p>
                    <p className="text-2xl font-bold text-red-700">{modalProdutoLento.estoque_atual} un</p>
                  </div>
                  <div className="bg-white/70 p-4 rounded-lg">
                    <p className="text-sm text-gray-600 mb-1">Capital Parado</p>
                    <p className="text-2xl font-bold text-orange-700">R$ {modalProdutoLento.custo_parado.toFixed(2)}</p>
                  </div>
                  <div className="bg-white/70 p-4 rounded-lg">
                    <p className="text-sm text-gray-600 mb-1">Perda Mensal</p>
                    <p className="text-2xl font-bold text-red-700">R$ {modalProdutoLento.perda_mensal.toFixed(2)}</p>
                  </div>
                  <div className="bg-white/70 p-4 rounded-lg">
                    <p className="text-sm text-gray-600 mb-1">Giro de Estoque</p>
                    <p className="text-2xl font-bold text-purple-700">{modalProdutoLento.giro_estoque.toFixed(2)}x</p>
                  </div>
                </div>
                <div className="mt-4 bg-red-100 border border-red-300 rounded-lg p-4">
                  <p className="text-sm text-red-900">
                    <strong>⚠️ Alerta:</strong> Este produto está consumindo capital que poderia ser investido em produtos mais rentáveis.
                    Tempo estimado para vender estoque atual: <strong>{modalProdutoLento.dias_estoque} dias</strong>
                  </p>
                </div>
              </div>

              {/* Estratégias de Liquidação */}
              <div className="bg-gradient-to-r from-orange-50 to-yellow-50 rounded-xl p-6 border border-orange-200">
                <h3 className="font-bold text-orange-900 mb-4 flex items-center gap-2">
                  <Target className="w-5 h-5" />
                  🎯 Estratégias de Liquidação (Prioridade Alta)
                </h3>
                <div className="space-y-3">
                  <div className="bg-white/70 p-4 rounded-lg border-l-4 border-red-500">
                    <p className="font-semibold text-red-900 mb-2">1. Promoção Relâmpago (Ação Imediata)</p>
                    <p className="text-sm text-gray-700 mb-2">
                      • <strong>Desconto Sugerido:</strong> 30-40% OFF por 7 dias
                    </p>
                    <p className="text-sm text-gray-700 mb-2">
                      • <strong>Comunicação:</strong> "Queima de Estoque - Últimas Unidades!"
                    </p>
                    <p className="text-sm text-gray-700">
                      • <strong>Meta:</strong> Vender pelo menos 50% do estoque em 1 semana
                    </p>
                  </div>

                  <div className="bg-white/70 p-4 rounded-lg border-l-4 border-orange-500">
                    <p className="font-semibold text-orange-900 mb-2">2. Combos Estratégicos</p>
                    <p className="text-sm text-gray-700 mb-2">
                      • <strong>Combo 1:</strong> "Leve este produto + Produto Estrela" com 20% OFF
                    </p>
                    <p className="text-sm text-gray-700 mb-2">
                      • <strong>Combo 2:</strong> "Leve 2, Pague 1,5" (50% OFF na 2ª unidade)
                    </p>
                    <p className="text-sm text-gray-700">
                      • <strong>Posicionamento:</strong> Coloque ao lado de produtos de alta rotação
                    </p>
                  </div>

                  <div className="bg-white/70 p-4 rounded-lg border-l-4 border-yellow-500">
                    <p className="font-semibold text-yellow-900 mb-2">3. Programa de Fidelidade</p>
                    <p className="text-sm text-gray-700 mb-2">
                      • <strong>Pontos Dobrados:</strong> Ganhe 2x pontos comprando este produto
                    </p>
                    <p className="text-sm text-gray-700 mb-2">
                      • <strong>Brinde:</strong> Na compra de 3 unidades, ganhe 1 grátis
                    </p>
                    <p className="text-sm text-gray-700">
                      • <strong>Sorteio:</strong> Cada compra = 1 cupom para sorteio mensal
                    </p>
                  </div>

                  <div className="bg-white/70 p-4 rounded-lg border-l-4 border-green-500">
                    <p className="font-semibold text-green-900 mb-2">4. Venda para Clientes VIP</p>
                    <p className="text-sm text-gray-700 mb-2">
                      • <strong>WhatsApp:</strong> Envie oferta exclusiva para top 20 clientes
                    </p>
                    <p className="text-sm text-gray-700 mb-2">
                      • <strong>Mensagem:</strong> "Oferta VIP só para você: {modalProdutoLento.nome} com 35% OFF"
                    </p>
                    <p className="text-sm text-gray-700">
                      • <strong>Urgência:</strong> "Válido apenas hoje até 18h"
                    </p>
                  </div>
                </div>
              </div>

              {/* Análise Financeira da Liquidação */}
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-200">
                <h3 className="font-bold text-blue-900 mb-4 flex items-center gap-2">
                  <DollarIcon className="w-5 h-5" />
                  💰 Análise Financeira da Liquidação
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-white/70 p-4 rounded-lg">
                    <p className="text-sm text-gray-600 mb-2">Cenário Atual (Sem Ação)</p>
                    <p className="text-xl font-bold text-red-700">
                      - R$ {modalProdutoLento.perda_mensal.toFixed(2)}/mês
                    </p>
                    <p className="text-xs text-gray-600 mt-1">Perda de oportunidade</p>
                  </div>
                  <div className="bg-white/70 p-4 rounded-lg">
                    <p className="text-sm text-gray-600 mb-2">Com Desconto 30%</p>
                    <p className="text-xl font-bold text-orange-700">
                      R$ {(modalProdutoLento.custo_parado * 0.7).toFixed(2)}
                    </p>
                    <p className="text-xs text-gray-600 mt-1">Recuperação de 70% do capital</p>
                  </div>
                  <div className="bg-white/70 p-4 rounded-lg">
                    <p className="text-sm text-gray-600 mb-2">Benefício Líquido</p>
                    <p className="text-xl font-bold text-green-700">
                      + R$ {((modalProdutoLento.custo_parado * 0.7) - modalProdutoLento.perda_mensal).toFixed(2)}
                    </p>
                    <p className="text-xs text-gray-600 mt-1">Vs. manter estoque parado</p>
                  </div>
                </div>
              </div>

              {/* Plano de Ação Passo a Passo */}
              <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl p-6 border border-purple-200">
                <h3 className="font-bold text-purple-900 mb-4 flex items-center gap-2">
                  <ChartBar className="w-5 h-5" />
                  📋 Plano de Ação - Próximos 7 Dias
                </h3>
                <div className="space-y-3">
                  <div className="flex items-start gap-3 bg-white/70 p-3 rounded-lg">
                    <div className="w-8 h-8 bg-purple-500 text-white rounded-full flex items-center justify-center font-bold flex-shrink-0">1</div>
                    <div>
                      <p className="font-semibold text-gray-900">Dia 1-2: Preparação</p>
                      <p className="text-sm text-gray-700">Crie material de divulgação, defina desconto, treine equipe</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3 bg-white/70 p-3 rounded-lg">
                    <div className="w-8 h-8 bg-purple-500 text-white rounded-full flex items-center justify-center font-bold flex-shrink-0">2</div>
                    <div>
                      <p className="font-semibold text-gray-900">Dia 3-5: Lançamento</p>
                      <p className="text-sm text-gray-700">Envie WhatsApp para clientes VIP, coloque cartazes na loja</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3 bg-white/70 p-3 rounded-lg">
                    <div className="w-8 h-8 bg-purple-500 text-white rounded-full flex items-center justify-center font-bold flex-shrink-0">3</div>
                    <div>
                      <p className="font-semibold text-gray-900">Dia 6-7: Intensificação</p>
                      <p className="text-sm text-gray-700">Se não atingir meta, aumente desconto para 40-50%</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Decisão Final */}
              <div className="bg-gradient-to-r from-gray-50 to-slate-50 rounded-xl p-6 border border-gray-300">
                <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5" />
                  ⚖️ Decisão Final (Se Não Vender)
                </h3>
                <div className="space-y-2 text-sm text-gray-700">
                  <p>• <strong>Doação:</strong> Doe para instituições e obtenha benefício fiscal</p>
                  <p>• <strong>Troca com Fornecedor:</strong> Negocie troca por produtos de maior giro</p>
                  <p>• <strong>Venda em Lote:</strong> Venda todo estoque para outro comerciante com desconto maior</p>
                  <p>• <strong>Última Opção:</strong> Descarte responsável e aprenda com o erro</p>
                </div>
              </div>

              {/* Lições Aprendidas */}
              <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl p-6 border border-green-200">
                <h3 className="font-bold text-green-900 mb-4 flex items-center gap-2">
                  <Lightbulb className="w-5 h-5" />
                  💡 Lições para Evitar no Futuro
                </h3>
                <div className="space-y-2 text-sm text-gray-700">
                  <p>• <strong>Teste Pequeno:</strong> Ao comprar produto novo, comece com quantidade mínima</p>
                  <p>• <strong>Análise de Demanda:</strong> Pesquise se clientes realmente querem o produto</p>
                  <p>• <strong>Monitoramento:</strong> Acompanhe vendas semanalmente, não mensalmente</p>
                  <p>• <strong>Fornecedor Flexível:</strong> Prefira fornecedores que aceitem devolução</p>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="flex justify-end gap-3 p-6 border-t border-gray-200 bg-gray-50">
              <button
                onClick={() => setModalProdutoLento(null)}
                className="px-6 py-2 bg-white text-gray-700 rounded-lg hover:bg-gray-100 transition-colors font-medium border border-gray-300"
              >
                Fechar
              </button>
              <button
                onClick={() => {
                  const mensagem = `🔥 OFERTA ESPECIAL VIP!\n\n${modalProdutoLento.nome}\n💰 30% OFF - Só hoje!\n\nEstoque limitado. Aproveite!`;
                  alert(`Mensagem copiada para WhatsApp:\n\n${mensagem}`);
                }}
                className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium"
              >
                📱 Copiar Mensagem WhatsApp
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 🔥 MODAIS RESTAURADOS */}
      {selectedAnomaly && (
        <AnomalyDetailsModal
          anomaly={selectedAnomaly}
          isOpen={!!selectedAnomaly}
          onClose={() => setSelectedAnomaly(null)}
        />
      )}

      {selectedCorrelation && (
        <CorrelationDetailsModal
          correlation={selectedCorrelation}
          isOpen={!!selectedCorrelation}
          onClose={() => setSelectedCorrelation(null)}
        />
      )}

      {selectedRecommendation && (
        <RecommendationDetailsModal
          recommendation={selectedRecommendation}
          isOpen={!!selectedRecommendation}
          onClose={() => setSelectedRecommendation(null)}
        />
      )}

      {/* 🔥 NOVO: MODAL DE HISTÓRICO DE KPI - SIMPLIFICADO */}
      {kpiModalAberto && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl w-full max-w-5xl max-h-[90vh] overflow-y-auto shadow-2xl">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-slate-700 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-slate-800 dark:to-slate-900">
              <div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  📊 Histórico: {kpiModalAberto}
                </h2>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  Análise temporal detalhada
                </p>
              </div>
              <button
                onClick={() => {
                  setKpiModalAberto(null);
                  setVisualizacaoModal('dias');
                }}
                className="p-2 hover:bg-white dark:hover:bg-slate-800 rounded-lg transition-colors"
              >
                <X className="w-6 h-6 text-gray-600 dark:text-gray-400" />
              </button>
            </div>

            <div className="p-6">
              {/* Toggle Simples: Dias vs Meses */}
              <div className="flex gap-3 mb-6">
                <button
                  onClick={() => setVisualizacaoModal('dias')}
                  className={`flex-1 px-6 py-3 rounded-xl font-semibold transition-all ${visualizacaoModal === 'dias'
                    ? 'bg-blue-600 text-white shadow-lg scale-105'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                >
                  📅 Últimos 30 Dias
                </button>
                <button
                  onClick={() => setVisualizacaoModal('meses')}
                  className={`flex-1 px-6 py-3 rounded-xl font-semibold transition-all ${visualizacaoModal === 'meses'
                    ? 'bg-purple-600 text-white shadow-lg scale-105'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                >
                  📊 Últimos 12 Meses
                </button>
              </div>

              {/* Gráfico */}
              <div className="bg-gradient-to-br from-gray-50 to-blue-50 dark:from-slate-800 dark:to-slate-900 rounded-xl p-6 shadow-inner">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                  {visualizacaoModal === 'dias' ? '📈 Evolução Diária (30 dias)' : '📊 Evolução Mensal (12 meses)'}
                </h3>

                {analise_temporal?.tendencia_vendas && analise_temporal.tendencia_vendas.length > 0 ? (
                  <div className="h-[400px] bg-white dark:bg-slate-900 rounded-lg p-4">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart
                        data={
                          visualizacaoModal === 'dias'
                            ? analise_temporal.tendencia_vendas.slice(-30) // Últimos 30 dias
                            : (() => {
                              // Agrupar por mês para visualização mensal
                              const vendasPorMes: Record<string, { mes: string; total: number; count: number }> = {};

                              analise_temporal.tendencia_vendas.forEach((item: any) => {
                                if (item.data) {
                                  const mesAno = item.data.substring(0, 7); // "2026-02"
                                  if (!vendasPorMes[mesAno]) {
                                    vendasPorMes[mesAno] = { mes: mesAno, total: 0, count: 0 };
                                  }
                                  vendasPorMes[mesAno].total += item.vendas || 0;
                                  vendasPorMes[mesAno].count += 1;
                                }
                              });

                              const mesesNomes = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];

                              return Object.keys(vendasPorMes)
                                .sort()
                                .slice(-12) // Últimos 12 meses
                                .map(mesAno => {
                                  const [ano, mes] = mesAno.split('-');
                                  const mesNumero = parseInt(mes);
                                  return {
                                    data: `${mesesNomes[mesNumero - 1]}/${ano.substring(2)}`,
                                    vendas: vendasPorMes[mesAno].total
                                  };
                                });
                            })()
                        }
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                        <XAxis
                          dataKey="data"
                          tick={{ fontSize: 12, fill: '#6B7280' }}
                          tickFormatter={(value) => {
                            if (visualizacaoModal === 'dias') {
                              const date = new Date(value);
                              return `${date.getDate()}/${date.getMonth() + 1}`;
                            }
                            return value; // Já formatado para meses
                          }}
                        />
                        <YAxis
                          tick={{ fontSize: 12, fill: '#6B7280' }}
                          tickFormatter={(value) => `R$ ${(value / 1000).toFixed(0)}k`}
                        />
                        <Tooltip
                          content={({ payload, label }) => {
                            if (!payload || payload.length === 0) return null;
                            return (
                              <div className="bg-white dark:bg-slate-800 p-4 shadow-xl rounded-lg border-2 border-blue-200 dark:border-blue-700">
                                <p className="font-bold text-gray-900 dark:text-gray-100 mb-1">
                                  {visualizacaoModal === 'dias'
                                    ? new Date(label).toLocaleDateString('pt-BR')
                                    : label
                                  }
                                </p>
                                <p className="text-lg font-semibold text-blue-600 dark:text-blue-400">
                                  R$ {payload[0]?.value?.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                                </p>
                              </div>
                            );
                          }}
                        />
                        <Line
                          type="monotone"
                          dataKey="vendas"
                          stroke={visualizacaoModal === 'dias' ? '#3B82F6' : '#9333EA'}
                          strokeWidth={3}
                          dot={{ fill: visualizacaoModal === 'dias' ? '#3B82F6' : '#9333EA', r: 4 }}
                          activeDot={{ r: 6, stroke: '#fff', strokeWidth: 2 }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="h-[400px] flex items-center justify-center bg-white dark:bg-slate-900 rounded-lg">
                    <div className="text-center">
                      <AlertTriangle className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-500 dark:text-gray-400">Dados insuficientes para gerar gráfico</p>
                    </div>
                  </div>
                )}
              </div>

              {/* Estatísticas Resumidas */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-xl p-4 border border-blue-200 dark:border-blue-800">
                  <p className="text-sm text-blue-700 dark:text-blue-400 mb-1 font-medium">💰 Valor Total</p>
                  <p className="text-xl font-bold text-blue-900 dark:text-blue-300">
                    {kpiModalAberto === 'Faturamento' && `R$ ${(mes?.total_vendas || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`}
                    {kpiModalAberto === 'Lucro Líquido' && `R$ ${(mes?.lucro_bruto || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`}
                    {kpiModalAberto === 'Ticket Médio' && `R$ ${(hoje?.ticket_medio || 0).toFixed(2)}`}
                    {kpiModalAberto === 'Despesas' && `R$ ${(mes?.total_despesas || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`}
                  </p>
                </div>

                <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-xl p-4 border border-green-200 dark:border-green-800">
                  <p className="text-sm text-green-700 dark:text-green-400 mb-1 font-medium">📈 Crescimento</p>
                  <p className={`text-xl font-bold ${(mes?.crescimento_mensal || 0) >= 0 ? 'text-green-900 dark:text-green-300' : 'text-red-900 dark:text-red-300'}`}>
                    {(mes?.crescimento_mensal || 0) >= 0 ? '+' : ''}{(mes?.crescimento_mensal || 0).toFixed(1)}%
                  </p>
                </div>

                <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 rounded-xl p-4 border border-purple-200 dark:border-purple-800">
                  <p className="text-sm text-purple-700 dark:text-purple-400 mb-1 font-medium">📅 Período</p>
                  <p className="text-xl font-bold text-purple-900 dark:text-purple-300">
                    {periodoDias} dias
                  </p>
                </div>

                <div className="bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20 rounded-xl p-4 border border-orange-200 dark:border-orange-800">
                  <p className="text-sm text-orange-700 dark:text-orange-400 mb-1 font-medium">📊 Média Diária</p>
                  <p className="text-xl font-bold text-orange-900 dark:text-orange-300">
                    {kpiModalAberto === 'Faturamento' && `R$ ${((mes?.total_vendas || 0) / periodoDias).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`}
                    {kpiModalAberto === 'Lucro Líquido' && `R$ ${((mes?.lucro_bruto || 0) / periodoDias).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`}
                    {kpiModalAberto === 'Ticket Médio' && `R$ ${(hoje?.ticket_medio || 0).toFixed(2)}`}
                    {kpiModalAberto === 'Despesas' && `R$ ${((mes?.total_despesas || 0) / periodoDias).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`}
                  </p>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="flex justify-end gap-3 p-6 border-t border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-800">
              <button
                onClick={() => {
                  setKpiModalAberto(null);
                  setVisualizacaoModal('dias');
                }}
                className="px-6 py-2 bg-white dark:bg-slate-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-600 transition-colors font-medium border border-gray-300 dark:border-slate-600"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DashboardPage;
