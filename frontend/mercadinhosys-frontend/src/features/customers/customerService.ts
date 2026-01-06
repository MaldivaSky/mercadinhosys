import { apiClient } from '../../api/apiClient';
import { Cliente } from '../../types';

export const customerService = {
  async list(): Promise<Cliente[]> {
    const res = await apiClient.get('/clientes/');
    if (res.data && res.data.clientes) {
      return res.data.clientes;
    }
    return [];
  },
  async create(cliente: Partial<Cliente>): Promise<Cliente> {
    // Garante que o estabelecimento_id seja enviado (ajuste para produção conforme login)
    const payload = { ...cliente, estabelecimento_id: 1 };
    const res = await apiClient.post('/clientes', payload);
    // Ajuste para buscar cliente na resposta correta
    if (res.data && res.data.cliente) {
      return res.data.cliente;
    }
    throw new Error(res.data?.error || 'Erro ao criar cliente');
  },
  async update(id: number, cliente: Partial<Cliente>): Promise<Cliente> {
    const res = await apiClient.put(`/clientes/${id}`, cliente);
    if (res.data && res.data.cliente) {
      return res.data.cliente;
    }
    throw new Error(res.data?.error || 'Erro ao atualizar cliente');
  },
  async remove(id: number): Promise<void> {
    await apiClient.delete(`/clientes/${id}`);
  },
};
