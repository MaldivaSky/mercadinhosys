// src/features/expenses/components/ResumoFinanceiroPanel.tsx
import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  BadgeDollarSign,
  BarChart3,
  Bell,
  ChevronRight,
  RefreshCw,
  TrendingDown,
  TrendingUp,
  Wallet,
  XCircle,
} from 'lucide-react';
import { expensesService, ResumoFinanceiro, AlertaFinanceiro } from '../expensesService';

function formatCurrency(value: number) {
  return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

interface ResumoFinanceiroPanelProps {
  className?: string;
}

const ResumoFinanceiroPanel: React.FC<ResumoFinanceiroPanelProps> = ({ className = '' }) => {
  const [resumo, setResumo] = useState<ResumoFinanceiro | null>(null);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [expandido, setExpandido] = useState(true);

  const carregarResumo = async () => {
    setLoading(true);
    setErro(null);
    try {
      const data = await expensesService.resumoFinanceiro();
      setResumo(data);
    } catch (err: any) {
      console.error('Erro ao carregar resumo financeiro:', err);
      setErro('Erro ao carregar dados financeiros');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    carregarResumo();
  }, []);

  const getSeverityColor = (severidade: string) => {
    switch (severidade) {
      case 'critica': return { bg: 'bg-red-50 dark:bg-red-900/30', border: 'border-red-200 dark:border-red-800', text: 'text-red-800 dark:text-red-200', icon: 'text-red-600 dark:text-red-400' };
      case 'alta': return { bg: 'bg-orange-50 dark:bg-orange-900/30', border: 'border-orange-200 dark:border-orange-800', text: 'text-orange-800 dark:text-orange-200', icon: 'text-orange-600 dark:text-orange-400' };
      case 'media': return { bg: 'bg-yellow-50 dark:bg-yellow-900/30', border: 'border-yellow-200 dark:border-yellow-800', text: 'text-yellow-800 dark:text-yellow-200', icon: 'text-yellow-600 dark:text-yellow-400' };
      default: return { bg: 'bg-blue-50 dark:bg-blue-900/30', border: 'border-blue-200 dark:border-blue-800', text: 'text-blue-800 dark:text-blue-200', icon: 'text-blue-600 dark:text-blue-400' };
    }
  };

  const getAlertIcon = (tipo: string) => {
    switch (tipo) {
      case 'boleto_vencido': return XCircle;
      case 'boleto_vencendo': return Bell;
      case 'cliente_inadimplente': return AlertTriangle;
      case 'fluxo_caixa_negativo': return TrendingDown;
      case 'despesas_fixas_altas': return AlertTriangle;
      default: return Bell;
    }
  };

  if (loading) {
    return (
      <div className={`bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 ${className}`}>
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="w-8 h-8 text-blue-600 animate-spin" />
          <span className="ml-3 text-gray-600 dark:text-gray-300">Carregando resumo financeiro...</span>
        </div>
      </div>
    );
  }

  if (erro || !resumo) {
    return (
      <div className={`bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 ${className}`}>
        <div className="text-center py-8">
          <AlertTriangle className="w-12 h-12 text-yellow-500 mx-auto mb-3" />
          <p className="text-gray-600 dark:text-gray-300">{erro || 'Dados indisponíveis'}</p>
          <button
            onClick={carregarResumo}
            className="mt-3 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm transition-colors"
          >
            Tentar Novamente
          </button>
        </div>
      </div>
    );
  }

  const fluxo = resumo.fluxo_caixa_real;
  const fluxoPositivo = fluxo.saldo >= 0;

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
        <div
          className="p-5 flex items-center justify-between cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
          onClick={() => setExpandido(!expandido)}
        >
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl shadow-md">
              <Wallet className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                Painel Financeiro
                <span className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full">V2.0 PRO</span>
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Visão consolidada: contas a pagar, pressão de caixa e saúde financeira
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {resumo.total_alertas > 0 && (
              <span className="flex items-center gap-1.5 px-3 py-1.5 bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300 rounded-full text-sm font-medium animate-pulse">
                <Bell className="w-4 h-4" />
                {resumo.total_alertas} alerta{resumo.total_alertas > 1 ? 's' : ''}
              </span>
            )}
            <button
              onClick={(e) => { e.stopPropagation(); carregarResumo(); }}
              className="p-2 text-gray-400 hover:text-blue-600 transition-colors rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              title="Atualizar"
            >
              <RefreshCw className="w-5 h-5" />
            </button>
            <ChevronRight className={`w-5 h-5 text-gray-400 transition-transform duration-300 ${expandido ? 'rotate-90' : ''}`} />
          </div>
        </div>

        {expandido && (
          <div className="border-t border-gray-100 dark:border-gray-700">
            {/* KPIs Principais */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-0 divide-y sm:divide-y-0 sm:divide-x divide-gray-100 dark:divide-gray-700">
              {/* Contas a Pagar */}
              <div className="p-5 group">
                <div className="flex items-center gap-2 mb-3">
                  <Wallet className="w-5 h-5 text-red-500" />
                  <span className="text-sm font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wide">A Pagar</span>
                </div>
                <div className="text-2xl font-bold text-red-600 dark:text-red-400 mb-1">
                  {formatCurrency(resumo.contas_pagar.total_aberto)}
                </div>
                <div className="space-y-1">
                  {resumo.contas_pagar.qtd_vencidos > 0 && (
                    <div className="flex items-center gap-1.5 text-xs text-red-600 dark:text-red-400 font-medium">
                      <XCircle className="w-3.5 h-3.5" />
                      {resumo.contas_pagar.qtd_vencidos} vencido{resumo.contas_pagar.qtd_vencidos > 1 ? 's' : ''}: {formatCurrency(resumo.contas_pagar.total_vencido)}
                    </div>
                  )}
                  {resumo.contas_pagar.qtd_vence_7d > 0 && (
                    <div className="flex items-center gap-1.5 text-xs text-orange-600 dark:text-orange-400">
                      <Bell className="w-3.5 h-3.5" />
                      {resumo.contas_pagar.qtd_vence_7d} vence{resumo.contas_pagar.qtd_vence_7d > 1 ? 'm' : ''} em 7 dias
                    </div>
                  )}
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    Pago no mes: {formatCurrency(resumo.contas_pagar.pago_no_mes)}
                  </div>
                </div>
              </div>


              {/* Despesas do Mes */}
              <div className="p-5 group">
                <div className="flex items-center gap-2 mb-3">
                  <BadgeDollarSign className="w-5 h-5 text-purple-500" />
                  <span className="text-sm font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wide">Despesas Mes</span>
                </div>
                <div className="text-2xl font-bold text-purple-600 dark:text-purple-400 mb-1">
                  {formatCurrency(resumo.despesas_mes.total)}
                </div>
                <div className="space-y-1">
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    Fixas: {formatCurrency(resumo.despesas_mes.recorrentes)}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    Variaveis: {formatCurrency(resumo.despesas_mes.variaveis)}
                  </div>
                  {resumo.despesas_mes.total > 0 && (
                    <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-1.5 mt-1">
                      <div
                        className="bg-purple-500 h-1.5 rounded-full transition-all"
                        style={{ width: `${Math.min(100, (resumo.despesas_mes.recorrentes / resumo.despesas_mes.total) * 100)}%` }}
                      />
                    </div>
                  )}
                </div>
              </div>

              {/* Fluxo de Caixa */}
              <div className="p-5 group">
                <div className="flex items-center gap-2 mb-3">
                  <BarChart3 className="w-5 h-5 text-blue-500" />
                  <span className="text-sm font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wide">Fluxo de Caixa (Realizado)</span>
                </div>
                <div className={`text-2xl font-bold mb-1 ${fluxoPositivo ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}`}>
                  {fluxoPositivo ? '+' : ''}{formatCurrency(fluxo.saldo)}
                </div>
                <div className="space-y-1">
                  <div className="flex items-center gap-1.5 text-xs text-emerald-600 dark:text-emerald-400">
                    <TrendingUp className="w-3.5 h-3.5" />
                    Entradas: {formatCurrency(fluxo.entradas)}
                  </div>
                  <div className="flex items-center gap-1.5 text-xs text-red-600 dark:text-red-400">
                    <TrendingDown className="w-3.5 h-3.5" />
                    Saidas: {formatCurrency(fluxo.saidas)}
                  </div>
                </div>
              </div>
            </div>

            {/* Monitor de Gestão Owner-First */}
            <div className="px-5 pb-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Indicador 1: Comprometimento de Vendas */}
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-xl p-4 border border-blue-100 dark:border-blue-800/50 shadow-sm relative overflow-hidden group">
                  <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:scale-125 transition-transform">
                    <BarChart3 className="w-12 h-12 text-blue-900 dark:text-blue-100" />
                  </div>
                  <div className="flex items-center justify-between mb-3 relative">
                    <span className="text-[10px] font-black text-blue-800 dark:text-blue-300 uppercase tracking-widest">Comprometimento de Vendas</span>
                    <span className={`text-lg font-black ${resumo.indicadores_gestao.indice_comprometimento > 80 ? 'text-red-600' : 'text-blue-700 dark:text-blue-400'}`}>
                      {resumo.indicadores_gestao.indice_comprometimento.toFixed(1)}%
                    </span>
                  </div>
                  <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full mb-3 overflow-hidden">
                    <div
                      className={`h-full transition-all duration-1000 ${resumo.indicadores_gestao.indice_comprometimento > 80 ? 'bg-red-500' : 'bg-blue-500'}`}
                      style={{ width: `${Math.min(100, resumo.indicadores_gestao.indice_comprometimento)}%` }}
                    />
                  </div>
                  <p className="text-[10px] text-gray-600 dark:text-gray-400 leading-tight">
                    <strong>Relação Dívida/Venda:</strong> Para cada R$ 1,00 que você vende, <strong>{formatCurrency(resumo.indicadores_gestao.indice_comprometimento / 100)}</strong> já está "prometido" a fornecedores.
                  </p>
                </div>

                {/* Indicador 2: Pressão de Caixa Diária */}
                <div className="bg-gradient-to-br from-orange-50 to-red-50 dark:from-orange-900/20 dark:to-red-900/20 rounded-xl p-4 border border-orange-100 dark:border-orange-800/50 shadow-sm relative overflow-hidden group">
                  <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:scale-125 transition-transform">
                    <TrendingDown className="w-12 h-12 text-red-900 dark:text-red-100" />
                  </div>
                  <div className="flex items-center justify-between mb-3 relative">
                    <span className="text-[10px] font-black text-orange-800 dark:text-orange-300 uppercase tracking-widest">Pressão de Caixa (Hoje)</span>
                    <span className={`text-lg font-black ${resumo.indicadores_gestao.pressao_caixa_diaria > 100 ? 'text-red-600' : 'text-orange-700 dark:text-orange-400'}`}>
                      {resumo.indicadores_gestao.pressao_caixa_diaria.toFixed(0)}%
                    </span>
                  </div>
                  <div className="flex items-baseline gap-1 relative">
                    <span className="text-xl font-black text-gray-900 dark:text-white">{formatCurrency(resumo.indicadores_gestao.vence_hoje_valor)}</span>
                    <span className="text-[10px] text-gray-500 uppercase font-bold">Vence Hoje</span>
                  </div>
                  <p className="text-[10px] text-gray-600 dark:text-gray-400 mt-2">
                    {resumo.indicadores_gestao.pressao_caixa_diaria > 100
                      ? "Média de vendas não cobre os boletos de hoje."
                      : `Sua venda média de ${formatCurrency(resumo.indicadores_gestao.venda_media_diaria)} cobre os compromissos de hoje.`}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Alertas Financeiros */}
      {expandido && resumo.alertas.length > 0 && (
        <div className="space-y-2">
          {resumo.alertas.map((alerta: AlertaFinanceiro, idx: number) => {
            const colors = getSeverityColor(alerta.severidade);
            const Icon = getAlertIcon(alerta.tipo);
            return (
              <div
                key={idx}
                className={`${colors.bg} ${colors.border} border rounded-xl p-4 flex items-start gap-3 transition-all hover:shadow-md`}
              >
                <div className={`p-2 rounded-lg ${colors.bg}`}>
                  <Icon className={`w-5 h-5 ${colors.icon}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <h4 className={`font-semibold text-sm ${colors.text}`}>
                      {alerta.titulo}
                    </h4>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${alerta.severidade === 'critica' ? 'bg-red-200 dark:bg-red-800 text-red-800 dark:text-red-200'
                      : alerta.severidade === 'alta' ? 'bg-orange-200 dark:bg-orange-800 text-orange-800 dark:text-orange-200'
                        : 'bg-yellow-200 dark:bg-yellow-800 text-yellow-800 dark:text-yellow-200'
                      }`}>
                      {alerta.severidade}
                    </span>
                  </div>
                  <p className={`text-sm ${colors.text} opacity-80`}>
                    {alerta.descricao}
                  </p>
                  <p className={`text-xs mt-1 ${colors.text} opacity-60 italic`}>
                    {alerta.acao}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default ResumoFinanceiroPanel;
