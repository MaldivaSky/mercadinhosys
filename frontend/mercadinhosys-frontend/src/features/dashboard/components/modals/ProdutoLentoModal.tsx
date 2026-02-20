import React from 'react';
import { AlertTriangle, DollarSign, Target, ChartBar, Lightbulb, Clock } from 'lucide-react';
import { Button } from '../../../../components/ui/button';
import ResponsiveModal from '../../../../components/ui/ResponsiveModal';

interface ProdutoLentoData {
  id: number;
  nome: string;
  quantidade: number;
  total_vendido: number;
  dias_estoque: number;
  giro_estoque: number;
  custo_parado: number;
  perda_mensal: number;
  estoque_atual: number;
  margem: number;
}

interface ProdutoLentoModalProps {
  produto: ProdutoLentoData | null;
  isOpen: boolean;
  onClose: () => void;
}

export const ProdutoLentoModal: React.FC<ProdutoLentoModalProps> = ({
  produto,
  isOpen,
  onClose
}) => {
  if (!produto) return null;

  const recuperacao70 = produto.custo_parado * 0.7;
  const beneficioLiquido = recuperacao70 - produto.perda_mensal;

  const handleCopyMessage = () => {
    const mensagem = `🔥 OFERTA ESPECIAL VIP!\n\n${produto.nome}\n💰 30% OFF - Só hoje!\n\nEstoque limitado. Aproveite!`;
    navigator.clipboard.writeText(mensagem);
    alert('Mensagem copiada! Cole no WhatsApp dos seus clientes VIP.');
  };

  return (
    <ResponsiveModal
      isOpen={isOpen}
      onClose={onClose}
      title={produto.nome}
      subtitle="Produto Lento - Requer Ação Imediata"
      headerIcon={<AlertTriangle className="w-6 h-6 text-white" />}
      headerColor="red"
      size="xl"
      footer={
        <div className="flex gap-3 w-full">
          <Button variant="outline" onClick={onClose} className="flex-1">
            Fechar
          </Button>
          <Button onClick={handleCopyMessage} className="flex-1 bg-green-600 hover:bg-green-700 text-white">
            📱 Copiar Mensagem WhatsApp
          </Button>
        </div>
      }
    >
      <div className="space-y-8">
        {/* Diagnóstico de Risco Capital */}
        <div className="bg-rose-50/50 dark:bg-rose-900/10 border border-rose-100 dark:border-rose-800/50 rounded-2xl p-6 shadow-sm">
          <h3 className="font-black text-rose-900 dark:text-rose-400 mb-6 flex items-center gap-2 uppercase tracking-tighter text-lg">
            <AlertTriangle className="w-6 h-6" />
            Vulnerabilidade de Caixa
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {[
              { label: 'Estoque Parado', val: `${produto.estoque_atual} un`, color: 'text-red-700 dark:text-red-400' },
              { label: 'Capital Preso', val: `R$ ${produto.custo_parado.toFixed(2)}`, color: 'text-orange-700 dark:text-orange-400' },
              { label: 'Dreno Mensal', val: `R$ ${produto.perda_mensal.toFixed(2)}`, color: 'text-rose-700 dark:text-rose-400' },
              { label: 'Giro (KPI)', val: `${produto.giro_estoque.toFixed(2)}x`, color: 'text-purple-700 dark:text-purple-400' }
            ].map((item, i) => (
              <div key={i} className="space-y-1">
                <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest">{item.label}</p>
                <p className={`text-xl font-black tabular-nums ${item.color}`}>{item.val}</p>
              </div>
            ))}
          </div>
          <div className="mt-6 p-4 bg-white dark:bg-gray-800 rounded-xl border border-rose-200 dark:border-rose-900 flex items-center gap-4">
            <div className="w-12 h-12 rounded-full bg-rose-100 dark:bg-rose-900 flex items-center justify-center flex-shrink-0">
              <Clock className="w-6 h-6 text-rose-600" />
            </div>
            <p className="text-sm font-bold text-gray-700 dark:text-gray-300">
              Tempo estimado para escoar estoque atual: <span className="text-rose-600 font-black">{produto.dias_estoque} dias</span> no ritmo atual.
            </p>
          </div>
        </div>

        {/* Matriz de Decisão Estratégica */}
        <div className="space-y-4">
          <h3 className="font-black text-gray-900 dark:text-gray-100 flex items-center gap-2 text-lg uppercase tracking-tighter">
            <Target className="w-6 h-6 text-orange-500" />
            Iniciativas de Liquidez
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white dark:bg-gray-800/50 p-5 rounded-2xl border border-gray-100 dark:border-gray-700">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                <p className="font-black text-xs uppercase tracking-widest text-red-600">Flash Sale (Crítico)</p>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-300 font-medium leading-relaxed">
                Aplicar desconto de <strong className="text-gray-900 dark:text-white">35% OFF</strong> por 72h. Foco em clientes da Curva C que buscam preço baixo.
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800/50 p-5 rounded-2xl border border-gray-100 dark:border-gray-700">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                <p className="font-black text-xs uppercase tracking-widest text-orange-600">Product Bundling</p>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-300 font-medium leading-relaxed">
                Criar kit "Essentials" com produto <strong className="text-gray-900 dark:text-white">Estrela</strong>. Escoamento por associação de demanda.
              </p>
            </div>
          </div>
        </div>

        {/* Análise de Recuperação */}
        <div className="bg-blue-50/50 dark:bg-blue-900/10 rounded-2xl p-6 border border-blue-100 dark:border-blue-800">
          <h3 className="font-black text-blue-900 dark:text-blue-300 mb-6 flex items-center gap-2 uppercase tracking-tighter text-lg">
            <DollarSign className="w-6 h-6" />
            Recuperação de Fluxo
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="space-y-1">
              <p className="text-[10px] font-black text-blue-600 uppercase">Cenário Inércia</p>
              <p className="text-xl font-black text-rose-600">- R$ {produto.perda_mensal.toFixed(2)}/mês</p>
              <p className="text-[10px] text-gray-400 font-bold uppercase italic">Custo de oportunidade</p>
            </div>
            <div className="space-y-1">
              <p className="text-[10px] font-black text-blue-600 uppercase">Cenário Ação (30% DESC)</p>
              <p className="text-xl font-black text-orange-600">R$ {recuperacao70.toFixed(2)}</p>
              <p className="text-[10px] text-gray-400 font-bold uppercase italic">Capital Rejetado</p>
            </div>
            <div className="space-y-1">
              <p className="text-[10px] font-black text-blue-600 uppercase">Benefício Líquido</p>
              <p className="text-xl font-black text-green-600">+ R$ {beneficioLiquido.toFixed(2)}</p>
              <p className="text-[10px] text-gray-400 font-bold uppercase italic">Fluxo de Caixa Liberado</p>
            </div>
          </div>
        </div>

        {/* Roadmap de Desmobilização */}
        <div className="space-y-4">
          <h3 className="font-black text-gray-900 dark:text-gray-100 flex items-center gap-2 text-lg uppercase tracking-tighter">
            <ChartBar className="w-6 h-6 text-purple-500" />
            Plano de Escoamento (7 Dias)
          </h3>
          <div className="grid grid-cols-3 gap-2">
            {[
              { d: '48h', t: 'Preparação', s: 'Re-etiquetagem e sinalização' },
              { d: '72h', t: 'Divulgação', s: 'CRM & WhatsApp Marketing' },
              { d: '24h', t: 'Fechamento', s: 'Ajuste de margem agressiva' }
            ].map((step, i) => (
              <div key={i} className="bg-gray-50 dark:bg-gray-900/50 p-4 rounded-2xl border border-gray-100 dark:border-gray-700 text-center">
                <span className="text-purple-600 font-black text-xl">{step.d}</span>
                <p className="text-xs font-black uppercase text-gray-900 dark:text-gray-100 mt-1">{step.t}</p>
                <p className="text-[10px] text-gray-500 font-medium mt-1 leading-tight">{step.s}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Mentoria Preditiva */}
        <div className="bg-emerald-50/50 dark:bg-emerald-900/10 rounded-2xl p-6 border border-emerald-100 dark:border-emerald-800">
          <h3 className="font-black text-emerald-900 dark:text-emerald-400 mb-4 flex items-center gap-2 text-sm uppercase tracking-widest">
            <Lightbulb className="w-5 h-5" />
            Insights de Prevenção
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-3">
            {[
              { t: 'Pilotagem', d: 'Produtos novos devem entrar com 25% da carga normal.' },
              { t: 'Ciclo Audit', d: 'Auditoria de giro deve ser semanal, não mensal.' },
              { t: 'Vendor Logic', d: 'Dar preferência para fornecedores com política de devolução.' },
              { t: 'Focus ABC', d: 'Concentrar 80% do capital no topo da Curva A.' }
            ].map((tip, i) => (
              <div key={i} className="flex gap-3">
                <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full mt-1.5 flex-shrink-0"></div>
                <p className="text-sm text-gray-700 dark:text-gray-300 font-medium">
                  <strong className="text-emerald-900 dark:text-emerald-400">{tip.t}:</strong> {tip.d}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </ResponsiveModal>
  );
};
