// src/components/layout/MainLayout.tsx
import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import HeaderProfessional from './HeaderProfessional';
import FootPage from './FootPage';
import WelcomeTour from '../WelcomeTour';

const MainLayout: React.FC = () => {
    const [isCollapsed, setIsCollapsed] = React.useState(false);

    return (
        <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
            <WelcomeTour />
            <Sidebar isCollapsed={isCollapsed} setIsCollapsed={setIsCollapsed} />
            <div className={`flex-1 flex flex-col h-full overflow-hidden transition-all duration-300`}>
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
