import React, { useState, useEffect } from 'react';
import {
    Users,
    Truck,
    Plus,
    Check,
    X,
    Star,
    Phone,
    CreditCard,
    ShieldCheck
} from 'lucide-react';
import { deliveryService, Motorista, Veiculo } from './deliveryService';
import toast from 'react-hot-toast';
import { motion } from 'framer-motion';

const DriverManagement: React.FC = () => {
    const [motoristas, setMotoristas] = useState<Motorista[]>([]);
    const [veiculos, setVeiculos] = useState<Veiculo[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [motRes, veiRes] = await Promise.all([
                deliveryService.getMotoristas(),
                deliveryService.getVeiculos()
            ]);
            if (motRes.success) setMotoristas(motRes.motoristas);
            if (veiRes.success) setVeiculos(veiRes.veiculos);
        } catch (error) {
            toast.error('Erro ao carregar frota');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-6 space-y-8 max-w-[1600px] mx-auto">
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
                {/* Motoristas Section */}
                <div className="space-y-6">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center text-white">
                                <Users className="w-6 h-6" />
                            </div>
                            <h2 className="text-xl font-bold dark:text-white">Motoristas Parceiros</h2>
                        </div>
                        <button className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-bold transition-all active:scale-95 shadow-lg shadow-indigo-500/20">
                            <Plus className="w-4 h-4" /> Novo Motorista
                        </button>
                    </div>

                    <div className="grid gap-4">
                        {loading ? (
                            Array(3).fill(0).map((_, i) => <div key={i} className="h-24 bg-gray-100 dark:bg-gray-800 animate-pulse rounded-2xl" />)
                        ) : motoristas.map((m) => (
                            <motion.div
                                key={m.id}
                                whileHover={{ scale: 1.01 }}
                                className="bg-white dark:bg-gray-800 p-5 rounded-3xl border border-gray-100 dark:border-gray-700 shadow-sm flex items-center justify-between"
                            >
                                <div className="flex items-center gap-4">
                                    <div className="w-14 h-14 rounded-2xl bg-gray-50 dark:bg-gray-900 flex items-center justify-center relative">
                                        <User className="w-8 h-8 text-gray-400" />
                                        {m.disponivel && (
                                            <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 border-2 border-white dark:border-gray-800 rounded-full" />
                                        )}
                                    </div>
                                    <div>
                                        <h4 className="font-bold text-gray-900 dark:text-white">{m.nome}</h4>
                                        <div className="flex items-center gap-3 mt-1">
                                            <span className="flex items-center text-xs text-amber-500 font-bold">
                                                <Star className="w-3 h-3 mr-1 fill-current" /> {m.avaliacao_media || '5.0'}
                                            </span>
                                            <span className="text-xs text-gray-400 flex items-center">
                                                <Truck className="w-3 h-3 mr-1" /> {m.total_entregas} entregas
                                            </span>
                                        </div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <button className="p-2 hover:bg-gray-50 dark:hover:bg-gray-900 rounded-xl text-gray-400 transition-colors">
                                        <Phone className="w-5 h-5" />
                                    </button>
                                    <button className="p-2 hover:bg-gray-50 dark:hover:bg-gray-900 rounded-xl text-gray-400 transition-colors">
                                        <CreditCard className="w-5 h-5" />
                                    </button>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                </div>

                {/* Veículos Section */}
                <div className="space-y-6">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-emerald-600 rounded-xl flex items-center justify-center text-white">
                                <Truck className="w-6 h-6" />
                            </div>
                            <h2 className="text-xl font-bold dark:text-white">Frota de Veículos</h2>
                        </div>
                        <button className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-sm font-bold transition-all active:scale-95 shadow-lg shadow-emerald-500/20">
                            <Plus className="w-4 h-4" /> Novo Veículo
                        </button>
                    </div>

                    <div className="grid gap-4">
                        {loading ? (
                            Array(3).fill(0).map((_, i) => <div key={i} className="h-24 bg-gray-100 dark:bg-gray-800 animate-pulse rounded-2xl" />)
                        ) : veiculos.map((v) => (
                            <div
                                key={v.id}
                                className="bg-white dark:bg-gray-800 p-5 rounded-3xl border border-gray-100 dark:border-gray-700 shadow-sm flex items-center justify-between group"
                            >
                                <div className="flex items-center gap-4">
                                    <div className="w-14 h-14 rounded-2xl bg-emerald-50 dark:bg-emerald-900/20 flex items-center justify-center text-emerald-600">
                                        <Truck className="w-8 h-8" />
                                    </div>
                                    <div>
                                        <div className="flex items-center gap-2">
                                            <h4 className="font-bold text-gray-900 dark:text-white uppercase">{v.placa}</h4>
                                            <span className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-900 rounded text-[10px] font-black text-gray-500">{v.tipo}</span>
                                        </div>
                                        <p className="text-sm text-gray-500 mt-1">{v.modelo}</p>
                                    </div>
                                </div>
                                <div className={`flex items-center gap-1 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest ${v.ativo ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
                                    }`}>
                                    {v.ativo ? <Check className="w-3 h-3 mr-1" /> : <X className="w-3 h-3 mr-1" />}
                                    {v.ativo ? 'Operante' : 'Manutenção'}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Banner Informativo */}
            <div className="bg-white dark:bg-gray-800 p-8 rounded-[2rem] border border-gray-100 dark:border-gray-700 flex flex-col md:flex-row items-center justify-between gap-8 mt-12 overflow-hidden relative">
                <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/5 rounded-full -mr-32 -mt-32 blur-3xl" />
                <div className="space-y-4 relative z-10">
                    <div className="flex items-center gap-2 text-indigo-600 font-black text-xs uppercase tracking-[0.2em]">
                        <ShieldCheck className="w-4 h-4" /> Segurança Logística
                    </div>
                    <h3 className="text-2xl font-bold dark:text-white">Conformidade Total</h3>
                    <p className="text-gray-500 max-w-xl">
                        Todos os seus motoristas passam por verificação automática de CNH.
                        O sistema alerta sobre vencimentos de licenciamento e revisões preventivas da frota.
                    </p>
                </div>
                <button className="px-8 py-4 bg-gray-900 dark:bg-white dark:text-gray-950 text-white font-bold rounded-2xl hover:bg-gray-800 transition-all relative z-10 shadow-xl active:scale-95">
                    Relatório de Conformidade
                </button>
            </div>
        </div>
    );
};

const User = ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" />
    </svg>
);

export default DriverManagement;
