import React, { useMemo } from 'react';
import { 
  X, Lightbulb, CheckCircle, BarChart2 
} from 'lucide-react';
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer
} from 'recharts';

interface CorrelationItem {
  variavel1: string;
  variavel2: string;
  correlacao: number;
  significancia: number;
  insight: string;
  explicacao?: string;
  acoes?: string[];
}

interface CorrelationDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  correlation: CorrelationItem | null;
}

const generateScatterData = (correlation: number, count = 100) => {
  const data = [];
  const slope = correlation;
  const noiseFactor = 30 * (1 - Math.abs(correlation)); // Menos ruído para correlações fortes

  for (let i = 0; i < count; i++) {
    const x = Math.random() * 100;
    // y = mx + c + noise
    // Offset base 50 para evitar negativos
    let y = (slope * x) + 50 + ((Math.random() - 0.5) * noiseFactor);
    
    // Ajuste para visualização ficar bonita (sempre positivo)
    y = Math.max(0, y);
    
    data.push({ x, y });
  }
  return data;
};

export const CorrelationDetailsModal: React.FC<CorrelationDetailsModalProps> = ({ 
  isOpen, onClose, correlation 
}) => {
  if (!isOpen || !correlation) return null;

  const data = useMemo(() => 
    generateScatterData(correlation.correlacao), 
    [correlation]
  );

  const getCorrelationColor = (val: number) => {
    if (Math.abs(val) > 0.7) return '#10b981'; // Verde (Forte)
    if (Math.abs(val) > 0.4) return '#f59e0b'; // Amarelo (Moderada)
    return '#6b7280'; // Cinza (Fraca)
  };

  const strengthText = Math.abs(correlation.correlacao) > 0.7 ? 'Forte' : 
                       Math.abs(correlation.correlacao) > 0.4 ? 'Moderada' : 'Fraca';
  
  const directionText = correlation.correlacao > 0 ? 'Positiva' : 'Negativa';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto flex flex-col">
        
        {/* Header */}
        <div className="p-6 border-b border-gray-100 flex justify-between items-start sticky top-0 bg-white z-10">
          <div>
            <div className="flex items-center gap-2 text-indigo-600 font-bold text-sm uppercase tracking-wider mb-1">
              <BarChart2 className="w-4 h-4" />
              Análise de Correlação
            </div>
            <h2 className="text-2xl font-bold text-gray-900">
              {correlation.variavel1} <span className="text-gray-400">vs</span> {correlation.variavel2}
            </h2>
          </div>
          <button 
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors text-gray-500 hover:text-gray-700"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6 grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Coluna Esquerda: Gráfico */}
          <div className="space-y-6">
            <div className="bg-gray-50 rounded-xl p-6 border border-gray-100 h-[400px]">
              <h3 className="font-bold text-gray-700 mb-4 text-center">Simulação Visual da Correlação</h3>
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis 
                    type="number" 
                    dataKey="x" 
                    name={correlation.variavel1} 
                    unit=" un" 
                    tick={{ fontSize: 12 }}
                  />
                  <YAxis 
                    type="number" 
                    dataKey="y" 
                    name={correlation.variavel2} 
                    unit=" un" 
                    tick={{ fontSize: 12 }}
                  />
                  <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                  <Scatter 
                    name="Amostras" 
                    data={data} 
                    fill={getCorrelationColor(correlation.correlacao)} 
                  />
                </ScatterChart>
              </ResponsiveContainer>
              <p className="text-xs text-center text-gray-400 mt-2">
                * Gráfico gerado via simulação estatística baseada no coeficiente r={correlation.correlacao}
              </p>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="bg-blue-50 p-4 rounded-xl border border-blue-100 text-center">
                <p className="text-sm text-blue-600 font-medium">Coeficiente (r)</p>
                <p className="text-2xl font-bold text-blue-800">{correlation.correlacao}</p>
              </div>
              <div className="bg-purple-50 p-4 rounded-xl border border-purple-100 text-center">
                <p className="text-sm text-purple-600 font-medium">Força</p>
                <p className="text-xl font-bold text-purple-800">{strengthText}</p>
              </div>
              <div className="bg-orange-50 p-4 rounded-xl border border-orange-100 text-center">
                <p className="text-sm text-orange-600 font-medium">Direção</p>
                <p className="text-xl font-bold text-orange-800">{directionText}</p>
              </div>
            </div>
          </div>

          {/* Coluna Direita: Conteúdo Didático */}
          <div className="space-y-6">
            
            {/* O que é */}
            <div className="bg-indigo-50 rounded-xl p-6 border border-indigo-100">
              <h3 className="flex items-center gap-2 font-bold text-indigo-900 mb-3">
                <Lightbulb className="w-5 h-5 text-indigo-600" />
                O que isso significa?
              </h3>
              <p className="text-indigo-800 leading-relaxed">
                {correlation.explicacao || correlation.insight}
              </p>
              <div className="mt-4 pt-4 border-t border-indigo-200 text-sm text-indigo-700">
                <span className="font-semibold">Conceito: </span>
                {correlation.correlacao > 0 
                  ? "Quando uma variável aumenta, a outra também tende a aumentar." 
                  : "Quando uma variável aumenta, a outra tende a diminuir (relação inversa)."}
              </div>
            </div>

            {/* Ações Recomendadas */}
            <div>
              <h3 className="flex items-center gap-2 font-bold text-gray-900 mb-4">
                <CheckCircle className="w-5 h-5 text-green-600" />
                Plano de Ação Recomendado
              </h3>
              {correlation.acoes && correlation.acoes.length > 0 ? (
                <ul className="space-y-3">
                  {correlation.acoes.map((acao, idx) => (
                    <li key={idx} className="flex items-start gap-3 bg-gray-50 p-3 rounded-lg border border-gray-100 hover:border-green-200 transition-colors">
                      <div className="bg-green-100 text-green-700 w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold">
                        {idx + 1}
                      </div>
                      <span className="text-gray-700">{acao}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-gray-500 italic">Nenhuma ação específica listada para esta correlação.</p>
              )}
            </div>

            <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-100 text-sm text-yellow-800">
              <strong>Nota de Significância:</strong> p-valor = {correlation.significancia}. 
              Isso indica que há {((1 - correlation.significancia) * 100).toFixed(1)}% de chance dessa relação ser real e não obra do acaso.
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
};
