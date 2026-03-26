import React from 'react';
import { MapPin, Truck, Navigation, Shield } from 'lucide-react';
import { motion } from 'framer-motion';

const LiveTracking: React.FC<{ entrega: any }> = ({ entrega }) => {
    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white dark:bg-gray-800 rounded-3xl p-6 shadow-2xl border border-gray-100 dark:border-gray-700 overflow-hidden relative group text-left"
        >
            <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/10 rounded-full -mr-16 -mt-16 blur-3xl group-hover:bg-blue-500/20 transition-all" />

            <div className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center text-white shadow-lg shadow-blue-500/20">
                        <Navigation className="w-5 h-5 animate-pulse" />
                    </div>
                    <div>
                        <h4 className="font-bold text-gray-900 dark:text-white">Rastreamento Live</h4>
                        <p className="text-[10px] text-blue-600 font-black uppercase tracking-widest">Sincronizado via Satélite</p>
                    </div>
                </div>
                <div className="flex items-center gap-2 px-3 py-1 bg-green-50 dark:bg-green-900/20 rounded-full">
                    <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-ping" />
                    <span className="text-[10px] font-bold text-green-600">ATIVO</span>
                </div>
            </div>

            {/* Simulação de Map/Timeline */}
            <div className="relative pl-8 space-y-8 before:absolute before:left-[11px] before:top-2 before:bottom-2 before:w-0.5 before:bg-gradient-to-b before:from-blue-600 before:via-blue-200 before:to-gray-100 dark:before:via-blue-900 dark:before:to-gray-800">
                <div className="relative">
                    <div className="absolute -left-[29px] top-0 w-6 h-6 rounded-full bg-blue-600 flex items-center justify-center border-4 border-white dark:border-gray-800 shadow-sm z-10">
                        <Truck className="w-3 h-3 text-white" />
                    </div>
                    <div>
                        <p className="text-xs font-black text-blue-600 uppercase">Saiu para Entrega</p>
                        <p className="text-sm font-bold text-gray-700 dark:text-gray-200">Motorista em deslocamento</p>
                        <p className="text-[10px] text-gray-400 mt-1">HÁ 12 MINUTOS • MANAUS, AM</p>
                    </div>
                </div>

                <div className="relative opacity-50">
                    <div className="absolute -left-[29px] top-0 w-6 h-6 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center border-4 border-white dark:border-gray-800 shadow-sm z-10">
                        <MapPin className="w-3 h-3 text-gray-400" />
                    </div>
                    <div>
                        <p className="text-xs font-black text-gray-400 uppercase">Destino Final</p>
                        <p className="text-sm font-bold text-gray-400">{entrega?.endereco_bairro || 'Endereço do Cliente'}</p>
                        <p className="text-[10px] text-gray-300 mt-1">PREVISÃO: 14:45</p>
                    </div>
                </div>
            </div>

            <div className="mt-8 pt-6 border-t border-gray-50 dark:border-gray-700 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Shield className="w-4 h-4 text-emerald-500" />
                    <span className="text-[10px] font-bold text-gray-400 uppercase">Entrega Segura</span>
                </div>
                <button className="text-xs font-bold text-blue-600 hover:underline">ABRIR MAPA FULL</button>
            </div>
        </motion.div>
    );
};

export default LiveTracking;
