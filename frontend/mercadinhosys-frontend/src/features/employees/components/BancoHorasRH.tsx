import { useState, useEffect } from 'react';
import { Clock, Filter, TrendingUp, TrendingDown, Minus, User, AlertCircle } from 'lucide-react';
import { apiClient } from '../../../api/apiClient';

interface BancoHorasRegistro {
  id: number;
  funcionario_id: number;
  funcionario_nome: string;
  funcionario_cargo: string;
  mes_referencia: string;
  saldo_minutos: number;
  saldo_horas: number;
  saldo_formatado: string;
  valor_hora_extra: number;
  horas_trabalhadas: number;
  horas_esperadas: number;
  status: 'positivo' | 'negativo' | 'zerado';
}

interface Funcionario {
  id: number;
  nome: string;
  cargo: string;
}

export default function BancoHorasRH() {
  const [registros, setRegistros] = useState<BancoHorasRegistro[]>([]);
  const [funcionarios, setFuncionarios] = useState<Funcionario[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [filtroFuncionarioId, setFiltroFuncionarioId] = useState<string>('');
  const [filtroMes, setFiltroMes] = useState<string>('');

  useEffect(() => {
    loadFuncionarios();
  }, []);

  useEffect(() => {
    loadBancoHoras();
  }, [filtroFuncionarioId, filtroMes]);

  const loadFuncionarios = async () => {
    try {
      const response = await apiClient.get('/funcionarios');
      const items = response?.data?.data || response?.data?.funcionarios || response?.data || [];
      setFuncionarios(Array.isArray(items) ? items : []);
    } catch (err) {
      console.error('Erro ao carregar funcionários:', err);
      setFuncionarios([]);
    }
  };

  const loadBancoHoras = async () => {
    try {
      setLoading(true);
      setError(null);
      const params: any = {};
      if (filtroFuncionarioId) params.funcionario_id = filtroFuncionarioId;
      if (filtroMes) params.mes_referencia = filtroMes;

      const response = await apiClient.get('/rh/banco-horas', { params });
      setRegistros(response.data?.data || []);
    } catch (err: any) {
      console.error('Erro ao carregar banco de horas:', err);
      setError(err.message || 'Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    if (status === 'positivo') return <TrendingUp className="w-4 h-4 text-green-600" />;
    if (status === 'negativo') return <TrendingDown className="w-4 h-4 text-red-600" />;
    return <Minus className="w-4 h-4 text-gray-400" />;
  };

  const getStatusBadge = (status: string) => {
    if (status === 'positivo') return 'bg-green-100 text-green-700 border-green-200';
    if (status === 'negativo') return 'bg-red-100 text-red-700 border-red-200';
    return 'bg-gray-100 text-gray-600 border-gray-200';
  };

  // Resumo totais
  const totalPositivo = registros.filter(r => r.status === 'positivo').length;
  const totalNegativo = registros.filter(r => r.status === 'negativo').length;
  const saldoGeral = registros.reduce((acc, r) => acc + r.saldo_horas, 0);

  // Meses únicos para filtro
  const mesesUnicos = [...new Set(registros.map(r => r.mes_referencia))].sort().reverse();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Banco de Horas</h2>
          <p className="text-sm text-gray-600 mt-1">Controle de saldos de horas extras e devidas</p>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl shadow-md p-5 border border-gray-100">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-blue-100 rounded-lg">
              <Clock className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-xs text-gray-500 font-medium">Registros</p>
              <p className="text-xl font-bold text-gray-900">{registros.length}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-md p-5 border border-gray-100">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-green-100 rounded-lg">
              <TrendingUp className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-xs text-gray-500 font-medium">Saldo Positivo</p>
              <p className="text-xl font-bold text-green-600">{totalPositivo}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-md p-5 border border-gray-100">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-red-100 rounded-lg">
              <TrendingDown className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <p className="text-xs text-gray-500 font-medium">Saldo Negativo</p>
              <p className="text-xl font-bold text-red-600">{totalNegativo}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-md p-5 border border-gray-100">
          <div className="flex items-center gap-3">
            <div className={`p-2.5 rounded-lg ${saldoGeral >= 0 ? 'bg-emerald-100' : 'bg-red-100'}`}>
              <Clock className={`w-5 h-5 ${saldoGeral >= 0 ? 'text-emerald-600' : 'text-red-600'}`} />
            </div>
            <div>
              <p className="text-xs text-gray-500 font-medium">Saldo Geral</p>
              <p className={`text-xl font-bold ${saldoGeral >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                {saldoGeral >= 0 ? '+' : ''}{saldoGeral.toFixed(1)}h
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Filtros */}
      <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
        <div className="flex items-center gap-2 mb-4">
          <Filter className="w-5 h-5 text-gray-500" />
          <h3 className="font-bold text-gray-900">Filtros</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Funcionário</label>
            <select
              value={filtroFuncionarioId}
              onChange={(e) => setFiltroFuncionarioId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
            >
              <option value="">Todos</option>
              {funcionarios.map(f => (
                <option key={f.id} value={f.id}>{f.nome}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Mês Referência</label>
            <select
              value={filtroMes}
              onChange={(e) => setFiltroMes(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
            >
              <option value="">Todos os meses</option>
              {mesesUnicos.map(m => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Tabela */}
      <div className="bg-white rounded-xl shadow-md border border-gray-100 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Carregando banco de horas...</p>
            </div>
          </div>
        ) : error ? (
          <div className="p-6 bg-red-50 border border-red-200 rounded-xl">
            <div className="flex items-center gap-3 text-red-700">
              <AlertCircle className="w-6 h-6" />
              <div>
                <h3 className="font-bold">Erro ao carregar banco de horas</h3>
                <p className="text-sm">{error}</p>
              </div>
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-gray-50 text-gray-600 font-medium">
                <tr>
                  <th className="px-4 py-3">Funcionário</th>
                  <th className="px-4 py-3">Cargo</th>
                  <th className="px-4 py-3">Mês</th>
                  <th className="px-4 py-3 text-right">Horas Trabalhadas</th>
                  <th className="px-4 py-3 text-right">Horas Esperadas</th>
                  <th className="px-4 py-3 text-center">Saldo</th>
                  <th className="px-4 py-3 text-right">Valor H/E</th>
                  <th className="px-4 py-3 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {registros.length > 0 ? (
                  registros.map((r) => (
                    <tr key={r.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                            <User className="w-4 h-4 text-purple-600" />
                          </div>
                          <span className="font-medium text-gray-900">{r.funcionario_nome}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-gray-600">{r.funcionario_cargo || '-'}</td>
                      <td className="px-4 py-3 font-mono text-gray-700">{r.mes_referencia}</td>
                      <td className="px-4 py-3 text-right font-mono">{r.horas_trabalhadas}h</td>
                      <td className="px-4 py-3 text-right font-mono">{r.horas_esperadas}h</td>
                      <td className="px-4 py-3 text-center">
                        <span className={`inline-flex items-center gap-1 px-2.5 py-1 text-xs font-bold rounded-full border ${getStatusBadge(r.status)}`}>
                          {getStatusIcon(r.status)}
                          {r.saldo_formatado}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-gray-600">
                        R$ {r.valor_hora_extra.toFixed(2)}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={`px-2 py-1 text-xs font-bold rounded-full ${
                          r.status === 'positivo' ? 'bg-green-100 text-green-700' :
                          r.status === 'negativo' ? 'bg-red-100 text-red-700' :
                          'bg-gray-100 text-gray-600'
                        }`}>
                          {r.status === 'positivo' ? 'Crédito' : r.status === 'negativo' ? 'Débito' : 'Zerado'}
                        </span>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={8} className="px-4 py-10 text-center text-gray-400">
                      Nenhum registro de banco de horas encontrado
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
