import { useState } from 'react';
import { Package, AlertTriangle, ArrowDownRight, ChartBar } from 'lucide-react';
import { formatCurrency } from '../../../../utils/formatters';

interface InventoryTabProps {
  data: any;
}

export default function InventoryTab({ data }: InventoryTabProps) {
  const inventoryValue = data?.inventory?.total_value?.value || data?.inventory?.valor_total || 0;
  const abc = data?.inventory?.abc_analysis || data?.abc || {};
  const abcResumo = abc?.resumo || {};
  
  // Extract products
      
  const totalABC = (abcResumo?.A?.faturamento_total || 0) +
                   (abcResumo?.B?.faturamento_total || 0) +
                   (abcResumo?.C?.faturamento_total || 0);

  const [selectedABC, setSelectedABC] = useState<'all' | 'A' | 'B' | 'C'>('all');

  const filteredProducts = selectedABC === 'all' 
    ? (abc?.produtos || [])
    : (abc?.produtos || []).filter((p: any) => p.classe === selectedABC);

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      
      {/* Resumo Estoque - KPIs Globais */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-800/80 backdrop-blur-xl rounded-3xl p-6 border border-slate-700/60 shadow-xl relative overflow-hidden group hover:border-blue-500/30 transition-colors">
          <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/10 rounded-full blur-3xl group-hover:bg-blue-500/20 transition-all"></div>
          <div className="flex items-center gap-3 mb-4">
             <div className="p-3 bg-blue-500/10 rounded-xl border border-blue-500/20 text-blue-400">
               <Package className="w-5 h-5" />
             </div>
             <h3 className="text-slate-300 font-bold tracking-wide">Capital Imobilizado</h3>
          </div>
          <div className="text-4xl font-black text-white tracking-tight mb-2">
            {formatCurrency(inventoryValue)}
          </div>
          <p className="text-sm text-slate-400 font-medium">Valor total alocado em mercadorias</p>
        </div>
        
        <div className="bg-slate-800/80 backdrop-blur-xl rounded-3xl p-6 border border-slate-700/60 shadow-xl relative overflow-hidden group hover:border-amber-500/30 transition-colors">
          <div className="absolute top-0 right-0 w-32 h-32 bg-amber-500/10 rounded-full blur-3xl group-hover:bg-amber-500/20 transition-all"></div>
          <div className="flex items-center gap-3 mb-4">
             <div className="p-3 bg-amber-500/10 rounded-xl border border-amber-500/20 text-amber-400">
               <AlertTriangle className="w-5 h-5" />
             </div>
             <h3 className="text-slate-300 font-bold tracking-wide">Risco de Ruptura</h3>
          </div>
          <div className="text-4xl font-black text-amber-400 tracking-tight mb-2">
            {data?.inventory?.low_stock_alert?.value || 0} <span className="text-xl text-amber-500/70 font-medium">itens</span>
          </div>
          <p className="text-sm text-slate-400 font-medium">Estoque abaixo da margem de segurança</p>
        </div>

        <div className="bg-slate-800/80 backdrop-blur-xl rounded-3xl p-6 border border-slate-700/60 shadow-xl relative overflow-hidden group hover:border-red-500/30 transition-colors">
          <div className="absolute top-0 right-0 w-32 h-32 bg-red-500/10 rounded-full blur-3xl group-hover:bg-red-500/20 transition-all"></div>
          <div className="flex items-center gap-3 mb-4">
             <div className="p-3 bg-red-500/10 rounded-xl border border-red-500/20 text-red-400">
               <ArrowDownRight className="w-5 h-5" />
             </div>
             <h3 className="text-slate-300 font-bold tracking-wide">Curva C (Lentidão)</h3>
          </div>
          <div className="text-4xl font-black text-white tracking-tight mb-2">
            {formatCurrency(abcResumo?.C?.faturamento_total || 0)}
          </div>
          <p className="text-sm text-slate-400 font-medium">Custo paralisado em baixo giro</p>
        </div>
      </div>

      {/* Curva ABC de Pareto - Reconstrução Detalhada */}
      <div className="bg-slate-800/80 backdrop-blur-xl rounded-3xl border border-slate-700/60 shadow-2xl overflow-hidden">
        
        {/* Header ABC */}
        <div className="p-6 border-b border-slate-700/60 bg-slate-800/90 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-center gap-4">
             <div className="p-3 bg-gradient-to-br from-indigo-400 to-indigo-600 rounded-2xl shadow-lg shadow-indigo-500/20">
               <ChartBar className="w-6 h-6 text-white" />
             </div>
             <div>
               <h2 className="text-xl font-black text-white tracking-tight">Curva ABC de Pareto</h2>
               <p className="text-sm text-slate-400 font-medium mt-1">
                 Análise 80/20 do Estoque • {abc?.pareto_80_20 ? <span className="text-emerald-400 font-bold">Lei Confirmada</span> : <span className="text-amber-400 font-bold">Distribuição Atípica</span>}
               </p>
             </div>
          </div>
          
          {/* Filtros ABC */}
          <div className="flex bg-slate-900/50 p-1 rounded-xl border border-slate-700/50">
             {(['all', 'A', 'B', 'C'] as const).map((classe) => (
               <button
                 key={classe}
                 onClick={() => setSelectedABC(classe)}
                 className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${
                   selectedABC === classe 
                     ? classe === 'A' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                     : classe === 'B' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                     : classe === 'C' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                     : 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
                     : 'text-slate-400 hover:text-white border border-transparent'
                 }`}
               >
                 {classe === 'all' ? 'Todos' : `Curva ${classe}`}
               </button>
             ))}
          </div>
        </div>

        {/* Resumo Estatístico das 3 Classes */}
        <div className="grid grid-cols-1 md:grid-cols-3 border-b border-slate-700/60">
          {(['A', 'B', 'C'] as const).map((classe) => {
             const dados = abcResumo?.[classe];
             const percentual = totalABC > 0 ? (dados?.faturamento_total || 0) / totalABC * 100 : 0;
             const isA = classe === 'A';
             const isB = classe === 'B';
             
             return (
               <div key={classe} className={`p-6 ${classe !== 'C' ? 'border-b md:border-b-0 md:border-r border-slate-700/60' : ''} bg-slate-800/30`}>
                 <div className="flex items-center justify-between mb-4">
                   <div className={`w-10 h-10 rounded-xl flex items-center justify-center font-black text-lg shadow-inner ${
                     isA ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                     isB ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' :
                     'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                   }`}>
                     {classe}
                   </div>
                   <span className={`text-xs font-bold px-3 py-1 rounded-full ${
                     isA ? 'bg-emerald-500/10 text-emerald-400' :
                     isB ? 'bg-blue-500/10 text-blue-400' :
                     'bg-amber-500/10 text-amber-400'
                   }`}>
                     {percentual.toFixed(1)}% do Faturamento
                   </span>
                 </div>
                 
                 <div className="space-y-1">
                   <p className="text-2xl font-black text-white">{formatCurrency(dados?.faturamento_total || 0)}</p>
                   <p className="text-sm text-slate-400 font-medium">Geração de Caixa Absoluta</p>
                 </div>
                 
                 <div className="mt-4 pt-4 border-t border-slate-700/40 flex justify-between text-sm">
                   <span className="text-slate-400">Total de Itens:</span>
                   <span className="text-white font-bold">{dados?.quantidade_produtos || 0} produtos</span>
                 </div>
               </div>
             );
          })}
        </div>

        {/* Tabela de Produtos Detalhada */}
        <div className="p-0 overflow-x-auto max-h-[400px] overflow-y-auto custom-scrollbar">
          {filteredProducts.length === 0 ? (
             <div className="p-12 text-center flex flex-col items-center">
               <Package className="w-12 h-12 text-slate-600 mb-4" />
               <h3 className="text-lg font-bold text-slate-300">Nenhum produto analisado</h3>
               <p className="text-slate-500 mt-2">Sem histórico suficiente para processar a Curva ABC neste período.</p>
             </div>
          ) : (
            <table className="w-full text-left whitespace-nowrap">
              <thead className="sticky top-0 bg-slate-900/90 backdrop-blur z-10">
                <tr className="text-slate-400 border-b border-slate-700/60 text-xs uppercase tracking-wider font-bold">
                  <th className="px-6 py-4">Produto</th>
                  <th className="px-6 py-4">Classe</th>
                  <th className="px-6 py-4 text-right">Faturamento</th>
                  <th className="px-6 py-4 text-right">Acumulado</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50">
                {filteredProducts.map((p: any, idx: number) => {
                  const isA = p.classe === 'A';
                  const isB = p.classe === 'B';
                  return (
                    <tr key={idx} className="hover:bg-slate-700/20 transition-colors group">
                      <td className="px-6 py-4">
                        <div className="font-bold text-white group-hover:text-indigo-400 transition-colors">{p.nome}</div>
                        <div className="text-xs text-slate-500 font-medium">ID: {p.produto_id || '-'}</div>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center justify-center w-8 h-8 rounded-lg font-bold shadow-inner ${
                          isA ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                          isB ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' :
                          'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                        }`}>
                          {p.classe}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right font-black text-white">
                        {formatCurrency(p.valor_total)}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex flex-col items-end gap-1">
                           <span className="font-bold text-slate-300">{(p.percentual_acumulado || 0).toFixed(1)}%</span>
                           <div className="w-24 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                             <div 
                               className={`h-full rounded-full ${
                                 isA ? 'bg-emerald-500' : isB ? 'bg-blue-500' : 'bg-amber-500'
                               }`}
                               style={{ width: `${Math.min(p.percentual_acumulado || 0, 100)}%` }}
                             ></div>
                           </div>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>

    </div>
  );
}
