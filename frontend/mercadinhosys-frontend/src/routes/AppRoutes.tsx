import React, { Suspense, lazy, useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from '../components/layout/MainLayout';
import ConnectionTest from '../components/ConnectionTest';
import { LoginPage } from '../features/auth/LoginPage';
import { RegisterPage } from '../features/auth/RegisterPage';
import { authService } from '../features/auth/authService';
import SuperAdminRoute from '../components/routes/SuperAdminRoute';
import PlanoGuard from '../components/routes/PlanoGuard';

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
const DeliveryPage = lazy(() => import('../features/delivery/DeliveryPage'));




const AppRoutes: React.FC = () => {
    const [isAuthenticated, setIsAuthenticated] = useState(authService.isAuthenticated());

    useEffect(() => {
        const checkAuth = () => {
            setIsAuthenticated(authService.isAuthenticated());
        };
        window.addEventListener('auth-change', checkAuth);
        return () => window.removeEventListener('auth-change', checkAuth);
    }, []);

    return (
        <Suspense fallback={<div className="flex items-center justify-center min-h-screen">Carregando...</div>}>
            <Routes>
                <Route path="/" element={<LandingPage />} />
                <Route path="/login" element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage />} />
                <Route path="/register" element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <RegisterPage />} />
                <Route path="/test" element={<ConnectionTest />} />

                <Route element={isAuthenticated ? <MainLayout /> : <Navigate to="/login" replace />}>
                    <Route path="dashboard" element={<PlanoGuard planoRequerido="gratuito"><DashboardPage /></PlanoGuard>} />
                    <Route path="pdv" element={<PlanoGuard planoRequerido="gratuito"><PDVPage /></PlanoGuard>} />
                    <Route path="products" element={<PlanoGuard planoRequerido="gratuito"><ProductsPage /></PlanoGuard>} />
                    <Route path="suppliers" element={<PlanoGuard planoRequerido="gratuito"><SuppliersPage /></PlanoGuard>} />
                    <Route path="customers" element={<PlanoGuard planoRequerido="gratuito"><CustomersPage /></PlanoGuard>} />
                    <Route path="settings" element={<PlanoGuard planoRequerido="gratuito"><SettingsPage /></PlanoGuard>} />
                    <Route path="delivery" element={<PlanoGuard planoRequerido="gratuito"><DeliveryPage /></PlanoGuard>} />

                    {/* USANDO PRO EM VEZ DE ENTERPRISE PARA CONSISTÊNCIA */}
                    <Route path="sales" element={<PlanoGuard planoRequerido="pro"><SalesPage /></PlanoGuard>} />
                    <Route path="expenses" element={<PlanoGuard planoRequerido="pro"><ExpensesPage /></PlanoGuard>} />
                    <Route path="employees" element={<PlanoGuard planoRequerido="gratuito"><EmployeesPage /></PlanoGuard>} />
                    <Route path="rh" element={<PlanoGuard planoRequerido="pro"><RHPage /></PlanoGuard>} />
                    <Route path="ponto" element={<PlanoGuard planoRequerido="pro"><PontoPage /></PlanoGuard>} />
                    <Route path="ponto-historico" element={<PlanoGuard planoRequerido="pro"><PontoHistoricoPage /></PlanoGuard>} />
                    <Route path="ponto-relatorios" element={<PlanoGuard planoRequerido="pro"><RelatoriosPontoPage /></PlanoGuard>} />
                    <Route path="ponto-diagnostico" element={<PlanoGuard planoRequerido="pro"><DiagnosticoFotos /></PlanoGuard>} />
                    <Route path="reports" element={<PlanoGuard planoRequerido="pro"><ReportsPage /></PlanoGuard>} />

                    <Route path="estabelecimentos" element={<SuperAdminRoute><EstabelecimentosPage /></SuperAdminRoute>} />
                    <Route path="monitor" element={<SuperAdminRoute><SystemMonitorPage /></SuperAdminRoute>} />
                    <Route path="leads" element={<SuperAdminRoute><LeadDashboard /></SuperAdminRoute>} />
                </Route>

                <Route path="*" element={<Navigate to={isAuthenticated ? "/dashboard" : "/"} replace />} />
            </Routes>
        </Suspense>
    );
};

export default AppRoutes;