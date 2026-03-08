import React, { useState, useEffect, useCallback } from 'react';
import {
    Activity,
    RefreshCcw,
    Search,
    ShoppingBag,
    UserPlus,
    Package,
    AlertCircle,
    Building2,
    DollarSign,
    Clock
} from 'lucide-react';
import { apiClient } from '../../api/apiClient';

interface Log {
    id: number;
    estabelecimento_id: number;
    estabelecimento_nome: string;
    usuario_id: number;
    usuario_nome: string;
    tipo_evento: string;
    descricao: string;
    valor: number;
    data_evento: string;
    detalhes: any;
}

interface Summary {
    total_estabelecimentos: number;
    vendas_hoje_qtd: number;
    vendas_hoje_valor: number;
    novos_clientes_recentes: Array<{ nome: string, data: string }>;
}

const SystemMonitorPage: React.FC = () => {
    const [logs, setLogs] = useState<Log[]>([]);
    const [summary, setSummary] = useState<Summary | null>(null);
    const [loading, setLoading] = useState(true);
    const [autoRefresh, setAutoRefresh] = useState(true);
    const [filterType, setFilterType] = useState<string>('');
    const [searchTerm, setSearchTerm] = useState('');

    const fetchData = useCallback(async () => {
        try {
            const [logsRes, summaryRes] = await Promise.all([
                apiClient.get('/saas/monitor/logs'),
                apiClient.get('/saas/monitor/summary')
            ]);

            if (logsRes.data?.success) setLogs(logsRes.data.logs);
            if (summaryRes.data?.success) setSummary(summaryRes.data.summary);
        } catch (error) {
            console.error('Erro ao buscar dados do monitor:', error);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchData();
        let interval: any;
        if (autoRefresh) {
            interval = setInterval(fetchData, 10000); // Poll a cada 10s
        }
        return () => clearInterval(interval);
    }, [fetchData, autoRefresh]);

    const getEventIcon = (type: string) => {
        switch (type) {
            case 'venda_finalizada': return <ShoppingBag className="text-green-500" size={20} />;
            case 'estabelecimento_registrado': return <UserPlus className="text-blue-500" size={20} />;
            case 'produto_criado': return <Package className="text-orange-500" size={20} />;
            default: return <Activity className="text-gray-400" size={20} />;
        }
    };

    const filteredLogs = logs.filter(log => {
        const matchesType = !filterType || log.tipo_evento === filterType;
        const matchesSearch = !searchTerm ||
            log.estabelecimento_nome.toLowerCase().includes(searchTerm.toLowerCase()) ||
            log.descricao.toLowerCase().includes(searchTerm.toLowerCase());
        return matchesType && matchesSearch;
    });

    return (
        <div className="space-y-6">
            <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                        <Activity className="text-indigo-600" />
                        Gerenciamento & Logs Real-Time
                    </h1>
                    <p className="text-gray-500">Monitoramento centralizado de todos os clientes SaaS</p>
                </div>

                <div className="flex items-center gap-4">
                    <button
                        onClick={() => setAutoRefresh(!autoRefresh)}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium transition-colors ${autoRefresh
                            ? 'bg-indigo-50 border-indigo-200 text-indigo-700'
                            : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                            }`}
                    >
                        <RefreshCcw size={16} className={autoRefresh ? 'animate-spin' : ''} />
                        {autoRefresh ? 'Auto-Update Ligado' : 'Auto-Update Desligado'}
                    </button>
                    <button
                        onClick={() => { setLoading(true); fetchData(); }}
                        className="p-2 bg-white border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                    >
                        <RefreshCcw size={20} />
                    </button>
                </div>
            </header>

            {/* Top Cards Summary */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
                            <Building2 size={24} />
                        </div>
                        <div>
                            <p className="text-sm text-gray-500 uppercase font-semibold">Clientes Ativos</p>
                            <h2 className="text-2xl font-bold">{summary?.total_estabelecimentos || 0}</h2>
                        </div>
                    </div>
                </div>

                <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-green-50 text-green-600 rounded-lg">
                            <DollarSign size={24} />
                        </div>
                        <div>
                            <p className="text-sm text-gray-500 uppercase font-semibold">Faturamento Global Hoje</p>
                            <h2 className="text-2xl font-bold text-green-600">R$ {summary?.vendas_hoje_valor.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) || '0,00'}</h2>
                        </div>
                    </div>
                    <p className="text-xs text-gray-400 mt-2">{summary?.vendas_hoje_qtd || 0} vendas processadas hoje</p>
                </div>

                <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-purple-50 text-purple-600 rounded-lg">
                            <UserPlus size={24} />
                        </div>
                        <div>
                            <p className="text-sm text-gray-500 uppercase font-semibold">Integridade do Sistema</p>
                            <div className="flex items-center gap-2 mt-1">
                                <span className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></span>
                                <span className="font-semibold text-green-700">Online</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Filters & Content */}
            <div className="bg-white border rounded-xl overflow-hidden shadow-sm">
                <div className="p-4 border-b bg-gray-50 flex flex-col md:flex-row gap-4">
                    <div className="relative flex-1">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                        <input
                            type="text"
                            placeholder="Buscar por cliente ou descrição..."
                            className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                    <div className="flex gap-2">
                        <select
                            className="px-4 py-2 border rounded-lg bg-white"
                            value={filterType}
                            onChange={(e) => setFilterType(e.target.value)}
                        >
                            <option value="">Todos Eventos</option>
                            <option value="venda_finalizada">Vendas</option>
                            <option value="produto_criado">Cadastros</option>
                            <option value="estabelecimento_registrado">Onboarding</option>
                        </select>
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead className="bg-gray-50 text-gray-500 text-xs uppercase font-medium">
                            <tr>
                                <th className="px-6 py-3">Tipo</th>
                                <th className="px-6 py-3">Cliente (Estabelecimento)</th>
                                <th className="px-6 py-3">Atividade / Descrição</th>
                                <th className="px-6 py-3">Valor</th>
                                <th className="px-6 py-3">Horário</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {loading ? (
                                Array(5).fill(0).map((_, i) => (
                                    <tr key={i} className="animate-pulse">
                                        <td colSpan={5} className="px-6 py-4 h-12 bg-gray-50"></td>
                                    </tr>
                                ))
                            ) : filteredLogs.length > 0 ? (
                                filteredLogs.map((log) => (
                                    <tr key={log.id} className="hover:bg-gray-50 transition-colors">
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-2">
                                                {getEventIcon(log.tipo_evento)}
                                                <span className="text-xs font-semibold capitalize bg-gray-100 px-2 py-1 rounded text-gray-600">
                                                    {log.tipo_evento.replace('_', ' ')}
                                                </span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex flex-col">
                                                <span className="font-bold text-gray-900">{log.estabelecimento_nome}</span>
                                                <span className="text-xs text-gray-400">ID: {log.estabelecimento_id}</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex flex-col">
                                                <span className="text-sm text-gray-700">{log.descricao}</span>
                                                <span className="text-xs text-gray-400">Por: {log.usuario_nome}</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            {log.valor > 0 ? (
                                                <span className="font-bold text-green-600">
                                                    R$ {log.valor.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                                                </span>
                                            ) : (
                                                <span className="text-gray-400">-</span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-1 text-xs text-gray-500 whitespace-nowrap">
                                                <Clock size={12} />
                                                {new Date(log.data_evento).toLocaleString('pt-BR')}
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            ) : (
                                <tr>
                                    <td colSpan={5} className="px-6 py-12 text-center text-gray-400">
                                        <div className="flex flex-col items-center gap-2">
                                            <AlertCircle size={40} />
                                            <p>Nenhum log de atividade encontrado para os filtros atuais.</p>
                                        </div>
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default SystemMonitorPage;
