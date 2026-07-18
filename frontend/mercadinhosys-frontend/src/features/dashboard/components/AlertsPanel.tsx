import React, { useEffect, useState } from 'react';
import { AlertTriangle, Clock, PackageX } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

export interface AlertaItem {
    id: string | number;
    tipo: 'ruptura' | 'vencimento' | 'vencido';
    produto_nome: string;
    quantidade?: number;
    estoque_minimo?: number;
    data_validade?: string;
}

const AlertsPanel: React.FC = () => {
    const navigate = useNavigate();
    const [alertas, setAlertas] = useState<AlertaItem[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchAlertas = async () => {
            setLoading(true);
            try {
                const { apiClient } = await import('../../../api/apiClient');
                const res = await apiClient.get('/dashboard/alertas');
                setAlertas(res.data.alertas || []);
            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
            }
        };
        fetchAlertas();
    }, []);

    if (loading) {
        return (
            <div className="p-6 bg-white dark:bg-slate-900 rounded-3xl border border-slate-100 dark:border-slate-800 animate-pulse">
                <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-1/3 mb-4"></div>
                <div className="h-10 bg-slate-100 dark:bg-slate-800 rounded mb-2"></div>
                <div className="h-10 bg-slate-100 dark:bg-slate-800 rounded"></div>
            </div>
        );
    }

    if (alertas.length === 0) return null;

    return (
        <div className="p-6 bg-white dark:bg-slate-900 rounded-3xl border border-orange-200 dark:border-orange-900 shadow-sm relative overflow-hidden">
            <div className="absolute top-0 right-0 p-4 opacity-10">
                <AlertTriangle className="w-24 h-24 text-orange-500" />
            </div>
            
            <div className="flex items-center gap-3 mb-6 relative z-10">
                <div className="p-3 bg-orange-100 dark:bg-orange-900/30 text-orange-600 rounded-xl">
                    <AlertTriangle className="w-5 h-5" />
                </div>
                <div>
                    <h3 className="text-lg font-black text-slate-800 dark:text-white">Alertas Operacionais</h3>
                    <p className="text-xs text-slate-500 dark:text-slate-400">Ruptura de estoque e vencimentos</p>
                </div>
            </div>

            <div className="space-y-3 relative z-10">
                <AnimatePresence>
                    {alertas.map(alerta => (
                        <motion.div
                            key={alerta.id}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className={`p-4 rounded-xl border flex items-center gap-4 ${
                                alerta.tipo === 'vencido' 
                                    ? 'bg-red-50 dark:bg-red-900/10 border-red-200 dark:border-red-900/30'
                                    : alerta.tipo === 'ruptura'
                                        ? 'bg-orange-50 dark:bg-orange-900/10 border-orange-200 dark:border-orange-900/30'
                                        : 'bg-yellow-50 dark:bg-yellow-900/10 border-yellow-200 dark:border-yellow-900/30'
                            }`}
                        >
                            <div className={`p-2 rounded-lg ${
                                alerta.tipo === 'vencido' ? 'bg-red-200 text-red-700' :
                                alerta.tipo === 'ruptura' ? 'bg-orange-200 text-orange-700' :
                                'bg-yellow-200 text-yellow-700'
                            }`}>
                                {alerta.tipo === 'ruptura' ? <PackageX className="w-5 h-5" /> : <Clock className="w-5 h-5" />}
                            </div>
                            <div className="flex-1">
                                <p className="text-sm font-bold text-slate-800 dark:text-slate-200">{alerta.produto_nome}</p>
                                <p className="text-xs text-slate-600 dark:text-slate-400 font-medium">
                                    {alerta.tipo === 'ruptura' 
                                        ? `Estoque atual: ${alerta.quantidade} (Mínimo: ${alerta.estoque_minimo})`
                                        : alerta.tipo === 'vencido'
                                            ? `Venceu em: ${new Date(alerta.data_validade!).toLocaleDateString()}`
                                            : `Vence em: ${new Date(alerta.data_validade!).toLocaleDateString()}`
                                    }
                                </p>
                            </div>
                            <button 
                                onClick={() => {
                                    const produtoId = String(alerta.id).split('_')[1];
                                    if (produtoId) {
                                        navigate(`/products/${produtoId}`);
                                    } else {
                                        navigate('/products');
                                    }
                                }}
                                className="px-3 py-1 bg-black/5 dark:bg-black/20 hover:bg-black/10 dark:hover:bg-black/40 text-gray-700 dark:text-slate-200 rounded text-xs font-bold uppercase transition-all">
                                Resolver
                            </button>
                        </motion.div>
                    ))}
                </AnimatePresence>
            </div>
        </div>
    );
};

export default AlertsPanel;
