import React from 'react';
import { TrendingUp, TrendingDown, Link2 } from 'lucide-react';
import { Button } from '../../../../components/ui/button';
import { Badge } from '../../../../components/ui/badge';
import ResponsiveModal from '../../../../components/ui/ResponsiveModal';

interface CorrelationData {
  variavel1: string;
  variavel2: string;
  forca: number;
  implicacoes?: string;
  exemplos?: string[];
}

interface CorrelationDetailsModalProps {
  correlation: CorrelationData | null;
  isOpen: boolean;
  onClose: () => void;
}

export const CorrelationDetailsModal: React.FC<CorrelationDetailsModalProps> = ({
  correlation,
  isOpen,
  onClose
}) => {
  if (!correlation) return null;

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
    <ResponsiveModal
      isOpen={isOpen}
      onClose={onClose}
      title="Detalhes da Correlação"
      headerIcon={<Link2 className="w-6 h-6 text-white" />}
      headerColor="blue"
      footer={
        <Button onClick={onClose} className="w-full">
          Entendido
        </Button>
      }
    >
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-gray-50 dark:bg-gray-900/50 p-4 rounded-xl border border-gray-100 dark:border-gray-700">
            <h3 className="font-bold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
              <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
              Variáveis Analisadas
            </h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-800">
                <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Variável Principal</span>
                <span className="text-sm font-semibold text-gray-700 dark:text-gray-200">{correlation.variavel1}</span>
              </div>
              <div className="flex items-center justify-between py-2">
                <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Variável Relacionada</span>
                <span className="text-sm font-semibold text-gray-700 dark:text-gray-200">{correlation.variavel2}</span>
              </div>
            </div>
          </div>

          <div className="bg-gray-50 dark:bg-gray-900/50 p-4 rounded-xl border border-gray-100 dark:border-gray-700">
            <h3 className="font-bold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
              <span className="w-2 h-2 bg-indigo-500 rounded-full"></span>
              Métrica Científica
            </h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Força do Elo</span>
                <Badge className={getCorrelationColor(correlation.forca)}>
                  {getCorrelationStrength(correlation.forca)}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Coeficiente (r)</span>
                <div className="flex items-center gap-2">
                  {getDirectionIcon(correlation.forca)}
                  <span className="text-sm font-mono font-bold">{correlation.forca.toFixed(3)}</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Direção</span>
                <span className={`text-sm font-bold ${correlation.forca > 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {correlation.forca > 0 ? 'Positiva (Direta)' : 'Negativa (Inversa)'}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-5 shadow-sm">
          <h3 className="font-bold text-blue-900 dark:text-blue-300 mb-2 flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            Interpretação do Expert
          </h3>
          <p className="text-sm text-blue-800 dark:text-blue-200 leading-relaxed font-medium">
            {correlation.forca > 0 ? (
              <>A análise indica que quando <strong>{correlation.variavel1}</strong> sobe, há uma tendência científica de que <strong>{correlation.variavel2}</strong> acompanhe esse crescimento.</>
            ) : (
              <>Observamos uma relação inversa: quando <strong>{correlation.variavel1}</strong> aumenta, <strong>{correlation.variavel2}</strong> tende a recuar.</>
            )}
          </p>
        </div>

        {correlation.implicacoes && (
          <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl p-5 shadow-sm">
            <h3 className="font-bold text-green-900 dark:text-green-300 mb-2 flex items-center gap-2">
              <Link2 className="w-5 h-5" />
              Implicações Práticas
            </h3>
            <p className="text-sm text-green-800 dark:text-green-200 leading-relaxed font-medium">
              {correlation.implicacoes}
            </p>
          </div>
        )}

        {correlation.exemplos && correlation.exemplos.length > 0 && (
          <div>
            <h3 className="font-bold text-gray-900 dark:text-gray-100 mb-3 ml-1">Observações Reais</h3>
            <div className="space-y-2">
              {correlation.exemplos.slice(0, 3).map((exemplo, index) => (
                <div key={index} className="bg-gray-50/50 dark:bg-gray-800/50 rounded-lg p-3 border border-gray-100 dark:border-gray-700 italic text-sm text-gray-600 dark:text-gray-400">
                  "{exemplo}"
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800/50 rounded-xl p-5">
          <h3 className="font-bold text-amber-900 dark:text-amber-300 mb-3 text-sm uppercase tracking-wider">Ações Recomendadas</h3>
          <ul className="text-sm text-amber-800 dark:text-amber-200 space-y-2">
            <li className="flex items-start gap-2">
              <span className="text-amber-500 mt-1">•</span>
              <span>Use este padrão para prever a demanda futura e ajustar seu estoque preventivamente.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-amber-500 mt-1">•</span>
              <span>Alinhe suas promoções baseando-se no comportamento dessas variáveis correlacionadas.</span>
            </li>
          </ul>
        </div>
      </div>
    </ResponsiveModal>
  );
};