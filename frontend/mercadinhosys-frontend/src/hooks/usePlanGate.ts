import { useEffect, useState } from 'react';
import { authService } from '../features/auth/authService';

/**
 * Hook Sênior para controle de acesso unificado.
 * Centraliza a inteligência de permissões baseada no plano e cargo.
 */
export const usePlanGate = () => {
    const [userData, setUserData] = useState<any>(authService.getCurrentUser());

    useEffect(() => {
        const handleAuthChange = () => {
            setUserData(authService.getCurrentUser());
        };

        window.addEventListener('auth-change', handleAuthChange);
        return () => window.removeEventListener('auth-change', handleAuthChange);
    }, []);

    // Inteligência de Normalização
    const rawRole = (userData?.role || 'FUNCIONARIO').toString().toUpperCase();
    const isSuperAdmin = !!userData?.is_super_admin;
    const isAdmin = isSuperAdmin || ['ADMIN', 'ADMINISTRADOR', 'PROPRIETARIO', 'GERENTE', 'DONO', 'MASTER'].includes(rawRole);

    // Normalização de Plano (Sênior)
    const rawPlano = (userData?.plano || 'Gratuito').toString().trim().toLowerCase();

    // 🔥 SuperAdmins sempre têm acesso PRO (ou superior), mas Admins de Tenant dependem do plano real
    const isPro = isSuperAdmin || ['pro', 'pago', 'premium', 'elite', 'advanced', 'enterprise', 'master'].some(p => rawPlano.includes(p));

    // Mapeamento de Features (Baseado apenas em isPro e isAdmin para simplicidade e robustez)
    const PLAN_FEATURES = {
        hasAdvancedDashboard: isPro,
        hasDetailedReports: isPro,
        hasAIInsights: isPro,
        hasInventoryPredictor: isPro,
        hasRHTools: isPro,
        hasFinancialAdvanced: isPro,
        hasMultiTenant: isSuperAdmin,
        hasExportTools: isPro
    };

    return {
        plano: isPro ? 'Pro' : 'Gratuito',
        isPro,
        isSuperAdmin,
        isAdmin,
        userData,
        refreshPlan: () => authService.syncUserData(),
        ...PLAN_FEATURES
    };
};
