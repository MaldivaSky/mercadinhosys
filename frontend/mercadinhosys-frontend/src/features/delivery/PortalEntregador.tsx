import React, { useEffect, useState, useCallback, useRef } from 'react';
import { authService } from '../auth/authService';
import { deliveryService, Entrega } from './deliveryService';
import { apiClient } from '../../api/apiClient';
import {
    Navigation, MapPin, Phone, CheckCircle2, Clock,
    PackageCheck, Truck, AlertCircle, RefreshCw,
    Smartphone, Package, Radio, WifiOff
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';
import DetalheEntregaModal from './DetalheEntregaModal';


// ─── Detecta mobile ───────────────────────────────────────────────────────────
const isMobile = () =>
    window.innerWidth < 900 || /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent);

// ─── Intervalo de envio GPS (ms) ─────────────────────────────────────────────
const GPS_INTERVAL_MS = 15_000; // 15 segundos

// ─── Hook: GPS Tracker ────────────────────────────────────────────────────────
// Quando ativo, captura a posição do celular a cada 15s e envia para o backend.
// Para de enviar automaticamente quando `entregaAtiva` for null.
function useGpsTracker(entregaAtiva: Entrega | null) {
    const [gpsStatus, setGpsStatus] = useState<'idle' | 'tracking' | 'denied' | 'unsupported'>('idle');
    const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const watchRef = useRef<number | null>(null);
    const lastPosRef = useRef<GeolocationCoordinates | null>(null);

    const enviarPing = useCallback(async (coords: GeolocationCoordinates, entrega: Entrega) => {
        try {
            await apiClient.post('/logistica/eventos', {
                venda_id: entrega.venda_id,
                status: 'em_rota',
                latitude: coords.latitude,
                longitude: coords.longitude,
            });
        } catch {
            // Falha silenciosa no ping — não interrompe o motorista
        }
    }, []);

    useEffect(() => {
        // Para tudo se não há entrega ativa em rota
        if (!entregaAtiva || entregaAtiva.status !== 'em_rota') {
            if (intervalRef.current) clearInterval(intervalRef.current);
            if (watchRef.current !== null) navigator.geolocation?.clearWatch(watchRef.current);
            setGpsStatus('idle');
            return;
        }

        if (!navigator.geolocation) {
            setGpsStatus('unsupported');
            return;
        }

        // Pede permissão e começa a rastrear
        watchRef.current = navigator.geolocation.watchPosition(
            (pos) => {
                lastPosRef.current = pos.coords;
                setGpsStatus('tracking');
            },
            (err) => {
                if (err.code === err.PERMISSION_DENIED) setGpsStatus('denied');
            },
            { enableHighAccuracy: true, maximumAge: 10_000 }
        );

        // Envia ping a cada 15s usando a última posição conhecida
        intervalRef.current = setInterval(() => {
            if (lastPosRef.current) {
                enviarPing(lastPosRef.current, entregaAtiva);
            }
        }, GPS_INTERVAL_MS);

        return () => {
            if (intervalRef.current) clearInterval(intervalRef.current);
            if (watchRef.current !== null) navigator.geolocation?.clearWatch(watchRef.current);
        };
    }, [entregaAtiva, enviarPing]);

    return gpsStatus;
}

// ─── Configuração visual por status ──────────────────────────────────────────
const STATUS_CFG: Record<string, { label: string; color: string; bg: string; icon: React.ElementType }> = {
    pendente:   { label: 'Aguardando',  color: 'text-amber-700',  bg: 'bg-amber-100',   icon: Clock },
    em_preparo: { label: 'Em Preparo',  color: 'text-blue-700',   bg: 'bg-blue-100',    icon: PackageCheck },
    em_rota:    { label: 'Em Rota',     color: 'text-indigo-700', bg: 'bg-indigo-100',  icon: Truck },
    entregue:   { label: 'Entregue',    color: 'text-green-700',  bg: 'bg-green-100',   icon: CheckCircle2 },
    cancelada:  { label: 'Cancelada',   color: 'text-red-700',    bg: 'bg-red-100',     icon: AlertCircle },
};

