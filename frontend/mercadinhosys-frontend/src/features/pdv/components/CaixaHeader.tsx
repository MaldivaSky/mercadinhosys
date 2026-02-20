import React, { useState, useEffect } from 'react';
import { User, TrendingUp, DollarSign, ShoppingBag, Clock } from 'lucide-react';
import { pdvService } from '../pdvService';
import { formatCurrency } from '../../../utils/formatters';

interface CaixaHeaderProps {
    funcionarioNome?: string;
    funcionarioRole?: string;
    /** Quando muda, força novo carregamento das estatísticas (ex: após finalizar venda) */
    refreshKey?: number | string;
}

const CaixaHeader: React.FC<CaixaHeaderProps> = ({ funcionarioNome, funcionarioRole, refreshKey }) => {
    const [stats, setStats] = useState<any>(null);
    const [horaAtual, setHoraAtual] = useState(new Date());

    // Atualizar relógio a cada segundo
    useEffect(() => {
        const interval = setInterval(() => {
            setHoraAtual(new Date());
        }, 1000);

        return () => clearInterval(interval);
    }, []);

    // Carregar estatísticas do dia (e quando refreshKey muda, ex: após venda)
    useEffect(() => {
        const carregarStats = async () => {
            try {
                const data = await pdvService.getEstatisticasRapidas();
                setStats(data);
            } catch (error: any) {
                console.error('❌ Erro ao carregar estatísticas:', error);
                if (error.code !== 'ERR_NETWORK') {
                    console.warn('Estatísticas indisponíveis:', error.message);
                }
            }
        };

        carregarStats();

        // Atualizar a cada 30 segundos
        const interval = setInterval(carregarStats, 30000);
        return () => clearInterval(interval);
    }, [refreshKey]);

    const formatarHora = (data: Date) => {
        return data.toLocaleTimeString('pt-BR', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    };

    const formatarData = (data: Date) => {
        return data.toLocaleDateString('pt-BR', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    };

    return (
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 dark:from-blue-800 dark:to-blue-900 text-white rounded-xl shadow-lg p-4 md:p-6 mb-6">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4">
                {/* Informações do Caixa */}
                <div className="flex items-center space-x-4">
                    <div className="p-4 bg-white bg-opacity-20 rounded-xl backdrop-blur-sm">
                        <User className="w-8 h-8" />
                    </div>
                    <div>
                        <div className="flex flex-wrap items-center gap-2">
                            <h2 className="text-xl md:text-2xl font-bold truncate max-w-[200px] md:max-w-none">
                                {funcionarioNome || 'Carregando...'}
                            </h2>
                            {funcionarioRole && (
                                <span className="px-3 py-1 bg-white bg-opacity-20 rounded-full text-xs md:text-sm font-medium uppercase tracking-wider">
                                    {funcionarioRole}
                                </span>
                            )}
                        </div>
                        <p className="text-blue-100 mt-1 text-xs md:text-sm flex items-center">
                            <Clock className="w-3 h-3 mr-1 md:hidden" />
                            {formatarData(horaAtual)}
                        </p>
                    </div>
                </div>

                {/* Relógio */}
                <div className="flex items-center space-x-2 bg-white bg-opacity-20 px-4 md:px-6 py-2 md:py-3 rounded-xl backdrop-blur-sm w-full md:w-auto justify-center md:justify-start">
                    <Clock className="w-5 h-5 md:w-6 md:h-6" />
                    <span className="text-2xl md:text-3xl font-bold font-mono">
                        {formatarHora(horaAtual)}
                    </span>
                </div>
            </div>

            {/* Estatísticas do Dia */}
            {stats && (
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 md:gap-4 mt-6">
                    <div className="bg-white bg-opacity-10 rounded-lg p-4 backdrop-blur-sm">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-blue-100 text-sm">Vendas Hoje</p>
                                <p className="text-2xl font-bold mt-1">
                                    {stats.total_vendas || 0}
                                </p>
                            </div>
                            <div className="p-3 bg-white bg-opacity-20 rounded-lg">
                                <ShoppingBag className="w-6 h-6" />
                            </div>
                        </div>
                    </div>

                    <div className="bg-white bg-opacity-10 rounded-lg p-4 backdrop-blur-sm">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-blue-100 text-sm">Faturamento</p>
                                <p className="text-2xl font-bold mt-1">
                                    {formatCurrency(stats.faturamento || 0)}
                                </p>
                            </div>
                            <div className="p-3 bg-white bg-opacity-20 rounded-lg">
                                <DollarSign className="w-6 h-6" />
                            </div>
                        </div>
                    </div>

                    <div className="bg-white bg-opacity-10 rounded-lg p-4 backdrop-blur-sm">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-blue-100 text-sm">Ticket Médio</p>
                                <p className="text-2xl font-bold mt-1">
                                    {formatCurrency(stats.ticket_medio || 0)}
                                </p>
                            </div>
                            <div className="p-3 bg-white bg-opacity-20 rounded-lg">
                                <TrendingUp className="w-6 h-6" />
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default CaixaHeader;
