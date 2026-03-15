import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

interface SuperAdminRouteProps {
  children: React.ReactNode;
}

/**
 * Componente wrapper que protege rotas exclusivas para Super Admins do SaaS
 */
const SuperAdminRoute: React.FC<SuperAdminRouteProps> = ({ children }) => {
  const { user, loading } = useAuth();

  console.log('🛡️ [SuperAdminRoute] Verificando acesso:', {
    username: user?.username || user?.nome,
    is_super_admin: user?.is_super_admin,
    type: typeof user?.is_super_admin
  });

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">Carregando permissões...</div>;
  }

  // Se não estiver autenticado, redireciona para login
  if (!user) {
    console.warn('🛡️ [SuperAdminRoute] Usuário não autenticado. Redirecionando para /login');
    return <Navigate to="/login" replace />;
  }

  // Se não for super admin, redireciona para dashboard
  if (user.is_super_admin !== true) {
    console.warn('🛡️ [SuperAdminRoute] Usuário não é Super Admin. Bloqueando acesso e redirecionando para /dashboard');
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

export default SuperAdminRoute;
