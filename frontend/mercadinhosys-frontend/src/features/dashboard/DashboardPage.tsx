import React, { useEffect, useState } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  ShoppingCart, 
  Users, 
  Package, 
  CreditCard,
  DollarSign,
  BarChart,
  AlertTriangle,
  Clock,
  Star,
  Calendar,
  Zap,
  Target,
  Award,
  Activity,
  Percent
} from 'lucide-react';
import { apiClient } from '../../api/apiClient';

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
      meta_atingida?: number;
      vendas_por_forma_pagamento?: Record<string, number>;
    };
    mes: {
      total_vendas: number;
      total_despesas: number;
      lucro_bruto: number;
      margem_lucro: number;
      crescimento_mensal: number;
    };
    alertas: {
      estoque_baixo: Array<{
        id: number;
        nome: string;
        quantidade: number;
        quantidade_minima: number;
        categoria: string;
      }>;
      validade_proxima: Array<{
        id: number;
        nome: string;
        data_validade: string;
        quantidade: number;
        categoria: string;
      }>;
    };
    analise_temporal: {
      vendas_por_hora: Array<{
        hora: number;
        quantidade: number;
        total: number;
      }>;
      vendas_por_categoria: Array<{
        categoria: string;
        total: number;
      }>;
      vendas_ultimos_7_dias: Array<{
        data: string;
        total: number;
      }>;
      clientes_novos_mes: number;
    };
    ultimas_vendas: Array<{
      id: number;
      codigo: string;
      cliente: string;
      total: number;
      forma_pagamento: string;
      data_venda: string;
    }>;
    insights?: Array<{
      tipo: string;
      titulo: string;
      descricao: string;
      prioridade?: string;
      acao?: string;
    }>;
    previsoes?: {
      confianca?: number;
      direcao?: string;
      inclinacao?: number;
      intervalo_confianca?: [number, number];
      p_value?: number;
      previsao?: number;
      r_quadrado?: number;
    };
    analise_produtos?: {
      top_produtos: Array<{
        id: number;
        nome: string;
        quantidade_vendida: number;
        total_vendido: number;
      }>;
      produtos_estrela?: Array<{
        id: number;
        nome: string;
        classificacao: string;
        margem: number;
      }>;
    };
    analise_clientes?: {
      top_clientes: Array<{
        id: number;
        nome: string;
        total_compras: number;
      }>;
      segmentacao?: {
        champions?: number;
        loyal?: number;
        at_risk?: number;
        lost?: number;
      };
    };
    kpis_avancados?: {
      customer_lifetime_value?: number;
      churn_rate?: number;
      repeat_customer_rate?: number;
      average_order_value?: number;
      conversion_rate?: number;
    };
    dono?: {
      meta_diaria?: number;
      projecoes?: {
        faturamento_mes?: number;
        lucro_mes?: number;
      };
      resumo_executivo?: {
        status_geral?: string;
        principais_problemas?: string[];
        oportunidades?: string[];
      };
    };
  };
}

