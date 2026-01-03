import React, { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from '../components/layout/MainLayout';
import ConnectionTest from '../components/ConnectionTest';
import LoginPage from '../features/auth/LoginPage';

// Lazy loading das páginas
const DashboardPage = lazy(() => import('../features/dashboard/DashboardPage'));
const PDVPage = lazy(() => import('../features/pdv/PDVPage'));
const ProductsPage = lazy(() => import('../features/products/ProductsPage'));
const CustomersPage = lazy(() => import('../features/customers/CustomersPage'));
const SalesPage = lazy(() => import('../features/sales/SalesPage'));
const ExpensesPage = lazy(() => import('../features/expenses/ExpensesPage'));
const EmployeesPage = lazy(() => import('../features/employees/EmployeesPage'));
const ReportsPage = lazy(() => import('../features/reports/ReportsPage'));
const SettingsPage = lazy(() => import('../features/settings/SettingsPage'));

const AppRoutes: React.FC = () => {
    const isAuthenticated = localStorage.getItem('access_token');

    return (
        <Suspense fallback={<div className="flex items-center justify-center min-h-screen">Carregando...</div>}>
            <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/test" element={<ConnectionTest />} />

                {isAuthenticated ? (
                    <Route path="/" element={<MainLayout />}>
                        <Route index element={<Navigate to="/dashboard" replace />} />
                        <Route path="dashboard" element={<DashboardPage />} />
                        <Route path="pdv" element={<PDVPage />} />
                        <Route path="products" element={<ProductsPage />} />
                        <Route path="customers" element={<CustomersPage />} />
                        <Route path="sales" element={<SalesPage />} />
                        <Route path="expenses" element={<ExpensesPage />} />
                        <Route path="employees" element={<EmployeesPage />} />
                        <Route path="reports" element={<ReportsPage />} />
                        <Route path="settings" element={<SettingsPage />} />
                    </Route>
                ) : (
                    <Route path="*" element={<Navigate to="/login" replace />} />
                )}

                <Route path="*" element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />} />
            </Routes>
        </Suspense>
    );
};

export default AppRoutes;