import React, { useState, useEffect } from 'react';
import {
    Search,
    Filter,
    MoreVertical,
    ExternalLink,
    User,
    Calendar,
    MapPin,
    Hash
} from 'lucide-react';
import { deliveryService, Entrega } from './deliveryService';
import toast from 'react-hot-toast';

const DeliveryList: React.FC = () => {
    const [entregas, setEntregas] = useState<Entrega[]>([]);
    const [loading, setLoading] = useState(true);
    const [filtroStatus, setFiltroStatus] = useState('todos');

    useEffect(() => {
        carregarEntregas();
    }, [filtroStatus]);

    const carregarEntregas = async () => {
        try {
            setLoading(true);
            const res = await deliveryService.getEntregas(filtroStatus);
            if (res.success) setEntregas(res.entregas);
        } catch (error) {
            toast.error('Erro ao listar entregas');
        } finally {
            setLoading(false);
        }
    };

    const getStatusStyle = (status: string) => {
        switch (status) {
            case 'entregue': return 'bg-green-100 text-green-700 border-green-200';
            case 'em_rota': return 'bg-blue-100 text-blue-700 border-blue-200';
            case 'cancelada': return 'bg-red-100 text-red-700 border-red-200';
            default: return 'bg-amber-100 text-amber-700 border-amber-200';
        }
    };

    return (
        <div className="p-6 space-y-6 max-w-[1600px] mx-auto">
            {/* Toolbar */}
            <div className="bg-white dark:bg-gray-800 p-4 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 flex flex-col md:flex-row gap-4 items-center justify-between">
                <div className="relative w-full md:w-96">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                        type="text"
                        placeholder="Buscar por código ou cliente..."
                        className="w-full pl-10 pr-4 py-2 bg-gray-50 dark:bg-gray-900 border-none rounded-xl text-sm focus:ring-2 focus:ring-blue-500 transition-all"
                    />
                </div>

                <div className="flex items-center gap-3 w-full md:w-auto">
                    <div className="flex bg-gray-50 dark:bg-gray-900 p-1 rounded-xl">
                        {['todos', 'pendente', 'em_rota', 'entregue'].map((s) => (
                            <button
                                key={s}
                                onClick={() => setFiltroStatus(s)}
                                className={`px-4 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider transition-all ${filtroStatus === s
                                    ? 'bg-white dark:bg-gray-800 shadow-sm text-blue-600'
                                    : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
                                    }`}
                            >
                                {s}
                            </button>
                        ))}
                    </div>
                    <button className="p-2 bg-gray-50 dark:bg-gray-900 rounded-xl hover:bg-gray-100 transition-colors">
                        <Filter className="w-5 h-5 text-gray-600" />
                    </button>
                </div>
            </div>

            {/* Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                {loading ? (
                    Array(6).fill(0).map((_, i) => (
                        <div key={i} className="h-64 bg-gray-100 dark:bg-gray-800 animate-pulse rounded-3xl" />
                    ))
                ) : entregas.map((entrega) => (
                    <div
                        key={entrega.id}
                        className="bg-white dark:bg-gray-800 rounded-3xl p-6 shadow-sm border border-gray-100 dark:border-gray-700 hover:shadow-xl hover:-translate-y-1 transition-all group"
                    >
                        <div className="flex justify-between items-start mb-6">
                            <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border ${getStatusStyle(entrega.status)}`}>
                                {entrega.status.replace('_', ' ')}
                            </span>
                            <button className="p-1.5 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors">
                                <MoreVertical className="w-5 h-5 text-gray-400" />
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-xl bg-blue-50 dark:bg-blue-900/20 flex items-center justify-center text-blue-600">
                                    <Hash className="w-5 h-5" />
                                </div>
                                <h3 className="font-bold text-gray-900 dark:text-white text-lg">
                                    {entrega.codigo_rastreamento}
                                </h3>
                            </div>

                            <div className="grid grid-cols-2 gap-4 pt-2">
                                <div className="space-y-1">
                                    <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider flex items-center">
                                        <User className="w-3 h-3 mr-1" /> Motorista
                                    </p>
                                    <p className="text-sm font-semibold text-gray-700 dark:text-gray-200 truncate">
                                        {entrega.motorista_nome || 'Não atribuído'}
                                    </p>
                                </div>
                                <div className="space-y-1">
                                    <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider flex items-center">
                                        <Calendar className="w-3 h-3 mr-1" /> Previsão
                                    </p>
                                    <p className="text-sm font-semibold text-gray-700 dark:text-gray-200">
                                        {new Date(entrega.data_prevista).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                    </p>
                                </div>
                            </div>

                            <div className="pt-4 border-t border-gray-100 dark:border-gray-700 flex items-center justify-between">
                                <div className="flex items-center text-xs text-gray-500">
                                    <MapPin className="w-3.5 h-3.5 mr-1 text-gray-400" />
                                    {entrega.endereco_bairro}
                                </div>
                                <button className="flex items-center gap-1.5 text-xs font-bold text-blue-600 hover:text-blue-700 transition-colors group-hover:translate-x-1 duration-300">
                                    DETALHES <ExternalLink className="w-3 h-3" />
                                </button>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {!loading && entregas.length === 0 && (
                <div className="py-24 text-center">
                    <div className="w-20 h-20 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
                        <Search className="w-10 h-10 text-gray-300" />
                    </div>
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white">Nenhuma entrega encontrada</h3>
                    <p className="text-gray-500">Tente mudar os filtros ou realizar uma nova busca.</p>
                </div>
            )}
        </div>
    );
};

export default DeliveryList;
