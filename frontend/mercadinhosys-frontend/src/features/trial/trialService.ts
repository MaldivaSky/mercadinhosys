import { apiClient } from '../../api/apiClient';

export interface TrialStatus {
    plano: string;
    plano_status: string;
    ativo: boolean;
    vencimento_plano: string | null;
    dias_restantes: number | null;
    em_trial: boolean;
    vencido: boolean;
}

export const trialService = {
    /** Status do período de teste do estabelecimento logado (null em erro/sem trial). */
    getStatus: async (): Promise<TrialStatus | null> => {
        try {
            const { data } = await apiClient.get('/saas/trial-status');
            return data?.data ?? null;
        } catch {
            return null;
        }
    },
};

export default trialService;
