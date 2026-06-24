import { Activity } from 'lucide-react';
import { formatCurrency } from '../../../../utils/formatters';

interface FinancialTabProps {
  data: any;
}

export default function FinancialTab({ data }: FinancialTabProps) {
  const faturamento = data?.financials?.revenue || data?.summary?.revenue?.value || 0;
  const cogs = data?.financials?.cogs || 0;
  const lucroBruto = data?.financials?.gross_profit || data?.summary?.gross_profit?.value || (faturamento - cogs);
  const despesas = data?.financials?.expenses || data?.total_despesas || 0;
  const lucroLiquido = data?.financials?.net_profit || data?.lucro_liquido || 0;
  const margemLiquida = data?.financials?.net_margin || 0;
  
  return (
    <div className="space-y-8">
      {/* Resumo Financeiro */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-slate-800/60 rounded-2xl p-6 border border-slate-700/60">
          <p className="text-slate-400 font-bold mb-2">Entradas (Faturamento)</p>
          <p className="text-2xl font-black text-blue-400">{formatCurrency(faturamento)}</p>
        </div>
        <div className="bg-slate-800/60 rounded-2xl p-6 border border-slate-700/60">
          <p className="text-slate-400 font-bold mb-2">CMV (Custo Mercadoria)</p>
          <p className="text-2xl font-black text-amber-400">{formatCurrency(cogs)}</p>
        </div>
        <div className="bg-slate-800/60 rounded-2xl p-6 border border-slate-700/60">
          <p className="text-slate-400 font-bold mb-2">Despesas Operacionais</p>
          <p className="text-2xl font-black text-red-400">{formatCurrency(despesas)}</p>
        </div>
        <div className="bg-slate-800/60 rounded-2xl p-6 border border-slate-700/60">
          <p className="text-slate-400 font-bold mb-2">Lucro Líquido</p>
          <p className="text-2xl font-black text-emerald-400">{formatCurrency(lucroLiquido)}</p>
        </div>
      </div>

      {/* DRE Simplificado */}
      <div className="bg-slate-800/60 rounded-3xl border border-slate-700/60 overflow-hidden">
        <div className="p-6 border-b border-slate-700/60 bg-slate-800/80">
           <h2 className="text-lg font-bold text-white flex items-center gap-2">
             <Activity className="text-blue-400" /> DRE Gerencial Simplificado
           </h2>
        </div>
        <div className="p-6">
           <div className="space-y-4">
             
             {/* Faturamento */}
             <div className="flex justify-between items-center pb-4 border-b border-slate-700/50">
               <span className="font-bold text-slate-300">(=) Receita Bruta</span>
               <span className="font-bold text-white">{formatCurrency(faturamento)}</span>
             </div>
             
             {/* Deduções */}
             <div className="flex justify-between items-center pb-4 border-b border-slate-700/50">
               <span className="text-slate-400">(-) Custo das Mercadorias Vendidas (CMV)</span>
               <span className="text-red-400">{formatCurrency(cogs)}</span>
             </div>
             
             {/* Lucro Bruto */}
             <div className="flex justify-between items-center pb-4 border-b border-slate-700/50">
               <span className="font-bold text-blue-300">(=) Lucro Bruto</span>
               <span className="font-bold text-blue-400">{formatCurrency(lucroBruto)}</span>
             </div>
             
             {/* Despesas */}
             <div className="flex justify-between items-center pb-4 border-b border-slate-700/50">
               <span className="text-slate-400">(-) Despesas Operacionais e Folha</span>
               <span className="text-red-400">{formatCurrency(despesas)}</span>
             </div>
             
             {/* Lucro Líquido */}
             <div className="flex justify-between items-center pt-2">
               <span className="font-black text-emerald-400 text-xl">(=) Lucro Líquido</span>
               <div className="text-right">
                 <span className="font-black text-emerald-400 text-xl">{formatCurrency(lucroLiquido)}</span>
                 <p className="text-sm text-slate-400 mt-1">Margem Líquida: {margemLiquida.toFixed(1)}%</p>
               </div>
             </div>
             
           </div>
        </div>
      </div>
    </div>
  );
}
