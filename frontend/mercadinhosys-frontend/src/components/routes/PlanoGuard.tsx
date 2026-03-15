import React, { useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { authService } from '../../features/auth/authService';
import toast from 'react-hot-toast';

interface PlanoGuardProps {
  children: React.ReactNode;
  planoRequerido: 'gratuito' | 'advanced' | 'superadmin';
  fallback?: string;
}

interface User {
  nome: string;
  role: string;
  is_super_admin?: boolean;
  plano?: 'gratuito' | 'advanced' | 'superadmin';
}

/**
 * Componente wrapper que protege rotas baseado no PLANO SaaS
 * Lógica correta: Verifica assinatura/plano, não apenas role
 */
const PlanoGuard: React.FC<PlanoGuardProps> = ({ 
  children, 
  planoRequerido, 
  fallback = '/dashboard' 
}) => {
  const user = authService.getCurrentUser() as User;
  const userPlano = user?.plano || 'gratuito'; // Default: gratuito
  const isSuperAdmin = user?.is_super_admin === true;

  const hasAccess = (): boolean => {
    // SuperAdmin tem acesso a tudo
    if (isSuperAdmin) {
      return true;
    }

    // Verificar acesso baseado no plano
    switch (planoRequerido) {
      case 'gratuito':
        // Plano gratuito tem acesso apenas ao básico
        return true;
        
      case 'advanced':
        // Apenas plano advanced ou superior
        return userPlano === 'advanced' || userPlano === 'superadmin';
        
      case 'superadmin':
        // Apenas SuperAdmin
        return isSuperAdmin;
        
      default:
        return false;
    }
  };

  useEffect(() => {
    // Se não tiver plano requerido, mostra toast informativo
    if (user && !hasAccess()) {
      const planos = {
        gratuito: 'Plano Gratuito',
        advanced: 'Plano Advanced',
        superadmin: 'Super Admin'
      };
      
      toast.error(`Acesso restrito: Esta funcionalidade requer ${planos[planoRequerido]}.`, {
        duration: 4000,
        position: 'top-center',
      });
    }
  }, [user, planoRequerido, hasAccess]);

  // Se não estiver autenticado, redireciona para login
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Se não tiver acesso, redireciona para fallback
  if (!hasAccess()) {
    return <Navigate to={fallback} replace />;
  }

  // Se tiver acesso, renderiza o conteúdo
  return <>{children}</>;
};

export default PlanoGuard;
