import React, { useEffect, useState } from 'react';
import { Sparkles, Plus, Search, CheckCircle } from 'lucide-react';
import { showToast } from '../../../components/elements/Toast';
import beneficiosService, { Beneficio, FuncionarioSimples } from '../beneficiosService';
import { formatCurrency } from '../../../utils/formatters';

const BENEFICIOS_PADRAO = [
  "Vale Transporte",
  "Vale Refeição",
  "Vale Alimentação",
  "Plano de Saúde",
  "Plano Odontológico",
  "Auxílio Creche",
  "Gympass / TotalPass",
  "Seguro de Vida"
];

export default function BeneficiosRH() {
  const [beneficios, setBeneficios] = useState<Beneficio[]>([]);
  const [funcionarios, setFuncionarios] = useState<FuncionarioSimples[]>([]);
  const [loading, setLoading] = useState(false);
  const [busca, setBusca] = useState('');
  const [showModal, setShowModal] = useState(false);

  // Form
  const [funcId, setFuncId] = useState('');
  const [nomeBeneficio, setNomeBeneficio] = useState('');
  const [valorMensal, setValorMensal] = useState('');
  const [obs, setObs] = useState('');

  const [isCustomBeneficio, setIsCustomBeneficio] = useState(false);

  const loadBeneficios = async () => {
    setLoading(true);
    try {
      const [resBen, funcs] = await Promise.all([
        beneficiosService.listarBeneficiosAtribuidos(),
        beneficiosService.listarFuncionariosParaBeneficio()
      ]);
      setBeneficios(resBen.data || []);
      setFuncionarios(funcs);
    } catch (err: any) {
      showToast.error(err.response?.data?.message || 'Erro ao carregar benefícios');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBeneficios();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!funcId || !nomeBeneficio || !valorMensal) {
      showToast.error('Preencha os campos obrigatórios');
      return;
    }

    try {
      await beneficiosService.atribuirBeneficio({
        funcionario_id: parseInt(funcId),
        nome_beneficio: nomeBeneficio,
        valor_mensal: parseFloat(valorMensal.replace(',', '.')),
        observacao: obs,
        data_inicio: new Date().toISOString().split('T')[0]
      });
      showToast.success('Benefício atribuído com sucesso!');
      setShowModal(false);
      setFuncId('');
      setNomeBeneficio('');
      setValorMensal('');
      setObs('');
      setIsCustomBeneficio(false);
      loadBeneficios();
    } catch (err: any) {
      showToast.error(err.response?.data?.message || 'Erro ao atribuir benefício');
    }
  };

  const beneficiosFiltrados = beneficios.filter(b => 
    b.funcionario_nome?.toLowerCase().includes(busca.toLowerCase()) ||
    b.nome_beneficio?.toLowerCase().includes(busca.toLowerCase())
  );

  const totalMensal = beneficios.reduce((acc, curr) => acc + (curr.ativo ? curr.valor_mensal : 0), 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-2xl bg-purple-100 dark:bg-purple-500/20 text-purple-600 dark:text-purple-400">
            <Sparkles className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-2xl font-black text-gray-900 dark:text-white tracking-tight">Gestão de Benefícios</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">Administre vales, convênios e descontos da equipe</p>
          </div>
        </div>
        <button 
          onClick={() => setShowModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-xl font-bold text-sm shadow-lg shadow-purple-500/30 transition-all"
        >
          <Plus className="w-4 h-4" /> Atribuir Benefício
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-5 rounded-2xl bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 font-medium">Benefícios Ativos</p>
            <p className="text-2xl font-black text-gray-900 dark:text-white mt-1">{beneficios.filter(b => b.ativo).length}</p>
          </div>
          <div className="p-3 bg-indigo-50 dark:bg-indigo-500/10 text-indigo-500 rounded-xl">
            <CheckCircle className="w-6 h-6" />
          </div>
        </div>
        
        <div className="p-5 rounded-2xl bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 font-medium">Custo Mensal</p>
            <p className="text-2xl font-black text-purple-600 dark:text-purple-400 mt-1">{formatCurrency(totalMensal)}</p>
          </div>
          <div className="p-3 bg-purple-50 dark:bg-purple-500/10 text-purple-500 rounded-xl">
            <Sparkles className="w-6 h-6" />
          </div>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-gray-100 dark:border-gray-700">
          <div className="relative max-w-md">
            <Search className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input 
              type="text" 
              placeholder="Buscar por funcionário ou benefício..." 
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500/20 focus:border-purple-500"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 dark:bg-gray-900/50 text-gray-500 dark:text-gray-400 uppercase text-xs font-bold">
              <tr>
                <th className="px-6 py-4">Funcionário</th>
                <th className="px-6 py-4">Benefício</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">Data Início</th>
                <th className="px-6 py-4 text-right">Valor Mensal</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
              {loading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                    Carregando benefícios...
                  </td>
                </tr>
              ) : beneficiosFiltrados.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                    Nenhum benefício encontrado.
                  </td>
                </tr>
              ) : (
                beneficiosFiltrados.map((ben) => (
                  <tr key={ben.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                    <td className="px-6 py-4">
                      <p className="font-bold text-gray-900 dark:text-white">{ben.funcionario_nome}</p>
                      <p className="text-xs text-gray-500">{ben.funcionario_cargo}</p>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-purple-100 dark:bg-purple-500/20 text-purple-600 dark:text-purple-400 flex items-center justify-center">
                          <Sparkles className="w-4 h-4" />
                        </div>
                        <div>
                          <p className="font-semibold text-gray-900 dark:text-white">{ben.nome_beneficio}</p>
                          {ben.descricao && <p className="text-xs text-gray-500">{ben.descricao}</p>}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      {ben.ativo ? (
                        <span className="px-2.5 py-1 text-xs font-bold rounded-full bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-400">ATIVO</span>
                      ) : (
                        <span className="px-2.5 py-1 text-xs font-bold rounded-full bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400">INATIVO</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-gray-500 dark:text-gray-400">
                      {new Date(ben.data_inicio).toLocaleDateString('pt-BR')}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <p className="font-black text-gray-900 dark:text-white">{formatCurrency(ben.valor_mensal)}</p>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white dark:bg-gray-800 rounded-3xl w-full max-w-lg overflow-hidden shadow-2xl border border-gray-200 dark:border-gray-700">
            <div className="p-6 bg-gray-50 dark:bg-gray-900/50 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-bold text-gray-900 dark:text-white">Atribuir Novo Benefício</h3>
              <p className="text-sm text-gray-500 mt-1">Vincule um benefício (como VT ou VR) a um colaborador.</p>
            </div>
            
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Funcionário *</label>
                <select 
                  value={funcId} 
                  onChange={(e) => setFuncId(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  required
                >
                  <option value="">Selecione um colaborador</option>
                  {funcionarios.map(f => (
                    <option key={f.funcionario_id} value={f.funcionario_id}>{f.funcionario_nome}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Nome do Benefício *</label>
                {!isCustomBeneficio ? (
                  <select 
                    value={nomeBeneficio} 
                    onChange={(e) => {
                      if (e.target.value === 'OUTRO') {
                        setIsCustomBeneficio(true);
                        setNomeBeneficio('');
                      } else {
                        setNomeBeneficio(e.target.value);
                      }
                    }}
                    className="w-full px-4 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    required
                  >
                    <option value="">Selecione do Catálogo</option>
                    {BENEFICIOS_PADRAO.map(b => (
                      <option key={b} value={b}>{b}</option>
                    ))}
                    <option value="OUTRO">+ Outro Benefício (Personalizado)</option>
                  </select>
                ) : (
                  <div className="flex gap-2">
                    <input 
                      type="text" 
                      value={nomeBeneficio} 
                      onChange={(e) => setNomeBeneficio(e.target.value)}
                      placeholder="Ex: Auxílio Internet"
                      className="w-full px-4 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      required
                    />
                    <button 
                      type="button"
                      onClick={() => { setIsCustomBeneficio(false); setNomeBeneficio(''); }}
                      className="px-4 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded-xl font-semibold text-sm transition-colors text-gray-700 dark:text-gray-300"
                    >
                      Voltar
                    </button>
                  </div>
                )}
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Valor Mensal (R$) *</label>
                <input 
                  type="number" 
                  step="0.01"
                  value={valorMensal} 
                  onChange={(e) => setValorMensal(e.target.value)}
                  placeholder="0,00"
                  className="w-full px-4 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Observação (opcional)</label>
                <input 
                  type="text" 
                  value={obs} 
                  onChange={(e) => setObs(e.target.value)}
                  placeholder="Ex: 2 passagens diárias"
                  className="w-full px-4 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>

              <div className="flex items-center gap-3 pt-4">
                <button 
                  type="button" 
                  onClick={() => setShowModal(false)}
                  className="flex-1 px-4 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 font-bold hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  Cancelar
                </button>
                <button 
                  type="submit" 
                  className="flex-1 px-4 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white font-bold"
                >
                  Salvar Benefício
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
