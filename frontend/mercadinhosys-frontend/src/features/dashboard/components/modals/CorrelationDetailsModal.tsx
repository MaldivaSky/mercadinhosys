import React from 'react';
import { X, TrendingUp, TrendingDown, Link2 } from 'lucide-react';
import { Button } from '../../../../components/ui/button';
import { Badge } from '../../../../components/ui/badge';

interface CorrelationDetailsModalProps {
  correlation: any;
  isOpen: boolean;
  onClose: () => void;
}

export const CorrelationDetailsModal: React.FC<CorrelationDetailsModalProps> = ({
  correlation,
  isOpen,
  onClose
}) => {
  if (!isOpen || !correlation) return null;

  const getCorrelationStrength = (forca: number) => {
    if (Math.abs(forca) >= 0.7) return 'Forte';
    if (Math.abs(forca) >= 0.4) return 'Moderada';
    return 'Fraca';
  };

  const getCorrelationColor = (forca: number) => {
    const absForca = Math.abs(forca);
    if (absForca >= 0.7) return 'text-green-600 bg-green-100 dark:text-green-400 dark:bg-green-900/30';
    if (absForca >= 0.4) return 'text-blue-600 bg-blue-100 dark:text-blue-400 dark:bg-blue-900/30';
    return 'text-gray-600 bg-gray-100 dark:text-gray-400 dark:bg-gray-900/30';
  };

  const getDirectionIcon = (forca: number) => {
    return forca > 0 ? 
      <TrendingUp className="w-4 h-4 text-green-600" /> : 
      <TrendingDown className="w-4 h-4 text-red-600" />;
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-slate-900 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-slate-700">
          <div className="flex items-center gap-3">
            <Link2 className="w-6 h-6 text-blue-600" />
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
              Detalhes da Correlação
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
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-3">Variáveis Correlacionadas</h3>
              <div className="space-y-2">
                <div className="flex items-center justify-between py-2 border-b border-gray-100 dark:border-slate-700">
                  <span className="text-sm font-medium">Variável 1</span>
                  <span className="text-sm text-gray-600 dark:text-gray-300">{correlation.variavel1}</span>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-gray-100 dark:border-slate-700">
                  <span className="text-sm font-medium">Variável 2</span>
                  <span className="text-sm text-gray-600 dark:text-gray-300">{correlation.variavel2}</span>
                </div>
              </div>
            </div>

            <div>
              <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-3">Métrica da Correlação</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Força</span>
                  <Badge className={getCorrelationColor(correlation.forca)}>
                    {getCorrelationStrength(correlation.forca)}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Coeficiente (r)</span>
                  <div className="flex items-center gap-2">
                    {getDirectionIcon(correlation.forca)}
                    <span className="text-sm font-mono">{correlation.forca.toFixed(3)}</span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Direção</span>
                  <span className="text-sm">
                    {correlation.forca > 0 ? 'Positiva' : 'Negativa'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div>
            <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-3">Interpretação</h3>
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <p className="text-sm text-blue-800 dark:text-blue-200">
                {correlation.forca > 0 ? (
                  <>Quando <strong>{correlation.variavel1}</strong> aumenta, <strong>{correlation.variavel2}</strong> tende a aumentar também.</>
                ) : (
                  <>Quando <strong>{correlation.variavel1}</strong> aumenta, <strong>{correlation.variavel2}</strong> tende a diminuir.</>
                )}
              </p>
              <p className="text-xs text-blue-600 dark:text-blue-300 mt-2">
                Força da relação: {getCorrelationStrength(correlation.forca).toLowerCase()}
              </p>
            </div>
          </div>

          {correlation.implicacoes && (
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-3">Implicações Práticas</h3>
              <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
                <p className="text-sm text-green-800 dark:text-green-200">
                  {correlation.implicacoes}
                </p>
              </div>
            </div>
          )}

          {correlation.exemplos && correlation.exemplos.length > 0 && (
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-3">Exemplos Observados</h3>
              <div className="space-y-2">
                {correlation.exemplos.slice(0, 3).map((exemplo: any, index: number) => (
                  <div key={index} className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
                    <p className="text-sm text-gray-700 dark:text-gray-300">{exemplo}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div>
            <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-3">Recomendações</h3>
            <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
              <ul className="text-sm text-amber-800 dark:text-amber-200 space-y-1">
                <li>• Utilize esta correlação para prever comportamentos futuros</li>
                <li>• Considere esta relação no planejamento de estoque e promoções</li>
                <li>• Monitore ambas as variáveis para detectar mudanças no padrão</li>
              </ul>
            </div>
          </div>
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