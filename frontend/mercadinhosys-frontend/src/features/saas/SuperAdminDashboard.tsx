// src/features/saas/SuperAdminDashboard.tsx
import React, { useState, useEffect } from 'react';
import { Building2, Users, Package, DollarSign, TrendingUp, Eye, ChevronDown } from 'lucide-react';
import { apiClient } from '../../api/apiClient';
import toast from 'react-hot-toast';

interface Estabelecimento {
    id: number;
    nome_fantasia: string;
    razao_social: string;
    cnpj: string;
    cidade: string;
    estado: string;
    plano: string;
    total_funcionarios: number;
    total_produtos: number;
    total_clientes: number;
    faturamento_total: number;
}

const SuperAdminDashboard: React.FC = () => {
    const [estabelecimentos, setEstabelecimentos] = useState<Estabelecimento[]>([]);
    const [estabelecimentoSelecionado, setEstabelecimentoSelecionado] = useState<Estabelecimento | null>(null);
    const [loading, setLoading] = useState(false);
    const [isDropdownOpen, setIsDropdownOpen] = useState(false);
    const [view, setView] = useState<'overview' | 'estabelecimentos' | 'clientes' | 'financeiro'>('overview');

    useEffect(() => {
        carregarEstabelecimentos();
    }, []);

    const carregarEstabelecimentos = async () => {
        try {
            setLoading(true);
            const response = await apiClient.get('/estabelecimentos');
            if (response.data?.success) {
                const estabs = response.data.estabelecimentos || [];
                setEstabelecimentos(estabs);
                
                // Selecionar o primeiro por padrão
                if (estabs.length > 0 && !estabelecimentoSelecionado) {
                    setEstabelecimentoSelecionado(estabs[0]);
                    toast.success(f'Estabelecimento {estabs[0].nome_fantasia} selecionado');
                }
            }
        } catch (error) {
            toast.error('Erro ao carregar estabelecimentos');
        } finally {
            setLoading(false);
        }
    };

    const handleSelectEstabelecimento = (estabelecimento: Estabelecimento) => {
        setEstabelecimentoSelecionado(estabelecimento);
        setIsDropdownOpen(false);
        toast.success(f'Estabelecimento {estabelecimento.nome_fantasia} selecionado');
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                    <p className="mt-4 text-gray-600 dark:text-gray-400">Carregando estabelecimentos...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
            {/* Header COM seletor VISÍVEL */}
            <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700 sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between h-16">
                        <div className="flex items-center space-x-4">
                            <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                                Super Admin Dashboard
                            </h1>
                            
                            {/* SELETOR DE ESTABELECIMENTOS - VISÍVEL */}
                            <div className="relative">
                                <button
                                    onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                                    className="flex items-center space-x-2 px-4 py-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg shadow-sm border border-blue-200 dark:border-blue-800 hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors"
                                >
                                    <Building2 className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                                    <span className="font-medium text-blue-600 dark:text-blue-400">
                                        {estabelecimentoSelecionado?.nome_fantasia || 'Selecione...'}
                                    </span>
                                    <ChevronDown className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                                </button>
                                
                                {/* Dropdown */}
                                {isDropdownOpen && (
                                    <div className="absolute top-full left-0 mt-1 w-80 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50">
                                        <div className="p-2">
                                            <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
                                                Selecionar Estabelecimento
                                            </h3>
                                            <div className="max-h-60 overflow-y-auto">
                                                {estabelecimentos.map((estabelecimento) => (
                                                    <button
                                                        key={estabelecimento.id}
                                                        onClick={() => handleSelectEstabelecimento(estabelecimento)}
                                                        className={`w-full text-left px-3 py-2 rounded-md transition-colors ${
                                                            estabelecimentoSelecionado?.id === estabelecimento.id
                                                                ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
                                                                : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300'
                                                        }`}
                                                    >
                                                        <div className="font-medium">{estabelecimento.nome_fantasia}</div>
                                                        <div className="text-xs text-gray-500 dark:text-gray-400">
                                                            {estabelecimento.razao_social}
                                                        </div>
                                                    </button>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                        
                        {/* INDICADOR VISUAL DO ESTABELECIMENTO ATUAL */}
                        {estabelecimentoSelecionado && (
                            <div className="flex items-center space-x-2 px-3 py-1 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
                                <Eye className="w-4 h-4 text-green-600 dark:text-green-400" />
                                <span className="text-sm font-medium text-green-600 dark:text-green-400">
                                    Visualizando: {estabelecimentoSelecionado.nome_fantasia}
                                </span>
                            </div>
                        )}
                    </div>
                </div>
            </header>

            {/* Menu de navegação */}
            <nav className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex space-x-8 py-3">
                        <button
                            onClick={() => setView('overview')}
                            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                                view === 'overview' 
                                    ? 'bg-blue-600 text-white' 
                                    : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                            }`}
                        >
                            Overview
                        </button>
                        <button
                            onClick={() => setView('estabelecimentos')}
                            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                                view === 'estabelecimentos' 
                                    ? 'bg-blue-600 text-white' 
                                    : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                            }`}
                        >
                            Estabelecimentos
                        </button>
                        <button
                            onClick={() => setView('clientes')}
                            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                                view === 'clientes' 
                                    ? 'bg-blue-600 text-white' 
                                    : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                            }`}
                        >
                            Clientes SaaS
                        </button>
                        <button
                            onClick={() => setView('financeiro')}
                            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                                view === 'financeiro' 
                                    ? 'bg-blue-600 text-white' 
                                    : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                            }`}
                        >
                            Financeiro
                        </button>
                    </div>
                </div>
            </nav>

            {/* Conteúdo principal */}
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {view === 'overview' && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                            <div className="flex items-center">
                                <Building2 className="w-8 h-8 text-blue-600 dark:text-blue-400" />
                                <div className="ml-4">
                                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Total Estabelecimentos</h3>
                                    <p className="text-2xl font-bold text-gray-900 dark:text-white">{estabelecimentos.length}</p>
                                </div>
                            </div>
                        </div>
                        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                            <div className="flex items-center">
                                <Users className="w-8 h-8 text-green-600 dark:text-green-400" />
                                <div className="ml-4">
                                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Total Usuários</h3>
                                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                                        {estabelecimentos.reduce((sum, est) => sum + (est.total_funcionarios || 0), 0)}
                                    </p>
                                </div>
                            </div>
                        </div>
                        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                            <div className="flex items-center">
                                <Package className="w-8 h-8 text-purple-600 dark:text-purple-400" />
                                <div className="ml-4">
                                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Total Produtos</h3>
                                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                                        {estabelecimentos.reduce((sum, est) => sum + (est.total_produtos || 0), 0)}
                                    </p>
                                </div>
                            </div>
                        </div>
                        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                            <div className="flex items-center">
                                <DollarSign className="w-8 h-8 text-orange-600 dark:text-orange-400" />
                                <div className="ml-4">
                                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Faturamento Total</h3>
                                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                                        R$ {estabelecimentos.reduce((sum, est) => sum + (est.faturamento_total || 0), 0).toLocaleString()}
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {view === 'estabelecimentos' && (
                    <div>
                        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Todos os Estabelecimentos</h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {estabelecimentos.map((estabelecimento) => (
                                <div key={estabelecimento.id} className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 border border-gray-200 dark:border-gray-700">
                                    <div className="flex items-center justify-between mb-4">
                                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                                            {estabelecimento.nome_fantasia}
                                        </h3>
                                        <button
                                            onClick={() => handleSelectEstabelecimento(estabelecimento)}
                                            className="px-3 py-1 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm"
                                        >
                                            Selecionar
                                        </button>
                                    </div>
                                    <div className="space-y-2 text-sm">
                                        <p><span className="font-medium">Razão Social:</span> {estabelecimento.razao_social}</p>
                                        <p><span className="font-medium">CNPJ:</span> {estabelecimento.cnpj}</p>
                                        <p><span className="font-medium">Cidade/Estado:</span> {estabelecimento.cidade}/{estabelecimento.estado}</p>
                                        <div className="grid grid-cols-2 gap-4 mt-4">
                                            <div>
                                                <p className="text-gray-500 dark:text-gray-400">Funcionários: {estabelecimento.total_funcionarios}</p>
                                                <p className="text-gray-500 dark:text-gray-400">Produtos: {estabelecimento.total_produtos}</p>
                                            </div>
                                            <div>
                                                <p className="text-gray-500 dark:text-gray-400">Clientes: {estabelecimento.total_clientes}</p>
                                                <p className="text-gray-500 dark:text-gray-400">Faturamento: R$ {estabelecimento.faturamento_total?.toLocaleString()}</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {view === 'clientes' && (
                    <div>
                        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Clientes SaaS</h2>
                        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                            <p className="text-gray-600 dark:text-gray-400">
                                👥 Gestão de todos os clientes do sistema SaaS
                            </p>
                        </div>
                    </div>
                )}

                {view === 'financeiro' && (
                    <div>
                        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Financeiro SaaS</h2>
                        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                            <p className="text-gray-600 dark:text-gray-400">
                                💰 Gestão financeira de todos os estabelecimentos
                            </p>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
};

export default SuperAdminDashboard;