const DashboardPage: React.FC = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get('/dashboard/resumo');
      console.log('📊 Dashboard completo:', response.data);
      console.log('🔍 Insights:', response.data?.data?.insights);
      console.log('🔮 Previsões:', response.data?.data?.previsoes);
      console.log('💳 Formas pagamento:', response.data?.data?.hoje?.vendas_por_forma_pagamento);
      console.log('⏰ Vendas por hora:', response.data?.data?.analise_temporal?.vendas_por_hora);
      setData(response.data);
    } catch (error) {
      console.error('Erro ao carregar dashboard:', error);
      setError('Erro ao carregar dados do dashboard');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-100 text-red-700 rounded-lg">
        {error}
      </div>
    );
  }

  if (!data) return null;

  const { hoje, mes, alertas, analise_temporal, kpis_avancados, dono } = data.data;

  // Cards principais
  const mainStats = [
    {
      title: 'Vendas Hoje',
      value: `R$ ${(hoje?.total_vendas ?? 0).toFixed(2)}`,
      subtitle: `${hoje?.quantidade_vendas ?? 0} vendas`,
      icon: ShoppingCart,
      trend: hoje?.crescimento_vs_ontem ?? 0,
      color: 'bg-green-500',
      meta: dono?.meta_diaria ? `Meta: R$ ${dono.meta_diaria.toFixed(2)}` : null,
    },
    {
      title: 'Ticket Médio',
      value: `R$ ${(hoje?.ticket_medio ?? 0).toFixed(2)}`,
      subtitle: `${hoje?.clientes_atendidos ?? 0} clientes atendidos`,
      icon: DollarSign,
      trend: 0,
      color: 'bg-blue-500',
    },
    {
      title: 'Lucro Bruto Mês',
      value: `R$ ${(mes?.lucro_bruto ?? 0).toFixed(2)}`,
      subtitle: `Margem: ${(mes?.margem_lucro ?? 0).toFixed(1)}%`,
      icon: CreditCard,
      trend: mes?.crescimento_mensal ?? 0,
      color: 'bg-indigo-500',
    },
    {
      title: 'Total Vendas Mês',
      value: `R$ ${(mes?.total_vendas ?? 0).toFixed(2)}`,
      subtitle: `Despesas: R$ ${(mes?.total_despesas ?? 0).toFixed(2)}`,
      icon: BarChart,
      trend: mes?.crescimento_mensal ?? 0,
      color: 'bg-pink-500',
    },
  ];

  // KPIs Avançados (se disponível)
  const kpiCards = kpis_avancados ? [
    {
      title: 'Valor Vitalício do Cliente',
      value: `R$ ${(kpis_avancados.customer_lifetime_value ?? 0).toFixed(2)}`,
      subtitle: 'Valor médio por cliente',
      icon: Award,
      color: 'bg-yellow-500',
    },
    {
      title: 'Taxa de Retenção',
      value: `${((1 - (kpis_avancados.churn_rate ?? 0)) * 100).toFixed(1)}%`,
      subtitle: 'Clientes que continuam comprando',
      icon: Users,
      color: 'bg-teal-500',
    },
    {
      title: 'Taxa de Repetição',
      value: `${((kpis_avancados.repeat_customer_rate ?? 0) * 100).toFixed(1)}%`,
      subtitle: 'Clientes que compram novamente',
      icon: Activity,
      color: 'bg-purple-500',
    },
    {
      title: 'Taxa de Conversão',
      value: `${((kpis_avancados.conversion_rate ?? 0) * 100).toFixed(1)}%`,
      subtitle: 'Conversão de visitas em vendas',
      icon: Percent,
      color: 'bg-orange-500',
    },
  ] : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-800 dark:text-white">
            Dashboard Executivo
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Bem-vindo, {data.usuario.nome} • {hoje?.data ? new Date(hoje.data).toLocaleDateString('pt-BR', { 
              weekday: 'long', 
              day: 'numeric', 
              month: 'long' 
            }) : ''}
          </p>
        </div>
        <button 
          onClick={loadDashboard}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg flex items-center gap-2 transition-colors"
        >
          <Zap className="w-4 h-4" />
          Atualizar
        </button>
      </div>

      {/* Previsões (se disponível) */}
      {data.data.previsoes && typeof data.data.previsoes === 'object' && Object.keys(data.data.previsoes).length > 0 && (
        <div className="bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 rounded-xl shadow-lg p-6 border border-purple-200 dark:border-purple-800">
          <div className="flex items-center gap-2 mb-3">
            <Target className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            <h2 className="text-lg font-semibold text-gray-800 dark:text-white">Previsões Inteligentes</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Previsão para Próximos 7 Dias */}
            <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border-l-4 border-purple-500">
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Próximos 7 Dias</p>
              <p className="text-2xl font-bold text-purple-600">
                {Array.isArray(data.data.previsoes.previsao) && data.data.previsoes.previsao.length > 0
                  ? `R$ ${data.data.previsoes.previsao.reduce((sum: number, p: any) => sum + (p.valor || 0), 0).toFixed(2)}`
                  : 'R$ 0.00'}
              </p>
              <p className="text-xs text-gray-400 mt-1">Previsão de faturamento</p>
            </div>

            {/* Tendência */}
            <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border-l-4 border-blue-500">
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Tendência</p>
              <p className="text-2xl font-bold text-gray-800 dark:text-white capitalize">
                {data.data.previsoes.direcao === 'crescente' ? '📈 Crescente' : 
                 data.data.previsoes.direcao === 'decrescente' ? '📉 Decrescente' : '➡️ Estável'}
              </p>
              <p className="text-xs text-gray-400 mt-1">
                {data.data.previsoes.tendencia && typeof data.data.previsoes.tendencia === 'object' && data.data.previsoes.tendencia.slope !== undefined
                  ? `${(data.data.previsoes.tendencia.slope > 0 ? '+' : '')}${data.data.previsoes.tendencia.slope.toFixed(1)}% ao dia`
                  : 'Baseado em histórico'}
              </p>
            </div>

            {/* Meta do Mês */}
            <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border-l-4 border-green-500">
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Meta do Mês</p>
              <p className="text-2xl font-bold text-green-600">
                {data.data.dono?.projecoes?.meta?.atingido_percentual !== undefined
                  ? `${data.data.dono.projecoes.meta.atingido_percentual.toFixed(1)}%`
                  : mes?.total_vendas && dono?.meta_diaria
                    ? `${((mes.total_vendas / (dono.meta_diaria * 30)) * 100).toFixed(1)}%`
                    : '0%'}
              </p>
              <p className="text-xs text-gray-400 mt-1">
                {data.data.dono?.projecoes?.meta?.diferenca !== undefined && data.data.dono.projecoes.meta.diferenca > 0
                  ? `Faltam R$ ${data.data.dono.projecoes.meta.diferenca.toFixed(2)}`
                  : 'Atingimento da meta'}
              </p>
            </div>

            {/* Crescimento Semanal */}
            <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border-l-4 border-orange-500">
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">vs Semana Passada</p>
              <p className={`text-2xl font-bold ${
                data.data.metricas_comparativas?.vs_semana_passada?.percentual_crescimento > 0 
                  ? 'text-green-600' 
                  : data.data.metricas_comparativas?.vs_semana_passada?.percentual_crescimento < 0
                    ? 'text-red-600'
                    : 'text-gray-600'
              }`}>
                {data.data.metricas_comparativas?.vs_semana_passada?.percentual_crescimento !== undefined
                  ? `${data.data.metricas_comparativas.vs_semana_passada.percentual_crescimento > 0 ? '+' : ''}${data.data.metricas_comparativas.vs_semana_passada.percentual_crescimento.toFixed(1)}%`
                  : '0%'}
              </p>
              <p className="text-xs text-gray-400 mt-1">
                {data.data.metricas_comparativas?.vs_semana_passada?.diferenca_valor !== undefined
                  ? `${data.data.metricas_comparativas.vs_semana_passada.diferenca_valor > 0 ? '+' : ''}R$ ${Math.abs(data.data.metricas_comparativas.vs_semana_passada.diferenca_valor).toFixed(2)}`
                  : 'Crescimento semanal'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* NOVA SEÇÃO: Recomendações Inteligentes e Ações Imediatas */}
      {data.data.recomendacoes && (
        <div className="bg-gradient-to-r from-red-50 to-orange-50 dark:from-red-900/20 dark:to-orange-900/20 rounded-xl shadow-lg p-6 border-2 border-red-300 dark:border-red-700">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="w-6 h-6 text-red-600 dark:text-red-400 animate-pulse" />
            <h2 className="text-xl font-bold text-gray-800 dark:text-white">🎯 Ações Recomendadas Agora</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Urgentes */}
            {data.data.recomendacoes.urgentes && data.data.recomendacoes.urgentes.length > 0 && (
              <div>
                <h3 className="font-bold text-red-600 dark:text-red-400 mb-3 flex items-center gap-2">
                  <span className="inline-block w-3 h-3 bg-red-600 rounded-full animate-pulse"></span>
                  Urgente
                </h3>
                <div className="space-y-3">
                  {data.data.recomendacoes.urgentes.map((rec: any, idx: number) => (
                    <div key={idx} className="bg-white dark:bg-gray-800 p-4 rounded-lg border-l-4 border-red-500 shadow-md hover:shadow-lg transition-shadow">
                      <h4 className="font-bold text-gray-800 dark:text-white text-sm mb-1">{rec.titulo}</h4>
                      <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">{rec.descricao}</p>
                      <div className="bg-red-50 dark:bg-red-900/20 p-2 rounded mt-2">
                        <p className="text-xs font-semibold text-red-700 dark:text-red-400">
                          ✓ {rec.acao}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Atenção */}
            {data.data.recomendacoes.atencao && data.data.recomendacoes.atencao.length > 0 && (
              <div>
                <h3 className="font-bold text-orange-600 dark:text-orange-400 mb-3 flex items-center gap-2">
                  <span className="inline-block w-3 h-3 bg-orange-600 rounded-full"></span>
                  Atenção
                </h3>
                <div className="space-y-3">
                  {data.data.recomendacoes.atencao.map((rec: any, idx: number) => (
                    <div key={idx} className="bg-white dark:bg-gray-800 p-4 rounded-lg border-l-4 border-orange-500 shadow-md hover:shadow-lg transition-shadow">
                      <h4 className="font-bold text-gray-800 dark:text-white text-sm mb-1">{rec.titulo}</h4>
                      <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">{rec.descricao}</p>
                      <div className="bg-orange-50 dark:bg-orange-900/20 p-2 rounded mt-2">
                        <p className="text-xs font-semibold text-orange-700 dark:text-orange-400">
                          ✓ {rec.acao}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Oportunidades */}
            {data.data.recomendacoes.oportunidades && data.data.recomendacoes.oportunidades.length > 0 && (
              <div>
                <h3 className="font-bold text-green-600 dark:text-green-400 mb-3 flex items-center gap-2">
                  <span className="inline-block w-3 h-3 bg-green-600 rounded-full"></span>
                  Oportunidades
                </h3>
                <div className="space-y-3">
                  {data.data.recomendacoes.oportunidades.map((rec: any, idx: number) => (
                    <div key={idx} className="bg-white dark:bg-gray-800 p-4 rounded-lg border-l-4 border-green-500 shadow-md hover:shadow-lg transition-shadow">
                      <h4 className="font-bold text-gray-800 dark:text-white text-sm mb-1">{rec.titulo}</h4>
                      <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">{rec.descricao}</p>
                      <div className="bg-green-50 dark:bg-green-900/20 p-2 rounded mt-2">
                        <p className="text-xs font-semibold text-green-700 dark:text-green-400">
                          ✓ {rec.acao}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* NOVA SEÇÃO: Previsão de Ruptura de Estoque */}
      {data.data.analise_produtos?.previsao_demanda?.produtos && data.data.analise_produtos.previsao_demanda.produtos.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2 mb-4">
            <Package className="w-6 h-6 text-purple-600" />
            <h2 className="text-xl font-bold text-gray-800 dark:text-white">📦 Previsão de Estoque (Próximos 7 Dias)</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b-2 border-gray-200 dark:border-gray-700">
                  <th className="text-left py-3 px-4 text-sm font-bold text-gray-700 dark:text-gray-300">Produto</th>
                  <th className="text-center py-3 px-4 text-sm font-bold text-gray-700 dark:text-gray-300">Estoque Atual</th>
                  <th className="text-center py-3 px-4 text-sm font-bold text-gray-700 dark:text-gray-300">Demanda/Dia</th>
                  <th className="text-center py-3 px-4 text-sm font-bold text-gray-700 dark:text-gray-300">Dias Restantes</th>
                  <th className="text-center py-3 px-4 text-sm font-bold text-gray-700 dark:text-gray-300">Status</th>
                </tr>
              </thead>
              <tbody>
                {data.data.analise_produtos.previsao_demanda.produtos.slice(0, 10).map((produto: any, idx: number) => {
                  const diasRestantes = produto.demanda_diaria_prevista > 0 
                    ? produto.estoque_atual / produto.demanda_diaria_prevista 
                    : 999;
                  const isRisco = diasRestantes < 7;
                  const isCritico = diasRestantes < 3;
                  
                  return (
                    <tr key={idx} className={`border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700/50 ${isCritico ? 'bg-red-50 dark:bg-red-900/10' : isRisco ? 'bg-yellow-50 dark:bg-yellow-900/10' : ''}`}>
                      <td className="py-3 px-4 font-medium text-gray-800 dark:text-white">{produto.produto_nome}</td>
                      <td className="py-3 px-4 text-center font-semibold">{produto.estoque_atual}</td>
                      <td className="py-3 px-4 text-center text-blue-600 dark:text-blue-400">{produto.demanda_diaria_prevista.toFixed(1)}</td>
                      <td className="py-3 px-4 text-center">
                        <span className={`font-bold ${isCritico ? 'text-red-600' : isRisco ? 'text-orange-600' : 'text-green-600'}`}>
                          {diasRestantes < 999 ? Math.floor(diasRestantes) : '∞'} dias
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center">
                        {isCritico ? (
                          <span className="px-3 py-1 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-full text-xs font-bold">
                            🚨 Crítico
                          </span>
                        ) : isRisco ? (
                          <span className="px-3 py-1 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 rounded-full text-xs font-bold">
                            ⚠️ Atenção
                          </span>
                        ) : (
                          <span className="px-3 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded-full text-xs font-bold">
                            ✓ OK
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
      )}

      {/* Cards Principais */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {mainStats.map((stat) => (
          <div
            key={stat.title}
            className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700 hover:shadow-xl transition-shadow"
          >
            <div className="flex items-center justify-between mb-4">
              <div className={`${stat.color} p-3 rounded-lg shadow-md`}>
                <stat.icon className="w-6 h-6 text-white" />
              </div>
              {stat.trend !== 0 && (
                <div className={`flex items-center ${stat.trend > 0 ? 'text-green-500' : 'text-red-500'}`}>
                  {stat.trend > 0 ? (
                    <TrendingUp className="w-4 h-4 mr-1" />
                  ) : (
                    <TrendingDown className="w-4 h-4 mr-1" />
                  )}
                  <span className="text-sm font-semibold">{Math.abs(stat.trend).toFixed(1)}%</span>
                </div>
              )}
            </div>
            <h3 className="text-sm text-gray-500 dark:text-gray-400 font-medium">{stat.title}</h3>
            <p className="text-2xl font-bold text-gray-800 dark:text-white mt-1">{stat.value}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{stat.subtitle}</p>
            {stat.meta && (
              <p className="text-xs text-blue-600 dark:text-blue-400 mt-1 font-medium">{stat.meta}</p>
            )}
          </div>
        ))}
      </div>

      {/* KPIs Avançados */}
      {kpiCards.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold text-gray-800 dark:text-white mb-4">KPIs Avançados</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {kpiCards.map((kpi) => (
              <div
                key={kpi.title}
                className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700"
              >
                <div className={`${kpi.color} p-3 rounded-lg shadow-md inline-block mb-3`}>
                  <kpi.icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-sm text-gray-500 dark:text-gray-400 font-medium">{kpi.title}</h3>
                <p className="text-2xl font-bold text-gray-800 dark:text-white mt-1">{kpi.value}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{kpi.subtitle}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Insights Automáticos */}
      {data.data.insights && Array.isArray(data.data.insights) && data.data.insights.length > 0 && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-xl shadow-lg p-6 border border-blue-200 dark:border-blue-800">
          <div className="flex items-center gap-2 mb-4">
            <Star className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            <h2 className="text-lg font-semibold text-gray-800 dark:text-white">Insights Inteligentes</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data.data.insights.slice(0, 4).map((insight, idx) => (
              <div 
                key={idx}
                className={`p-4 rounded-lg ${
                  insight.tipo === 'positivo' 
                    ? 'bg-green-100 dark:bg-green-900/30 border-l-4 border-green-500' 
                    : insight.tipo === 'negativo' || insight.tipo === 'alerta'
                    ? 'bg-red-100 dark:bg-red-900/30 border-l-4 border-red-500'
                    : 'bg-yellow-100 dark:bg-yellow-900/30 border-l-4 border-yellow-500'
                }`}
              >
                <div className="flex items-start justify-between">
                  <h3 className="font-semibold text-gray-800 dark:text-white mb-1">{insight.titulo}</h3>
                  {insight.prioridade && (
                    <span className={`text-xs px-2 py-1 rounded ${
                      insight.prioridade === 'alta' ? 'bg-red-200 text-red-800' :
                      insight.prioridade === 'media' ? 'bg-yellow-200 text-yellow-800' :
                      'bg-green-200 text-green-800'
                    }`}>
                      {insight.prioridade}
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">{insight.descricao}</p>
                {insight.acao && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 italic">💡 {insight.acao}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Alertas e Vendas por Tipo de Pagamento */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Estoque Baixo */}
        {alertas.estoque_baixo.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-orange-200 dark:border-orange-800">
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="w-5 h-5 text-orange-600" />
              <h2 className="text-lg font-semibold text-gray-800 dark:text-white">
                Estoque Baixo ({alertas.estoque_baixo.length})
              </h2>
            </div>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {alertas.estoque_baixo.map((produto) => (
                <div 
                  key={produto.id}
                  className="flex justify-between items-center p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg"
                >
                  <div>
                    <p className="font-medium text-gray-800 dark:text-white">{produto.nome}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">{produto.categoria}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-orange-600">{produto.quantidade} un</p>
                    <p className="text-xs text-gray-500">Mín: {produto.quantidade_minima}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Validade Próxima */}
        {alertas.validade_proxima.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-red-200 dark:border-red-800">
            <div className="flex items-center gap-2 mb-4">
              <Calendar className="w-5 h-5 text-red-600" />
              <h2 className="text-lg font-semibold text-gray-800 dark:text-white">
                Validade Próxima ({alertas.validade_proxima.length})
              </h2>
            </div>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {alertas.validade_proxima.map((produto) => (
                <div 
                  key={produto.id}
                  className="flex justify-between items-center p-3 bg-red-50 dark:bg-red-900/20 rounded-lg"
                >
                  <div>
                    <p className="font-medium text-gray-800 dark:text-white">{produto.nome}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">{produto.categoria}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-red-600">
                      {new Date(produto.data_validade).toLocaleDateString('pt-BR')}
                    </p>
                    <p className="text-xs text-gray-500">{produto.quantidade} un</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Vendas por Tipo de Pagamento */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-blue-200 dark:border-blue-800">
          <div className="flex items-center gap-2 mb-4">
            <DollarSign className="w-5 h-5 text-blue-600" />
            <h2 className="text-lg font-semibold text-gray-800 dark:text-white">
              Total Vendas por Tipo de Pagamento
            </h2>
          </div>
          {data.data.hoje?.vendas_por_forma_pagamento && Object.keys(data.data.hoje.vendas_por_forma_pagamento).length > 0 ? (
            <div className="space-y-3">
              {Object.entries(data.data.hoje.vendas_por_forma_pagamento).map(([forma, valor]) => {
                const formasPagamento = data.data.hoje.vendas_por_forma_pagamento || {};
                const total = Object.values(formasPagamento).reduce((sum: number, v) => sum + Number(v), 0);
                const percentual = total > 0 ? (Number(valor) / total) * 100 : 0;
                
                return (
                  <div key={forma} className="space-y-1">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300 capitalize">
                        {forma}
                      </span>
                      <span className="text-sm font-bold text-gray-800 dark:text-white">
                        R$ {Number(valor).toFixed(2)}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${
                          forma === 'dinheiro' ? 'bg-green-500' :
                          forma === 'credito' ? 'bg-blue-500' :
                          forma === 'debito' ? 'bg-purple-500' :
                          'bg-orange-500'
                        }`}
                        style={{ width: `${percentual}%` }}
                      />
                    </div>
                    <p className="text-xs text-gray-500">{percentual.toFixed(1)}%</p>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              <p className="text-sm">Nenhuma venda registrada hoje</p>
            </div>
          )}
        </div>
      </div>

      {/* Segmentação de Clientes RFM */}
      {data.data.analise_clientes?.segmentacao && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700">
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-gray-800 dark:text-white">Segmentação de Clientes por Valor</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Análise baseada em <span className="font-semibold">Recência</span> (quando comprou), 
              <span className="font-semibold"> Frequência</span> (quantas vezes compra) e 
              <span className="font-semibold"> Valor Monetário</span> (quanto gasta)
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-green-50 dark:bg-green-900/20 p-5 rounded-lg border-l-4 border-green-500">
              <p className="text-4xl font-bold text-green-600 mb-2">{data.data.analise_clientes.segmentacao.champions ?? 0}</p>
              <p className="text-sm font-semibold text-gray-800 dark:text-white">Campeões</p>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                Compram frequentemente e gastam muito
              </p>
            </div>
            <div className="bg-blue-50 dark:bg-blue-900/20 p-5 rounded-lg border-l-4 border-blue-500">
              <p className="text-4xl font-bold text-blue-600 mb-2">{data.data.analise_clientes.segmentacao.loyal ?? 0}</p>
              <p className="text-sm font-semibold text-gray-800 dark:text-white">Fiéis</p>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                Clientes regulares e confiáveis
              </p>
            </div>
            <div className="bg-yellow-50 dark:bg-yellow-900/20 p-5 rounded-lg border-l-4 border-yellow-500">
              <p className="text-4xl font-bold text-yellow-600 mb-2">{data.data.analise_clientes.segmentacao.at_risk ?? 0}</p>
              <p className="text-sm font-semibold text-gray-800 dark:text-white">Em Risco</p>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                Não compram há algum tempo
              </p>
            </div>
            <div className="bg-red-50 dark:bg-red-900/20 p-5 rounded-lg border-l-4 border-red-500">
              <p className="text-4xl font-bold text-red-600 mb-2">{data.data.analise_clientes.segmentacao.lost ?? 0}</p>
              <p className="text-sm font-semibold text-gray-800 dark:text-white">Perdidos</p>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                Inativos por muito tempo
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Vendas por Categoria */}
        {analise_temporal.vendas_por_categoria && analise_temporal.vendas_por_categoria.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">
              Vendas por Categoria
            </h2>
            <div className="space-y-4">
              {analise_temporal.vendas_por_categoria.map((item) => {
                const maxTotal = Math.max(...analise_temporal.vendas_por_categoria.map(i => i.total));
                const percentage = (item.total / maxTotal) * 100;
                return (
                  <div key={item.categoria}>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm text-gray-600 dark:text-gray-300 font-medium">
                        {item.categoria}
                      </span>
                      <span className="text-sm font-semibold text-gray-800 dark:text-white">
                        R$ {(item?.total ?? 0).toFixed(2)}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                      <div
                        className="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full transition-all duration-500"
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Vendas Últimos 7 Dias - Gráfico de Linhas */}
        {analise_temporal.vendas_ultimos_7_dias && analise_temporal.vendas_ultimos_7_dias.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">
              Vendas Últimos 7 Dias
            </h2>
            <div className="relative h-64 px-2">
              {/* Eixo Y - valores de referência */}
              <div className="absolute left-0 top-0 bottom-8 flex flex-col justify-between text-xs text-gray-500 dark:text-gray-400">
                {(() => {
                  const maxTotal = Math.max(...analise_temporal.vendas_ultimos_7_dias.map(i => i.total), 1);
                  return [
                    <span key="max">R$ {maxTotal.toFixed(0)}</span>,
                    <span key="mid">R$ {(maxTotal / 2).toFixed(0)}</span>,
                    <span key="min">R$ 0</span>
                  ];
                })()}
              </div>

              {/* Área do gráfico */}
              <div className="ml-16 h-full flex items-end">
                <svg className="w-full h-full" preserveAspectRatio="none" viewBox="0 0 100 100">
                  {/* Grid lines */}
                  <line x1="0" y1="0" x2="100" y2="0" stroke="currentColor" className="text-gray-300 dark:text-gray-600" strokeWidth="0.2" />
                  <line x1="0" y1="50" x2="100" y2="50" stroke="currentColor" className="text-gray-300 dark:text-gray-600" strokeWidth="0.2" strokeDasharray="1,1" />
                  <line x1="0" y1="100" x2="100" y2="100" stroke="currentColor" className="text-gray-300 dark:text-gray-600" strokeWidth="0.2" />
                  
                  {/* Linha do gráfico */}
                  <polyline
                    points={analise_temporal.vendas_ultimos_7_dias.map((item, index) => {
                      const maxTotal = Math.max(...analise_temporal.vendas_ultimos_7_dias.map(i => i.total), 1);
                      const x = (index / (analise_temporal.vendas_ultimos_7_dias.length - 1)) * 100;
                      const y = 100 - ((item.total / maxTotal) * 100);
                      return `${x},${y}`;
                    }).join(' ')}
                    fill="none"
                    stroke="#10b981"
                    strokeWidth="2"
                    className="drop-shadow-lg"
                  />
                  
                  {/* Área preenchida sob a linha */}
                  <polygon
                    points={`0,100 ${analise_temporal.vendas_ultimos_7_dias.map((item, index) => {
                      const maxTotal = Math.max(...analise_temporal.vendas_ultimos_7_dias.map(i => i.total), 1);
                      const x = (index / (analise_temporal.vendas_ultimos_7_dias.length - 1)) * 100;
                      const y = 100 - ((item.total / maxTotal) * 100);
                      return `${x},${y}`;
                    }).join(' ')} 100,100`}
                    fill="url(#gradient)"
                    opacity="0.3"
                  />
                  
                  {/* Pontos */}
                  {analise_temporal.vendas_ultimos_7_dias.map((item, index) => {
                    const maxTotal = Math.max(...analise_temporal.vendas_ultimos_7_dias.map(i => i.total), 1);
                    const x = (index / (analise_temporal.vendas_ultimos_7_dias.length - 1)) * 100;
                    const y = 100 - ((item.total / maxTotal) * 100);
                    return (
                      <g key={`point-${item.data}-${index}`}>
                        <circle cx={x} cy={y} r="2" fill="#10b981" className="drop-shadow" />
                        <title>R$ {item.total.toFixed(2)}</title>
                      </g>
                    );
                  })}
                  
                  <defs>
                    <linearGradient id="gradient" x1="0%" y1="0%" x2="0%" y2="100%">
                      <stop offset="0%" stopColor="#10b981" stopOpacity="0.5" />
                      <stop offset="100%" stopColor="#10b981" stopOpacity="0" />
                    </linearGradient>
                  </defs>
                </svg>
              </div>

              {/* Eixo X - datas */}
              <div className="ml-16 flex justify-between mt-2">
                {analise_temporal.vendas_ultimos_7_dias.map((item) => (
                  <div key={item.data} className="text-center flex-1">
                    <p className="text-xs text-gray-600 dark:text-gray-400 font-medium">
                      {new Date(item.data).toLocaleDateString('pt-BR', { weekday: 'short' })}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-500">
                      {new Date(item.data).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Top Produtos e Top Clientes */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Produtos */}
        {data.data.analise_produtos?.top_produtos && data.data.analise_produtos.top_produtos.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-2 mb-4">
              <Package className="w-5 h-5 text-purple-600" />
              <h2 className="text-lg font-semibold text-gray-800 dark:text-white">
                Top Produtos Vendidos
              </h2>
            </div>
            <div className="space-y-3">
              {data.data.analise_produtos.top_produtos.slice(0, 5).map((produto, idx) => (
                <div 
                  key={produto.id}
                  className="flex items-center justify-between p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-purple-600 text-white rounded-full flex items-center justify-center font-bold">
                      {idx + 1}
                    </div>
                    <div>
                      <p className="font-medium text-gray-800 dark:text-white">{produto.nome}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">{produto?.quantidade_vendida ?? 0} unidades</p>
                    </div>
                  </div>
                  <p className="font-semibold text-purple-600">
                    R$ {(produto?.total_vendido ?? 0).toFixed(2)}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Top Clientes */}
        {data.data.analise_clientes?.top_clientes && data.data.analise_clientes.top_clientes.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-2 mb-4">
              <Users className="w-5 h-5 text-green-600" />
              <h2 className="text-lg font-semibold text-gray-800 dark:text-white">
                Top Clientes do Mês
              </h2>
            </div>
            <div className="space-y-3">
              {data.data.analise_clientes.top_clientes.slice(0, 5).map((cliente, idx) => (
                <div 
                  key={cliente.id}
                  className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-green-600 text-white rounded-full flex items-center justify-center font-bold">
                      {idx + 1}
                    </div>
                    <p className="font-medium text-gray-800 dark:text-white">{cliente?.nome ?? 'Cliente'}</p>
                  </div>
                  <p className="font-semibold text-green-600">
                    R$ {(cliente?.total_compras ?? 0).toFixed(2)}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Vendas por Hora */}
      {analise_temporal.vendas_por_hora && analise_temporal.vendas_por_hora.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2 mb-4">
            <Clock className="w-5 h-5 text-blue-600" />
            <h2 className="text-lg font-semibold text-gray-800 dark:text-white">
              Vendas por Hora (Últimas 24h)
            </h2>
          </div>
          <div className="flex items-end justify-between gap-1 h-48 px-2">
            {analise_temporal.vendas_por_hora.map((item) => {
              const maxTotal = Math.max(...analise_temporal.vendas_por_hora.map(i => i.total || 0));
              const heightPercent = maxTotal > 0 ? ((item.total || 0) / maxTotal) * 100 : 0;
              const heightPx = maxTotal > 0 ? Math.max((heightPercent / 100) * 192, 4) : 4; // 192px = h-48
              
              return (
                <div key={item.hora} className="flex-1 flex flex-col items-center gap-1 group relative">
                  <div 
                    className="w-full bg-gradient-to-t from-blue-600 to-blue-400 rounded-t hover:from-blue-700 hover:to-blue-500 transition-all cursor-pointer"
                    style={{ height: `${heightPx}px` }}
                  >
                    {/* Tooltip */}
                    <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 bg-gray-900 dark:bg-gray-700 text-white px-3 py-2 rounded text-xs opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10 shadow-lg pointer-events-none">
                      <div className="font-semibold">Hora: {item.hora}:00</div>
                      <div>R$ {(item.total || 0).toFixed(2)}</div>
                      <div>{item.quantidade || 0} vendas</div>
                      {/* Seta do tooltip */}
                      <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900 dark:border-t-gray-700"></div>
                    </div>
                  </div>
                  <span className="text-xs text-gray-600 dark:text-gray-400 font-medium mt-1">{item.hora}h</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* NOVA SEÇÃO: Análise Financeira */}
      {data.data.analise_financeira && (
        <div className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-xl shadow-lg p-6 border border-green-200 dark:border-green-800">
          <div className="flex items-center gap-2 mb-4">
            <DollarSign className="w-6 h-6 text-green-600 dark:text-green-400" />
            <h2 className="text-xl font-bold text-gray-800 dark:text-white">💰 Análise Financeira do Mês</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border-l-4 border-green-500">
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Faturamento</p>
              <p className="text-2xl font-bold text-green-600">
                R$ {(mes?.total_vendas ?? 0).toFixed(2)}
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border-l-4 border-red-500">
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Despesas</p>
              <p className="text-2xl font-bold text-red-600">
                R$ {(data.data.analise_financeira.despesas_mes ?? 0).toFixed(2)}
              </p>
              <p className="text-xs text-gray-400 mt-1">
                R$ {(data.data.analise_financeira.despesas_por_dia ?? 0).toFixed(2)}/dia
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border-l-4 border-blue-500">
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Lucro Bruto</p>
              <p className="text-2xl font-bold text-blue-600">
                R$ {(data.data.analise_financeira.lucro_bruto ?? 0).toFixed(2)}
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border-l-4 border-purple-500">
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Margem de Lucro</p>
              <p className="text-2xl font-bold text-purple-600">
                {(data.data.analise_financeira.margem_lucro_percentual ?? 0).toFixed(1)}%
              </p>
            </div>
          </div>
        </div>
      )}

      {/* NOVA SEÇÃO: Inteligência de Produtos */}
      {data.data.analise_produtos && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Classificação ABC */}
          {data.data.analise_produtos.classificacao_abc?.classificacao && (
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700">
              <div className="flex items-center gap-2 mb-4">
                <BarChart className="w-5 h-5 text-indigo-600" />
                <h2 className="text-lg font-semibold text-gray-800 dark:text-white">📊 Curva ABC - Produtos</h2>
              </div>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                  <div>
                    <p className="font-semibold text-green-700 dark:text-green-400">Classe A - Essenciais</p>
                    <p className="text-xs text-gray-500">80% do faturamento</p>
                  </div>
                  <span className="text-2xl font-bold text-green-600">
                    {data.data.analise_produtos.classificacao_abc.resumo.A ?? 0}
                  </span>
                </div>
                <div className="flex items-center justify-between p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                  <div>
                    <p className="font-semibold text-yellow-700 dark:text-yellow-400">Classe B - Importantes</p>
                    <p className="text-xs text-gray-500">15% do faturamento</p>
                  </div>
                  <span className="text-2xl font-bold text-yellow-600">
                    {data.data.analise_produtos.classificacao_abc.resumo.B ?? 0}
                  </span>
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div>
                    <p className="font-semibold text-gray-700 dark:text-gray-400">Classe C - Secundários</p>
                    <p className="text-xs text-gray-500">5% do faturamento</p>
                  </div>
                  <span className="text-2xl font-bold text-gray-600">
                    {data.data.analise_produtos.classificacao_abc.resumo.C ?? 0}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Produtos Estrela vs Lentos */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp className="w-5 h-5 text-yellow-600" />
              <h2 className="text-lg font-semibold text-gray-800 dark:text-white">⭐ Produtos Estratégicos</h2>
            </div>
            <div className="space-y-4">
              {/* Produtos Estrela */}
              <div>
                <h3 className="font-semibold text-green-600 dark:text-green-400 mb-2 flex items-center gap-1">
                  🌟 Top Performers
                </h3>
                {data.data.analise_produtos.produtos_estrela && data.data.analise_produtos.produtos_estrela.length > 0 ? (
                  <div className="space-y-2">
                    {data.data.analise_produtos.produtos_estrela.slice(0, 3).map((produto: any, idx: number) => (
                      <div key={idx} className="flex justify-between items-center p-2 bg-green-50 dark:bg-green-900/20 rounded">
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{produto.nome}</span>
                        <span className="text-xs font-semibold text-green-600">{produto.market_share?.toFixed(1)}%</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500 italic">Nenhum produto estrela identificado</p>
                )}
              </div>

              {/* Produtos Lentos */}
              <div className="pt-3 border-t border-gray-200 dark:border-gray-700">
                <h3 className="font-semibold text-orange-600 dark:text-orange-400 mb-2 flex items-center gap-1">
                  🐌 Atenção Necessária
                </h3>
                {data.data.analise_produtos.produtos_lentos && data.data.analise_produtos.produtos_lentos.length > 0 ? (
                  <div className="space-y-2">
                    {data.data.analise_produtos.produtos_lentos.slice(0, 3).map((produto: any, idx: number) => (
                      <div key={idx} className="flex justify-between items-center p-2 bg-orange-50 dark:bg-orange-900/20 rounded">
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{produto.nome}</span>
                        <span className="text-xs text-gray-500">{produto.quantidade} un</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500 italic">Todos os produtos com bom giro</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* NOVA SEÇÃO: Top Produtos por Categoria */}
      {data.data.analise_produtos?.top_por_categoria && Object.keys(data.data.analise_produtos.top_por_categoria).length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2 mb-4">
            <Package className="w-6 h-6 text-purple-600" />
            <h2 className="text-xl font-bold text-gray-800 dark:text-white">🏆 Top 5 por Categoria</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Object.entries(data.data.analise_produtos.top_por_categoria).map(([categoria, produtos]: [string, any]) => (
              <div key={categoria} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <h3 className="font-bold text-gray-800 dark:text-white mb-3 pb-2 border-b border-gray-200 dark:border-gray-700">
                  {categoria}
                </h3>
                <div className="space-y-2">
                  {produtos.slice(0, 5).map((produto: any, idx: number) => {
                    const maxTotal = Math.max(...produtos.slice(0, 5).map((p: any) => p.total_vendido));
                    const widthPercent = maxTotal > 0 ? (produto.total_vendido / maxTotal) * 100 : 0;
                    
                    return (
                      <div key={idx} className="space-y-1">
                        <div className="flex justify-between items-center text-sm">
                          <span className="font-medium text-gray-700 dark:text-gray-300 truncate flex-1">
                            {idx + 1}. {produto.nome}
                          </span>
                          <span className="font-bold text-green-600 ml-2 whitespace-nowrap">
                            R$ {produto.total_vendido.toFixed(2)}
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div 
                            className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full transition-all"
                            style={{ width: `${widthPercent}%` }}
                          />
                        </div>
                        <p className="text-xs text-gray-500">{produto.quantidade_vendida} unidades</p>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Últimas Vendas */}
      {data.data.ultimas_vendas && data.data.ultimas_vendas.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">
            Últimas Vendas
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left py-2 px-3 text-sm font-semibold text-gray-600 dark:text-gray-300">Código</th>
                  <th className="text-left py-2 px-3 text-sm font-semibold text-gray-600 dark:text-gray-300">Cliente</th>
                  <th className="text-left py-2 px-3 text-sm font-semibold text-gray-600 dark:text-gray-300">Pagamento</th>
                  <th className="text-right py-2 px-3 text-sm font-semibold text-gray-600 dark:text-gray-300">Valor</th>
                  <th className="text-right py-2 px-3 text-sm font-semibold text-gray-600 dark:text-gray-300">Horário</th>
                </tr>
              </thead>
              <tbody>
                {data.data.ultimas_vendas.slice(0, 10).map((venda) => (
                  <tr key={venda.id} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                    <td className="py-3 px-3 text-sm text-gray-800 dark:text-white font-mono">{venda.codigo}</td>
                    <td className="py-3 px-3 text-sm text-gray-800 dark:text-white">{venda.cliente}</td>
                    <td className="py-3 px-3 text-sm text-gray-600 dark:text-gray-300 capitalize">{venda.forma_pagamento.replace('_', ' ')}</td>
                    <td className="py-3 px-3 text-sm text-gray-800 dark:text-white font-semibold text-right">
                      R$ {(venda?.total ?? 0).toFixed(2)}
                    </td>
                    <td className="py-3 px-3 text-sm text-gray-600 dark:text-gray-300 text-right">
                      {new Date(venda.data_venda).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default DashboardPage;
