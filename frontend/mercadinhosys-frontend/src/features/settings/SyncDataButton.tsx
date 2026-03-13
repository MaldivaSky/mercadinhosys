import React, { useState } from 'react';
import { RefreshCw, Cloud, CheckCircle2, AlertCircle } from 'lucide-react';
import { apiClient } from '../../api/apiClient';
import { showToast } from '../../components/elements/Toast';

export const SyncDataButton: React.FC = () => {
    const [syncing, setSyncing] = useState(false);
    const [lastSync, setLastSync] = useState<string | null>(null);

    const handleSync = async () => {
        setSyncing(true);
        try {
            const res = await apiClient.post('/sync_hybrid/upload');
            if (res.data.success) {
                showToast.success('Dados Master sincronizados com Vercel!');
                setLastSync(new Date().toLocaleTimeString());
            } else {
                showToast.error('Falha na sincronização: ' + res.data.error);
            }
        } catch (err: any) {
            showToast.error('Erro de conexão com o servidor de sincronização.');
        } finally {
            setSyncing(false);
        }
    };

    return (
        <div className="p-6 bg-blue-50 dark:bg-blue-900/10 rounded-2xl border border-blue-100 dark:border-blue-800/30">
            <div className="flex items-start justify-between">
                <div className="space-y-1">
                    <h3 className="text-lg font-bold text-blue-900 dark:text-blue-100 flex items-center gap-2">
                        <RefreshCw className={`w-5 h-5 ${syncing ? 'animate-spin' : ''}`} />
                        Sincronização Híbrida Magnitude
                    </h3>
                    <p className="text-sm text-blue-700/70 dark:text-blue-300/60 max-w-md">
                        Envia todos os dados do Gêmeo Digital Master (Local/Docker) para a infraestrutura Vercel/Cloud.
                        Recomendado após alterações massivas na simulação.
                    </p>
                </div>
                {lastSync && (
                    <span className="text-xs font-medium text-green-600 bg-green-100 dark:bg-green-900/30 dark:text-green-400 px-2.5 py-1 rounded-full flex items-center gap-1">
                        <CheckCircle2 size={12} />
                        Último push: {lastSync}
                    </span>
                )}
            </div>

            <div className="mt-6">
                <button
                    onClick={handleSync}
                    disabled={syncing}
                    className="group relative inline-flex items-center justify-center gap-3 px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold shadow-lg shadow-blue-500/20 transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-70 disabled:hover:scale-100"
                >
                    {syncing ? (
                        <RefreshCw className="w-5 h-5 animate-spin" />
                    ) : (
                        <div className="w-5 h-5 flex items-center justify-center">
                            <div className="absolute w-5 h-5 bg-white/20 rounded-full animate-ping group-hover:block hidden"></div>
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                            </svg>
                        </div>
                    )}
                    {syncing ? 'SINCRONIZANDO MAGNITUDE...' : 'SINCRONIZAR COM VERCEL'}
                </button>
            </div>

            <div className="mt-4 flex items-center gap-2 text-xs text-blue-600/50 dark:text-blue-400/40">
                <AlertCircle size={14} />
                <span>Isolamento Tenant garantido via Auditoria Forense</span>
            </div>
        </div>
    );
};
