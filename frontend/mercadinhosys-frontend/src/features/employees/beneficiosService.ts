import { apiClient } from '../../api/apiClient';

export interface Beneficio {
  id: number;
  funcionario_id: number;
  funcionario_nome: string;
  funcionario_cargo: string;
  beneficio_id: number;
  nome_beneficio: string;
  descricao: string;
  tipo: string;
  valor_mensal: number;
  data_inicio: string;
  ativo: boolean;
}

export interface FuncionarioSimples {
  funcionario_id: number;
  funcionario_nome: string;
}

export interface AtribuirBeneficioPayload {
  funcionario_id: number;
  nome_beneficio: string;
  valor_mensal: number;
  observacao?: string;
  data_inicio: string;
}

class BeneficiosService {
  async listarBeneficiosAtribuidos(): Promise<{ data: Beneficio[] }> {
    const response = await apiClient.get('/rh/beneficios');
    return response.data;
  }

  async atribuirBeneficio(payload: AtribuirBeneficioPayload): Promise<void> {
    await apiClient.post('/rh/beneficios', payload);
  }

  async listarFuncionariosParaBeneficio(): Promise<FuncionarioSimples[]> {
    const response = await apiClient.get('/rh/provisoes');
    return (response.data?.data || []).map((p: any) => ({
      funcionario_id: p.funcionario_id,
      funcionario_nome: p.funcionario_nome
    }));
  }
}

export default new BeneficiosService();
