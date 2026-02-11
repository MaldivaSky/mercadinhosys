import React, { useState, useEffect } from 'react';
import { Gift, Plus, Trash2, Edit2, AlertCircle } from 'lucide-react';
import { apiClient } from '../../../api/apiClient';

interface Beneficio {
  id: number;
  funcionario_id: number;
  nome_beneficio: string;
  tipo: 'vale_refeicao' | 'vale_transporte' | 'vale_alimentacao' | 'seguro_saude' | 'outro';
  valor_mensal: number;
  data_inicio: string;
  data_fim?: string;
  ativo: boolean;
  observacao?: string;
}

interface Funcionario {
  id: number;
  nome: string;
  cargo: string;
}

export default function BeneficiosFuncionario() {
  const [beneficios, setBeneficios] = useState<Beneficio[]>([]);
  const [funcionarios, setFuncionarios] = useState<Funcionario[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [filtroFuncionario, setFiltroFuncionario] = useState<string>('');
  const [filtroAtivos, setFiltroAtivos] = useState<string>('true');

  const [modalAberto, setModalAberto] = useState(false);
  const [novoBeneficio, setNovoBeneficio] = useState({
    funcionario_id: '',
    nome_beneficio: '',
    tipo: 'vale_refeicao' as any,
    valor_mensal: '',
    data_inicio: new Date().toISOString().split('T')[0],
    data_fim: '',
    observacao: ''
  });

  useEffect(() => {
    loadFuncionarios();
    loadBeneficios();
  }, [filtroFuncionario, filtroAtivos]);

  const loadFuncionarios = async () => {
    try {
      const response = await apiClient.get('/funcionarios');
      const items = response?.data?.data || response?.data?.funcionarios || [];
      setFuncionarios(Array.isArray(items) ? items : []);
    } catch (err) {
      console.error('Erro ao carregar funcionários:', err);
    }
  };

  const loadBeneficios = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (filtroFuncionario) params.funcionario_id = filtroFuncionario;
      if (filtroAtivos) params.ativo = filtroAtivos === 'true';

      const response = await apiClient.get('/rh/beneficios', { params });
      setBeneficios(response.data?.data || []);
    } catch (err: any) {
      console.error('Erro ao carregar benefícios:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiClient.post('/rh/beneficios', novoBeneficio);
      setModalAberto(false);
      loadBeneficios();
      setNovoBeneficio({
        funcionario_id: '',
        nome_beneficio: '',
        tipo: 'vale_refeicao',
        valor_mensal: '',
        data_inicio: new Date().toISOString().split('T')[0],
        data_fim: '',
        observacao: ''
      });
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Gift className="w-6 h-6" />
          Benefícios de Funcionários
        </h1>
        <button
          onClick={() => setModalAberto(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          Novo Benefício
        </button>
      </div>

      {/* Filtros */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Funcionário</label>
            <select
              value={filtroFuncionario}
              onChange={(e) => setFiltroFuncionario(e.target.value)}
              className="w-full border rounded px-3 py-2"
            >
              <option value="">Todos</option>
              {funcionarios.map(func => (
                <option key={func.id} value={func.id}>{func.nome}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Status</label>
            <select
              value={filtroAtivos}
              onChange={(e) => setFiltroAtivos(e.target.value)}
              className="w-full border rounded px-3 py-2"
            >
              <option value="">Todos</option>
              <option value="true">Ativos</option>
              <option value="false">Inativos</option>
            </select>
          </div>
        </div>
      </div>

      {/* Lista de Benefícios */}
      {loading ? (
        <div className="text-center py-8">Carregando...</div>
      ) : error ? (
        <div className="bg-red-50 text-red-600 p-4 rounded-lg flex items-center gap-2">
          <AlertCircle className="w-5 h-5" />
          {error}
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Funcionário</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Benefício</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tipo</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Valor Mensal</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {beneficios.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-4 text-center text-gray-500">
                    Nenhum benefício encontrado
                  </td>
                </tr>
              ) : (
                beneficios.map((beneficio) => (
                  <tr key={beneficio.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {funcionarios.find(f => f.id === beneficio.funcionario_id)?.nome || '-'}
                    </td>
                    <td className="px-6 py-4">{beneficio.nome_beneficio}</td>
                    <td className="px-6 py-4">{beneficio.tipo}</td>
                    <td className="px-6 py-4">R$ {beneficio.valor_mensal.toFixed(2)}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded text-xs ${beneficio.ativo ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                        {beneficio.ativo ? 'Ativo' : 'Inativo'}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <button className="text-blue-600 hover:text-blue-800 mr-2">
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button className="text-red-600 hover:text-red-800">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal */}
      {modalAberto && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Novo Benefício</h2>
            <form onSubmit={handleSubmit}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Funcionário</label>
                  <select
                    value={novoBeneficio.funcionario_id}
                    onChange={(e) => setNovoBeneficio({ ...novoBeneficio, funcionario_id: e.target.value })}
                    className="w-full border rounded px-3 py-2"
                    required
                  >
                    <option value="">Selecione</option>
                    {funcionarios.map(func => (
                      <option key={func.id} value={func.id}>{func.nome}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Nome do Benefício</label>
                  <input
                    type="text"
                    value={novoBeneficio.nome_beneficio}
                    onChange={(e) => setNovoBeneficio({ ...novoBeneficio, nome_beneficio: e.target.value })}
                    className="w-full border rounded px-3 py-2"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Tipo</label>
                  <select
                    value={novoBeneficio.tipo}
                    onChange={(e) => setNovoBeneficio({ ...novoBeneficio, tipo: e.target.value })}
                    className="w-full border rounded px-3 py-2"
                  >
                    <option value="vale_refeicao">Vale Refeição</option>
                    <option value="vale_transporte">Vale Transporte</option>
                    <option value="vale_alimentacao">Vale Alimentação</option>
                    <option value="seguro_saude">Seguro Saúde</option>
                    <option value="outro">Outro</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Valor Mensal</label>
                  <input
                    type="number"
                    step="0.01"
                    value={novoBeneficio.valor_mensal}
                    onChange={(e) => setNovoBeneficio({ ...novoBeneficio, valor_mensal: e.target.value })}
                    className="w-full border rounded px-3 py-2"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Data Início</label>
                  <input
                    type="date"
                    value={novoBeneficio.data_inicio}
                    onChange={(e) => setNovoBeneficio({ ...novoBeneficio, data_inicio: e.target.value })}
                    className="w-full border rounded px-3 py-2"
                    required
                  />
                </div>
              </div>
              <div className="flex gap-2 mt-6">
                <button
                  type="button"
                  onClick={() => setModalAberto(false)}
                  className="flex-1 bg-gray-200 text-gray-800 px-4 py-2 rounded hover:bg-gray-300"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="flex-1 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
                >
                  Salvar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
