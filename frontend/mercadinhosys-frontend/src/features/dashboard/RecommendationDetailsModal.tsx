import React from 'react';
import { X, Target, Layers, CheckCircle, AlertTriangle } from 'lucide-react';
import { ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, BarChart, Bar } from 'recharts';

interface RecommendationItem {
  area: string;
  acao: string;
  impacto_esperado: number;
  complexidade: 'baixa' | 'media' | 'alta';
  esforco?: number; // 1..3
  acoes_detalhadas?: string[];
}

interface RecommendationDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  recommendation: RecommendationItem | null;
}

const complexityToScore = (c: RecommendationItem['complexidade']) => {
  if (c === 'baixa') return 1;
  if (c === 'media') return 2;
  return 3;
};

export const RecommendationDetailsModal: React.FC<RecommendationDetailsModalProps> = ({
  isOpen,
  onClose,
  recommendation
}) => {
  if (!isOpen || !recommendation) return null;

  const valueVsEffort = [
    { x: recommendation.esforco ?? complexityToScore(recommendation.complexidade), y: recommendation.impacto_esperado }
  ];

  const impactoData = [{ name: 'Impacto', valor: recommendation.impacto_esperado }];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-100 flex justify-between items-start sticky top-0 bg-white z-10">
          <div>
            <div className="flex items-center gap-2 text-green-600 font-bold text-sm uppercase tracking-wider mb-1">
              <Target className="w-4 h-4" />
              Recomendação de Otimização
            </div>
            <h2 className="text-2xl font-bold text-gray-900">{recommendation.area}</h2>
            <p className="text-gray-600">{recommendation.acao}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors text-gray-500 hover:text-gray-700"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6 grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="space-y-6">
            <div className="bg-gray-50 rounded-xl p-6 border border-gray-100 h-[240px]">
              <h3 className="font-bold text-gray-700 mb-4 flex items-center gap-2">
                <Layers className="w-5 h-5 text-gray-600" />
                Matriz Valor x Esforço
              </h3>
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis type="number" dataKey="x" name="Esforço" domain={[1, 3]} tick={{ fontSize: 12 }} />
                  <YAxis type="number" dataKey="y" name="Impacto (%)" tick={{ fontSize: 12 }} />
                  <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                  <Scatter data={valueVsEffort} fill="#10b981" />
                </ScatterChart>
              </ResponsiveContainer>
              <p className="text-xs text-center text-gray-400 mt-2">
                * Priorize quadrante de alto impacto e baixo esforço.
              </p>
            </div>

            <div className="bg-green-50 rounded-xl p-6 border border-green-100 h-[160px]">
              <h3 className="font-bold text-green-900 mb-3">Impacto Esperado</h3>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={impactoData} margin={{ top: 10, right: 10, bottom: 10, left: 0 }}>
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="valor" fill="#10b981" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="space-y-6">
            <div className="bg-indigo-50 rounded-xl p-6 border border-indigo-100">
              <h3 className="flex items-center gap-2 font-bold text-indigo-900 mb-3">
                <CheckCircle className="w-5 h-5 text-indigo-600" />
                Passos Recomendados
              </h3>
              {recommendation.acoes_detalhadas && recommendation.acoes_detalhadas.length > 0 ? (
                <ul className="space-y-3">
                  {recommendation.acoes_detalhadas.map((acao, idx) => (
                    <li key={idx} className="flex items-start gap-3 bg-white p-3 rounded-lg border border-indigo-100">
                      <div className="bg-indigo-100 text-indigo-700 w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold">
                        {idx + 1}
                      </div>
                      <span className="text-gray-700">{acao}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-gray-600">Sem passos detalhados informados para esta recomendação.</p>
              )}
              <div className="mt-4 pt-4 border-t border-indigo-200 text-sm text-indigo-700">
                Complexidade: <strong>{recommendation.complexidade.toUpperCase()}</strong> •
                Impacto: <strong>{recommendation.impacto_esperado.toFixed(1)}%</strong>
              </div>
            </div>

            <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-100 text-sm text-yellow-800">
              <AlertTriangle className="w-4 h-4 inline mr-2" />
              Dica: valide rapidamente com um teste pequeno antes de implantar em larga escala.
            </div>
          </div>
        </div>

        <div className="p-6 border-t border-gray-100 bg-gray-50 rounded-b-2xl flex justify-end">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors font-medium"
          >
            Entendi
          </button>
        </div>
      </div>
    </div>
  );
}
