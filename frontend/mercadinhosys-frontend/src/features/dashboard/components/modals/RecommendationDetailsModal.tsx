import React from 'react';
import { X, TrendingUp, AlertCircle, Lightbulb } from 'lucide-react';
import { Button } from '../../../../components/ui/button';
import { Badge } from '../../../../components/ui/badge';

interface RecommendationDetailsModalProps {
  recommendation: any;
  isOpen: boolean;
  onClose: () => void;
}

export const RecommendationDetailsModal: React.FC<RecommendationDetailsModalProps> = ({
  recommendation,
  isOpen,
  onClose
}) => {
  if (!isOpen || !recommendation) return null;

  const getIcon = (tipo: string) => {
    switch (tipo?.toLowerCase()) {
      case 'oportunidade': return <TrendingUp className="w-5 h-5 text-green-600" />;
      case 'alerta': return <AlertCircle className="w-5 h-5 text-amber-600" />;
      case 'insight': return <Lightbulb className="w-5 h-5 text-blue-600" />;
      default: return <Lightbulb className="w-5 h-5 text-gray-600" />;
    }
  };

  const formatCurrency = (val: number) => new Intl.NumberFormat('pt-BR', { 
    style: 'currency', currency: 'BRL' 
  }).format(val);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-slate-900 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-slate-700">
          <div className="flex items-center gap-3">
            {getIcon(recommendation.tipo)}
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
              {recommendation.tipo || 'Recomendação'}
            </h2>
          </div>
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
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">Descrição</h3>
            <p className="text-gray-600 dark:text-gray-300">{recommendation.mensagem}</p>
          </div>

          {recommendation.impacto_estimado && (
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">Impacto Estimado</h3>
              <Badge variant="secondary" className="bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
                {formatCurrency(recommendation.impacto_estimado)}
              </Badge>
            </div>
          )}

          {recommendation.produtos_envolvidos && recommendation.produtos_envolvidos.length > 0 && (
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">Produtos Envolvidos</h3>
              <div className="space-y-2">
                {recommendation.produtos_envolvidos.slice(0, 5).map((produto: any, index: number) => (
                  <div key={index} className="flex justify-between items-center py-2 border-b border-gray-100 dark:border-slate-700">
                    <span className="text-sm text-gray-600 dark:text-gray-300">{produto.nome}</span>
                    <Badge variant="outline">{produto.quantidade} unidades</Badge>
                  </div>
                ))}
              </div>
            </div>
          )}

          {recommendation.acao_sugerida && (
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">Ação Sugerida</h3>
              <p className="text-gray-600 dark:text-gray-300">{recommendation.acao_sugerida}</p>
            </div>
          )}

          {recommendation.prazo_sugerido && (
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">Prazo Sugerido</h3>
              <p className="text-gray-600 dark:text-gray-300">{recommendation.prazo_sugerido}</p>
            </div>
          )}
        </div>

        <div className="p-6 border-t border-gray-200 dark:border-slate-700">
          <Button onClick={onClose} className="w-full">
            Fechar
          </Button>
        </div>
      </div>
    </div>
  );
};