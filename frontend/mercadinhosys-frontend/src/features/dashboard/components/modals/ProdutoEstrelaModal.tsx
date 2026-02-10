import React from 'react';
import { X, Star, DollarSign, Target, TrendingUp, AlertCircle } from 'lucide-react';

interface ProdutoEstrelaModalProps {
  produto: any;
  periodoDias: number;
  isOpen: boolean;
  onClose: () => void;
}

export const ProdutoEstrelaModal: React.FC<ProdutoEstrelaModalProps> = ({
  produto,
  periodoDias,
  isOpen,
  onClose
}) => {
  if (!isOpen || !produto) return null;

  const precoVenda = produto.faturamento / produto.quantidade_vendida;
  const lucroTotal = produto.faturamento - (produto.custo_unitario * produto.quantidade_vendida);
  const lucroPorUnidade = precoVenda - produto.custo_unitario;
  const demandaDiaria = produto.quantidade_vendida / periodoDias;
  const estoqueRecomendado = Math.ceil(demandaDiaria * 15);
  const pontoReposicao = Math.ceil(demandaDiaria * 7);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gradient-to-r from-yellow-50 to-orange-50 sticky top-0 z-10">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-r from-yellow-500 to-orange-500 rounded-lg flex items-center justify-center">
              <Star className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">⭐ {produto.nome}</h2>
              <p className="text-sm text-gray-600">Produto Estrela - Alta Performance</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white rounded-lg transition-colors"
          >
            <X className="w-6 h-6 text-gray-600" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Métricas Principais */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl p-4 border border-green-200">
              <p className="text-sm text-green-700 mb-1">💰 Preço de Venda</p>
              <p className="text-2xl font-bold text-green-900">
                R$ {precoVenda.toFixed(2)}
              </p>
            </div>
            <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-xl p-4 border border-blue-200">
              <p className="text-sm text-blue-700 mb-1">📦 Custo Unitário</p>
              <p className="text-2xl font-bold text-blue-900">
                R$ {produto.custo_unitario.toFixed(2)}
              </p>
            </div>
            <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-4 border border-purple-200">
              <p className="text-sm text-purple-700 mb-1">📈 Margem de Lucro</p>
              <p className="text-2xl font-bold text-purple-900">
                {produto.margem.toFixed(1)}%
              </p>
            </div>
            <div className="bg-gradient-to-br from-orange-50 to-red-50 rounded-xl p-4 border border-orange-200">
              <p className="text-sm text-orange-700 mb-1">🎯 Vendas ({periodoDias}d)</p>
              <p className="text-2xl font-bold text-orange-900">
                {produto.quantidade_vendida} un
              </p>
            </div>
          </div>

          {/* Análise Financeira */}
          <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl p-6 border border-green-200">
            <h3 className="font-bold text-green-900 mb-4 flex items-center gap-2">
              <DollarSign className="w-5 h-5" />
              💵 Análise Financeira Detalhada
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white/70 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Faturamento Total</p>
                <p className="text-xl font-bold text-green-700">R$ {produto.faturamento.toFixed(2)}</p>
              </div>
              <div className="bg-white/70 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Lucro Total</p>
                <p className="text-xl font-bold text-blue-700">
                  R$ {lucroTotal.toFixed(2)}
                </p>
              </div>
              <div className="bg-white/70 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Lucro por Unidade</p>
                <p className="text-xl font-bold text-purple-700">
                  R$ {lucroPorUnidade.toFixed(2)}
                </p>
              </div>
            </div>
          </div>

          {/* Plano de Ação */}
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-200">
            <h3 className="font-bold text-blue-900 mb-4 flex items-center gap-2">
              <Target className="w-5 h-5" />
              🎯 Plano de Ação Estratégico
            </h3>
            <div className="space-y-3">
              <div className="bg-white/70 p-4 rounded-lg">
                <p className="font-semibold text-blue-900 mb-2">1. Gestão de Estoque</p>
                <p className="text-sm text-gray-700 mb-2">
                  • <strong>Demanda Diária:</strong> {demandaDiaria.toFixed(1)} unidades/dia
                </p>
                <p className="text-sm text-gray-700 mb-2">
                  • <strong>Estoque Recomendado:</strong> {estoqueRecomendado} unidades (15 dias)
                </p>
                <p className="text-sm text-gray-700">
                  • <strong>Ponto de Reposição:</strong> {pontoReposicao} unidades (7 dias)
                </p>
              </div>
              
              <div className="bg-white/70 p-4 rounded-lg">
                <p className="font-semibold text-green-900 mb-2">2. Estratégia de Precificação</p>
                <p className="text-sm text-gray-700 mb-2">
                  • <strong>Margem Atual:</strong> {produto.margem.toFixed(1)}% - {produto.margem > 30 ? '✅ Excelente' : produto.margem > 20 ? '✅ Boa' : '⚠️ Revisar'}
                </p>
                <p className="text-sm text-gray-700 mb-2">
                  • <strong>Potencial de Aumento:</strong> Teste aumentar 5-10% e monitore vendas
                </p>
                <p className="text-sm text-gray-700">
                  • <strong>Combos Sugeridos:</strong> Crie kits com produtos complementares
                </p>
              </div>
              
              <div className="bg-white/70 p-4 rounded-lg">
                <p className="font-semibold text-purple-900 mb-2">3. Marketing e Exposição</p>
                <p className="text-sm text-gray-700 mb-2">
                  • <strong>Posicionamento:</strong> Coloque em local de destaque (altura dos olhos)
                </p>
                <p className="text-sm text-gray-700 mb-2">
                  • <strong>Promoções:</strong> "Leve 3, Pague 2" para aumentar volume
                </p>
                <p className="text-sm text-gray-700">
                  • <strong>Comunicação:</strong> Destaque como "Mais Vendido" ou "Favorito dos Clientes"
                </p>
              </div>
              
              <div className="bg-white/70 p-4 rounded-lg">
                <p className="font-semibold text-orange-900 mb-2">4. Análise de Fornecedor</p>
                <p className="text-sm text-gray-700 mb-2">
                  • <strong>Negociação:</strong> Com alto volume, negocie desconto de 5-10%
                </p>
                <p className="text-sm text-gray-700 mb-2">
                  • <strong>Pagamento:</strong> Solicite prazo maior (30-45 dias)
                </p>
                <p className="text-sm text-gray-700">
                  • <strong>Alternativas:</strong> Pesquise 2-3 fornecedores para comparar
                </p>
              </div>
            </div>
          </div>

          {/* Projeções */}
          <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl p-6 border border-purple-200">
            <h3 className="font-bold text-purple-900 mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              📊 Projeções e Metas
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-white/70 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-2">Projeção Próximos {periodoDias} Dias</p>
                <p className="text-xl font-bold text-purple-700">
                  {produto.quantidade_vendida} unidades
                </p>
                <p className="text-sm text-gray-600 mt-1">
                  Faturamento: R$ {produto.faturamento.toFixed(2)}
                </p>
              </div>
              <div className="bg-white/70 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-2">Meta de Crescimento (+10%)</p>
                <p className="text-xl font-bold text-green-700">
                  {Math.ceil(produto.quantidade_vendida * 1.1)} unidades
                </p>
                <p className="text-sm text-gray-600 mt-1">
                  Faturamento: R$ {(produto.faturamento * 1.1).toFixed(2)}
                </p>
              </div>
            </div>
          </div>

          {/* Alertas */}
          <div className="bg-gradient-to-r from-yellow-50 to-amber-50 rounded-xl p-6 border border-yellow-200">
            <h3 className="font-bold text-yellow-900 mb-4 flex items-center gap-2">
              <AlertCircle className="w-5 h-5" />
              ⚠️ Alertas e Cuidados
            </h3>
            <div className="space-y-2 text-sm text-gray-700">
              <p>• <strong>Ruptura de Estoque:</strong> Nunca deixe faltar! Perda de vendas e clientes.</p>
              <p>• <strong>Validade:</strong> Se perecível, monitore prazo de validade rigorosamente.</p>
              <p>• <strong>Concorrência:</strong> Acompanhe preços dos concorrentes semanalmente.</p>
              <p>• <strong>Sazonalidade:</strong> Produto pode ter variação sazonal - ajuste estoque.</p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 p-6 border-t border-gray-200 bg-gray-50 sticky bottom-0">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-white text-gray-700 rounded-lg hover:bg-gray-100 transition-colors font-medium border border-gray-300"
          >
            Fechar
          </button>
          <button
            onClick={() => {
              const plano = `PLANO DE AÇÃO - ${produto.nome}\n\n` +
                `📊 MÉTRICAS:\n` +
                `• Preço: R$ ${precoVenda.toFixed(2)}\n` +
                `• Custo: R$ ${produto.custo_unitario.toFixed(2)}\n` +
                `• Margem: ${produto.margem.toFixed(1)}%\n` +
                `• Vendas: ${produto.quantidade_vendida} un\n\n` +
                `🎯 AÇÕES:\n` +
                `1. Manter estoque de ${estoqueRecomendado} unidades\n` +
                `2. Repor quando atingir ${pontoReposicao} unidades\n` +
                `3. Posicionar em local de destaque\n` +
                `4. Negociar desconto com fornecedor`;
              
              navigator.clipboard.writeText(plano);
              alert('Plano de ação copiado para área de transferência!');
            }}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            📄 Copiar Plano
          </button>
        </div>
      </div>
    </div>
  );
};
