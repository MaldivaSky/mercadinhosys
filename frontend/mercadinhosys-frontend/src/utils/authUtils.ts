/**
 * Authentication utilities and constants
 */

// Tipos para o contexto de autenticação (ajustar conforme implementação real)
export interface User {
  id: number;
  name: string;
  email: string;
  username: string;
  role: string;
  is_super_admin?: boolean;
}

export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
}

// Constantes para verificação de Super Admin
export const SUPER_ADMIN_EMAILS = ['admin@mercadinhosys.com'];
export const SUPER_ADMIN_USERNAMES = ['admin', 'maldivas'];

// Mock do contexto - substituir com o contexto real
export const useAuth = (): AuthContextType => {
  // Implementação mock - substituir com contexto real
  return {
    user: null,
    isAuthenticated: false,
    loading: false
  };
};
