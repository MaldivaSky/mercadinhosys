/**
 * MercadinhoSys - Super Admin Route Wrapper
 * Protege rotas que exigem privilégios de Super Admin
 */

import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth, SUPER_ADMIN_EMAILS, SUPER_ADMIN_USERNAMES } from '../utils/authUtils';
import { useIsSuperAdmin } from '../hooks/useIsSuperAdmin';

interface SuperAdminRouteProps {
  children: React.ReactNode;
  redirectTo?: string;
}

/**
 * Wrapper de rota que permite acesso apenas a Super Admins
 * Usuários com role='ADMIN' são redirecionados
 */
export const SuperAdminRoute: React.FC<SuperAdminRouteProps> = ({ 
  children, 
  redirectTo = '/dashboard' 
}) => {
  const { user, isAuthenticated, loading } = useAuth();
  const location = useLocation();

  // Enquanto carrega, mostra loading ou nada
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // Se não estiver autenticado, redireciona para login
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Verifica se é Super Admin
  const isSuperAdmin = user?.is_super_admin === true || 
                       (user?.role === 'ADMIN' && 
                        (SUPER_ADMIN_EMAILS.includes(user?.email) || 
                         SUPER_ADMIN_USERNAMES.includes(user?.username)));

  // Se não for Super Admin, redireciona
  if (!isSuperAdmin) {
    return <Navigate to={redirectTo} replace />;
  }

  // Se for Super Admin, renderiza os filhos
  return <>{children}</>;
};

/**
 * Componente para renderizar conteúdo condicional baseado em privilégios
 */
interface SuperAdminOnlyProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export const SuperAdminOnly: React.FC<SuperAdminOnlyProps> = ({ 
  children, 
  fallback = null 
}) => {
  const isSuperAdmin = useIsSuperAdmin();
  
  return <>{isSuperAdmin ? children : fallback}</>;
};

/**
 * Componente para menus que devem ser visíveis apenas para Super Admins
 */
interface SuperAdminMenuItemProps {
  children: React.ReactNode;
  icon?: React.ReactNode;
  to?: string;
  onClick?: () => void;
}

export const SuperAdminMenuItem: React.FC<SuperAdminMenuItemProps> = ({
  children,
  icon,
  to,
  onClick
}) => {
  const isSuperAdmin = useIsSuperAdmin();

  if (!isSuperAdmin) {
    return null;
  }

  const content = (
    <div className="flex items-center gap-2">
      {icon && <span className="text-red-600">{icon}</span>}
      <span>{children}</span>
    </div>
  );

  if (to) {
    return (
      <a 
        href={to}
        className="flex items-center px-3 py-2 text-sm font-medium text-red-600 hover:text-red-800 hover:bg-red-50 rounded-md transition-colors"
      >
        {content}
      </a>
    );
  }

  if (onClick) {
    return (
      <button
        onClick={onClick}
        className="flex items-center w-full px-3 py-2 text-sm font-medium text-red-600 hover:text-red-800 hover:bg-red-50 rounded-md transition-colors"
      >
        {content}
      </button>
    );
  }

  return (
    <div className="flex items-center px-3 py-2 text-sm font-medium text-red-600">
      {content}
    </div>
  );
};

export default SuperAdminRoute;
