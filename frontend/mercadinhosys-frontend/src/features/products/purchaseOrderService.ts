// src/features/products/purchaseOrderService.ts
import { apiClient } from '../../api/apiClient';

export interface PedidoCompra {
  id: number;
  numero_pedido: string;
  fornecedor_id: number;
  fornecedor_nome?: string;
  funcionario_nome?: string;
  status: 'pendente' | 'recebido' | 'cancelado';
  data_pedido: string;
  data_previsao_entrega?: string;
  data_recebimento?: string;
  subtotal: number;
  desconto: number;
  frete: number;
  total: number;
  condicao_pagamento?: string;
  observacoes?: string;
  total_itens: number;
  itens?: PedidoCompraItem[];
  // Campos expandidos para detalhes
  fornecedor?: {
    cnpj: string;
    email: string;
  };
  funcionario?: {
    cargo: string;
  };
  numero_nota_fiscal?: string;
  serie_nota_fiscal?: string;
}

export interface PedidoCompraItem {
  id?: number;
  produto_id: number;
  produto_nome: string;
  quantidade_solicitada: number;
  quantidade_recebida: number;
  preco_unitario: number;
  desconto_percentual: number;
  total_item: number;
  status: string;
  produto_unidade?: string;
}

export interface BoletoFornecedor {
  id: number;
  numero_documento: string;
  fornecedor_nome: string;
  fornecedor_id: number;
  valor_original: number;
  valor_atual: number;
  data_emissao: string;
  data_vencimento: string;
  dias_vencimento: number;
  status_vencimento: 'vencido' | 'vence_hoje' | 'vence_em_breve' | 'normal';
  pedido_numero?: string;
  pedido_id?: number;
  data_pedido?: string;
  observacoes?: string;
  valor_juros?: number;
  valor_desconto?: number;
  itens?: PedidoCompraItem[];
}

export interface CreatePedidoData {
  fornecedor_id: number;
  condicao_pagamento?: string;
  observacoes?: string;
  desconto?: number;
  frete?: number;
  itens: {
    produto_id: number;
    quantidade: number;
    preco_unitario?: number;
    desconto_percentual?: number;
  }[];
}

export interface ReceberPedidoData {
  pedido_id: number;
  numero_nota_fiscal?: string;
  serie_nota_fiscal?: string;
  gerar_boleto: boolean;
  data_vencimento?: string;
  numero_documento?: string;
  itens: {
    item_id: number;
    quantidade_recebida: number;
    data_validade?: string;  // NOVO
    numero_lote?: string;    // NOVO
  }[];
}

class PurchaseOrderService {
  // ==================== PEDIDOS DE COMPRA ====================

  async listarPedidos(params?: {
    page?: number;
    per_page?: number;
    status?: string;
    fornecedor_id?: number;
    data_inicio?: string;
    data_fim?: string;
  }) {
    const response = await apiClient.get<{
      pedidos: PedidoCompra[];
      paginacao: {
        pagina_atual: number;
        total_paginas: number;
        total_itens: number;
        itens_por_pagina: number;
      };
    }>('/pedidos-compra/', { params });
    return response.data;
  }

  async obterPedido(id: number) {
    const response = await apiClient.get<{ pedido: PedidoCompra }>(`/pedidos-compra/${id}`);
    return response.data.pedido;
  }

  async criarPedido(data: CreatePedidoData) {
    const response = await apiClient.post<{
      message: string;
      pedido: PedidoCompra;
    }>('/pedidos-compra/', data);
    return response.data;
  }

  async receberPedido(data: ReceberPedidoData) {
    const response = await apiClient.post<{
      message: string;
      pedido: PedidoCompra;
    }>('/pedidos-compra/receber', data);
    return response.data;
  }

  // ==================== BOLETOS DE FORNECEDORES ====================

  async listarBoletos(params?: {
    page?: number;
    per_page?: number;
    status?: string;
    fornecedor_id?: number;
    vencimento_ate?: string;
    apenas_vencidos?: boolean;
  }) {
    const response = await apiClient.get<{
      boletos: BoletoFornecedor[];
      estatisticas: {
        total_aberto: number;
        vencidos: number;
        vence_hoje: number;
        vence_7_dias: number;
      };
      paginacao: {
        pagina_atual: number;
        total_paginas: number;
        total_itens: number;
        itens_por_pagina: number;
      };
    }>('/boletos-fornecedores/', { params });
    return response.data;
  }

  async pagarBoleto(id: number, data: {
    valor_pago: number;
    data_pagamento?: string;
    forma_pagamento?: string;
    observacoes?: string;
  }) {
    const response = await apiClient.post<{
      message: string;
      conta: BoletoFornecedor;
    }>(`/boletos-fornecedores/${id}/pagar`, data);
    return response.data;
  }

  // ==================== INTEGRAÇÃO COM DESPESAS ====================

  async boletosAVencer(params?: {
    dias?: number;
    apenas_vencidos?: boolean;
  }) {
    const response = await apiClient.get<{
      boletos: BoletoFornecedor[];
      resumo: {
        total_boletos: number;
        total_valor: number;
        vencidos: number;
        vence_hoje: number;
        vence_7_dias: number;
        valor_vencidos: number;
        valor_vence_hoje: number;
        valor_vence_7_dias: number;
      };
    }>('/despesas/boletos-a-vencer/', { params });
    return response.data;
  }
}

export const purchaseOrderService = new PurchaseOrderService();