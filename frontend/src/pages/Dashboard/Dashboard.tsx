import React from 'react';
import {
    TrendingUp,
    TrendingDown,
    DollarSign,
    Package,
    AlertTriangle,
    Users,
    ShoppingCart,
    BarChart3,
    Calendar
} from 'lucide-react';
import Card from '../../components/UI/Card';

const Dashboard: React.FC = () => {
    // Dados dos KPIs
    const kpis = [
        {
            title: 'Vendas Hoje',
            value: 'R$ 2.450,80',
            icon: <DollarSign className="h-6 w-6" />,
            color: 'bg-blue-100 text-azul-principal',
            change: '+12%',
            trend: 'up',
            description: 'Em relação a ontem'
        },
        {
            title: 'Produtos em Estoque',
            value: '1.245',
            icon: <Package className="h-6 w-6" />,
            color: 'bg-green-100 text-verde-positivo',
            change: '-3%',
            trend: 'down',
            description: '3 abaixo do mínimo'
        },
        {
            title: 'Alertas de Validade',
            value: '23',
            icon: <AlertTriangle className="h-6 w-6" />,
            color: 'bg-orange-100 text-laranja-alerta',
            change: '+5',
            trend: 'up',
            description: 'Produtos próximos do vencimento'
        },
        {
            title: 'Clientes Ativos',
            value: '156',
            icon: <Users className="h-6 w-6" />,
            color: 'bg-purple-100 text-purple-600',
            change: '+8%',
            trend: 'up',
            description: 'Este mês'
        }
    ];

    // Produtos mais vendidos
    const topProducts = [
        { id: 1, name: 'Arroz 5kg', category: 'Mercearia', sales: 156, stock: 42, status: 'em_estoque' },
        { id: 2, name: 'Café 500g', category: 'Mercearia', sales: 89, stock: 15, status: 'baixo' },
        { id: 3, name: 'Leite 1L', category: 'Laticínios', sales: 203, stock: 67, status: 'em_estoque' },
        { id: 4, name: 'Óleo 900ml', category: 'Mercearia', sales: 120, stock: 28, status: 'atencao' },
        { id: 5, name: 'Açúcar 1kg', category: 'Mercearia', sales: 95, stock: 18, status: 'baixo' },
    ];

    // Função para obter status
    const getStatusBadge = (status: string) => {
        const statusMap: Record<string, { text: string; color: string; bg: string }> = {
            em_estoque: { text: 'Em Estoque', color: 'text-green-700', bg: 'bg-green-100' },
            atencao: { text: 'Atenção', color: 'text-yellow-700', bg: 'bg-yellow-100' },
            baixo: { text: 'Baixo Estoque', color: 'text-laranja-alerta', bg: 'bg-orange-100' },
        };

        const statusInfo = statusMap[status] || statusMap.em_estoque;
        return (
            <span className={`px-3 py-1 rounded-full text-xs font-medium ${statusInfo.bg} ${statusInfo.color}`}>
                {statusInfo.text}
            </span>
        );
    };

    return (
        <div className="space-y-6">
            {/* Cabeçalho */}
            <div className="flex flex-col md:flex-row md:items-center justify-between">
                <div>
                    <h1 className="text-2xl md:text-3xl font-bold text-gray-800">Dashboard</h1>
                    <p className="text-gray-600 mt-1">
                        {new Date().toLocaleDateString('pt-BR', {
                            weekday: 'long',
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric'
                        })}
                    </p>
                </div>

                <div className="mt-4 md:mt-0 flex space-x-3">
                    <button className="bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded-lg flex items-center space-x-2 hover:bg-gray-50">
                        <Calendar className="h-4 w-4" />
                        <span>Hoje</span>
                    </button>
                    <button className="bg-azul-principal text-white px-4 py-2 rounded-lg flex items-center space-x-2 hover:bg-blue-700">
                        <BarChart3 className="h-4 w-4" />
                        <span>Gerar Relatório</span>
                    </button>
                </div>
            </div>

            {/* Grid de KPIs */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                {kpis.map((kpi, index) => (
                    <Card
                        key={index}
                        title={kpi.title}
                        className="hover:shadow-lg transition-shadow duration-300"
                        icon={
                            <div className={`p-3 rounded-lg ${kpi.color}`}>
                                {kpi.icon}
                            </div>
                        }
                        footer={
                            <div className="flex items-center justify-between text-sm">
                                <span className="text-gray-500">{kpi.description}</span>
                                <span className={`flex items-center ${kpi.trend === 'up' ? 'text-green-600' : 'text-red-600'}`}>
                                    {kpi.trend === 'up' ? (
                                        <TrendingUp className="h-4 w-4 mr-1" />
                                    ) : (
                                        <TrendingDown className="h-4 w-4 mr-1" />
                                    )}
                                    {kpi.change}
                                </span>
                            </div>
                        }
                    >
                        <h3 className="text-2xl font-bold text-gray-800 mt-2">{kpi.value}</h3>
                    </Card>
                ))}
            </div>

            {/* Duas colunas: Produtos + Ações rápidas */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Coluna 1: Produtos mais vendidos */}
                <div className="lg:col-span-2">
                    <Card
                        title="Produtos Mais Vendidos"
                        icon={<ShoppingCart className="h-5 w-5" />}
                        footer={
                            <a href="#" className="text-azul-principal hover:text-blue-700 font-medium text-sm">
                                Ver todos os produtos →
                            </a>
                        }
                    >
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b">
                                        <th className="text-left py-3 px-2 text-gray-600 font-medium">Produto</th>
                                        <th className="text-left py-3 px-2 text-gray-600 font-medium">Categoria</th>
                                        <th className="text-left py-3 px-2 text-gray-600 font-medium">Vendas</th>
                                        <th className="text-left py-3 px-2 text-gray-600 font-medium">Estoque</th>
                                        <th className="text-left py-3 px-2 text-gray-600 font-medium">Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {topProducts.map((product) => (
                                        <tr key={product.id} className="border-b hover:bg-gray-50">
                                            <td className="py-3 px-2 font-medium">{product.name}</td>
                                            <td className="py-3 px-2 text-gray-600">{product.category}</td>
                                            <td className="py-3 px-2">
                                                <span className="font-medium">{product.sales}</span>
                                                <span className="text-gray-500 text-sm ml-1">unid.</span>
                                            </td>
                                            <td className="py-3 px-2">
                                                <span className="font-medium">{product.stock}</span>
                                                <span className="text-gray-500 text-sm ml-1">unid.</span>
                                            </td>
                                            <td className="py-3 px-2">{getStatusBadge(product.status)}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </Card>
                </div>

                {/* Coluna 2: Ações rápidas */}
                <div>
                    <Card title="Ações Rápidas">
                        <div className="space-y-4">
                            <button className="w-full bg-azul-principal hover:bg-blue-700 text-white p-4 rounded-xl flex items-center justify-center transition-colors">
                                <ShoppingCart className="h-5 w-5 mr-2" />
                                <span className="font-semibold">Nova Venda</span>
                            </button>

                            <button className="w-full bg-verde-positivo hover:bg-green-700 text-white p-4 rounded-xl flex items-center justify-center transition-colors">
                                <Package className="h-5 w-5 mr-2" />
                                <span className="font-semibold">Adicionar Produto</span>
                            </button>

                            <button className="w-full bg-laranja-alerta hover:bg-orange-700 text-white p-4 rounded-xl flex items-center justify-center transition-colors">
                                <AlertTriangle className="h-5 w-5 mr-2" />
                                <span className="font-semibold">Ver Alertas</span>
                            </button>

                            <div className="pt-4 border-t border-gray-100">
                                <h4 className="font-medium text-gray-700 mb-3">Atalhos</h4>
                                <div className="space-y-2">
                                    <a href="#" className="flex items-center justify-between p-2 hover:bg-gray-100 rounded-lg">
                                        <span className="text-gray-600">Histórico de Vendas</span>
                                        <span className="text-gray-400">→</span>
                                    </a>
                                    <a href="#" className="flex items-center justify-between p-2 hover:bg-gray-100 rounded-lg">
                                        <span className="text-gray-600">Clientes Frequentes</span>
                                        <span className="text-gray-400">→</span>
                                    </a>
                                    <a href="#" className="flex items-center justify-between p-2 hover:bg-gray-100 rounded-lg">
                                        <span className="text-gray-600">Relatório Financeiro</span>
                                        <span className="text-gray-400">→</span>
                                    </a>
                                </div>
                            </div>
                        </div>
                    </Card>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;