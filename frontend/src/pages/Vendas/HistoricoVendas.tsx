import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { Search, Calendar, Filter, Download, Eye, Receipt, User, Package } from 'lucide-react';
import { vendaService } from '../../services/vendaService';
import Card from '../../components/UI/Card';
import Button from '../../components/UI/Button';

interface Venda {
    id: number;
    codigo: string;
    cliente_id: number | null;
    cliente_nome?: string;
    total: number;
    forma_pagamento: string;
    status: string;
    created_at: string;
    itens: Array<{
        id: number;
        produto_id: number;
        produto_nome: string;
        quantidade: number;
        preco_unitario: number;
        total_item: number;
    }>;
}

const HistoricoVendas: React.FC = () => {
    const [vendas, setVendas] = useState<Venda[]>([]);
    const [vendasFiltradas, setVendasFiltradas] = useState<Venda[]>([]);
    const [loading, setLoading] = useState(true);
    const [filtros, setFiltros] = useState({
        dataInicio: '',
        dataFim: '',
        formaPagamento: '',
        busca: ''
    });

    // Carrega vendas
    const carregarVendas = useCallback(async () => {
        try {
            setLoading(true);
            const params: Record<string, string> = {};

            if (filtros.dataInicio) params.data_inicio = filtros.dataInicio;
            if (filtros.dataFim) params.data_fim = filtros.dataFim;
            if (filtros.formaPagamento) params.forma_pagamento = filtros.formaPagamento;

            const response = await vendaService.listar();
            const vendasData = (Array.isArray(response.data) ? response.data : (response.data as unknown[] || [])) as Venda[];
            setVendas(vendasData);
            setVendasFiltradas(vendasData);
        } catch (error) {
            console.error('Erro ao carregar vendas:', error);
            alert('Erro ao carregar histórico de vendas');
        } finally {
            setLoading(false);
        }
    }, [filtros]);

    // Filtra vendas localmente (incluindo busca por produtos)
    const filtrarVendasLocalmente = useCallback(() => {
        if (!filtros.busca) {
            setVendasFiltradas(vendas);
            return;
        }

        const termoBusca = filtros.busca.toLowerCase();
        const vendasFiltradas = vendas.filter(venda => {
            // Busca no código da venda
            if (venda.codigo.toLowerCase().includes(termoBusca)) {
                return true;
            }

            // Busca no nome do cliente
            if (venda.cliente_nome && venda.cliente_nome.toLowerCase().includes(termoBusca)) {
                return true;
            }

            // Busca nos produtos da venda
            const temProduto = venda.itens.some(item =>
                item.produto_nome.toLowerCase().includes(termoBusca)
            );

            return temProduto;
        });

        setVendasFiltradas(vendasFiltradas);
    }, [filtros.busca, vendas]);

    // Carrega ao iniciar
    useEffect(() => {
        carregarVendas();
    }, [carregarVendas]);

    // Aplica filtro local quando busca mudar
    useEffect(() => {
        filtrarVendasLocalmente();
    }, [filtrarVendasLocalmente]);

    // Formata data
    const formatarData = (dataString: string) => {
        const data = new Date(dataString);
        return data.toLocaleDateString('pt-BR') + ' ' + data.toLocaleTimeString('pt-BR').slice(0, 5);
    };

    // Formata moeda
    const formatarMoeda = (valor: number) => {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(valor);
    };

    // Obtém cor do status
    const getStatusColor = (status: string) => {
        switch (status) {
            case 'finalizada': return 'bg-green-100 text-green-800';
            case 'cancelada': return 'bg-red-100 text-red-800';
            case 'pendente': return 'bg-yellow-100 text-yellow-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    // Obtém ícone da forma de pagamento
    const getPaymentIcon = (forma: string) => {
        switch (forma) {
            case 'dinheiro': return '💰';
            case 'cartao': return '💳';
            case 'pix': return '📱';
            default: return '💵';
        }
    };

    // Estatísticas das vendas filtradas
    const estatisticas = useMemo(() => {
        const totalVendas = vendasFiltradas.length;
        const totalValor = vendasFiltradas.reduce((total, venda) => total + venda.total, 0);
        const ticketMedio = totalVendas > 0 ? totalValor / totalVendas : 0;

        return { totalVendas, totalValor, ticketMedio };
    }, [vendasFiltradas]);

    return (
        <div className="space-y-6">
            {/* Cabeçalho */}
            <div className="flex flex-col md:flex-row md:items-center justify-between">
                <div>
                    <h1 className="text-2xl md:text-3xl font-bold text-gray-800">
                        <Receipt className="inline-block mr-3 h-8 w-8 text-azul-principal" />
                        Histórico de Vendas
                    </h1>
                    <p className="text-gray-600 mt-1">Gerencie e consulte todas as vendas realizadas</p>
                </div>

                <div className="mt-4 md:mt-0">
                    <Button
                        variant="primary"
                        icon={<Download className="h-4 w-4" />}
                        onClick={() => alert('Exportar para Excel - Em desenvolvimento')}
                    >
                        Exportar
                    </Button>
                </div>
            </div>

            {/* Filtros */}
            <Card title="Filtros" className="mb-6">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Data Início
                        </label>
                        <input
                            type="date"
                            value={filtros.dataInicio}
                            onChange={(e) => setFiltros({ ...filtros, dataInicio: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-azul-principal focus:border-transparent"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Data Fim
                        </label>
                        <input
                            type="date"
                            value={filtros.dataFim}
                            onChange={(e) => setFiltros({ ...filtros, dataFim: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-azul-principal focus:border-transparent"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Forma de Pagamento
                        </label>
                        <select
                            value={filtros.formaPagamento}
                            onChange={(e) => setFiltros({ ...filtros, formaPagamento: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-azul-principal focus:border-transparent"
                        >
                            <option value="">Todas</option>
                            <option value="dinheiro">Dinheiro</option>
                            <option value="cartao">Cartão</option>
                            <option value="pix">PIX</option>
                        </select>
                    </div>

                    <div className="flex items-end">
                        <Button
                            variant="primary"
                            className="w-full"
                            onClick={carregarVendas}
                            disabled={loading}
                        >
                            <Filter className="h-4 w-4 mr-2" />
                            Aplicar Filtros
                        </Button>
                    </div>
                </div>

                {/* Busca Avançada */}
                <div className="mt-4">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        Buscar por código, cliente ou produto
                    </label>
                    <div className="flex">
                        <div className="relative flex-1">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                            <input
                                type="text"
                                value={filtros.busca}
                                onChange={(e) => setFiltros({ ...filtros, busca: e.target.value })}
                                placeholder="Código da venda, nome do cliente ou produto..."
                                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-l-lg focus:ring-2 focus:ring-azul-principal focus:border-transparent"
                            />
                        </div>
                        <Button
                            variant="primary"
                            className="rounded-l-none"
                            onClick={filtrarVendasLocalmente}
                            disabled={loading}
                        >
                            <Search className="h-4 w-4" />
                        </Button>
                    </div>
                    <p className="text-sm text-gray-500 mt-1 flex items-center">
                        <Package className="h-4 w-4 mr-1" />
                        A busca inclui produtos das vendas
                    </p>
                </div>
            </Card>

            {/* Estatísticas */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card title="Vendas">
                    <div className="text-center">
                        <div className="text-3xl font-bold text-azul-principal">
                            {estatisticas.totalVendas}
                        </div>
                        <div className="text-gray-600">Vendas filtradas</div>
                    </div>
                </Card>

                <Card title="Faturamento">
                    <div className="text-center">
                        <div className="text-3xl font-bold text-verde-positivo">
                            {formatarMoeda(estatisticas.totalValor)}
                        </div>
                        <div className="text-gray-600">Total vendido</div>
                    </div>
                </Card>

                <Card title="Ticket Médio">
                    <div className="text-center">
                        <div className="text-3xl font-bold text-purple-600">
                            {formatarMoeda(estatisticas.ticketMedio)}
                        </div>
                        <div className="text-gray-600">Ticket médio</div>
                    </div>
                </Card>
            </div>

            {/* Tabela de vendas */}
            <Card title={`Vendas (${vendasFiltradas.length})`}>
                {loading ? (
                    <div className="text-center py-8">
                        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-azul-principal"></div>
                        <p className="mt-2 text-gray-600">Carregando vendas...</p>
                    </div>
                ) : vendasFiltradas.length === 0 ? (
                    <div className="text-center py-8">
                        <Receipt className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                        <p className="text-gray-500">Nenhuma venda encontrada</p>
                        <p className="text-sm text-gray-400 mt-1">
                            {filtros.busca ? 'Tente ajustar os termos da busca' : 'Tente ajustar os filtros'}
                        </p>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b bg-gray-50">
                                    <th className="text-left py-3 px-4 text-gray-600 font-medium">Código</th>
                                    <th className="text-left py-3 px-4 text-gray-600 font-medium">Data/Hora</th>
                                    <th className="text-left py-3 px-4 text-gray-600 font-medium">Cliente</th>
                                    <th className="text-left py-3 px-4 text-gray-600 font-medium">Produtos</th>
                                    <th className="text-left py-3 px-4 text-gray-600 font-medium">Pagamento</th>
                                    <th className="text-left py-3 px-4 text-gray-600 font-medium">Status</th>
                                    <th className="text-left py-3 px-4 text-gray-600 font-medium">Total</th>
                                    <th className="text-left py-3 px-4 text-gray-600 font-medium">Ações</th>
                                </tr>
                            </thead>
                            <tbody>
                                {vendasFiltradas.map((venda) => (
                                    <tr key={venda.id} className="border-b hover:bg-gray-50">
                                        <td className="py-3 px-4 font-mono font-semibold">
                                            {venda.codigo}
                                        </td>
                                        <td className="py-3 px-4">
                                            <div className="flex items-center">
                                                <Calendar className="h-4 w-4 text-gray-400 mr-2" />
                                                {formatarData(venda.created_at)}
                                            </div>
                                        </td>
                                        <td className="py-3 px-4">
                                            {venda.cliente_id ? (
                                                <div className="flex items-center">
                                                    <User className="h-4 w-4 text-gray-400 mr-2" />
                                                    <span className="truncate max-w-[150px]">
                                                        {venda.cliente_nome || `Cliente #${venda.cliente_id}`}
                                                    </span>
                                                </div>
                                            ) : (
                                                <span className="text-gray-400">Não informado</span>
                                            )}
                                        </td>
                                        <td className="py-3 px-4">
                                            <div className="text-sm text-gray-600 max-w-[200px]">
                                                {venda.itens.slice(0, 2).map((item) => (
                                                    <div key={item.id} className="truncate">
                                                        {item.quantidade}x {item.produto_nome}
                                                    </div>
                                                ))}
                                                {venda.itens.length > 2 && (
                                                    <div className="text-azul-principal font-medium">
                                                        +{venda.itens.length - 2} produtos
                                                    </div>
                                                )}
                                            </div>
                                        </td>
                                        <td className="py-3 px-4">
                                            <div className="flex items-center">
                                                <span className="mr-2">{getPaymentIcon(venda.forma_pagamento)}</span>
                                                <span className="capitalize">{venda.forma_pagamento}</span>
                                            </div>
                                        </td>
                                        <td className="py-3 px-4">
                                            <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(venda.status)}`}>
                                                {venda.status}
                                            </span>
                                        </td>
                                        <td className="py-3 px-4 font-bold text-gray-800">
                                            {formatarMoeda(venda.total)}
                                        </td>
                                        <td className="py-3 px-4">
                                            <div className="flex space-x-2">
                                                <Button
                                                    variant="secondary"
                                                    size="sm"
                                                    onClick={() => alert(`Detalhes da venda ${venda.codigo} - Em desenvolvimento`)}
                                                    icon={<Eye className="h-4 w-4" />}
                                                >
                                                    Detalhes
                                                </Button>
                                                <Button
                                                    variant="secondary"
                                                    size="sm"
                                                    onClick={() => alert(`Imprimir venda ${venda.codigo} - Em desenvolvimento`)}
                                                    icon={<Receipt className="h-4 w-4" />}
                                                >
                                                    Comprovante
                                                </Button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                {/* Paginação */}
                {vendasFiltradas.length > 0 && (
                    <div className="flex justify-between items-center mt-6 pt-6 border-t border-gray-200">
                        <div className="text-sm text-gray-600">
                            Mostrando {vendasFiltradas.length} de {vendas.length} vendas
                        </div>
                        <div className="flex space-x-2">
                            <Button variant="secondary" size="sm" disabled>
                                Anterior
                            </Button>
                            <Button variant="secondary" size="sm" disabled>
                                Próxima
                            </Button>
                        </div>
                    </div>
                )}
            </Card>
        </div>
    );
};

export default HistoricoVendas;