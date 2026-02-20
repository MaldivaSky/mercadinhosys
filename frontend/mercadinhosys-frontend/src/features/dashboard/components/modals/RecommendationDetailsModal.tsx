import React from 'react';
import { TrendingUp, AlertCircle, Lightbulb, Package, Target, Clock } from 'lucide-react';
import { Button } from '../../../../components/ui/button';
import { Badge } from '../../../../components/ui/badge';
import ResponsiveModal from '../../../../components/ui/ResponsiveModal';

interface RecommendationProduct {
  nome: string;
  quantidade: number;
}

interface RecommendationData {
  tipo: 'Oportunidade' | 'Alerta' | 'Insight';
  mensagem: string;
  impacto_estimado?: number;
  produtos_envolvidos?: RecommendationProduct[];
  acao_sugerida?: string;
  prazo_sugerido?: string;
}

interface RecommendationDetailsModalProps {
  recommendation: RecommendationData | null;
  isOpen: boolean;
  onClose: () => void;
}

export const RecommendationDetailsModal: React.FC<RecommendationDetailsModalProps> = ({
  recommendation,
  isOpen,
  onClose
}) => {
  if (!recommendation) return null;

  const getIcon = (tipo: string) => {
    switch (tipo?.toLowerCase()) {
      case 'oportunidade': return <TrendingUp className="w-5 h-5 text-white" />;
      case 'alerta': return <AlertCircle className="w-5 h-5 text-white" />;
      case 'insight': return <Lightbulb className="w-5 h-5 text-white" />;
      default: return <Lightbulb className="w-5 h-5 text-white" />;
    }
  };

  const getHeaderColor = (tipo: string): 'indigo' | 'green' | 'red' | 'purple' | 'blue' => {
    switch (tipo?.toLowerCase()) {
      case 'oportunidade': return 'green';
      case 'alerta': return 'red';
      case 'insight': return 'blue';
      default: return 'indigo';
    }
  };

  const formatCurrency = (val: number) => new Intl.NumberFormat('pt-BR', {
    style: 'currency', currency: 'BRL'
  }).format(val);

  return (
    <ResponsiveModal
      isOpen={isOpen}
      onClose={onClose}
      title="Inteligência de Negócio"
      subtitle={recommendation.tipo || 'Sugestão do Sistema'}
      headerIcon={getIcon(recommendation.tipo)}
      headerColor={getHeaderColor(recommendation.tipo)}
      footer={
        <Button onClick={onClose} className="w-full">
          Compreendido
        </Button>
      }
    >
      <div className="space-y-6">
        <div className="bg-gray-50 dark:bg-gray-900/50 p-5 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-inner">
          <h3 className="text-xs font-black text-gray-400 uppercase tracking-widest mb-3 flex items-center gap-2">
            Insight Estratégico
          </h3>
          <p className="text-lg font-bold text-gray-900 dark:text-gray-100 leading-snug">
            {recommendation.mensagem}
          </p>
        </div>

        {recommendation.impacto_estimado && (
          <div className="flex items-center justify-between p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl">
            <div className="flex items-center gap-3">
              <div className="bg-green-100 dark:bg-green-900/50 p-2 rounded-lg">
                <TrendingUp className="w-5 h-5 text-green-600 dark:text-green-400" />
              </div>
              <span className="text-sm font-bold text-green-900 dark:text-green-300">Potencial de Retorno</span>
            </div>
            <span className="text-xl font-black text-green-600 dark:text-green-400 tabular-nums">
              {formatCurrency(recommendation.impacto_estimado)}
            </span>
          </div>
        )}

        {recommendation.produtos_envolvidos && recommendation.produtos_envolvidos.length > 0 && (
          <div className="space-y-3">
            <h3 className="font-black text-gray-900 dark:text-gray-100 flex items-center gap-2 text-sm uppercase tracking-wider">
              <Package className="w-4 h-4 text-indigo-500" />
              Ativos Relacionados
            </h3>
            <div className="grid grid-cols-1 gap-2">
              {recommendation.produtos_envolvidos.slice(0, 5).map((produto, index) => (
                <div key={index} className="flex justify-between items-center p-3 bg-white dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700 rounded-xl hover:border-indigo-200 dark:hover:border-indigo-800 transition-colors">
                  <span className="text-sm font-semibold text-gray-700 dark:text-gray-200">{produto.nome}</span>
                  <Badge variant="secondary" className="font-bold tabular-nums">
                    {produto.quantidade} un
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
          {recommendation.acao_sugerida && (
            <div className="bg-indigo-50/50 dark:bg-indigo-900/10 p-4 rounded-2xl border border-indigo-100 dark:border-indigo-800/50">
              <h4 className="text-[10px] font-black text-indigo-500 uppercase tracking-widest mb-2 flex items-center gap-1">
                <Target className="w-3 h-3" /> Plano de Ação
              </h4>
              <p className="text-sm text-indigo-900 dark:text-indigo-200 font-bold leading-relaxed">
                {recommendation.acao_sugerida}
              </p>
            </div>
          )}

          {recommendation.prazo_sugerido && (
            <div className="bg-purple-50/50 dark:bg-purple-900/10 p-4 rounded-2xl border border-purple-100 dark:border-purple-800/50">
              <h4 className="text-[10px] font-black text-purple-500 uppercase tracking-widest mb-2 flex items-center gap-1">
                <Clock className="w-3 h-3" /> Prazo Ótimo
              </h4>
              <p className="text-sm text-purple-900 dark:text-purple-200 font-bold leading-relaxed">
                {recommendation.prazo_sugerido}
              </p>
            </div>
          )}
        </div>
      </div>
    </ResponsiveModal>
  );
};
