import React, { useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { usePlanGate } from '../../hooks/usePlanGate';
import toast from 'react-hot-toast';

interface PlanoGuardProps {
  children: React.ReactNode;
  planoRequerido: string;
  fallback?: string;
}

const PlanoGuard: React.FC<PlanoGuardProps> = ({
  children,
  planoRequerido,
  fallback = '/dashboard'
}) => {
  const { plano, isSuperAdmin } = usePlanGate();

  const userLevel = plano === 'Pro' ? 2 : 1;
  const requiredLevel = planoRequerido.toLowerCase() === 'pro' || planoRequerido.toLowerCase() === 'enterprise' ? 2 : 1;

  const hasAccess = isSuperAdmin || userLevel >= requiredLevel;

  useEffect(() => {
    if (!hasAccess) {
      toast.error(`Acesso restrito: Esta funcionalidade requer o Plano Pro.`, {
        id: 'plano-guard-error',
        duration: 4000,
        position: 'top-center',
      });
    }
  }, [hasAccess, planoRequerido]);

  if (!hasAccess) {
    return <Navigate to={fallback} replace />;
  }

  return <>{children}</>;
};

export default PlanoGuard;
