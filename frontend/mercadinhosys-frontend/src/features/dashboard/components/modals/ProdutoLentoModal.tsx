import React from 'react';
import { X, AlertTriangle, DollarSign, Target, ChartBar, Lightbulb } from 'lucide-react';

interface ProdutoLentoModalProps {
  produto: any;
  isOpen: boolean;
  onClose: () => void;
}

export const ProdutoLentoModal: React.FC<ProdutoLentoModalProps> = ({
  produto,
  isOpen,
  onClose
}) => {
  if (!isOpen || !produto) return null;

  const recuperacao70 = produto.custo_parado * 0.7;
  const beneficioLiquido = recuperacao70 - produto.perda_mensal;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gradient-to-r from-red-50 to-pink-50 sticky top-0 z-10">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-r from-red-500 to-pink-500 rounded-lg flex items-center justify-center">
              <AlertTriangle className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">⚠️ {produto.nome}</h2>
              <p className="text-sm text-gray-600">Produto Lento - Requer Ação Imediata</p>
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
          {/* Diagnóstico do Problema */}
          <div className="bg-gradient-to-r from-red-50 to-pink-50 rounded-xl p-6 border border-red-200">
            <h3 className="font-bold text-red-900 mb-4 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5" />
              🔍 Diagnóstico do Problema
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-white/70 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Estoque Parado</p>
                <p className="text-2xl font-bold text-red-700">{produto.estoque_atual} un</p>
              </div>
              <div className="bg-white/70 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Capital Parado</p>
                <p className="text-2xl font-bold text-orange-700">R$ {produto.custo_parado.toFixed(2)}</p>
              </div>
              <div className="bg-white/70 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Perda Mensal</p>
                <p className="text-2xl font-bold text-red-700">R$ {produto.perda_mensal.toFixed(2)}</p>
              </div>
              <div className="bg-white/70 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Giro de Estoque</p>
                <p className="text-2xl font-bold text-purple-700">{produto.giro_estoque.toFixed(2)}x</p>
              </div>
            </div>
            <div className="mt-4 bg-red-100 border border-red-300 rounded-lg p-4">
              <p className="text-sm text-red-900">
                <strong>⚠️ Alerta:</strong> Este produto está consumindo capital que poderia ser investido em produtos mais rentáveis. 
                Tempo estimado para vender estoque atual: <strong>{produto.dias_estoque} dias</strong>
              </p>
            </div>
          </div>

          {/* Estratégias de Liquidação */}
          <div className="bg-gradient-to-r from-orange-50 to-yellow-50 rounded-xl p-6 border border-orange-200">
            <h3 className="font-bold text-orange-900 mb-4 flex items-center gap-2">
              <Target className="w-5 h-5" />
              🎯 Estratégias de Liquidação (Prioridade Alta)
            </h3>
            <div className="space-y-3">
              <div className="bg-white/70 p-4 rounded-lg border-l-4 border-red-500">
                <p className="font-semibold text-red-900 mb-2">1. Promoção Relâmpago (Ação Imediata)</p>
                <p className="text-sm text-gray-700 mb-2">
                  • <strong>Desconto Sugerido:</strong> 30-40% OFF por 7 dias
                </p>
                <p className="text-sm text-gray-700 mb-2">
                  • <strong>Comunicação:</strong> "Queima de Estoque - Últimas Unidades!"
                </p>
                <p className="text-sm text-gray-700">
                  • <strong>Meta:</strong> Vender pelo menos 50% do estoque em 1 semana
                </p>
              </div>
              
              <div className="bg-white/70 p-4 rounded-lg border-l-4 border-orange-500">
                <p className="font-semibold text-orange-900 mb-2">2. Combos Estratégicos</p>
                <p className="text-sm text-gray-700 mb-2">
                  • <strong>Combo 1:</strong> "Leve este produto + Produto Estrela" com 20% OFF
                </p>
                <p className="text-sm text-gray-700 mb-2">
                  • <strong>Combo 2:</strong> "Leve 2, Pague 1,5" (50% OFF na 2ª unidade)
                </p>
                <p className="text-sm text-gray-700">
                  • <strong>Posicionamento:</strong> Coloque ao lado de produtos de alta rotação
                </p>
              </div>
              
              <div className="bg-white/70 p-4 rounded-lg border-l-4 border-yellow-500">
                <p className="font-semibold text-yellow-900 mb-2">3. Programa de Fidelidade</p>
                <p className="text-sm text-gray-700 mb-2">
                  • <strong>Pontos Dobrados:</strong> Ganhe 2x pontos comprando este produto
                </p>
                <p className="text-sm text-gray-700 mb-2">
                  • <strong>Brinde:</strong> Na compra de 3 unidades, ganhe 1 grátis
                </p>
                <p className="text-sm text-gray-700">
                  • <strong>Sorteio:</strong> Cada compra = 1 cupom para sorteio mensal
                </p>
              </div>
              
              <div className="bg-white/70 p-4 rounded-lg border-l-4 border-green-500">
                <p className="font-semibold text-green-900 mb-2">4. Venda para Clientes VIP</p>
                <p className="text-sm text-gray-700 mb-2">
                  • <strong>WhatsApp:</strong> Envie oferta exclusiva para top 20 clientes
                </p>
                <p className="text-sm text-gray-700 mb-2">
                  • <strong>Mensagem:</strong> "Oferta VIP só para você: {produto.nome} com 35% OFF"
                </p>
                <p className="text-sm text-gray-700">
                  • <strong>Urgência:</strong> "Válido apenas hoje até 18h"
                </p>
              </div>
            </div>
          </div>

          {/* Análise Financeira da Liquidação */}
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-200">
            <h3 className="font-bold text-blue-900 mb-4 flex items-center gap-2">
              <DollarSign className="w-5 h-5" />
              💰 Análise Financeira da Liquidação
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white/70 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-2">Cenário Atual (Sem Ação)</p>
                <p className="text-xl font-bold text-red-700">
                  - R$ {produto.perda_mensal.toFixed(2)}/mês
                </p>
                <p className="text-xs text-gray-600 mt-1">Perda de oportunidade</p>
              </div>
              <div className="bg-white/70 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-2">Com Desconto 30%</p>
                <p className="text-xl font-bold text-orange-700">
                  R$ {recuperacao70.toFixed(2)}
                </p>
                <p className="text-xs text-gray-600 mt-1">Recuperação de 70% do capital</p>
              </div>
              <div className="bg-white/70 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-2">Benefício Líquido</p>
                <p className="text-xl font-bold text-green-700">
                  + R$ {beneficioLiquido.toFixed(2)}
                </p>
                <p className="text-xs text-gray-600 mt-1">Vs. manter estoque parado</p>
              </div>
            </div>
          </div>

          {/* Plano de Ação Passo a Passo */}
          <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl p-6 border border-purple-200">
            <h3 className="font-bold text-purple-900 mb-4 flex items-center gap-2">
              <ChartBar className="w-5 h-5" />
              📋 Plano de Ação - Próximos 7 Dias
            </h3>
            <div className="space-y-3">
              <div className="flex items-start gap-3 bg-white/70 p-3 rounded-lg">
                <div className="w-8 h-8 bg-purple-500 text-white rounded-full flex items-center justify-center font-bold flex-shrink-0">1</div>
                <div>
                  <p className="font-semibold text-gray-900">Dia 1-2: Preparação</p>
                  <p className="text-sm text-gray-700">Crie material de divulgação, defina desconto, treine equipe</p>
                </div>
              </div>
              <div className="flex items-start gap-3 bg-white/70 p-3 rounded-lg">
                <div className="w-8 h-8 bg-purple-500 text-white rounded-full flex items-center justify-center font-bold flex-shrink-0">2</div>
                <div>
                  <p className="font-semibold text-gray-900">Dia 3-5: Lançamento</p>
                  <p className="text-sm text-gray-700">Envie WhatsApp para clientes VIP, coloque cartazes na loja</p>
                </div>
              </div>
              <div className="flex items-start gap-3 bg-white/70 p-3 rounded-lg">
                <div className="w-8 h-8 bg-purple-500 text-white rounded-full flex items-center justify-center font-bold flex-shrink-0">3</div>
                <div>
                  <p className="font-semibold text-gray-900">Dia 6-7: Intensificação</p>
                  <p className="text-sm text-gray-700">Se não atingir meta, aumente desconto para 40-50%</p>
                </div>
              </div>
            </div>
          </div>

          {/* Decisão Final */}
          <div className="bg-gradient-to-r from-gray-50 to-slate-50 rounded-xl p-6 border border-gray-300">
            <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5" />
              ⚖️ Decisão Final (Se Não Vender)
            </h3>
            <div className="space-y-2 text-sm text-gray-700">
              <p>• <strong>Doação:</strong> Doe para instituições e obtenha benefício fiscal</p>
              <p>• <strong>Troca com Fornecedor:</strong> Negocie troca por produtos de maior giro</p>
              <p>• <strong>Venda em Lote:</strong> Venda todo estoque para outro comerciante com desconto maior</p>
              <p>• <strong>Última Opção:</strong> Descarte responsável e aprenda com o erro</p>
            </div>
          </div>

          {/* Lições Aprendidas */}
          <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl p-6 border border-green-200">
            <h3 className="font-bold text-green-900 mb-4 flex items-center gap-2">
              <Lightbulb className="w-5 h-5" />
              💡 Lições para Evitar no Futuro
            </h3>
            <div className="space-y-2 text-sm text-gray-700">
              <p>• <strong>Teste Pequeno:</strong> Ao comprar produto novo, comece com quantidade mínima</p>
              <p>• <strong>Análise de Demanda:</strong> Pesquise se clientes realmente querem o produto</p>
              <p>• <strong>Monitoramento:</strong> Acompanhe vendas semanalmente, não mensalmente</p>
              <p>• <strong>Fornecedor Flexível:</strong> Prefira fornecedores que aceitem devolução</p>
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
              const mensagem = `🔥 OFERTA ESPECIAL VIP!\n\n${produto.nome}\n💰 30% OFF - Só hoje!\n\nEstoque limitado. Aproveite!`;
              navigator.clipboard.writeText(mensagem);
              alert('Mensagem copiada! Cole no WhatsApp dos seus clientes VIP.');
            }}
            className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium"
          >
            📱 Copiar Mensagem WhatsApp
          </button>
        </div>
      </div>
    </div>
  );
};