// ─── Card de cada entrega ─────────────────────────────────────────────────────
const CardEntrega: React.FC<{ entrega: Entrega; onRefresh: () => void; onClickDetalhes: () => void; assumindo?: boolean; meuMotoristaId?: number | null }> = ({ entrega, onRefresh, onClickDetalhes, assumindo = false, meuMotoristaId = null }) => {
    const [loading, setLoading] = useState(false);
    
    let next = '';
    let labelAcao = '';
    if (assumindo) {
        labelAcao = 'Assumir e Iniciar';
        next = 'em_rota';
    } else if (entrega.status === 'em_preparo' || entrega.status === 'pendente') {
        labelAcao = 'Iniciar Entrega';
        next = 'em_rota';
    } else if (entrega.status === 'em_rota') {
        labelAcao = 'Confirmar Entrega';
        next = 'entregue';
    }

    const cfg = STATUS_CFG[entrega.status] ?? STATUS_CFG['pendente'];
    const Icon = cfg.icon;

    const handleAcao = async (e: React.MouseEvent) => {
        e.stopPropagation();
        if (!next) return;
        
        if (assumindo && !meuMotoristaId) {
            toast.error("Motorista não identificado. O admin precisa cadastrar você com o mesmo nome exato em 'Frota & Motoristas'.");
            return;
        }

        setLoading(true);
        try {
            const payload: any = {};
            if (next === 'em_rota') {
                payload.motorista_id = meuMotoristaId || (entrega as any).motorista_id;
            }
            
            await deliveryService.atualizarStatus(entrega.id, next, payload);
            toast.success(
                next === 'em_rota'
                    ? '🚀 Rota iniciada! GPS ativado automaticamente.'
                    : '✅ Entrega confirmada! GPS desativado.'
            );
            onRefresh();
        } catch {
            toast.error('Erro ao atualizar status');
        } finally {
            setLoading(false);
        }
    };

    const mapsUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(entrega.endereco_completo)}`;
    const telefone = (entrega as any).cliente_telefone?.replace(/\D/g, '');
    const wppUrl = telefone
        ? `https://wa.me/55${telefone}?text=${encodeURIComponent(
            `Olá! Sou o entregador. Estou a caminho com seu pedido #${entrega.codigo_rastreamento} 🛵`
          )}`
        : null;

    return (
        <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm overflow-hidden"
        >
            <div 
                className="flex items-center justify-between px-4 py-3 border-b border-gray-50 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                onClick={onClickDetalhes}
            >
                <div>
                    <p className="text-[10px] font-mono text-gray-400">#{entrega.codigo_rastreamento}</p>
                    <p className="font-bold text-gray-900 dark:text-white text-sm">{entrega.cliente_nome || 'Cliente'}</p>
                </div>
                <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold ${cfg.bg} ${cfg.color}`}>
                    <Icon className="w-3 h-3" />
                    {cfg.label}
                </span>
            </div>

            <div className="flex items-start gap-3 px-4 py-3">
                <MapPin className="w-4 h-4 text-blue-500 mt-0.5 shrink-0" />
                <div>
                    <p className="text-sm font-medium text-gray-700 dark:text-gray-200 leading-snug">{entrega.endereco_completo}</p>
                    <p className="text-xs text-gray-400 mt-0.5">{entrega.endereco_bairro}</p>
                </div>
            </div>

            {entrega.status !== 'entregue' && entrega.status !== 'cancelada' && (
                <div className="flex gap-2 p-3 bg-gray-50 dark:bg-gray-900/30 flex-wrap">
                    <button
                        onClick={onClickDetalhes}
                        className="flex-1 min-w-[30%] flex items-center justify-center gap-1.5 py-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-xl text-sm font-semibold text-gray-700 dark:text-gray-200 hover:border-blue-400 transition-all"
                    >
                        <Package className="w-4 h-4 text-blue-500" />
                        Pedido
                    </button>
                    
                    <a
                        href={mapsUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="flex-1 min-w-[30%] flex items-center justify-center gap-1.5 py-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-xl text-sm font-semibold text-gray-700 dark:text-gray-200 hover:border-blue-400 transition-all"
                    >
                        <Navigation className="w-4 h-4 text-blue-500" />
                        Navegar
                    </a>

                    {wppUrl && (
                        <a
                            href={wppUrl}
                            target="_blank"
                            rel="noreferrer"
                            className="flex-shrink-0 flex items-center justify-center px-4 py-2.5 bg-green-500 hover:bg-green-600 rounded-xl text-white transition-all"
                        >
                            <Phone className="w-4 h-4" />
                        </a>
                    )}

                    {labelAcao && (
                        <button
                            onClick={handleAcao}
                            disabled={loading}
                            className={`w-full flex items-center justify-center gap-1.5 py-2.5 rounded-xl text-sm font-bold text-white transition-all disabled:opacity-60 mt-1 ${
                                next === 'em_rota'
                                    ? 'bg-indigo-600 hover:bg-indigo-700'
                                    : 'bg-green-600 hover:bg-green-700'
                            }`}
                        >
                            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : labelAcao}
                        </button>
                    )}
                </div>
            )}
        </motion.div>
    );
};

