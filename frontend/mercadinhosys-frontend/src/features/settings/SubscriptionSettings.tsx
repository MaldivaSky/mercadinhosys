import React, { useEffect, useState } from 'react';
import { CreditCard, Calendar, CheckCircle2, ShieldCheck, Zap, ArrowRight, ExternalLink, RefreshCcw, Star } from 'lucide-react';
import settingsService, { SubscriptionStatus } from './settingsService';
import { showToast } from '../../utils/toast';

const SubscriptionSettings: React.FC = () => {
    const [status, setStatus] = useState<SubscriptionStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [processing, setProcessing] = useState(false);

    const loadStatus = async (silent = false) => {
        try {
            if (!silent) setLoading(true);
            const data = await settingsService.getSubscriptionStatus();
            setStatus(data);
        } catch (error) {
            console.error("Erro ao carregar assinatura:", error);
            if (!silent) showToast.error("Falha ao recuperar dados da assinatura.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadStatus();
    }, []);

    const formatDate = (dateString: string | null) => {
        if (!dateString) return 'Vigência Vitalícia';
        return new Date(dateString).toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: 'long',
            year: 'numeric'
        });
    };

    const handleAction = async (planName: string) => {
        try {
            setProcessing(true);
            const response = await settingsService.createCheckoutSession(planName);
            if (response.checkout_url) {
                window.location.href = response.checkout_url;
            }
        } catch (error) {
            showToast.error("Erro ao iniciar processamento de pagamento.");
        } finally {
            setProcessing(false);
        }
    };

    const handlePortal = async () => {
        try {
            setProcessing(true);
            const response = await settingsService.openPortal();
            if (response.portal_url) {
                window.location.href = response.portal_url;
            }
        } catch (error) {
            showToast.error("Erro ao acessar portal de faturamento.");
        } finally {
            setProcessing(false);
        }
    };

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center py-24 space-y-4">
                <div className="w-10 h-10 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
                <p className="text-sm font-medium text-gray-400">Verificando licença...</p>
            </div>
        );
    }

    if (!status) {
        return (
            <div className="max-w-xl mx-auto mt-12 p-10 bg-white dark:bg-gray-900 rounded-3xl border border-gray-100 dark:border-gray-800 shadow-xl text-center">
                <div className="w-16 h-16 bg-red-50 dark:bg-red-900/20 rounded-2xl flex items-center justify-center mx-auto mb-6">
                    <ShieldCheck className="w-8 h-8 text-red-500" />
                </div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Erro de Identificação</h2>
                <p className="text-gray-500 dark:text-gray-400 mb-8">Não conseguimos validar os dados da sua conta no momento. Isso pode ser uma falha de sincronização.</p>
                <button onClick={() => loadStatus()} className="inline-flex items-center gap-2 px-6 py-3 bg-gray-900 dark:bg-white dark:text-gray-900 text-white rounded-xl font-bold hover:opacity-90 transition-all">
                    <RefreshCcw className="w-4 h-4" /> Tentar Sincronizar
                </button>
            </div>
        );
    }

    const isActive = status.is_active;
    const isExperimental = status.status === 'experimental';

    return (
        <div className="max-w-6xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            {/* MAIN STATUS CARD */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* LEFT: PLAN INFO */}
                <div className="lg:col-span-2 bg-white dark:bg-gray-900 rounded-[2.5rem] p-10 border border-gray-100 dark:border-gray-800 shadow-sm relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-10 opacity-5 group-hover:opacity-10 transition-opacity">
                        <Star className="w-32 h-32 text-primary" />
                    </div>

                    <div className="relative z-10">
                        <div className="flex items-center gap-3 mb-8">
                            <span className={`px-4 py-1 rounded-full text-[10px] font-black uppercase tracking-[0.2em] border ${isActive ? 'bg-green-50 text-green-600 border-green-200 dark:bg-green-900/20 dark:border-green-800' : 'bg-red-50 text-red-600 border-red-200'}`}>
                                {isActive ? 'Assinatura Ativa' : 'Assinatura Expirada'}
                            </span>
                            {isExperimental && (
                                <span className="px-4 py-1 rounded-full text-[10px] font-black uppercase tracking-[0.2em] bg-blue-50 text-blue-600 border border-blue-200 dark:bg-blue-900/20 dark:border-blue-800">
                                    Trial
                                </span>
                            )}
                        </div>

                        <h1 className="text-5xl font-black text-gray-900 dark:text-white mb-6">
                            Mercadinho<span className="text-primary italic">Sys</span> {status.plano}
                        </h1>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-8 mb-10">
                            <div className="space-y-1">
                                <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Renovação / Validade</p>
                                <div className="flex items-center gap-2 text-gray-700 dark:text-gray-300">
                                    <Calendar className="w-5 h-5 text-gray-400" />
                                    <span className="text-lg font-bold">{formatDate(status.vencimento)}</span>
                                </div>
                            </div>
                            <div className="space-y-1">
                                <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Método de Cobrança</p>
                                <div className="flex items-center gap-2 text-gray-700 dark:text-gray-300">
                                    <CreditCard className="w-5 h-5 text-gray-400" />
                                    <span className="text-lg font-bold">Stripe Gateway</span>
                                </div>
                            </div>
                        </div>

                        <div className="flex flex-wrap gap-4">
                            {!isExperimental && isActive && (
                                <button
                                    onClick={handlePortal}
                                    disabled={processing}
                                    className="px-8 py-4 bg-gray-900 dark:bg-white text-white dark:text-gray-900 rounded-2xl font-black text-sm hover:opacity-90 transition-all flex items-center gap-2 disabled:opacity-50"
                                >
                                    Gerenciar Faturamento <ExternalLink className="w-4 h-4" />
                                </button>
                            )}
                            {(!isActive || isExperimental) && (
                                <button
                                    onClick={() => handleAction('Premium')}
                                    disabled={processing}
                                    className="px-10 py-4 bg-primary text-white rounded-2xl font-black text-sm shadow-xl shadow-primary/20 hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center gap-2 disabled:opacity-50"
                                >
                                    Fazer Upgrade Premium <Zap className="w-4 h-4 fill-current" />
                                </button>
                            )}
                        </div>
                    </div>
                </div>

                {/* RIGHT: QUICK FEATURES */}
                <div className="bg-gray-50 dark:bg-gray-800/30 rounded-[2.5rem] p-10 flex flex-col justify-between border border-gray-100 dark:border-gray-800">
                    <div>
                        <h3 className="text-xl font-black text-gray-900 dark:text-white mb-6">Recursos do Plano</h3>
                        <ul className="space-y-5">
                            {[
                                'Gestão de Estoque Inteligente',
                                'Emissão de NF-e e NFC-e',
                                'Relatórios Financeiros Avançados',
                                'Suporte Técnico Prioritário',
                                'Backup Diário Automático'
                            ].map(item => (
                                <li key={item} className="flex items-start gap-3 text-sm font-medium text-gray-600 dark:text-gray-400">
                                    <CheckCircle2 className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                                    {item}
                                </li>
                            ))}
                        </ul>
                    </div>

                    <div className="pt-8 border-t border-gray-200 dark:border-gray-700 mt-8">
                        <div className="flex items-center gap-3 text-xs font-bold text-gray-400 uppercase tracking-widest leading-relaxed">
                            <ShieldCheck className="w-4 h-4" />
                            Ambiente de Pagamento Certificado PCI-DSS
                        </div>
                    </div>
                </div>
            </div>

            {/* UPGRADE SECTION - PRICING TIERS */}
            <div className="pt-12">
                <div className="text-center mb-16">
                    <h2 className="text-4xl font-black text-gray-900 dark:text-white mb-4">Escolha a escala do seu sucesso</h2>
                    <p className="text-gray-500 dark:text-gray-400 max-w-2xl mx-auto font-medium">Planos desenhados para micro e pequenos empreendedores que buscam profissionalismo e eficiência.</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-5xl mx-auto">
                    {/* PLAN 1: PRO */}
                    <div className="bg-white dark:bg-gray-900 p-12 rounded-[3rem] border border-gray-100 dark:border-gray-800 hover:shadow-2xl transition-all duration-500 group">
                        <div className="mb-10">
                            <h3 className="text-2xl font-black text-gray-900 dark:text-white mb-2 italic">Essential</h3>
                            <p className="text-sm text-gray-400 font-bold uppercase tracking-widest">Para quem está começando</p>
                        </div>
                        <div className="mb-10">
                            <div className="flex items-baseline gap-1">
                                <span className="text-6xl font-black text-gray-900 dark:text-white leading-none tracking-tighter">R$ 97</span>
                                <span className="text-gray-400 font-bold mb-1">/mês</span>
                            </div>
                        </div>
                        <button
                            onClick={() => handleAction('Pro')}
                            disabled={processing}
                            className="w-full py-5 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white rounded-2xl font-black text-sm hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors mb-10 disabled:opacity-50"
                        >
                            Assinar Essential
                        </button>
                        <div className="space-y-4">
                            {['Até 3 usuários', 'Frente de Caixa (PDV)', 'Gestão Básica', 'Suporte via Ticket'].map(f => (
                                <div key={f} className="flex items-center gap-3 text-sm font-semibold text-gray-500 dark:text-gray-400">
                                    <div className="w-1.5 h-1.5 rounded-full bg-gray-300"></div> {f}
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* PLAN 2: PREMIUM */}
                    <div className="bg-gray-900 dark:bg-white p-12 rounded-[3rem] shadow-2xl shadow-primary/20 relative scale-105 border-4 border-primary/20">
                        <div className="absolute top-0 right-12 -translate-y-1/2 bg-primary text-white text-[10px] font-black uppercase tracking-[0.2em] px-6 py-2 rounded-full">Destaque</div>
                        <div className="mb-10">
                            <h3 className="text-2xl font-black text-white dark:text-gray-900 mb-2 italic">Premium Elite</h3>
                            <p className="text-sm text-gray-300 dark:text-gray-500 font-bold uppercase tracking-widest">Potência Máxima</p>
                        </div>
                        <div className="mb-10">
                            <div className="flex items-baseline gap-1">
                                <span className="text-6xl font-black text-white dark:text-gray-900 leading-none tracking-tighter">R$ 197</span>
                                <span className="text-gray-400 font-bold mb-1">/mês</span>
                            </div>
                        </div>
                        <button
                            onClick={() => handleAction('Premium')}
                            disabled={processing}
                            className="w-full py-5 bg-primary text-white rounded-2xl font-black text-sm hover:brightness-110 transition-all flex items-center justify-center gap-3 mb-10 shadow-lg shadow-primary/40 disabled:opacity-50"
                        >
                            Assinar Premium <ArrowRight className="w-4 h-4" />
                        </button>
                        <div className="space-y-4">
                            {['Usuários Ilimitados', 'Todas as NF-e e NFC-e', 'Suporte Prioritário VIP', 'Relatórios Customizados', 'Treinamento Exclusivo'].map(f => (
                                <div key={f} className="flex items-center gap-3 text-sm font-bold text-gray-100 dark:text-gray-700">
                                    <CheckCircle2 className="w-5 h-5 text-primary" /> {f}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* FOOTER NOTE */}
            <div className="mt-20 flex flex-col items-center justify-center text-center space-y-4 pb-10">
                <div className="flex items-center gap-6 opacity-30 grayscale hover:grayscale-0 transition-all cursor-default">
                    <img src="https://stripe.com/img/v3/home/social-card.png" className="h-6 w-auto hidden dark:block" alt="Stripe" />
                    <img src="https://upload.wikimedia.org/wikipedia/commons/b/ba/Stripe_Logo%2C_revised_2016.svg" className="h-4 w-auto dark:hidden" alt="Stripe" />
                </div>
                <p className="text-xs font-bold text-gray-400 uppercase tracking-widest max-w-md leading-relaxed">
                    Pagamento 100% criptografado. Cancele ou altere seu plano a qualquer momento sem burocracia.
                </p>
            </div>
        </div>
    );
};

export default SubscriptionSettings;
