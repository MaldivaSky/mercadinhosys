import { Package, AlertTriangle, ArrowDownRight, ArrowUpRight } from 'lucide-react';
import { formatCurrency } from '../../../../utils/formatters';

interface InventoryTabProps {
  data: any;
}

export default function InventoryTab({ data }: InventoryTabProps) {
  const inventoryValue = data?.inventory?.total_value?.value || data?.inventory?.valor_total || 0;
  const abc = data?.inventory?.abc_analysis || data?.abc || {};
  
  // Extract products
  const topProducts = data?.top_products || [];
  
  // Try to use backend expiring products or slow products
  const slowProducts = data?.produtos_lentos || [];
  
  return (
    <div className="space-y-8">
      {/* Resumo Estoque */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-800/60 rounded-2xl p-6 border border-slate-700/60">
          <div className="flex items-center gap-3 mb-4">
             <div className="p-2 bg-blue-500/20 rounded-lg"><Package className="text-blue-400" /></div>
             <h3 className="text-slate-300 font-bold">Valor Total em Estoque</h3>
          </div>
          <div className="text-3xl font-black text-white">{formatCurrency(inventoryValue)}</div>
          <p className="text-sm text-slate-400 mt-2 font-medium">Capital alocado em mercadorias</p>
        </div>
        
        <div className="bg-slate-800/60 rounded-2xl p-6 border border-slate-700/60">
          <div className="flex items-center gap-3 mb-4">
             <div className="p-2 bg-amber-500/20 rounded-lg"><AlertTriangle className="text-amber-400" /></div>
             <h3 className="text-slate-300 font-bold">Ruptura (Falta de Estoque)</h3>
          </div>
          <div className="text-3xl font-black text-amber-400">{data?.inventory?.low_stock_alert?.value || 0}</div>
          <p className="text-sm text-amber-500/70 mt-2 font-medium">Produtos precisando de reposição</p>
        </div>

        <div className="bg-slate-800/60 rounded-2xl p-6 border border-slate-700/60">
          <div className="flex items-center gap-3 mb-4">
             <div className="p-2 bg-red-500/20 rounded-lg"><ArrowDownRight className="text-red-400" /></div>
             <h3 className="text-slate-300 font-bold">Estoque Parado (Classe C)</h3>
          </div>
          <div className="text-3xl font-black text-white">{formatCurrency(abc?.resumo?.C?.faturamento_total || 0)}</div>
          <p className="text-sm text-slate-400 mt-2 font-medium">Mercadoria de baixo giro</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Top Produtos (Classe A) */}
        <div className="bg-slate-800/60 rounded-3xl border border-slate-700/60 overflow-hidden">
          <div className="p-6 border-b border-slate-700/60 bg-slate-800/80">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
               <ArrowUpRight className="text-emerald-400" /> Curva A (Trazem Dinheiro)
            </h2>
          </div>
          <div className="p-6">
            <div className="space-y-4">
               {topProducts.slice(0, 5).map((p: any, i: number) => (
                 <div key={i} className="flex justify-between items-center p-4 bg-slate-800/80 rounded-xl border border-slate-700/50">
                   <div>
                     <p className="font-bold text-white">{p.nome || p.produto_nome}</p>
                     <p className="text-xs text-slate-400 mt-1">Vendidos: {p.quantidade_vendida || p.quantidade} un</p>
                   </div>
                   <div className="text-right">
                     <p className="font-bold text-emerald-400">{formatCurrency(p.faturamento || p.valor_total || 0)}</p>
                   </div>
                 </div>
               ))}
               {topProducts.length === 0 && <p className="text-slate-500">Dados não disponíveis.</p>}
            </div>
          </div>
        </div>

        {/* Produtos Lentos (O que Queimar) */}
        <div className="bg-slate-800/60 rounded-3xl border border-slate-700/60 overflow-hidden">
          <div className="p-6 border-b border-slate-700/60 bg-slate-800/80 flex justify-between items-center">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
               <ArrowDownRight className="text-red-400" /> Curva C (Fazer Promoção)
            </h2>
            <button className="text-xs font-bold text-blue-400 bg-blue-500/10 px-3 py-1 rounded-lg">Ação Rápida</button>
          </div>
          <div className="p-6">
            <div className="space-y-4">
               {slowProducts.slice(0, 5).map((p: any, i: number) => (
                 <div key={i} className="flex justify-between items-center p-4 bg-slate-800/80 rounded-xl border border-slate-700/50">
                   <div>
                     <p className="font-bold text-white">{p.nome}</p>
                     <p className="text-xs text-slate-400 mt-1">Estoque: {p.estoque_atual} un • Dias Parado: {p.dias_estoque}</p>
                   </div>
                   <div className="text-right">
                     <p className="font-bold text-red-400">{formatCurrency(p.custo_parado || 0)}</p>
                     <button className="text-[10px] mt-1 bg-white/10 px-2 py-0.5 rounded text-slate-300 hover:bg-white/20">Criar Promocão</button>
                   </div>
                 </div>
               ))}
               {slowProducts.length === 0 && <p className="text-slate-500">Nenhum produto lento detectado.</p>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