// ─── Badge de status GPS ──────────────────────────────────────────────────────
const GpsBadge: React.FC<{ status: string }> = ({ status }) => {
    if (status === 'idle') return null;
    if (status === 'unsupported') return null;

    if (status === 'denied') return (
        <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl px-3 py-2 text-xs font-medium">
            <WifiOff className="w-3.5 h-3.5" />
            GPS negado — Gerente não vê sua posição
        </div>
    );

    return (
        <div className="flex items-center gap-2 bg-green-500/10 border border-green-500/20 text-green-400 rounded-xl px-3 py-2 text-xs font-medium">
            <Radio className="w-3.5 h-3.5 animate-pulse" />
            GPS ativo — Transmitindo posição a cada 15s
        </div>
    );
};

// ─── Painel Mobile (operação real em campo) ───────────────────────────────────
const PainelMobile: React.FC<{ user: any }> = ({ user }) => {
    const [entregas, setEntregas] = useState<Entrega[]>([]);
    const [loading, setLoading] = useState(true);
    const [tab, setTab] = useState<'disponiveis' | 'ativas' | 'concluidas'>('ativas');
    const [detalheModalId, setDetalheModalId] = useState<number | null>(null);
    const [meuMotoristaId, setMeuMotoristaId] = useState<number | null>(null);

    useEffect(() => {
        if (user?.nome) {
            deliveryService.getMotoristas(true).then(res => {
                const mots = res.motoristas || res.data || [];
                const match = mots.find((m: any) => m.nome.trim().toLowerCase() === user.nome.trim().toLowerCase());
                if (match) setMeuMotoristaId(match.id);
            }).catch(() => {});
        }
    }, [user?.nome]);

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const res = await deliveryService.getEntregas('todos');
            if (res.success) setEntregas(res.entregas ?? []);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { load(); }, [load]);

    const entregaEmRota = entregas.find(e => e.status === 'em_rota' && (e as any).motorista_id === meuMotoristaId) ?? null;
    const gpsStatus = useGpsTracker(entregaEmRota);

    const disponiveis = entregas.filter(e => (e.status === 'pendente' || e.status === 'em_preparo') && !(e as any).motorista_id);
    const ativas = entregas.filter(e => !['entregue', 'cancelada', 'pendente', 'em_preparo'].includes(e.status) && (e as any).motorista_id === meuMotoristaId);
    const concluidas = entregas.filter(e => e.status === 'entregue' && (e as any).motorista_id === meuMotoristaId);
    
    const lista = tab === 'ativas' ? ativas : tab === 'concluidas' ? concluidas : disponiveis;

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex flex-col">
            <div className="bg-gradient-to-br from-blue-700 to-indigo-800 px-5 pt-10 pb-5 text-white">
                <div className="flex items-center justify-between mb-4">
                    <div>
                        <p className="text-blue-200 text-[10px] font-bold uppercase tracking-widest">Painel do Entregador</p>
                        <h1 className="text-xl font-black mt-0.5">Olá, {user?.nome?.split(' ')[0] || 'Motorista'}!</h1>
                    </div>
                    <button
                        onClick={load}
                        disabled={loading}
                        className="w-9 h-9 rounded-full bg-white/10 flex items-center justify-center hover:bg-white/20 transition-all"
                    >
                        <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                    </button>
                </div>

                {entregaEmRota && (
                    <div className="mb-3">
                        <GpsBadge status={gpsStatus} />
                    </div>
                )}

                <div className="grid grid-cols-2 gap-3">
                    <div className="bg-white/10 rounded-2xl p-3 text-center">
                        <p className="text-2xl font-black">{ativas.length}</p>
                        <p className="text-blue-200 text-xs">Em Aberto</p>
                    </div>
                    <div className="bg-white/10 rounded-2xl p-3 text-center">
                        <p className="text-2xl font-black text-green-300">{concluidas.length}</p>
                        <p className="text-blue-200 text-xs">Concluídas</p>
                    </div>
                </div>
            </div>

            <div className="bg-blue-800 p-2 sticky top-0 z-10">
                <div className="grid grid-cols-3 gap-1 bg-blue-900/50 p-1 rounded-xl">
                    <button
                        onClick={() => setTab('disponiveis')}
                        className={`px-2 py-2 rounded-lg text-[10px] font-bold transition-all relative ${tab === 'disponiveis' ? 'bg-white text-blue-700 shadow-sm' : 'text-blue-200 hover:text-white'}`}
                    >
                        Disponíveis
                        {disponiveis.length > 0 && (
                            <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full text-[9px] flex items-center justify-center text-white border border-blue-700">
                                {disponiveis.length}
                            </span>
                        )}
                    </button>
                    <button
                        onClick={() => setTab('ativas')}
                        className={`px-2 py-2 rounded-lg text-[10px] font-bold transition-all ${tab === 'ativas' ? 'bg-white text-blue-700 shadow-sm' : 'text-blue-200 hover:text-white'}`}
                    >
                        Minha Rota
                    </button>
                    <button
                        onClick={() => setTab('concluidas')}
                        className={`px-2 py-2 rounded-lg text-[10px] font-bold transition-all ${tab === 'concluidas' ? 'bg-white text-blue-700 shadow-sm' : 'text-blue-200 hover:text-white'}`}
                    >
                        Concluídas
                    </button>
                </div>
            </div>

            <div className="flex-1 p-4 space-y-3 overflow-y-auto pb-8">
                <AnimatePresence mode='wait'>
                    {loading ? (
                        [1, 2].map(i => (
                            <div key={i} className="h-36 rounded-2xl bg-gray-200 dark:bg-gray-800 animate-pulse" />
                        ))
                    ) : lista.length > 0 ? (
                        lista.map(e => <CardEntrega key={e.id} entrega={e} onRefresh={load} onClickDetalhes={() => setDetalheModalId(e.id)} assumindo={tab === 'disponiveis'} meuMotoristaId={meuMotoristaId} />)
                    ) : (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="flex flex-col items-center justify-center py-20 text-gray-400"
                        >
                            <Package className="w-12 h-12 mb-3 opacity-30" />
                            <p className="font-medium text-center text-sm">
                                {tab === 'ativas'
                                    ? 'Nenhuma entrega atribuída no momento'
                                    : 'Nenhuma entrega concluída ainda hoje'}
                            </p>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
            
            <DetalheEntregaModal entregaId={detalheModalId} onClose={() => setDetalheModalId(null)} />
        </div>
    );
};

