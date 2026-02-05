import React, { Suspense, lazy, useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from '../components/layout/MainLayout';
import ConnectionTest from '../components/ConnectionTest';
import {LoginPage} from '../features/auth/LoginPage';
import { authService } from '../features/auth/authService';

// Lazy loading das páginas
const DashboardPage = lazy(() => import('../features/dashboard/DashboardPage'));
const PDVPage = lazy(() => import('../features/pdv/PDVPage'));
const ProductsPage = lazy(() => import('../features/products/ProductsPage'));
const SuppliersPage = lazy(() => import('../features/suppliers/SuppliersPage'));
const CustomersPage = lazy(() => import('../features/customers/CustomersPage'));
const SalesPage = lazy(() => import('../features/sales/SalesPage'));
const ExpensesPage = lazy(() => import('../features/expenses/ExpensesPage'));
const EmployeesPage = lazy(() => import('../features/employees/EmployeesPage'));
const PontoPage = lazy(() => import('../features/ponto/PontoPage'));
const ReportsPage = lazy(() => import('../features/reports/ReportsPage'));
const SettingsPage = lazy(() => import('../features/settings/SettingsPage'));

const AppRoutes: React.FC = () => {
    const [isAuthenticated, setIsAuthenticated] = useState(authService.isAuthenticated());

    // Monitora mudanças no localStorage via evento customizado
    useEffect(() => {
        const checkAuth = () => {
            setIsAuthenticated(authService.isAuthenticated());
        };

        // Escuta o evento customizado de mudança de autenticação
        window.addEventListener('auth-change', checkAuth);

        return () => {
            window.removeEventListener('auth-change', checkAuth);
        };
    }, []);

    return (
        <Suspense fallback={<div className="flex items-center justify-center min-h-screen">Carregando...</div>}>
            <Routes>
                {/* Rota de login - sempre acessível */}
                <Route path="/login" element={
                    isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage />
                } />

                {/* Rota de teste - sempre acessível */}
                <Route path="/test" element={<ConnectionTest />} />

                {/* Rotas protegidas */}
                {isAuthenticated ? (
                    <Route path="/" element={<MainLayout />}>
                        <Route index element={<Navigate to="/dashboard" replace />} />
                        <Route path="dashboard" element={<DashboardPage />} />
                        <Route path="pdv" element={<PDVPage />} />
                        <Route path="products" element={<ProductsPage />} />
                        <Route path="suppliers" element={<SuppliersPage />} />
                        <Route path="customers" element={<CustomersPage />} />
                        <Route path="sales" element={<SalesPage />} />
                        <Route path="expenses" element={<ExpensesPage />} />
                        <Route path="employees" element={<EmployeesPage />} />
                        <Route path="ponto" element={<PontoPage />} />
                        <Route path="reports" element={<ReportsPage />} />
                        <Route path="settings" element={<SettingsPage />} />
                    </Route>
                ) : (
                    // Se não autenticado, redireciona todas as rotas para login
                    <Route path="*" element={<Navigate to="/login" replace />} />
                )}

                {/* Fallback - se alguém acessar uma rota não definida */}
                <Route path="*" element={
                    <Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />
                } />
            </Routes>
        </Suspense>
    );
};

export default AppRoutes;