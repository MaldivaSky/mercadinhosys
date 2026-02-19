import { useMemo } from 'react';
import { Estabelecimento } from '../types';

export type FeatureKey =
    | 'advanced_dashboard'
    | 'rh_tools'
    | 'demand_forecast'
    | 'multitenancy'
    | 'white_label';

// Mapeamento de recursos por plano
const PLAN_FEATURES: Record<string, FeatureKey[]> = {
    'Basic': [],
    'Advanced': ['advanced_dashboard', 'rh_tools', 'demand_forecast'],
    'Premium': ['advanced_dashboard', 'rh_tools', 'demand_forecast', 'multitenancy', 'white_label'],
};

/**
 * Hook para controle de acesso a recursos baseado no plano de assinatura
 */
export const usePlanGate = () => {
    // Busca dados do estabelecimento do localStorage
    const estabelecimento = useMemo((): Partial<Estabelecimento> => {
        try {
            const data = localStorage.getItem('estabelecimento_data');
            return data ? JSON.parse(data) : {};
        } catch (error) {
            console.error('Erro ao ler dados do estabelecimento para gating:', error);
            return {};
        }
    }, []);

    const plano = (estabelecimento.plano || 'Basic') as string;
    const status = (estabelecimento.plano_status || 'experimental') as string;

    /**
     * Verifica se um recurso específico está disponível no plano atual
     */
    const hasFeature = (feature: FeatureKey): boolean => {
        // Bloqueia recursos premium se a assinatura não estiver ativa ou em período experimental
        if (!['ativo', 'experimental'].includes(status.toLowerCase())) {
            return false;
        }

        const features = PLAN_FEATURES[plano] || [];
        return features.includes(feature);
    };

    return {
        plano,
        status,
        hasFeature,
        hasAdvancedDashboard: hasFeature('advanced_dashboard'),
        hasRHTools: hasFeature('rh_tools'),
        isAdvanced: plano === 'Advanced' || plano === 'Premium',
        isPremium: plano === 'Premium',
        // Helper para UI: retorna se o estabelecimento está com pendência de pagamento
        isAtrasado: status.toLowerCase() === 'atrasado',
        isCancelado: status.toLowerCase() === 'cancelado'
    };
};