// ─── Aviso Desktop ────────────────────────────────────────────────────────────
const AvisoDesktop: React.FC<{ user: any }> = ({ user }) => (
    <div className="flex flex-col items-center justify-center py-20 px-6 text-center max-w-lg mx-auto">
        <div className="w-20 h-20 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center mb-6">
            <Smartphone className="w-10 h-10 text-blue-600" />
        </div>
        <h1 className="text-2xl font-black text-gray-900 dark:text-white mb-3">
            Olá, {user?.nome?.split(' ')[0] || 'Motorista'}!
        </h1>
        <p className="text-gray-500 dark:text-gray-400 mb-6 leading-relaxed">
            O painel de entregas é feito para ser usado <strong>no celular</strong>, durante a rota.
            <br /><br />
            Abra o navegador no seu celular, acesse o endereço abaixo e logue com suas credenciais.
            O sistema detecta que é mobile e abre seus pedidos direto.
        </p>
        <div className="bg-gray-50 dark:bg-gray-800 rounded-2xl p-4 w-full border border-gray-200 dark:border-gray-700 mb-4">
            <p className="text-xs text-gray-400 mb-1">Endereço do sistema</p>
            <p className="font-mono text-sm font-bold text-blue-600 break-all">{window.location.origin}</p>
        </div>
        <div className="flex items-start gap-3 bg-blue-50 dark:bg-blue-900/20 rounded-2xl p-4 text-left w-full">
            <Radio className="w-4 h-4 text-blue-500 mt-0.5 shrink-0" />
            <p className="text-xs text-blue-700 dark:text-blue-300">
                Quando você iniciar uma entrega pelo celular, o GPS do aparelho é ativado automaticamente
                e transmite sua posição ao gestor a cada 15 segundos em tempo real.
            </p>
        </div>
    </div>
);

// ─── Componente principal ─────────────────────────────────────────────────────
const PortalEntregador: React.FC = () => {
    const user = authService.getCurrentUser();
    return isMobile() ? <PainelMobile user={user} /> : <AvisoDesktop user={user} />;
};

export default PortalEntregador;
