
// src/features/saas/EstabelecimentoSelectorDashboard.tsx
import React, { useState, useEffect } from 'react';
import { Building2, Users, Package, DollarSign, TrendingUp, Eye, ArrowLeft } from 'lucide-react';
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

const EstabelecimentoSelectorDashboard: React.FC = () => {
    const [estabelecimentos, setEstabelecimentos] = useState<Estabelecimento[]>([]);
    const [estabelecimentoSelecionado, setEstabelecimentoSelecionado] = useState<Estabelecimento | null>(null);
    const [loading, setLoading] = useState(false);

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
                
                if (estabs.length > 0 && !estabelecimentoSelecionado) {
                    setEstabelecimentoSelecionado(estabs[0]);
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
        toast.success(f'Estabelecimento {estabelecimento.nome_fantasia} selecionado');
    };

    const handleAcessarSistema = () => {
        if (estabelecimentoSelecionado) {
            // Redirecionar para o dashboard do estabelecimento selecionado
            window.location.href = `/dashboard?estabelecimento_id=${estabelecimentoSelecionado.id}`;
        }
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
            {/* Header */}
            <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between h-16">
                        <div className="flex items-center space-x-4">
                            <button
                                onClick={() => window.history.back()}
                                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                            >
                                <ArrowLeft className="w-5 h-5 text-gray-600 dark:text-gray-300" />
                            </button>
                            <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                                Selecionar Estabelecimento
                            </h1>
                        </div>
                        {estabelecimentoSelecionado && (
                            <button
                                onClick={handleAcessarSistema}
                                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                            >
                                Acessar Sistema
                            </button>
                        )}
                    </div>
                </div>
            </header>

            {/* Conteúdo principal */}
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="mb-8">
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                        Escolha o Estabelecimento para Acessar
                    </h2>
                    <p className="text-gray-600 dark:text-gray-400">
                        Como Super Admin, você pode acessar qualquer estabelecimento para gerenciar seus dados.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {estabelecimentos.map((estabelecimento) => (
                        <div 
                            key={estabelecimento.id} 
                            className={`bg-white dark:bg-gray-800 rounded-lg shadow p-6 border-2 cursor-pointer transition-all ${
                                estabelecimentoSelecionado?.id === estabelecimento.id
                                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                            }`}
                            onClick={() => handleSelectEstabelecimento(estabelecimento)}
                        >
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                                    {estabelecimento.nome_fantasia}
                                </h3>
                                {estabelecimentoSelecionado?.id === estabelecimento.id && (
                                    <div className="flex items-center space-x-1 text-green-600 dark:text-green-400">
                                        <Eye className="w-4 h-4" />
                                        <span className="text-sm font-medium">Selecionado</span>
                                    </div>
                                )}
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
                                <div className="mt-4">
                                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                        estabelecimento.plano === 'premium' 
                                            ? 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900/20 dark:text-yellow-400'
                                            : 'bg-gray-100 text-gray-600 dark:bg-gray-900/20 dark:text-gray-400'
                                    }`}>
                                        {estabelecimento.plano}
                                    </span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </main>
        </div>
    );
};

export default EstabelecimentoSelectorDashboard;
