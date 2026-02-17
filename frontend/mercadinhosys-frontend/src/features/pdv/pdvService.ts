import { apiClient } from '../../api/apiClient';
import { ApiResponse, Produto, Cliente } from '../../types';

// Tipos específicos do PDV
export interface ConfiguracoesPDV {
    funcionario: {
        id: number;
        nome: string;
        role: string;
        pode_dar_desconto: boolean;
        limite_desconto: number;
        pode_cancelar_venda: boolean;
    };
    formas_pagamento: FormaPagamentoPDV[];
    permite_venda_sem_cliente: boolean;
    exige_observacao_desconto: boolean;
}

export interface FormaPagamentoPDV {
    tipo: string;
    label: string;
    taxa: number;
    permite_troco: boolean;
}

export interface ValidarProdutoRequest {
    produto_id?: number;
    codigo_barras?: string;
    quantidade: number;
}

export interface ValidarProdutoResponse {
    valido: boolean;
    produto: Produto;
    mensagem?: string;
}

export interface CalcularVendaRequest {
    items: {
        produto_id: number;
        quantidade: number;
        desconto: number;
    }[];
    desconto_geral: number;
    desconto_percentual: boolean;
    forma_pagamento: string;
    valor_recebido?: number;
}

export interface CalcularVendaResponse {
    success: boolean;
    calculo: {
        subtotal: number;
        desconto: number;
        total: number;
        troco: number;
        quantidade_itens: number;
        valor_recebido: number;
    };
}

export interface FinalizarVendaRequest {
    items: {
        id: number;
        quantity: number;
        discount: number;
    }[];
    subtotal: number;
    desconto: number;
    total: number;
    paymentMethod: string;
    valor_recebido: number;
    troco: number;
    cliente_id?: number;
    observacoes?: string;
}

export interface AutorizarGerenteRequest {
    username: string;
    password: string;
    acao: 'desconto' | 'cancelamento';
    valor_desconto?: number;
}

export interface ComprovanteVendaResponse {
    success: boolean;
    venda: {
        id: number;
        codigo: string;
        data: string;
    };
    estabelecimento?: {
        nome_fantasia?: string;
        razao_social?: string;
        cnpj?: string;
        inscricao_estadual?: string;
        telefone?: string;
        email?: string;
        endereco?: string;
    };
    comprovante: {
        funcionario: string;
        cliente: string;
        itens: Array<{
            nome: string;
            codigo?: string;
            quantidade: number;
            preco_unitario: number;
            total: number;
        }>;
        subtotal: number;
        desconto: number;
        total: number;
        forma_pagamento: string;
        valor_recebido: number;
        troco: number;
        rodape?: string;
    };
}

