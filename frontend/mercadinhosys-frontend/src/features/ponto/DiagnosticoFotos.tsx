import React, { useState } from 'react';
import { AlertCircle, CheckCircle, XCircle } from 'lucide-react';
import { pontoService } from './pontoService';

/**
 * Componente de diagnóstico para verificar:
 * 1. Se as fotos estão sendo salvas no backend
 * 2. Se o campo foto_url está sendo retornado na API
 * 3. A estrutura de resposta do /ponto/historico
 */
export const DiagnosticoFotos: React.FC = () => {
  const [resultado, setResultado] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const verificarFotos = async () => {
    setLoading(true);
    setErro(null);
    try {
      // Busca o histórico de hoje
      const historico = await pontoService.obterHistorico({
        data_inicio: new Date().toISOString().split('T')[0],
        data_fim: new Date().toISOString().split('T')[0],
        per_page: 100,
      });

      console.log('📸 RESPOSTA DO HISTÓRICO:', JSON.stringify(historico, null, 2));

      // Analisa cada registro
      const diagnostico = {
        total_registros: historico.data?.length || 0,
        registros_com_foto: 0,
        registros_sem_foto: 0,
        estrutura_resposta: {
          temSuccessField: 'success' in historico,
          temDataField: 'data' in historico,
          exemploRegistro: historico.data?.[0] || null,
          camposEncontrados: historico.data?.[0] ? Object.keys(historico.data[0]) : [],
        },
        detalhes: historico.data?.map((reg: any, idx: number) => ({
          index: idx,
          tem_foto_url: !!reg.foto_url,
          valor_foto_url: reg.foto_url || 'NULL',
          tem_foto: !!reg.foto,
          valor_foto: reg.foto ? `[${String(reg.foto).substring(0, 50)}...]` : 'NULL',
          tipo_registro: reg.tipo_registro,
          data: reg.data,
          hora: reg.hora,
          funcionario: reg.funcionario_nome,
        })) || [],
      };

      // Calcula estatísticas
      historico.data?.forEach((reg: any) => {
        if (reg.foto_url) {
          diagnostico.registros_com_foto++;
        } else {
          diagnostico.registros_sem_foto++;
        }
      });

      setResultado(diagnostico);
    } catch (error: any) {
      setErro(`Erro ao verificar: ${error.message}`);
      console.error('❌ ERRO NO DIAGNÓSTICO:', error);
    } finally {
      setLoading(false);
    }
  };

  const exportarDiagnostico = () => {
    const dataStr = JSON.stringify(resultado, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `diagnostico_fotos_${new Date().toISOString()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-white rounded-lg shadow p-6 max-w-4xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <AlertCircle className="w-6 h-6 text-blue-600" />
        <h2 className="text-2xl font-bold">🔍 Diagnóstico de Fotos</h2>
      </div>

      <p className="text-gray-600 mb-4">
        Este ferramental verifica se as fotos estão sendo salvas e retornadas corretamente pela API.
      </p>

      <button
        onClick={verificarFotos}
        disabled={loading}
        className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 mb-4"
      >
        {loading ? 'Verificando...' : '🔍 Verificar Fotos'}
      </button>

      {erro && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4 flex items-start gap-2">
          <XCircle className="w-5 h-5 mt-0.5 flex-shrink-0" />
          <div>
            <p className="font-semibold">Erro</p>
            <p>{erro}</p>
          </div>
        </div>
      )}

      {resultado && (
        <div className="space-y-4">
          {/* Resumo */}
          <div className="bg-gray-100 p-4 rounded-lg">
            <h3 className="font-bold mb-3 text-lg">📊 Resumo</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-gray-600">Total de Registros:</p>
                <p className="text-2xl font-bold">{resultado.total_registros}</p>
              </div>
              <div>
                <p className="text-gray-600">Com Foto (foto_url):</p>
                <p className="text-2xl font-bold text-green-600">{resultado.registros_com_foto}</p>
              </div>
              <div>
                <p className="text-gray-600">Sem Foto (foto_url):</p>
                <p className="text-2xl font-bold text-red-600">{resultado.registros_sem_foto}</p>
              </div>
              <div>
                <p className="text-gray-600">Taxa de Fotos:</p>
                <p className="text-2xl font-bold">
                  {resultado.total_registros > 0
                    ? `${((resultado.registros_com_foto / resultado.total_registros) * 100).toFixed(0)}%`
                    : 'N/A'}
                </p>
              </div>
            </div>
          </div>

          {/* Estrutura da Resposta */}
          <div className="bg-gray-100 p-4 rounded-lg">
            <h3 className="font-bold mb-3 text-lg">🏗️ Estrutura da Resposta API</h3>
            <div className="text-sm text-gray-700 space-y-2">
              <p>
                Campos encontrados no registro:
                <code className="bg-gray-200 px-2 py-1 rounded ml-2">
                  {resultado.estrutura_resposta.camposEncontrados.join(', ') || 'NENHUM'}
                </code>
              </p>
              {!resultado.estrutura_resposta.camposEncontrados.includes('foto_url') && (
                <p className="text-red-600 font-semibold">
                  ⚠️ PROBLEMA: Campo 'foto_url' NÃO está sendo retornado pela API!
                </p>
              )}
            </div>
          </div>

          {/* Detalhes */}
          <div className="bg-gray-100 p-4 rounded-lg overflow-x-auto">
            <h3 className="font-bold mb-3 text-lg">📋 Detalhes dos Registros</h3>
            <table className="w-full text-xs">
              <thead className="bg-gray-300">
                <tr>
                  <th className="text-left p-2">Tipo</th>
                  <th className="text-left p-2">Data/Hora</th>
                  <th className="text-left p-2">Funcionário</th>
                  <th className="text-center p-2">foto_url?</th>
                  <th className="text-center p-2">foto?</th>
                </tr>
              </thead>
              <tbody>
                {resultado.detalhes.map((det: any, idx: number) => (
                  <tr key={idx} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className="p-2">{det.tipo_registro}</td>
                    <td className="p-2">{det.data} {det.hora}</td>
                    <td className="p-2">{det.funcionario}</td>
                    <td className="text-center p-2">
                      {det.tem_foto_url ? (
                        <CheckCircle className="w-4 h-4 text-green-600 mx-auto" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-600 mx-auto" />
                      )}
                    </td>
                    <td className="text-center p-2">
                      {det.tem_foto ? (
                        <CheckCircle className="w-4 h-4 text-green-600 mx-auto" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-600 mx-auto" />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* JSON Bruto */}
          <details className="bg-gray-100 p-4 rounded-lg">
            <summary className="font-bold cursor-pointer mb-3">📝 JSON Completo (clique para expandir)</summary>
            <pre className="text-xs bg-gray-200 p-3 rounded overflow-auto max-h-96">
              {JSON.stringify(resultado, null, 2)}
            </pre>
          </details>

          {/* Botão de Export */}
          <button
            onClick={exportarDiagnostico}
            className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 w-full"
          >
            💾 Exportar Diagnóstico (JSON)
          </button>

          {/* Recomendações */}
          <div className="bg-yellow-100 border border-yellow-400 p-4 rounded-lg">
            <h3 className="font-bold mb-2">📌 Próximos Passos</h3>
            <ol className="text-sm space-y-2 list-decimal list-inside">
              {resultado.registros_sem_foto > 0 && (
                <>
                  <li>
                    O backend <strong>NÃO está retornando foto_url</strong>. Verificar:
                    <ul className="ml-6 mt-1 list-disc list-inside space-y-1">
                      <li>Se as fotos estão sendo salvas no banco de dados</li>
                      <li>Se o campo foto_url está sendo populado no registro</li>
                      <li>
                        Você pode verificar na estrutura da resposta acima se o campo 'foto' existe
                        (às vezes as fotos são salvas mas com nome diferente)
                      </li>
                    </ul>
                  </li>
                </>
              )}
              {resultado.estrutura_resposta.camposEncontrados.includes('foto') &&
                !resultado.estrutura_resposta.camposEncontrados.includes('foto_url') && (
                  <li>
                    ⚠️ Encontrado campo 'foto' mas não 'foto_url'. Precisamos renomear no frontend ou
                    Backend
                  </li>
                )}
              <li>
                Abra o Console do Navegador (F12) e verifique os logs com "RESPOSTA DO HISTÓRICO"
              </li>
              <li>Verifique o banco de dados se as fotos estão sendo inseridas (tabela pontos)</li>
            </ol>
          </div>
        </div>
      )}
    </div>
  );
};

export default DiagnosticoFotos;
