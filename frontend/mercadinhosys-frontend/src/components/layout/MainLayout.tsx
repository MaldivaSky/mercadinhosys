// src/components/layout/MainLayout.tsx
import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import HeaderProfessional from './HeaderProfessional';
import FootPage from './FootPage';

const MainLayout: React.FC = () => {
    return (
        <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
            <Sidebar />
            <div className="flex-1 flex flex-col overflow-hidden">
                <HeaderProfessional />
                <main className="flex-1 overflow-y-auto p-4 md:p-6 pb-[env(safe-area-inset-bottom)]">
                    {/* O Outlet renderiza as páginas aninhadas */}
                    <Outlet />
                </main>
                <FootPage />
            </div>
        </div>
    );
};

export default MainLayout;
