import React, { useState, useEffect } from 'react';
import {
    Truck,
    Package,
    CheckCircle,
    MapPin,
    TrendingUp,
    Users,
    ChevronRight,
    AlertCircle,
    Plus,
    Fuel,
    Navigation
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { deliveryService, Entrega } from './deliveryService';
import LiveTracking from './LiveTracking';
import CreateDeliveryModal from './CreateDeliveryModal';
import UnifiedDeliverySaleModal from './UnifiedDeliverySaleModal';
import toast from 'react-hot-toast';

const DeliveryDashboard: React.FC = () => {
    const [stats, setStats] = useState<any>(null);
    const [entregasRecentes, setEntregasRecentes] = useState<Entrega[]>([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isUnifiedModalOpen, setIsUnifiedModalOpen] = useState(false);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [statsRes, entregasRes] = await Promise.all([
                deliveryService.getStats(),
                deliveryService.getEntregas('todos')
            ]);

            if (statsRes.success) setStats(statsRes.stats);
            if (entregasRes.success) setEntregasRecentes(entregasRes.entregas.slice(0, 5));
        } catch (error) {
            toast.error('Erro ao carregar dados do delivery');
        } finally {
            setLoading(false);
        }
    };

    const StatusCard = ({ title, value, icon: Icon, color, delay }: any) => (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay }}
            className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm border border-gray-100 dark:border-gray-700 hover:shadow-md transition-all group"
        >
            <div className="flex items-center justify-between mb-4">
                <div className={`p-3 rounded-xl ${color} bg-opacity-10 group-hover:scale-110 transition-transform`}>
                    <Icon className={`w-6 h-6 ${color.replace('bg-', 'text-')}`} />
                </div>
                <div className="text-xs font-medium text-green-500 flex items-center bg-green-50 dark:bg-green-900/20 px-2 py-1 rounded-full">
                    <TrendingUp className="w-3 h-3 mr-1" />
                    +12%
                </div>
            </div>
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">{title}</h3>
            <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{value || 0}</p>
        </motion.div>
    );

    return (
        <div className="p-6 space-y-8 max-w-[1600px] mx-auto">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-white tracking-tight">
                        Centro de Logística <span className="text-blue-600">Sênior</span>
                    </h1>
                    <p className="text-gray-500 dark:text-gray-400 mt-1">
                        Monitoramento em tempo real da operação de entregas
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <button
                        onClick={fetchData}
                        className="px-4 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                    >
                        Atualizar Dados
                    </button>
                    <button
                        onClick={() => setIsUnifiedModalOpen(true)}
                        className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-blue-700 hover:from-indigo-700 hover:to-blue-800 text-white rounded-xl text-sm font-bold shadow-lg shadow-blue-500/30 transition-all active:scale-95 flex items-center gap-2 border border-white/10"
                    >
                        <Plus className="w-4 h-4" /> Venda Entrega
                    </button>
                </div>
            </div>

            {/* Stats Grid - Magnitude Senior */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatusCard
                    title="Pendentes"
                    value={stats?.pendentes}
                    icon={Package}
                    color="bg-orange-500"
                    delay={0.1}
                />
                <StatusCard
                    title="Em Rota"
                    value={stats?.em_rota}
                    icon={Truck}
                    color="bg-blue-500"
                    delay={0.2}
                />
                <StatusCard
                    title="Entregas (Hoje)"
                    value={stats?.entregues_hoje}
                    icon={CheckCircle}
                    color="bg-green-500"
                    delay={0.3}
                />
                <StatusCard
                    title="Ticket Médio Delivery"
                    value={new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(stats?.ticket_medio || 0)}
                    icon={TrendingUp}
                    color="bg-indigo-500"
                    delay={0.4}
                />
            </div>

            {/* Logistics Efficiency Section */}
            <motion.div
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                className="grid grid-cols-1 md:grid-cols-3 gap-6 bg-slate-900 rounded-3xl p-8 text-white shadow-2xl relative overflow-hidden group"
            >
                <div className="absolute top-0 right-0 w-64 h-64 bg-blue-600/10 rounded-full -mr-32 -mt-32 blur-3xl group-hover:bg-blue-600/20 transition-colors" />

                <div className="relative z-10">
                    <p className="text-blue-300/70 text-xs font-bold uppercase tracking-[0.2em] flex items-center gap-2">
                        <Navigation className="w-3 h-3" /> Distância Total
                    </p>
                    <div className="flex items-baseline gap-2 mt-3">
                        <span className="text-5xl font-black">{(stats?.km_totais || 0).toFixed(1)}</span>
                        <span className="text-blue-400 font-bold">KM</span>
                    </div>
                </div>

                <div className="relative z-10 md:border-l border-white/5 md:pl-8">
                    <p className="text-blue-300/70 text-xs font-bold uppercase tracking-[0.2em] flex items-center gap-2">
                        <Fuel className="w-3 h-3" /> Consumo Estimado
                    </p>
                    <div className="flex items-baseline gap-2 mt-3">
                        <span className="text-5xl font-black text-emerald-400">{(stats?.combustivel_total || 0).toFixed(1)}</span>
                        <span className="text-emerald-500/70 font-bold">LTS</span>
                    </div>
                </div>

                <div className="relative z-10 md:border-l border-white/5 md:pl-8">
                    <p className="text-blue-300/70 text-xs font-bold uppercase tracking-[0.2em]">Top Produto Entregue</p>
                    <div className="flex items-center gap-3 mt-4">
                        <div className="p-2 bg-white/5 rounded-lg">
                            <Package className="w-5 h-5 text-blue-400" />
                        </div>
                        <span className="text-xl font-bold truncate max-w-[200px]">{stats?.top_produto || 'Processando...'}</span>
                    </div>
                </div>
            </motion.div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Recent Deliveries */}
                <div className="lg:col-span-2 space-y-4">
                    <div className="flex items-center justify-between px-2">
                        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Fluxo de Entregas</h2>
                        <button className="text-sm font-medium text-blue-600 hover:text-blue-700 flex items-center">
                            Ver todas <ChevronRight className="w-4 h-4 ml-1" />
                        </button>
                    </div>

                    <div className="grid gap-4">
                        <AnimatePresence>
                            {loading ? (
                                Array(3).fill(0).map((_, i) => (
                                    <div key={i} className="h-24 bg-gray-100 dark:bg-gray-800 animate-pulse rounded-2xl" />
                                ))
                            ) : entregasRecentes.length > 0 ? (
                                entregasRecentes.map((entrega, index) => (
                                    <motion.div
                                        key={entrega.id}
                                        initial={{ opacity: 0, x: -20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: index * 0.1 }}
                                        className="bg-white dark:bg-gray-800 p-4 rounded-2xl border border-gray-100 dark:border-gray-700 flex items-center justify-between group hover:border-blue-200 dark:hover:border-blue-900/30 transition-all cursor-pointer"
                                    >
                                        <div className="flex items-center gap-4">
                                            <div className="w-12 h-12 rounded-xl bg-gray-50 dark:bg-gray-900 flex items-center justify-center text-gray-400 group-hover:text-blue-500 transition-colors">
                                                <Package className="w-6 h-6" />
                                            </div>
                                            <div>
                                                <h4 className="font-semibold text-gray-900 dark:text-white">#{entrega.codigo_rastreamento}</h4>
                                                <p className="text-sm text-gray-500 flex items-center mt-0.5">
                                                    <MapPin className="w-3 h-3 mr-1" /> {entrega.endereco_bairro}
                                                </p>
                                            </div>
                                        </div>

                                        <div className="hidden md:flex flex-col items-end gap-1">
                                            <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${entrega.status === 'entregue' ? 'bg-green-100 text-green-700' :
                                                entrega.status === 'em_rota' ? 'bg-blue-100 text-blue-700' :
                                                    'bg-amber-100 text-amber-700'
                                                }`}>
                                                {entrega.status.replace('_', ' ')}
                                            </span>
                                            <span className="text-xs text-gray-400">Previsão: {new Date(entrega.data_prevista).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                        </div>
                                    </motion.div>
                                ))
                            ) : (
                                <div className="bg-gray-50 dark:bg-gray-900/50 rounded-2xl p-12 text-center border-2 border-dashed border-gray-200 dark:border-gray-800">
                                    <Package className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                                    <p className="text-gray-500">Sem entregas ativas no momento</p>
                                </div>
                            )}
                        </AnimatePresence>
                    </div>
                </div>

                {/* Top Drivers / Info Sidebar */}
                <div className="space-y-6">
                    {entregasRecentes.find(e => e.status === 'em_rota') ? (
                        <LiveTracking entrega={entregasRecentes.find(e => e.status === 'em_rota')} />
                    ) : (
                        <div className="bg-gradient-to-br from-blue-600 to-indigo-700 rounded-3xl p-6 text-white shadow-xl shadow-blue-500/20">
                            <div className="flex items-center gap-3 mb-6">
                                <Users className="w-6 h-6" />
                                <h3 className="font-bold">Equipe Ativa</h3>
                            </div>
                            <div className="space-y-4">
                                {stats?.top_motoristas?.map((m: any, i: number) => (
                                    <div key={i} className="flex items-center justify-between bg-white/10 p-3 rounded-2xl backdrop-blur-sm">
                                        <span className="font-medium text-sm">{m.nome}</span>
                                        <div className="flex items-center gap-2">
                                            <span className="text-blue-200 text-xs">{(m.total || 0)} ent.</span>
                                            <div className="w-16 h-1.5 bg-white/10 rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-blue-400"
                                                    style={{ width: `${Math.min(100, (m.total / 10) * 100)}%` }}
                                                />
                                            </div>
                                        </div>
                                    </div>
                                ))}
                                {(!stats?.top_motoristas || stats.top_motoristas.length === 0) && (
                                    <p className="text-blue-100 text-sm opacity-80 italic">Aguardando dados da equipe...</p>
                                )}
                            </div>
                        </div>
                    )}

                    <div className="bg-amber-50 dark:bg-amber-900/20 p-6 rounded-3xl border border-amber-100 dark:border-amber-900/30">
                        <div className="flex items-start gap-4">
                            <AlertCircle className="w-6 h-6 text-amber-600 shrink-0" />
                            <div>
                                <h4 className="font-bold text-amber-900 dark:text-amber-100">Manutenção de Frota</h4>
                                <p className="text-sm text-amber-700 dark:text-amber-400 mt-1">Sua frota percorreu {(stats?.km_totais || 0).toFixed(0)}km. Recomendamos revisão preventiva a cada 5000km.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <AnimatePresence>
                {isModalOpen && (
                    <CreateDeliveryModal
                        isOpen={isModalOpen}
                        onClose={() => setIsModalOpen(false)}
                        onCreated={fetchData}
                    />
                )}
                {isUnifiedModalOpen && (
                    <UnifiedDeliverySaleModal
                        isOpen={isUnifiedModalOpen}
                        onClose={() => setIsUnifiedModalOpen(false)}
                        onCreated={fetchData}
                    />
                )}
            </AnimatePresence>
        </div>
    );
};

export default DeliveryDashboard;
