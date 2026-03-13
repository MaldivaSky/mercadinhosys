import React, { useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { authService } from '../../features/auth/authService';
import toast from 'react-hot-toast';

interface SuperAdminRouteProps {
  children: React.ReactNode;
}

/**
 * Componente wrapper que protege rotas exclusivas para Super Admins do SaaS
 * Verifica a flag is_super_admin no contexto de autenticação
 */
const SuperAdminRoute: React.FC<SuperAdminRouteProps> = ({ children }) => {
  const user = authService.getCurrentUser();
  const isSuperAdmin = user?.is_super_admin === true;

  useEffect(() => {
    // Se não for Super Admin, mostra toast de erro e redireciona
    if (!isSuperAdmin && user) {
      toast.error('Acesso restrito: Apenas o administrador do sistema pode acessar esta funcionalidade.', {
        duration: 4000,
        position: 'top-center',
      });
    }
  }, [isSuperAdmin, user]);

  // Se não estiver autenticado, redireciona para login
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Se não for Super Admin, redireciona para login com mensagem de acesso negado
  if (!isSuperAdmin) {
    return <Navigate to="/login" replace />;
  }

  // Se for Super Admin, renderiza o conteúdo
  return <>{children}</>;
};

export default SuperAdminRoute;
