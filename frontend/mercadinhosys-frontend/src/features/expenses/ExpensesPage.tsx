import React from 'react';
import { FileText } from 'lucide-react';

const ExpensesPage: React.FC = () => {
    return (
        <div className="space-y-6">
            <div className="flex items-center space-x-4">
                <div className="p-3 bg-yellow-500 rounded-lg">
                    <FileText className="w-8 h-8 text-white" />
                </div>
                <div>
                    <h1 className="text-2xl font-bold text-gray-800 dark:text-white">
                        Gestão de Despesas
                    </h1>
                    <p className="text-gray-600 dark:text-gray-400">
                        Controle as despesas e custos do seu estabelecimento
                    </p>
                </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-8 text-center">
                <FileText className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
                <h2 className="text-xl font-semibold text-gray-700 dark:text-gray-300 mb-2">
                    Página em Desenvolvimento
                </h2>
                <p className="text-gray-500 dark:text-gray-400">
                    Em breve você poderá gerenciar suas despesas aqui.
                </p>
            </div>
        </div>
    );
};

export default ExpensesPage;