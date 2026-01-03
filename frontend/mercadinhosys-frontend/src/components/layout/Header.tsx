import React from 'react';
import ThemeToggle from '../ui/ThemeToggle';
import { User, Bell } from 'lucide-react';

const Header: React.FC = () => {
    return (
        <header className="sticky top-0 z-50 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
            <div className="px-6 py-4 flex items-center justify-between">
                <div className="flex items-center space-x-4">
                    <h1 className="text-xl font-semibold text-gray-800 dark:text-white">
                        MercadinhoSys
                    </h1>
                </div>

                <div className="flex items-center space-x-4">
                    <button className="p-2 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full">
                        <Bell className="w-5 h-5" />
                    </button>

                    <ThemeToggle />

                    <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                            <User className="w-5 h-5 text-white" />
                        </div>
                        <div className="hidden md:block">
                            <p className="text-sm font-medium text-gray-800 dark:text-white">Usuário Admin</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">Administrador</p>
                        </div>
                    </div>
                </div>
            </div>
        </header>
    );
};

export default Header;