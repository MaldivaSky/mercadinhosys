import { apiClient } from '../../api/apiClient';
import { Cliente } from '../../types';

export const customerService = {
  // Carrega a carteira COMPLETA (todas as páginas). O backend pagina em 50 por
  // padrão; sem isto a página de clientes só via os 50 primeiros e a busca/
  // segmentação client-side não encontrava quem estivesse fora da 1ª página
  // (ex.: o cliente mais antigo, id baixo, com ordenação id desc).
  async list(): Promise<Cliente[]> {
    const perPage = 200;
    const first = await apiClient.get(`/clientes/?por_pagina=${perPage}&pagina=1`);
    const clientes: Cliente[] = first.data?.clientes ?? [];
    const totalPaginas: number = first.data?.total_paginas ?? 1;

    if (totalPaginas > 1) {
      const requests = [];
      for (let pagina = 2; pagina <= totalPaginas; pagina++) {
        requests.push(apiClient.get(`/clientes/?por_pagina=${perPage}&pagina=${pagina}`));
      }
      const restantes = await Promise.all(requests);
      for (const res of restantes) {
        clientes.push(...(res.data?.clientes ?? []));
      }
    }
    return clientes;
  },
  async create(cliente: Partial<Cliente>): Promise<Cliente> {
    const res = await apiClient.post('/clientes/', cliente);
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
