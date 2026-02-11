import React, { useState, useEffect } from 'react';
import { 
  Users, TrendingUp, DollarSign, Clock, AlertCircle, 
  Download, Calendar, Filter, ChevronDown, ChevronUp,
  UserCheck, UserX, Award, Target, GitMerge, BarChart
} from 'lucide-react';
import { 
  BarChart as RechartsBarChart, Bar, LineChart, Line, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, PieChart, Pie
} from 'recharts';
import { apiClient } from '../../../api/apiClient';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

interface RHMetrics {
  total_beneficios_mensal: number;
  total_salarios: number;
  custo_folha_estimado: number;
  funcionarios_ativos: number;
  total_entradas_periodo: number;
  total_atrasos_qtd: number;
  taxa_pontualidade: number;
  total_minutos_atraso: number;
  minutos_extras_estimados: number;
  custo_extras_estimado: number;
  turnover_rate?: number;
  admissoes_periodo?: number;
  demissoes_periodo?: number;
  evolution_turnover?: Array<{ mes: string; admissoes: number; demissoes: number; ausencias?: number; atrasos?: number; horas_extras?: number }>;
  benefits_breakdown?: Array<{ name: string; value: number }>;
  top_overtime_employees?: Array<{ nome: string; horas: number; custo_estimado: number }>;
  atrasos_por_funcionario_mes?: Array<{ funcionario_id: number; nome: string; cargo: string; atrasos_qtd: number; minutos_atraso: number }>;
  horas_extras_por_funcionario_mes?: Array<{ funcionario_id: number; nome: string; cargo: string; minutos_extras: number; custo_extras: number }>;
  faltas_por_funcionario_mes?: Array<{ funcionario_id: number; nome: string; cargo: string; faltas: number; dias_uteis: number; dias_presenca: number }>;
  espelho_pagamento_mes?: Array<{ 
    funcionario_id: number; nome: string; cargo: string; salario_base: number; 
    beneficios: number; horas_extras_horas: number; custo_horas_extras: number; 
    atrasos_minutos: number; faltas: number; total_estimado: number 
  }>;
  resumo_mes?: { inicio: string | null; fim: string | null; dias_uteis: number; total_atrasos_minutos: number; total_atrasos_qtd: number; total_extras_minutos: number; total_faltas: number };
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

export default function RHDashboard() {
  const [rhData, setRhData] = useState<RHMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    'metricas': true,
    'turnover': true,
    'beneficios': true,
    'folha': true,
    'atrasos': true
  });
  const [filtroAtrasados, setFiltroAtrasados] = useState(false);
  const [periodoDias, setPeriodoDias] = useState(30);

  useEffect(() => {
    loadRHData();
  }, [periodoDias]);

  const loadRHData = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get(`/dashboard/cientifico?days=${periodoDias}`);
      const rhMetrics = response.data?.data?.rh;
      
      if (rhMetrics) {
        setRhData(rhMetrics);
      } else {
        setError('Dados de RH não disponíveis');
      }
    } catch (err: any) {
      console.error('Erro ao carregar dados de RH:', err);
      setError(err.message || 'Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  };

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const exportarFolhaPagamentoPDF = () => {
    if (!rhData?.espelho_pagamento_mes) return;

    const doc = new jsPDF();
    
    doc.setFillColor(99, 102, 241);
    doc.rect(0, 0, 210, 40, 'F');
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(20);
    doc.text('Folha de Pagamento', 105, 20, { align: 'center' });
    doc.setFontSize(10);
    doc.text(`Período: ${rhData.resumo_mes?.inicio || '-'} a ${rhData.resumo_mes?.fim || '-'}`, 105, 30, { align: 'center' });

    const headers = [['Funcionário', 'Cargo', 'Salário Base', 'Benefícios', 'H. Extras', 'Faltas', 'Atrasos', 'Total']];
    const data = rhData.espelho_pagamento_mes.map(f => [
      f.nome,
      f.cargo,
      `R$ ${f.salario_base.toFixed(2)}`,
      `R$ ${f.beneficios.toFixed(2)}`,
      `${f.horas_extras_horas.toFixed(1)}h / R$ ${f.custo_horas_extras.toFixed(2)}`,
      f.faltas.toString(),
      `${f.atrasos_minutos}m`,
      `R$ ${f.total_estimado.toFixed(2)}`
    ]);

    autoTable(doc, {
      head: headers,
      body: data,
      startY: 50,
      theme: 'grid',
      styles: { fontSize: 8, cellPadding: 2 },
      headStyles: { fillColor: [99, 102, 241], textColor: [255, 255, 255] },
      alternateRowStyles: { fillColor: [245, 245, 245] }
    });

    const finalY = (doc as any).lastAutoTable.finalY + 10;
    doc.setFontSize(12);
    doc.setTextColor(0, 0, 0);
    doc.text(`Total Folha: R$ ${rhData.custo_folha_estimado.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`, 14, finalY);

    doc.save(`folha-pagamento-${new Date().toISOString().split('T')[0]}.pdf`);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Carregando dados de RH...</p>
        </div>
      </div>
    );
  }

  if (error || !rhData) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center gap-3 text-red-700">
          <AlertCircle className="w-6 h-6" />
          <div>
            <h3 className="font-bold">Erro ao carregar dados</h3>
            <p className="text-sm">{error || 'Dados não disponíveis'}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Dashboard de RH</h2>
          <p className="text-sm text-gray-600 mt-1">Análise completa de recursos humanos</p>
        </div>
        <select
          value={periodoDias}
          onChange={(e) => setPeriodoDias(Number(e.target.value))}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        >
          <option value={7}>Últimos 7 dias</option>
          <option value={15}>Últimos 15 dias</option>
          <option value={30}>Últimos 30 dias</option>
          <option value={60}>Últimos 60 dias</option>
          <option value={90}>Últimos 90 dias</option>
        </select>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-6 rounded-xl shadow-md border border-blue-200">
          <div className="flex items-center justify-between mb-2">
            <div className="p-3 bg-blue-500 rounded-lg">
              <Users className="w-6 h-6 text-white" />
            </div>
          </div>
          <p className="text-sm text-blue-700 font-medium">Funcionários Ativos</p>
          <h3 className="text-3xl font-bold text-blue-900 mt-1">{rhData.funcionarios_ativos}</h3>
        </div>

        <div className="bg-gradient-to-br from-green-50 to-green-100 p-6 rounded-xl shadow-md border border-green-200">
          <div className="flex items-center justify-between mb-2">
            <div className="p-3 bg-green-500 rounded-lg">
              <DollarSign className="w-6 h-6 text-white" />
            </div>
          </div>
          <p className="text-sm text-green-700 font-medium">Folha de Pagamento</p>
          <h3 className="text-2xl font-bold text-green-900 mt-1">
            R$ {rhData.custo_folha_estimado.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
          </h3>
          <p className="text-xs text-green-600 mt-1">Estimado mensal</p>
        </div>

        <div 
          className="bg-gradient-to-br from-red-50 to-red-100 p-6 rounded-xl shadow-md border border-red-200 cursor-pointer hover:shadow-lg transition-shadow"
          onClick={() => setFiltroAtrasados(!filtroAtrasados)}
        >
          <div className="flex items-center justify-between mb-2">
            <div className="p-3 bg-red-500 rounded-lg">
              <AlertCircle className="w-6 h-6 text-white" />
            </div>
            <span className="text-xs font-bold text-red-700 bg-red-200 px-2 py-1 rounded-full">
              Clique para filtrar
            </span>
          </div>
          <p className="text-sm text-red-700 font-medium">Total de Atrasos</p>
          <h3 className="text-3xl font-bold text-red-900 mt-1">{rhData.total_atrasos_qtd}</h3>
          <p className="text-xs text-red-600 mt-1">{rhData.total_minutos_atraso} minutos</p>
        </div>

        <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-6 rounded-xl shadow-md border border-purple-200">
          <div className="flex items-center justify-between mb-2">
            <div className="p-3 bg-purple-500 rounded-lg">
              <TrendingUp className="w-6 h-6 text-white" />
            </div>
          </div>
          <p className="text-sm text-purple-700 font-medium">Taxa de Pontualidade</p>
          <h3 className="text-3xl font-bold text-purple-900 mt-1">{rhData.taxa_pontualidade}%</h3>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold text-gray-900 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-gray-500" />
            Histórico de Admissões, Demissões, Ausências e Atrasos
          </h3>
          <button
            onClick={() => toggleSection('turnover')}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            {expandedSections['turnover'] ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </button>
        </div>
        
        {expandedSections['turnover'] && (
          <div className="h-[400px]">
            {rhData.evolution_turnover && rhData.evolution_turnover.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <RechartsBarChart data={rhData.evolution_turnover}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="mes" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip 
                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                  />
                  <Bar dataKey="admissoes" name="Admissões" fill="#10B981" />
                  <Bar dataKey="demissoes" name="Demissões" fill="#EF4444" />
                  <Bar dataKey="ausencias" name="Ausências" fill="#F59E0B" />
                  <Bar dataKey="atrasos" name="Atrasos" fill="#8B5CF6" />
                </RechartsBarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-gray-400">
                Sem dados históricos suficientes
              </div>
            )}
          </div>
        )}
      </div>

      <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold text-gray-900 flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-purple-600" />
            Folha de Pagamento Detalhada
          </h3>
          <div className="flex gap-2">
            <button
              onClick={exportarFolhaPagamentoPDF}
              className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              PDF
            </button>
            <button
              onClick={() => toggleSection('folha')}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              {expandedSections['folha'] ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {expandedSections['folha'] && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-gray-50 text-gray-600 font-medium">
                <tr>
                  <th className="px-4 py-3 rounded-l-lg">Funcionário</th>
                  <th className="px-4 py-3">Cargo</th>
                  <th className="px-4 py-3">Salário Base</th>
                  <th className="px-4 py-3">Benefícios</th>
                  <th className="px-4 py-3">H. Extras</th>
                  <th className="px-4 py-3">Faltas</th>
                  <th className="px-4 py-3">Atrasos</th>
                  <th className="px-4 py-3 rounded-r-lg text-right">Total Estimado</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {rhData.espelho_pagamento_mes && rhData.espelho_pagamento_mes.length > 0 ? (
                  rhData.espelho_pagamento_mes.map((row, idx) => (
                    <tr key={idx} className="hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3">
                        <p className="font-medium text-gray-900">{row.nome}</p>
                      </td>
                      <td className="px-4 py-3 text-gray-600">{row.cargo}</td>
                      <td className="px-4 py-3 text-gray-900">R$ {row.salario_base.toFixed(2)}</td>
                      <td className="px-4 py-3 text-gray-900">R$ {row.beneficios.toFixed(2)}</td>
                      <td className="px-4 py-3 text-gray-900">
                        {row.horas_extras_horas.toFixed(1)}h / R$ {row.custo_horas_extras.toFixed(2)}
                      </td>
                      <td className="px-4 py-3 text-gray-900">{row.faltas}</td>
                      <td className="px-4 py-3 text-gray-900">{row.atrasos_minutos}m</td>
                      <td className="px-4 py-3 text-right font-bold text-gray-900">
                        R$ {row.total_estimado.toFixed(2)}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={8} className="px-4 py-10 text-center text-gray-400">
                      Sem dados para espelho de pagamento
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
