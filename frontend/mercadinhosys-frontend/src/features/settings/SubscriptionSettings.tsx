import React, { useEffect, useState } from 'react';
import { CreditCard, Calendar, AlertTriangle, Star, Shield } from 'lucide-react';
import settingsService, { SubscriptionStatus } from './settingsService';
import { toast } from 'react-hot-toast';

const SubscriptionSettings: React.FC = () => {
    const [status, setStatus] = useState<SubscriptionStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [processingCheckout, setProcessingCheckout] = useState(false);

    useEffect(() => {
        const loadStatus = async () => {
            try {
                const data = await settingsService.getSubscriptionStatus();
                setStatus(data);
            } catch (error) {
                console.error("Erro ao carregar assinatura:", error);
                toast.error("Erro ao carregar detalhes da assinatura.");
            } finally {
                setLoading(false);
            }
        };
        loadStatus();
    }, []);

    if (loading) {
        return (
            <div className="flex justify-center items-center py-12">
                <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

    if (!status) {
        return (
            <div className="bg-red-50 dark:bg-red-900/20 p-6 rounded-xl border border-red-200 dark:border-red-800 text-center">
                <AlertTriangle className="w-10 h-10 text-red-500 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-red-700 dark:text-red-300">Erro ao carregar assinatura</h3>
                <p className="text-red-600 dark:text-red-400">Não foi possível obter os dados do seu plano.</p>
            </div>
        );
    }

    const isActive = status.is_active;

    const formatDate = (dateString: string | null) => {
        if (!dateString) return 'Vitalício';
        return new Date(dateString).toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: 'long',
            year: 'numeric'
        });
    };

    const handleCheckout = async (planName: string) => {
        try {
            setProcessingCheckout(true);
            const response = await settingsService.createCheckoutSession(planName);
            if (response.checkout_url) {
                window.location.href = response.checkout_url;
            } else {
                toast.error("Erro ao iniciar checkout. Tente novamente.");
            }
        } catch (error) {
            console.error("Erro checkout:", error);
            toast.error("Erro ao conectar com o pagamento. Verifique se as chaves Stripe estão configuradas.");
        } finally {
            setProcessingCheckout(false);
        }
    };

    const handlePortal = async () => {
        try {
            setProcessingCheckout(true);
            const response = await settingsService.openPortal();
            if (response.portal_url) {
                window.location.href = response.portal_url;
            } else {
                toast.error("Erro ao abrir portal. Tente novamente.");
            }
        } catch (error) {
            console.error("Erro portal:", error);
            toast.error("Erro ao abrir portal de gerenciamento.");
        } finally {
            setProcessingCheckout(false);
        }
    };

    return (
        <div className="space-y-6 animate-fadeIn">
            {/* Header / Current Plan Card */}
            <div className="bg-gradient-to-br from-blue-600 to-indigo-700 rounded-xl shadow-lg p-6 text-white relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-10">
                    <Star className="w-32 h-32 transform rotate-12" />
                </div>

                <div className="relative z-10 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div>
                        <div className="flex items-center gap-2 mb-2">
                            <span className="px-2 py-1 bg-white/20 rounded-md text-xs font-medium uppercase tracking-wider backdrop-blur-sm">
                                {status.status === 'experimental' ? 'Período de Teste' : 'Assinatura Ativa'}
                            </span>
                            {!isActive && (
                                <span className="px-2 py-1 bg-red-500 rounded-md text-xs font-medium uppercase tracking-wider">
                                    Expirado
                                </span>
                            )}
                        </div>
                        <h2 className="text-3xl font-bold mb-1">{status.plano}</h2>
                        <p className="text-blue-100 flex items-center gap-2">
                            <Calendar className="w-4 h-4" />
                            Vence em: {formatDate(status.vencimento)}
                        </p>
                    </div>

                    <div className="flex flex-col gap-2">
                        {isActive && status.status !== 'experimental' ? (
                            <button
                                onClick={handlePortal}
                                disabled={processingCheckout}
                                className="px-6 py-2 bg-white text-blue-700 hover:bg-blue-50 font-semibold rounded-lg transition-colors shadow-sm disabled:opacity-70 disabled:cursor-wait"
                            >
                                {processingCheckout ? 'Abrindo...' : 'Gerenciar Assinatura'}
                            </button>
                        ) : (
                            <button
                                onClick={() => handleCheckout('Premium')}
                                disabled={processingCheckout}
                                className="px-6 py-2 bg-white text-blue-700 hover:bg-blue-50 font-semibold rounded-lg transition-colors shadow-sm disabled:opacity-70 disabled:cursor-wait"
                            >
                                {processingCheckout ? 'Processando...' : (status.status === 'experimental' ? 'Assinar Agora' : 'Renovar Agora')}
                            </button>
                        )}
                    </div>
                </div>
            </div>

            {/* Features Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
                    <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4 flex items-center gap-2">
                        <Shield className="w-5 h-5 text-green-500" />
                        Status da Conta
                    </h3>
                    <div className="space-y-3">
                        <div className="flex justify-between items-center py-2 border-b border-gray-100 dark:border-gray-700">
                            <span className="text-gray-600 dark:text-gray-400">Plano Atual</span>
                            <span className="font-medium text-gray-900 dark:text-gray-100">{status.plano}</span>
                        </div>
                        <div className="flex justify-between items-center py-2 border-b border-gray-100 dark:border-gray-700">
                            <span className="text-gray-600 dark:text-gray-400">Situação</span>
                            <span className={`font-medium ${isActive ? 'text-green-600' : 'text-red-500'}`}>
                                {isActive ? 'Em dia' : 'Pagamento Pendente'}
                            </span>
                        </div>
                        <div className="flex justify-between items-center py-2">
                            <span className="text-gray-600 dark:text-gray-400">Próxima Fatura</span>
                            <span className="font-medium text-gray-900 dark:text-gray-100">
                                {status.vencimento ? formatDate(status.vencimento) : 'N/A'}
                            </span>
                        </div>
                    </div>
                </div>

                <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
                    <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4 flex items-center gap-2">
                        <CreditCard className="w-5 h-5 text-blue-500" />
                        Método de Pagamento
                    </h3>
                    <div className="flex flex-col items-center justify-center h-32 text-center text-gray-500">
                        <p className="mb-2">Gerenciado via Stripe (Pix/Cartão)</p>
                        <button
                            onClick={() => handleCheckout('Premium')}
                            className="text-blue-600 hover:text-blue-700 text-sm font-medium hover:underline"
                        >
                            Atualizar cartão de crédito
                        </button>
                    </div>
                </div>
            </div>

            {!isActive && (
                <div className="bg-orange-50 dark:bg-orange-900/20 p-4 rounded-lg border border-orange-200 dark:border-orange-800 flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-orange-600 dark:text-orange-400 flex-shrink-0 mt-0.5" />
                    <div>
                        <h4 className="font-medium text-orange-800 dark:text-orange-300">Atenção: Assinatura Expirada</h4>
                        <p className="text-sm text-orange-700 dark:text-orange-400 mt-1">
                            Sua assinatura expirou. Renove agora para continuar acessando todos os recursos premium e evitar bloqueios.
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
};

export default SubscriptionSettings;
