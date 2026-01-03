import React, { useEffect, useState } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  ShoppingCart, 
  Users, 
  Package, 
  CreditCard,
  DollarSign,
  BarChart
} from 'lucide-react';
import { dashboardService } from './dashboardService';
import { DashboardMetrics } from '../../types';

const DashboardPage: React.FC = () => {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMetrics();
  }, []);

  const loadMetrics = async () => {
    try {
      const data = await dashboardService.getMetrics();
      setMetrics(data);
    } catch (error) {
      console.error('Erro ao carregar métricas:', error);
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

  const stats = [
    {
      title: 'Vendas Hoje',
      value: `R$ ${metrics?.total_vendas_hoje.toFixed(2) || '0.00'}`,
      icon: ShoppingCart,
      trend: 'up',
      change: '+12%',
      color: 'bg-green-500',
    },
    {
      title: 'Ticket Médio',
      value: `R$ ${metrics?.ticket_medio.toFixed(2) || '0.00'}`,
      icon: DollarSign,
      trend: 'up',
      change: '+5%',
      color: 'bg-blue-500',
    },
    {
      title: 'Novos Clientes',
      value: metrics?.clientes_novos_mes.toString() || '0',
      icon: Users,
      trend: 'up',
      change: '+8%',
      color: 'bg-purple-500',
    },
    {
      title: 'Produtos Baixo Estoque',
      value: metrics?.produtos_baixo_estoque.toString() || '0',
      icon: Package,
      trend: 'down',
      change: '-3%',
      color: 'bg-yellow-500',
    },
    {
      title: 'Lucro Mês',
      value: `R$ ${metrics?.lucro_mes.toFixed(2) || '0.00'}`,
      icon: CreditCard,
      trend: 'up',
      change: '+15%',
      color: 'bg-indigo-500',
    },
    {
      title: 'Total Vendas Mês',
      value: `R$ ${metrics?.total_vendas_mes.toFixed(2) || '0.00'}`,
      icon: BarChart,
      trend: 'up',
      change: '+18%',
      color: 'bg-pink-500',
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800 dark:text-white">Dashboard</h1>
        <div className="flex space-x-2">
          <select className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-white">
            <option>Hoje</option>
            <option>Esta Semana</option>
            <option>Este Mês</option>
            <option>Este Ano</option>
          </select>
        </div>
      </div>

      {/* Cards de Estatísticas */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {stats.map((stat) => (
          <div
            key={stat.title}
            className="bg-white dark:bg-gray-800 rounded-xl shadow p-6 border border-gray-200 dark:border-gray-700"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">{stat.title}</p>
                <p className="text-2xl font-bold text-gray-800 dark:text-white mt-2">
                  {stat.value}
                </p>
                <div className="flex items-center mt-2">
                  {stat.trend === 'up' ? (
                    <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
                  ) : (
                    <TrendingDown className="w-4 h-4 text-red-500 mr-1" />
                  )}
                  <span
                    className={`text-sm ${
                      stat.trend === 'up' ? 'text-green-500' : 'text-red-500'
                    }`}
                  >
                    {stat.change}
                  </span>
                  <span className="text-sm text-gray-500 dark:text-gray-400 ml-2">
                    vs. mês anterior
                  </span>
                </div>
              </div>
              <div className={`${stat.color} p-3 rounded-lg`}>
                <stat.icon className="w-6 h-6 text-white" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Gráficos e Tabelas */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Vendas por Categoria */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6 border border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">
            Vendas por Categoria
          </h2>
          <div className="space-y-4">
            {metrics?.vendas_por_categoria.map((item) => (
              <div key={item.categoria}>
                <div className="flex justify-between mb-1">
                  <span className="text-sm text-gray-600 dark:text-gray-300">
                    {item.categoria}
                  </span>
                  <span className="text-sm font-medium text-gray-800 dark:text-white">
                    R$ {item.total.toFixed(2)}
                  </span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full"
                    style={{
                      width: `${(item.total / (metrics?.total_vendas_mes || 1)) * 100}%`,
                    }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Vendas Últimos 7 Dias */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6 border border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">
            Vendas Últimos 7 Dias
          </h2>
          <div className="space-y-4">
            {metrics?.vendas_ultimos_7_dias.map((item) => (
              <div key={item.data} className="flex items-center">
                <div className="w-24">
                  <span className="text-sm text-gray-600 dark:text-gray-300">
                    {new Date(item.data).toLocaleDateString('pt-BR')}
                  </span>
                </div>
                <div className="flex-1 ml-4">
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                    <div
                      className="bg-green-500 h-3 rounded-full"
                      style={{
                        width: `${(item.total / (metrics?.total_vendas_mes || 1)) * 100}%`,
                      }}
                    ></div>
                  </div>
                </div>
                <div className="w-20 text-right">
                  <span className="text-sm font-medium text-gray-800 dark:text-white">
                    R$ {item.total.toFixed(2)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Ações Rápidas */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6 border border-gray-200 dark:border-gray-700">
        <h2 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">
          Ações Rápidas
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <button className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors">
            <div className="flex flex-col items-center">
              <ShoppingCart className="w-8 h-8 text-blue-500 mb-2" />
              <span className="text-sm font-medium text-gray-800 dark:text-white">
                Nova Venda
              </span>
            </div>
          </button>
          <button className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg hover:bg-green-100 dark:hover:bg-green-900/30 transition-colors">
            <div className="flex flex-col items-center">
              <Package className="w-8 h-8 text-green-500 mb-2" />
              <span className="text-sm font-medium text-gray-800 dark:text-white">
                Adicionar Produto
              </span>
            </div>
          </button>
          <button className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg hover:bg-purple-100 dark:hover:bg-purple-900/30 transition-colors">
            <div className="flex flex-col items-center">
              <Users className="w-8 h-8 text-purple-500 mb-2" />
              <span className="text-sm font-medium text-gray-800 dark:text-white">
                Novo Cliente
              </span>
            </div>
          </button>
          <button className="p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg hover:bg-yellow-100 dark:hover:bg-yellow-900/30 transition-colors">
            <div className="flex flex-col items-center">
              <CreditCard className="w-8 h-8 text-yellow-500 mb-2" />
              <span className="text-sm font-medium text-gray-800 dark:text-white">
                Registrar Despesa
              </span>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;