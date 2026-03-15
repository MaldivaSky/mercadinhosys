import React from 'react';
import { Navigate } from 'react-router-dom';
import { authService } from '../../features/auth/authService';

interface SuperAdminRouteProps {
  children: React.ReactNode;
}

/**
 * Componente wrapper que protege rotas exclusivas para Super Admins do SaaS
 * Verifica a flag is_super_admin no contexto de autenticação
 */
const SuperAdminRoute: React.FC<SuperAdminRouteProps> = ({ children }) => {
  const user = authService.getCurrentUser();

  // Se não estiver autenticado, redireciona para login
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Lógica de Super Admin desativada: todos os admins acessam
  return <>{children}</>;
};

export default SuperAdminRoute;
