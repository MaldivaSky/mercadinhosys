import React from 'react';
import { BarChart3 } from 'lucide-react';

const ReportsPage: React.FC = () => {
    return (
        <div className="space-y-6">
            <div className="flex items-center space-x-4">
                <div className="p-3 bg-indigo-500 rounded-lg">
                    <BarChart3 className="w-8 h-8 text-white" />
                </div>
                <div>
                    <h1 className="text-2xl font-bold text-gray-800 dark:text-white">
                        Relatórios e Análises
                    </h1>
                    <p className="text-gray-600 dark:text-gray-400">
                        Relatórios detalhados e análises do seu negócio
                    </p>
                </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-8 text-center">
                <BarChart3 className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
                <h2 className="text-xl font-semibold text-gray-700 dark:text-gray-300 mb-2">
                    Página em Desenvolvimento
                </h2>
                <p className="text-gray-500 dark:text-gray-400">
                    Em breve você terá acesso a relatórios completos aqui.
                </p>
            </div>
        </div>
    );
};

export default ReportsPage;