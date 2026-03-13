import React, { Suspense, lazy, useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from '../components/layout/MainLayout';
import ConnectionTest from '../components/ConnectionTest';
import { LoginPage } from '../features/auth/LoginPage';
import { RegisterPage } from '../features/auth/RegisterPage';
import { authService } from '../features/auth/authService';
import SuperAdminRoute from '../components/routes/SuperAdminRoute';

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

// Componente para proteção de rotas por role
const RoleGuard = ({ children, allowedRoles, requireSuperAdmin }: { children: React.ReactNode, allowedRoles?: string[], requireSuperAdmin?: boolean }) => {
    const user = authService.getCurrentUser();
    const userRole = user?.role?.toLowerCase() || '';
    const isSuperAdmin = user?.is_super_admin || false;

    // Se exigir super admin e não for, bloqueia
    if (requireSuperAdmin && !isSuperAdmin) {
        return <Navigate to="/login" replace />;
    }

    // Se a rota for restrita a certos perfis (ex: admin)
    if (allowedRoles && !allowedRoles.includes(userRole)) {
        return <Navigate to="/login" replace />;
    }

    return <>{children}</>;
};

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
                    <Route path="dashboard" element={<RoleGuard allowedRoles={['admin', 'gerente', 'funcionario', 'caixa', 'estoquista']}><DashboardPage /></RoleGuard>} />
                    <Route path="pdv" element={<PDVPage />} />
                    <Route path="products" element={<RoleGuard allowedRoles={['admin', 'gerente', 'estoquista']}><ProductsPage /></RoleGuard>} />
                    <Route path="suppliers" element={<RoleGuard allowedRoles={['admin', 'gerente', 'estoquista']}><SuppliersPage /></RoleGuard>} />
                    <Route path="customers" element={<RoleGuard allowedRoles={['admin', 'gerente', 'funcionario', 'caixa', 'estoquista']}><CustomersPage /></RoleGuard>} />
                    <Route path="sales" element={<RoleGuard allowedRoles={['admin', 'gerente']}><SalesPage /></RoleGuard>} />
                    <Route path="expenses" element={<RoleGuard allowedRoles={['admin', 'gerente']}><ExpensesPage /></RoleGuard>} />
                    <Route path="employees" element={<RoleGuard allowedRoles={['admin', 'gerente']}><EmployeesPage /></RoleGuard>} />
                    <Route path="rh" element={<RoleGuard allowedRoles={['admin', 'gerente']}><RHPage /></RoleGuard>} />
                    <Route path="ponto" element={<RoleGuard allowedRoles={['admin', 'gerente', 'funcionario', 'caixa', 'estoquista']}><PontoPage /></RoleGuard>} />
                    <Route path="ponto-historico" element={<RoleGuard allowedRoles={['admin', 'gerente', 'funcionario', 'caixa', 'estoquista']}><PontoHistoricoPage /></RoleGuard>} />
                    <Route path="ponto-relatorios" element={<RoleGuard allowedRoles={['admin', 'gerente']}><RelatoriosPontoPage /></RoleGuard>} />
                    <Route path="ponto-diagnostico" element={<RoleGuard allowedRoles={['admin', 'gerente']}><DiagnosticoFotos /></RoleGuard>} />
                    <Route path="reports" element={<RoleGuard allowedRoles={['admin', 'gerente']}><ReportsPage /></RoleGuard>} />
                    <Route path="settings" element={<RoleGuard allowedRoles={['admin', 'gerente', 'funcionario', 'caixa', 'estoquista']}><SettingsPage /></RoleGuard>} />
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