import React from 'react';
import { Search, Filter, Plus, FileDown, RefreshCw } from 'lucide-react';

interface CustomersCommandToolbarProps {
    searchTerm: string;
    setSearchTerm: (term: string) => void;
    onNewCustomer: () => void;
    onExport: (event: React.MouseEvent<HTMLButtonElement>) => void;
    onSync: () => void;
    syncing: boolean;
    onFilterClick: () => void;
    hasActiveFilters: boolean;
}

const CustomersCommandToolbar: React.FC<CustomersCommandToolbarProps> = ({
    searchTerm,
    setSearchTerm,
    onNewCustomer,
    onExport,
    onSync,
    syncing,
    onFilterClick,
    hasActiveFilters,
}) => {
    return (
        <div className="flex flex-col md:flex-row gap-4 justify-between items-center bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm mb-4">
            <div className="relative w-full md:w-[450px]">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Search className="h-5 w-5 text-slate-400" />
                </div>
                <input
                    type="text"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="Buscar cliente por nome, CPF, email ou telefone..."
                    className="block w-full pl-10 pr-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all sm:text-sm"
                />
            </div>

            <div className="flex items-center gap-2 w-full md:w-auto overflow-x-auto pb-1 md:pb-0 scrollbar-hide">
                <button
                    onClick={onFilterClick}
                    className={`relative inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border text-sm font-medium transition-all ${
                        hasActiveFilters
                            ? 'bg-blue-50 border-blue-200 text-blue-700 dark:bg-blue-900/30 dark:border-blue-800/50 dark:text-blue-400'
                            : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50 dark:bg-slate-900 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800'
                    }`}
                >
                    <Filter className="h-4 w-4" />
                    Filtros
                    {hasActiveFilters && (
                        <span className="absolute -top-1.5 -right-1.5 w-3 h-3 bg-blue-500 rounded-full border-2 border-white dark:border-slate-900" />
                    )}
                </button>

                <div className="h-8 w-px bg-slate-200 dark:bg-slate-800 mx-1 shrink-0" />

                <button
                    onClick={onSync}
                    disabled={syncing}
                    className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 text-sm font-medium transition-all dark:bg-slate-900 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    <RefreshCw className={`h-4 w-4 ${syncing ? 'animate-spin' : ''}`} />
                    <span className="hidden sm:inline">Sincronizar CRM</span>
                </button>

                <button
                    onClick={onExport}
                    className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 text-sm font-medium transition-all dark:bg-slate-900 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
                >
                    <FileDown className="h-4 w-4" />
                    <span className="hidden sm:inline">Exportar</span>
                </button>

                <button
                    onClick={onNewCustomer}
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl border border-transparent bg-blue-600 text-white hover:bg-blue-700 shadow-sm shadow-blue-500/20 text-sm font-bold transition-all active:scale-95 whitespace-nowrap"
                >
                    <Plus className="h-4 w-4" />
                    Novo Cliente
                </button>
            </div>
        </div>
    );
};

export default CustomersCommandToolbar;
