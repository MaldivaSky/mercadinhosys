// Tipos base para todas as entidades do sistema
export interface ApiResponse<T = any> {
    success: boolean;
    data?: T;
    message?: string;
    error?: string;
    pagination?: {
        page: number;
        per_page: number;
        total: number;
        total_pages: number;
    };
}

// Tipos de autenticação
export interface User {
    id: number;
    username: string;
    role: 'admin' | 'employee' | 'owner';
    nome?: string;
    email?: string;
    ativo: boolean;
    criado_em: string;
}

export interface LoginRequest {
    username: string;
    password: string;
}

export interface LoginResponse {
    access_token: string;
    refresh_token: string;
    user: User;
}

// Tipos para clientes
export interface Cliente {
    id: number;
    nome: string;
    email?: string;
    telefone?: string;
    cpf_cnpj?: string;
    endereco?: string;
    data_nascimento?: string;
    ativo: boolean;
    pontos_fidelidade: number;
    total_compras: number;
    criado_em: string;
    atualizado_em: string;
}

// Tipos para produtos
export interface Produto {
    id: number;
    codigo_barras: string;
    nome: string;
    descricao?: string;
    categoria: string;
    preco_custo: number;
    preco_venda: number;
    margem_lucro: number;
    quantidade_estoque: number;
    estoque_minimo: number;
    unidade_medida: string;
    fornecedor_id?: number;
    fornecedor_nome?: string;
    ativo: boolean;
    imagem_url?: string;
    criado_em: string;
    atualizado_em: string;
}

// Tipos para vendas (PDV)
export interface ItemVenda {
    produto_id: number;
    quantidade: number;
    preco_unitario: number;
    desconto: number;
    total: number;
    produto?: Produto;
}

export interface Venda {
    id: number;
    codigo: string;
    cliente_id?: number;
    funcionario_id: number;
    tipo_pagamento: 'dinheiro' | 'cartao_credito' | 'cartao_debito' | 'pix' | 'transferencia';
    status: 'pendente' | 'concluida' | 'cancelada';
    subtotal: number;
    desconto: number;
    total: number;
    troco?: number;
    observacoes?: string;
    itens: ItemVenda[];
    cliente?: Cliente;
    funcionario?: User;
    criado_em: string;
}

// Tipos para despesas
export interface Despesa {
    id: number;
    descricao: string;
    categoria: string;
    valor: number;
    data_vencimento: string;
    data_pagamento?: string;
    status: 'pendente' | 'pago' | 'atrasado';
    forma_pagamento?: string;
    observacoes?: string;
    criado_em: string;
    criado_por: number;
}

// Tipos para funcionários
export interface Funcionario {
    id: number;
    nome: string;
    email: string;
    telefone?: string;
    cpf: string;
    cargo: string;
    salario: number;
    data_admissao: string;
    data_demissao?: string;
    ativo: boolean;
    usuario_id?: number;
    usuario?: User;
    endereco?: string;
    observacoes?: string;
    criado_em: string;
}

// Tipos para dashboard
export interface DashboardMetrics {
    total_vendas_hoje: number;
    total_vendas_mes: number;
    ticket_medio: number;
    clientes_novos_mes: number;
    produtos_baixo_estoque: number;
    despesas_mes: number;
    lucro_mes: number;
    vendas_por_categoria: Array<{
        categoria: string;
        total: number;
    }>;
    vendas_ultimos_7_dias: Array<{
        data: string;
        total: number;
    }>;
}

export interface DashboardDonoMetrics extends DashboardMetrics {
    faturamento_anual: number;
    margem_lucro_media: number;
    top_produtos: Array<{
        produto_id: number;
        nome: string;
        quantidade_vendida: number;
        total_vendido: number;
    }>;
    top_clientes: Array<{
        cliente_id: number;
        nome: string;
        total_compras: number;
    }>;
}