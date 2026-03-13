import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authService } from '../features/auth/authService';

interface User {
    id: number;
    username?: string;
    usuario?: string;
    nome: string;
    email?: string;
    role: string;
    cargo: string;
    estabelecimento_id: number;
    status: string;
    foto_url?: string;
    telefone?: string;
    is_super_admin?: boolean;
    permissoes: Record<string, boolean>;
}

interface AuthContextType {
    user: User | null;
    loading: boolean;
    login: (username: string, senha: string) => Promise<boolean>;
    logout: () => void;
    isAuthenticated: boolean;
    updateUser: (user: User) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
    children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const token = localStorage.getItem('access_token');
        const userData = localStorage.getItem('user_data');

        if (token && userData) {
            try {
                const parsedUser = JSON.parse(userData);
                setUser(parsedUser);
            } catch (error) {
                console.error('Erro ao parsear dados do usuário:', error);
                localStorage.removeItem('access_token');
                localStorage.removeItem('user_data');
                localStorage.removeItem('refresh_token');
            }
        }
        setLoading(false);
    }, []);

    const login = async (username: string, senha: string): Promise<boolean> => {
        try {
            const result = await authService.login(username, senha);
            if (result && result.success && result.data?.user) {
                setUser(result.data.user as unknown as User);
                // Senior-Grade Reset: Reload page to purge all old states/contexts
                window.location.href = '/dashboard';
                return true;
            }
            return false;
        } catch (error) {
            console.error('Erro no login Context:', error);
            return false;
        }
    };

    const logout = () => {
        authService.logout();
        setUser(null);
        // Radical Reset: Redirect to root to clear all memory state
        window.location.href = '/';
    };

    const updateUser = (updatedUser: User) => {
        setUser(updatedUser);
        localStorage.setItem('user_data', JSON.stringify(updatedUser));
    };

    const isAuthenticated = !!user;

    return (
        <AuthContext.Provider
            value={{
                user,
                loading,
                login,
                logout,
                isAuthenticated,
                updateUser,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = (): AuthContextType => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth deve ser usado dentro de um AuthProvider');
    }
    return context;
};

export default AuthContext;
