// src/routes/AppRoutes.tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LoginPage } from '../features/auth/LoginPage';
import App from '../App';

export function AppRoutes() {
    // Verifica se há token no localStorage
    const token = localStorage.getItem('token');
    const isAuthenticated = Boolean(token);

    return (
        <BrowserRouter>
            <Routes>
                {/* Rota para login */}
                <Route path="/login" element={<LoginPage />} />

                {/* Rota para dashboard (protegida) */}
                <Route
                    path="/dashboard"
                    element={isAuthenticated ? <App /> : <Navigate to="/login" />}
                />

                {/* Rota raiz - redireciona baseado na autenticação */}
                <Route
                    path="/"
                    element={
                        <Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />
                    }
                />

                {/* Rota para qualquer outra URL não encontrada */}
                <Route path="*" element={<Navigate to="/" />} />
            </Routes>
        </BrowserRouter>
    );
}