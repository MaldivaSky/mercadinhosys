import { Users, Clock, AlertTriangle, CheckCircle } from 'lucide-react';
import { formatCurrency } from '../../../../utils/formatters';

interface RHTabProps {
  data: any;
}

export default function RHTab({ data }: RHTabProps) {
  const rh = data?.rh || {};
  const totalSalarios = rh?.total_salarios || 0;
  const totalBeneficios = rh?.total_beneficios_mensal || 0;
  const funcionariosAtivos = rh?.funcionarios_ativos || 0;
  
  return (
    <div className="space-y-8">
      {/* Resumo RH */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-slate-800/60 rounded-2xl p-6 border border-slate-700/60">
          <div className="flex items-center gap-3 mb-4">
             <div className="p-2 bg-blue-500/20 rounded-lg"><Users className="text-blue-400" /></div>
             <h3 className="text-slate-300 font-bold">Colaboradores</h3>
          </div>
          <div className="text-3xl font-black text-white">{funcionariosAtivos}</div>
          <p className="text-sm text-slate-400 mt-2 font-medium">Ativos no sistema</p>
        </div>
        
        <div className="bg-slate-800/60 rounded-2xl p-6 border border-slate-700/60">
          <div className="flex items-center gap-3 mb-4">
             <div className="p-2 bg-purple-500/20 rounded-lg"><CheckCircle className="text-purple-400" /></div>
             <h3 className="text-slate-300 font-bold">Custo de Folha</h3>
          </div>
          <div className="text-3xl font-black text-white">{formatCurrency(totalSalarios + totalBeneficios)}</div>
          <p className="text-sm text-slate-400 mt-2 font-medium">Salários + Benefícios (Mês)</p>
        </div>

        <div className="bg-slate-800/60 rounded-2xl p-6 border border-slate-700/60">
          <div className="flex items-center gap-3 mb-4">
             <div className="p-2 bg-orange-500/20 rounded-lg"><Clock className="text-orange-400" /></div>
             <h3 className="text-slate-300 font-bold">Atrasos (Mês)</h3>
          </div>
          <div className="text-3xl font-black text-orange-400">{rh?.resumo_mes?.total_atrasos_minutos || 0} min</div>
          <p className="text-sm text-orange-500/70 mt-2 font-medium">Total de atrasos somados</p>
        </div>
        
        <div className="bg-slate-800/60 rounded-2xl p-6 border border-slate-700/60">
          <div className="flex items-center gap-3 mb-4">
             <div className="p-2 bg-red-500/20 rounded-lg"><AlertTriangle className="text-red-400" /></div>
             <h3 className="text-slate-300 font-bold">Faltas (Mês)</h3>
          </div>
          <div className="text-3xl font-black text-red-400">{rh?.resumo_mes?.total_faltas || 0}</div>
          <p className="text-sm text-red-500/70 mt-2 font-medium">Dias de falta registrados</p>
        </div>
      </div>
      
      {/* Alertas de RH */}
      <div className="bg-slate-800/60 rounded-3xl border border-slate-700/60 overflow-hidden">
        <div className="p-6 border-b border-slate-700/60 bg-slate-800/80">
           <h2 className="text-lg font-bold text-white flex items-center gap-2">
             <AlertTriangle className="text-amber-400" /> Pontos de Atenção
           </h2>
        </div>
        <div className="p-6">
           <p className="text-slate-400">
             Nenhuma anomalia grave na equipe detectada nos últimos dias. O painel completo de Ponto Eletrônico está sendo modernizado e as integrações chegarão em breve.
           </p>
        </div>
      </div>
    </div>
  );
}
