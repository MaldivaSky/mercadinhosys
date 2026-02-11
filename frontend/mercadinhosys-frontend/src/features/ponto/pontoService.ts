import { apiClient } from '../../api/apiClient';

export interface RegistroPonto {
  id: number;
  funcionario_id: number;
  funcionario_nome: string;
  data: string;
  hora: string;
  tipo_registro: 'entrada' | 'saida_almoco' | 'retorno_almoco' | 'saida';
  latitude?: number;
  longitude?: number;
  localizacao_endereco?: string;
  foto_url?: string;
  status: 'normal' | 'atrasado' | 'justificado';
  minutos_atraso: number;
  observacao?: string;
}

export interface ConfiguracaoHorario {
  id: number;
  estabelecimento_id: number;
  hora_entrada: string;
  hora_saida_almoco: string;
  hora_retorno_almoco: string;
  hora_saida: string;
  tolerancia_entrada: number;
  tolerancia_saida_almoco: number;
  tolerancia_retorno_almoco: number;
  tolerancia_saida: number;
  exigir_foto: boolean;
  exigir_localizacao: boolean;
  raio_permitido_metros: number;
}

export interface EstatisticasPonto {
  dias_trabalhados: number;
  total_atrasos: number;
  minutos_atraso_total: number;
  frequencia_tipo: {
    entrada: number;
    saida_almoco: number;
    retorno_almoco: number;
    saida: number;
  };
  grafico_frequencia: Array<{
    data: string;
    total_registros: number;
    teve_atraso: boolean;
    minutos_atraso: number;
  }>;
  taxa_presenca: number;
}

export const pontoService = {
  // Registrar ponto
  registrarPonto: async (dados: {
    tipo_registro: string;
    latitude?: number;
    longitude?: number;
    localizacao_endereco?: string;
    foto?: string;
    dispositivo?: string;
    observacao?: string;
  }) => {
    const response = await apiClient.post('/ponto/registrar', dados);
    return response.data;
  },

  // Obter pontos de hoje
  obterPontosHoje: async () => {
    const response = await apiClient.get('/ponto/hoje');
    return response.data;
  },

  // Obter histórico
  obterHistorico: async (params?: {
    data_inicio?: string;
    data_fim?: string;
    page?: number;
    per_page?: number;
  }) => {
    const response = await apiClient.get('/ponto/historico', { params });
    return response.data;
  },

  // Obter estatísticas
  obterEstatisticas: async () => {
    const response = await apiClient.get<{ success: boolean; data: EstatisticasPonto }>('/ponto/estatisticas');
    return response.data;
  },

  // Obter configuração
  obterConfiguracao: async () => {
    const response = await apiClient.get<{ success: boolean; data: ConfiguracaoHorario }>('/ponto/configuracao');
    return response.data;
  },

  // Atualizar configuração (admin)
  atualizarConfiguracao: async (dados: Partial<ConfiguracaoHorario>) => {
    const response = await apiClient.put('/ponto/configuracao', dados);
    return response.data;
  },

  // Relatório consolidado de todos funcionários
  obterRelatorioFuncionarios: async (params?: {
    data_inicio?: string;
    data_fim?: string;
  }) => {
    const response = await apiClient.get('/ponto/relatorio/funcionarios', { params });
    return response.data;
  },

  // Relatório detalhado de um funcionário específico
  obterRelatorioDetalhado: async (funcionarioId: number, params?: {
    data_inicio?: string;
    data_fim?: string;
  }) => {
    const response = await apiClient.get(`/ponto/relatorio/detalhado/${funcionarioId}`, { params });
    return response.data;
  },

  // Obter lista de funcionários (para filtros)
  obterFuncionarios: async () => {
    const response = await apiClient.get('/funcionarios');
    return response.data;
  },
};
