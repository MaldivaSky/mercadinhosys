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

export interface BeneficioCatalogo {
  id: number;
  nome: string;
  descricao: string;
  valor_padrao: number;
  ativo: boolean;
}

export interface AtribuirBeneficioPayload {
  funcionario_id: number;
  nome_beneficio?: string;
  beneficio_id?: number;
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

  // --- MÉTODOS DO CATÁLOGO DE BENEFÍCIOS ---
  async listarCatalogo(): Promise<BeneficioCatalogo[]> {
    const response = await apiClient.get('/rh/catalogo-beneficios');
    return response.data?.data || [];
  }

  async criarBeneficioCatalogo(payload: { nome: string; descricao?: string; valor_padrao?: number }): Promise<BeneficioCatalogo> {
    const response = await apiClient.post('/rh/catalogo-beneficios', payload);
    return response.data?.data;
  }

  async editarBeneficioCatalogo(id: number, payload: { nome?: string; descricao?: string; valor_padrao?: number }): Promise<BeneficioCatalogo> {
    const response = await apiClient.put(`/rh/catalogo-beneficios/${id}`, payload);
    return response.data?.data;
  }

  async excluirBeneficioCatalogo(id: number): Promise<void> {
    await apiClient.delete(`/rh/catalogo-beneficios/${id}`);
  }
}

export default new BeneficiosService();
