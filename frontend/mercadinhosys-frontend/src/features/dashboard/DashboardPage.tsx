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
  Zap
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
      acao: string;
    }>;
    analise_produtos?: {
      top_produtos: Array<{
        id: number;
        nome: string;
        quantidade_vendida: number;
        total_vendido: number;
      }>;
    };
    analise_clientes?: {
      top_clientes: Array<{
        id: number;
        nome: string;
        total_compras: number;
      }>;
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
      console.log('Dashboard completo:', response.data);
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

  const { hoje, mes, alertas, analise_temporal } = data.data;

  // Cards principais
  const mainStats = [
    {
      title: 'Vendas Hoje',
      value: `R$ ${(hoje?.total_vendas ?? 0).toFixed(2)}`,
      subtitle: `${hoje?.quantidade_vendas ?? 0} vendas`,
      icon: ShoppingCart,
      trend: hoje?.crescimento_vs_ontem ?? 0,
      color: 'bg-green-500',
    },
    {
      title: 'Ticket Médio',
      value: `R$ ${(hoje?.ticket_medio ?? 0).toFixed(2)}`,
      subtitle: 'Valor médio por venda',
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
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg flex items-center gap-2"
        >
          <Zap className="w-4 h-4" />
          Atualizar
        </button>
      </div>

      {/* Cards Principais */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {mainStats.map((stat) => (
          <div
            key={stat.title}
            className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700 hover:shadow-xl transition-shadow"
          >
            <div className="flex items-center justify-between mb-4">
              <div className={`${stat.color} p-3 rounded-lg`}>
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
          </div>
        ))}
      </div>

      {/* Insights Automáticos */}
      {data.data.insights && data.data.insights.length > 0 && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-xl shadow p-6 border border-blue-200 dark:border-blue-800">
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
                    : insight.tipo === 'negativo'
                    ? 'bg-red-100 dark:bg-red-900/30 border-l-4 border-red-500'
                    : 'bg-yellow-100 dark:bg-yellow-900/30 border-l-4 border-yellow-500'
                }`}
              >
                <h3 className="font-semibold text-gray-800 dark:text-white mb-1">{insight.titulo}</h3>
                <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">{insight.descricao}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400 italic">💡 {insight.acao}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Alertas */}
      {(alertas.estoque_baixo.length > 0 || alertas.validade_proxima.length > 0) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Estoque Baixo */}
          {alertas.estoque_baixo.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6 border border-orange-200 dark:border-orange-800">
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
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6 border border-red-200 dark:border-red-800">
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
        </div>
      )}

      {/* Gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Vendas por Categoria */}
        {analise_temporal.vendas_por_categoria && analise_temporal.vendas_por_categoria.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6 border border-gray-200 dark:border-gray-700">
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

        {/* Vendas Últimos 7 Dias */}
        {analise_temporal.vendas_ultimos_7_dias && analise_temporal.vendas_ultimos_7_dias.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6 border border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">
              Vendas Últimos 7 Dias
            </h2>
            <div className="space-y-3">
              {analise_temporal.vendas_ultimos_7_dias.map((item) => {
                const maxTotal = Math.max(...analise_temporal.vendas_ultimos_7_dias.map(i => i.total));
                const percentage = maxTotal > 0 ? (item.total / maxTotal) * 100 : 0;
                return (
                  <div key={item.data} className="flex items-center gap-4">
                    <div className="w-20 flex-shrink-0">
                      <span className="text-xs text-gray-600 dark:text-gray-300">
                        {new Date(item.data).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })}
                      </span>
                    </div>
                    <div className="flex-1">
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4">
                        <div
                          className="bg-gradient-to-r from-green-500 to-green-600 h-4 rounded-full transition-all duration-500 flex items-center justify-end pr-2"
                          style={{ width: `${percentage}%` }}
                        >
                          {(item?.total ?? 0) > 0 && (
                            <span className="text-xs text-white font-semibold">
                              R$ {(item?.total ?? 0).toFixed(0)}
                            </span>
                          )}
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

      {/* Top Produtos e Top Clientes */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Produtos */}
        {data.data.analise_produtos?.top_produtos && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6 border border-gray-200 dark:border-gray-700">
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
                      <p className="text-xs text-gray-500">{produto?.quantidade_vendida ?? 0} unidades</p>
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
        {data.data.analise_clientes?.top_clientes && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6 border border-gray-200 dark:border-gray-700">
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
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2 mb-4">
            <Clock className="w-5 h-5 text-blue-600" />
            <h2 className="text-lg font-semibold text-gray-800 dark:text-white">
              Vendas por Hora (Últimas 24h)
            </h2>
          </div>
          <div className="flex items-end justify-between gap-2 h-40">
            {analise_temporal.vendas_por_hora.map((item) => {
              const maxTotal = Math.max(...analise_temporal.vendas_por_hora.map(i => i.total));
              const height = maxTotal > 0 ? (item.total / maxTotal) * 100 : 0;
              return (
                <div key={item.hora} className="flex-1 flex flex-col items-center gap-1">
                  <div 
                    className="w-full bg-gradient-to-t from-blue-500 to-blue-400 rounded-t hover:from-blue-600 hover:to-blue-500 transition-all cursor-pointer group relative"
                    style={{ height: `${height}%` }}
                  >
                    <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white px-2 py-1 rounded text-xs opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                      R$ {(item?.total ?? 0).toFixed(2)}
                    </div>
                  </div>
                  <span className="text-xs text-gray-500 dark:text-gray-400">{item.hora}h</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Últimas Vendas */}
      {data.data.ultimas_vendas && data.data.ultimas_vendas.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6 border border-gray-200 dark:border-gray-700">
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
                  <tr key={venda.id} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700/50">
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
