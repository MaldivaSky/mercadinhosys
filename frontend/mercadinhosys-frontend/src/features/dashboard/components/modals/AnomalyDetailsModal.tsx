import React from 'react';
import { X, AlertTriangle, TrendingUp, TrendingDown } from 'lucide-react';
import { Button } from '../../../../components/ui/button';
import { Badge } from '../../../../components/ui/badge';

interface AnomalyDetailsModalProps {
  anomaly: any;
  isOpen: boolean;
  onClose: () => void;
}

export const AnomalyDetailsModal: React.FC<AnomalyDetailsModalProps> = ({
  anomaly,
  isOpen,
  onClose
}) => {
  if (!isOpen || !anomaly) return null;

  const getSeverityColor = (severity: string) => {
    switch (severity?.toLowerCase()) {
      case 'alta': return 'bg-rose-100 text-rose-800 dark:bg-rose-900/30 dark:text-rose-400';
      case 'média': return 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400';
      case 'baixa': return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400';
    }
  };

  const formatCurrency = (val: number) => new Intl.NumberFormat('pt-BR', { 
    style: 'currency', currency: 'BRL' 
  }).format(val);

  const formatNumber = (val: number) => new Intl.NumberFormat('pt-BR').format(val);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-slate-900 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-slate-700">
          <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
            Detalhes da Anomalia
          </h2>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="h-8 w-8"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="p-6 space-y-6">
          {/* Header com Severidade */}
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                {anomaly.tipo || 'Anomalia Detectada'}
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                {anomaly.categoria || 'Monitoramento de Performance'}
              </p>
            </div>
            <Badge className={getSeverityColor(anomaly.severidade)}>
              <AlertTriangle className="w-3 h-3 mr-1" />
              {anomaly.severidade || 'Média'} Severidade
            </Badge>
          </div>

          {/* Descrição da Anomalia */}
          <div>
            <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Descrição</h4>
            <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed">
              {anomaly.descricao || anomaly.mensagem || 
               'O sistema detectou um comportamento incomum nos dados analisados que pode indicar uma oportunidade de melhoria ou um risco potencial.'}
            </p>
          </div>

          {/* Métricas da Anomalia */}
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-900/20">
              <div className="flex items-center gap-2 mb-2">
                <TrendingDown className="w-4 h-4 text-rose-600" />
                <span className="text-sm font-medium text-rose-900 dark:text-rose-100">Desvio Detectado</span>
              </div>
              <p className="text-xl font-bold text-rose-600 dark:text-rose-400">
                {anomaly.desvio ? `${Math.abs(anomaly.desvio).toFixed(1)}%` : 'N/A'}
              </p>
              <p className="text-xs text-rose-600 dark:text-rose-400 mt-1">
                {anomaly.desvio > 0 ? 'Acima' : 'Abaixo'} do esperado
              </p>
            </div>

            <div className="p-4 rounded-xl bg-blue-50 dark:bg-blue-900/20">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="w-4 h-4 text-blue-600" />
                <span className="text-sm font-medium text-blue-900 dark:text-blue-100">Confiança</span>
              </div>
              <p className="text-xl font-bold text-blue-600 dark:text-blue-400">
                {anomaly.confianca ? `${anomaly.confianca}%` : '85%'}
              </p>
              <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                Nível de confiança estatística
              </p>
            </div>
          </div>

          {/* Impacto Financeiro */}
          {anomaly.impacto_estimado && (
            <div className="p-4 rounded-xl bg-amber-50 dark:bg-amber-900/20">
              <h4 className="font-medium text-amber-900 dark:text-amber-100 mb-2">Impacto Financeiro Estimado</h4>
              <p className="text-lg font-bold text-amber-700 dark:text-amber-300">
                {formatCurrency(Math.abs(anomaly.impacto_estimado))}
              </p>
              <p className="text-sm text-amber-600 dark:text-amber-400">
                {anomaly.impacto_estimado > 0 ? 'Oportunidade potencial' : 'Risco potencial'}
              </p>
            </div>
          )}

          {/* Recomendações de Ação */}
          <div>
            <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-3">Ações Recomendadas</h4>
            <div className="space-y-2">
              <div className="flex items-start gap-3 p-3 bg-gray-50 dark:bg-slate-800 rounded-lg">
                <div className="w-2 h-2 bg-indigo-500 rounded-full mt-2"></div>
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {anomaly.acao_recomendada || 'Investigar a causa raiz'}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Ação principal recomendada
                  </p>
                </div>
              </div>
              
              {anomaly.passos_investigacao && anomaly.passos_investigacao.map((passo: string, index: number) => (
                <div key={index} className="flex items-start gap-3 p-3 bg-gray-50 dark:bg-slate-800 rounded-lg">
                  <div className="w-2 h-2 bg-gray-400 rounded-full mt-2"></div>
                  <div>
                    <p className="text-sm text-gray-700 dark:text-gray-300">
                      {passo}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Timeline de Resolução */}
          <div>
            <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-3">Timeline de Resolução</h4>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div className="p-3 rounded-xl bg-green-50 dark:bg-green-900/20">
                <p className="text-sm font-medium text-green-900 dark:text-green-100">Investigação</p>
                <p className="text-lg font-bold text-green-600 dark:text-green-400">1-2</p>
                <p className="text-xs text-green-600 dark:text-green-400">dias</p>
              </div>
              <div className="p-3 rounded-xl bg-blue-50 dark:bg-blue-900/20">
                <p className="text-sm font-medium text-blue-900 dark:text-blue-100">Implementação</p>
                <p className="text-lg font-bold text-blue-600 dark:text-blue-400">3-5</p>
                <p className="text-xs text-blue-600 dark:text-blue-400">dias</p>
              </div>
              <div className="p-3 rounded-xl bg-purple-50 dark:bg-purple-900/20">
                <p className="text-sm font-medium text-purple-900 dark:text-purple-100">Monitoramento</p>
                <p className="text-lg font-bold text-purple-600 dark:text-purple-400">5-7</p>
                <p className="text-xs text-purple-600 dark:text-purple-400">dias</p>
              </div>
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-3 p-6 border-t border-gray-200 dark:border-slate-700">
          <Button variant="outline" onClick={onClose}>
            Fechar
          </Button>
          <Button onClick={() => {
            console.log('Anomalia investigada:', anomaly);
            onClose();
          }}>
            Iniciar Investigação
          </Button>
        </div>
      </div>
    </div>
  );
};