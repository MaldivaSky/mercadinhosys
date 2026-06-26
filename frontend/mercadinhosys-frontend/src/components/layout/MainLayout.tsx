import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import HeaderProfessional from './HeaderProfessional';
import FootPage from './FootPage';
import WelcomeTour from '../WelcomeTour';
import BottomNavigation from './BottomNavigation';
import GlobalShortcuts from '../../shortcuts/GlobalShortcuts';

const MainLayout: React.FC = () => {
    const [isCollapsed, setIsCollapsed] = React.useState(false);

    return (
        <div className="flex h-screen bg-gray-50 dark:bg-gray-900 overflow-hidden">
            <GlobalShortcuts />
            <WelcomeTour />
            <Sidebar isCollapsed={isCollapsed} setIsCollapsed={setIsCollapsed} />
            <div className="flex-1 flex flex-col h-full overflow-hidden transition-all duration-300 min-w-0 min-h-0">
                <HeaderProfessional />
                {/* On mobile, add padding bottom equal to the bottom navigation height (approx 4rem = 64px) plus safe area */}
                <main className="flex-1 overflow-y-auto p-4 md:p-6 pb-[calc(4rem+env(safe-area-inset-bottom))] md:pb-6 min-h-0">
                    <Outlet />
                </main>
                {/* Desktop Footer (Hidden on mobile to avoid clutter) */}
                <div className="hidden md:block">
                    <FootPage />
                </div>
            </div>
            <BottomNavigation />
        </div>
    );
};

export default MainLayout;