export const pdvService = {
    // ==================== CONFIGURAÇÕES PDV ====================

    /**
     * Carrega configurações do PDV incluindo permissões do funcionário
     */
    getConfiguracoes: async (): Promise<ConfiguracoesPDV> => {
        const response = await apiClient.get<any>('/pdv/configuracoes');
        return response.data.configuracoes;
    },

    // ==================== VALIDAÇÃO DE PRODUTOS ====================

    /**
     * Valida produto antes de adicionar ao carrinho
     * Verifica estoque disponível e retorna dados completos
     */
    validarProduto: async (data: ValidarProdutoRequest): Promise<ValidarProdutoResponse> => {
        const response = await apiClient.post<any>('/pdv/validar-produto', data);
        return {
            valido: response.data.valido,
            produto: response.data.produto,
            mensagem: response.data.mensagem
        };
    },

    /**
     * Busca produtos por nome, marca, categoria
     */
    buscarProduto: async (query: string): Promise<Produto[]> => {
        // OTIMIZAÇÃO: Usar endpoint de listagem que já retorna alertas e dados completos
        const response = await apiClient.get<any>('/produtos/', {
            params: {
                busca: query,
                por_pagina: 20, // Limitar resultados para performance
                ativo: true    // Apenas produtos ativos
            },
        });
        console.log('🔍 Resposta da API de busca:', response.data);

        if (response.data.success && Array.isArray(response.data.produtos)) {
            return response.data.produtos.map((p: any) => ({
                ...p,
                quantidade_estoque: p.quantidade // Garantir compatibilidade com PDV
            }));
        }

        return [];
    },

    /**
     * Busca produto por código de barras
     */
    buscarPorCodigoBarras: async (codigo: string): Promise<Produto | null> => {
        try {
            const validacao = await pdvService.validarProduto({
                codigo_barras: codigo,
                quantidade: 1
            });
            return validacao.valido ? validacao.produto : null;
        } catch (error) {
            console.error('Erro ao buscar por código de barras:', error);
            return null;
        }
    },

    // ==================== CÁLCULOS E PREVIEW ====================

    /**
     * Calcula totais em tempo real (preview)
     * Não persiste dados, apenas retorna cálculos
     */
    calcularVenda: async (data: CalcularVendaRequest): Promise<CalcularVendaResponse> => {
        const response = await apiClient.post<CalcularVendaResponse>('/pdv/calcular-venda', data);
        return response.data;
    },

    // ==================== FINALIZAÇÃO DE VENDA ====================

    /**
     * Finaliza venda de forma ATÔMICA
     * Atualiza estoque e registra movimentações
     */
    finalizarVenda: async (data: FinalizarVendaRequest): Promise<any> => {
        const response = await apiClient.post<any>('/pdv/finalizar', data);
        return response.data.venda;
    },

    // ==================== ESTATÍSTICAS E RESUMOS ====================

    /**
     * Retorna resumo das vendas de hoje
     */
    getVendasHoje: async (): Promise<any> => {
        const response = await apiClient.get<any>('/pdv/vendas-hoje');
        return response.data;
    },

    /**
     * Estatísticas rápidas do PDV
     */
    getEstatisticasRapidas: async (): Promise<any> => {
        const response = await apiClient.get<any>('/pdv/estatisticas-rapidas');
        return response.data.estatisticas;
    },

    // ==================== CANCELAMENTO ====================

    /**
     * Cancela venda (requer permissão)
     */
    cancelarVenda: async (vendaId: number, motivo: string): Promise<void> => {
        await apiClient.post(`/pdv/cancelar-venda/${vendaId}`, { motivo });
    },

    // ==================== AUTORIZAÇÃO DE GERENTE ====================

    /**
     * Solicita autorização de gerente para desconto/cancelamento
     */
    autorizarGerente: async (data: AutorizarGerenteRequest): Promise<boolean> => {
        try {
            const response = await apiClient.post<any>('/auth/login', {
                username: data.username,
                password: data.password
            });

            // Verifica se tem permissão necessária
            const user = response.data.data?.user;
            if (!user) return false;

            if (data.acao === 'desconto') {
                return user.permissoes?.pode_dar_desconto || user.role === 'gerente' || user.role === 'dono';
            } else if (data.acao === 'cancelamento') {
                return user.permissoes?.pode_cancelar_venda || user.role === 'gerente' || user.role === 'dono';
            }

            return false;
        } catch (error) {
            console.error('Erro ao autorizar gerente:', error);
            return false;
        }
    },

    // ==================== CLIENTES ====================

    /**
     * Busca clientes para vincular à venda
     */
    buscarClientes: async (query: string): Promise<Cliente[]> => {
        const response = await apiClient.get<any>('/clientes/buscar', {
            params: { q: query },
        });
        console.log('👥 Resposta da API de clientes:', response.data);

        // A API retorna { success: true, clientes: [...], total: X }
        if (response.data.success && Array.isArray(response.data.clientes)) {
            return response.data.clientes;
        }

        // Fallback para compatibilidade
        return Array.isArray(response.data) ? response.data : [];
    },

    // ==================== IMPRESSÃO ====================

    /**
     * Imprime comprovante da venda
     */
    imprimirComprovante: async (vendaId: number): Promise<Blob> => {
        const response = await apiClient.get(`/vendas/${vendaId}/comprovante`, {
            responseType: 'blob',
        });
        return response.data;
    },

    // ==================== EMAIL ====================

    /**
     * Envia cupom fiscal por email
     */
    enviarCupomEmail: async (vendaId: number): Promise<{ success: boolean; message: string }> => {
        const response = await apiClient.post<ApiResponse<any>>('/pdv/enviar-cupom', {
            venda_id: vendaId,
        });
        return {
            success: true,
            message: response.data.message || 'Email enviado com sucesso!',
        };
    },

    /**
     * Envia nota fiscal para email específico (para consumidor final ou cliente sem email)
     */
    enviarCupomFiscal: async (vendaId: number, email: string): Promise<{ success: boolean; message: string }> => {
        const response = await apiClient.post<ApiResponse<any>>('/pdv/enviar-cupom', {
            venda_id: vendaId,
            email_destino: email,
        });
        return {
            success: true,
            message: response.data.message || 'Nota fiscal enviada com sucesso!',
        };
    },

    /**
     * Busca comprovante completo para exibir em tela
     */
    obterComprovante: async (vendaId: number): Promise<ComprovanteVendaResponse> => {
        const response = await apiClient.get<ComprovanteVendaResponse>(`/pdv/comprovante/${vendaId}`);
        return response.data;
    },
};