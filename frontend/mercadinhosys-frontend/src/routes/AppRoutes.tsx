import React, { Suspense, lazy, useEffect } from 'react';
import { useNavigate, Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from '../components/layout/MainLayout';
import ConnectionTest from '../components/ConnectionTest';
import { LoginPage } from '../features/auth/LoginPage';
import { RegisterPage } from '../features/auth/RegisterPage';
import SuperAdminRoute from '../components/routes/SuperAdminRoute';
import PlanoGuard from '../components/routes/PlanoGuard';
import { useAuth } from '../contexts/AuthContext';

// Lazy loading das páginas
const DashboardPage = lazy(() => import('../features/dashboard/DashboardPage'));
const PDVPage = lazy(() => import('../features/pdv/PDVPage'));
const ProductsPage = lazy(() => import('../features/products/ProductsPage'));
const SuppliersPage = lazy(() => import('../features/suppliers/SuppliersPage'));
const CustomersPage = lazy(() => import('../features/customers/CustomersPage'));
const SalesPage = lazy(() => import('../features/sales/SalesPage'));
const ExpensesPage = lazy(() => import('../features/expenses/ExpensesPage'));
const EmployeesPage = lazy(() => import('../features/employees/EmployeesPage'));
const RHPage = lazy(() => import('../features/employees/RHPage'));
const PontoPage = lazy(() => import('../features/ponto/PontoPage'));
const PontoHistoricoPage = lazy(() => import('../features/ponto/PontoHistoricoPage'));
const RelatoriosPontoPage = lazy(() => import('../features/ponto/RelatoriosPontoPage'));
const DiagnosticoFotos = lazy(() => import('../features/ponto/DiagnosticoFotos'));
const ReportsPage = lazy(() => import('../features/reports/ReportsPage'));
const SettingsPage = lazy(() => import('../features/settings/SettingsPage'));
const LeadDashboard = lazy(() => import('../features/saas/LeadDashboard'));
const SystemMonitorPage = lazy(() => import('../features/saas/SystemMonitorPage'));
const LandingPage = lazy(() => import('../features/landing/LandingPage'));
const EstabelecimentosPage = lazy(() => import('../features/estabelecimentos/EstabelecimentosPage'));

const AppRoutes: React.FC = () => {
    const { isAuthenticated, loading } = useAuth();
    const navigate = useNavigate();

    // Efeito para redirecionamento após login (evita window.location.href)
    useEffect(() => {
        if (isAuthenticated && window.location.pathname === '/login') {
            navigate('/dashboard', { replace: true });
        }
    }, [isAuthenticated, navigate]);

    if (loading) {
        return <div className="flex items-center justify-center min-h-screen">Carregando...</div>;
    }

    return (
        <Suspense fallback={<div className="flex items-center justify-center min-h-screen">Carregando...</div>}>
            <Routes>
                {/* Rota Pública - Landing Page no Root */}
                <Route path="/" element={<LandingPage />} />

                {/* Rota de login - sempre acessível */}
                <Route path="/login" element={
                    isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage />
                } />

                {/* Rota de registro - sempre acessível */}
                <Route path="/register" element={
                    isAuthenticated ? <Navigate to="/dashboard" replace /> : <RegisterPage />
                } />

                {/* Rota de teste - sempre acessível */}
                <Route path="/test" element={<ConnectionTest />} />

                {/* Rotas protegidas (sem prefixo /app para evitar quebrar links) */}
                <Route element={isAuthenticated ? <MainLayout /> : <Navigate to="/login" replace />}>
                    {/* PLANO GRATUITO - Acesso básico para todos */}
                    <Route path="dashboard" element={<PlanoGuard planoRequerido="gratuito"><DashboardPage /></PlanoGuard>} />
                    <Route path="pdv" element={<PlanoGuard planoRequerido="gratuito"><PDVPage /></PlanoGuard>} />
                    <Route path="products" element={<PlanoGuard planoRequerido="gratuito"><ProductsPage /></PlanoGuard>} />
                    <Route path="suppliers" element={<PlanoGuard planoRequerido="gratuito"><SuppliersPage /></PlanoGuard>} />
                    <Route path="customers" element={<PlanoGuard planoRequerido="gratuito"><CustomersPage /></PlanoGuard>} />
                    <Route path="sales" element={<PlanoGuard planoRequerido="gratuito"><SalesPage /></PlanoGuard>} />
                    <Route path="settings" element={<PlanoGuard planoRequerido="gratuito"><SettingsPage /></PlanoGuard>} />

                    {/* PLANO ADVANCED - Funcionalidades pagas (Gestão de Equipe) */}
                    <Route path="employees" element={<PlanoGuard planoRequerido="advanced"><EmployeesPage /></PlanoGuard>} />
                    <Route path="rh" element={<PlanoGuard planoRequerido="advanced"><RHPage /></PlanoGuard>} />
                    <Route path="ponto" element={<PlanoGuard planoRequerido="advanced"><PontoPage /></PlanoGuard>} />
                    <Route path="ponto-historico" element={<PlanoGuard planoRequerido="advanced"><PontoHistoricoPage /></PlanoGuard>} />
                    <Route path="ponto-relatorios" element={<PlanoGuard planoRequerido="advanced"><RelatoriosPontoPage /></PlanoGuard>} />
                    <Route path="ponto-diagnostico" element={<PlanoGuard planoRequerido="advanced"><DiagnosticoFotos /></PlanoGuard>} />
                    <Route path="reports" element={<PlanoGuard planoRequerido="advanced"><ReportsPage /></PlanoGuard>} />
                    <Route path="expenses" element={<PlanoGuard planoRequerido="advanced"><ExpensesPage /></PlanoGuard>} />

                    {/* SUPER ADMIN - Acesso total ao sistema */}
                    <Route path="estabelecimentos" element={<SuperAdminRoute><EstabelecimentosPage /></SuperAdminRoute>} />
                    <Route path="monitor" element={<SuperAdminRoute><SystemMonitorPage /></SuperAdminRoute>} />
                    <Route path="leads" element={<SuperAdminRoute><LeadDashboard /></SuperAdminRoute>} />
                </Route>

                {/* Fallback - se alguém acessar uma rota não definida */}
                <Route path="*" element={
                    <Navigate to={isAuthenticated ? "/dashboard" : "/"} replace />
                } />
            </Routes>
        </Suspense>
    );
};

export default AppRoutes;