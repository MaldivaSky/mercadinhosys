import { Produto } from '../../../types';

/**
 * Calcula classificação ABC de um produto baseado em faturamento
 * Usa análise de Pareto (80/20)
 */
export const calcularClassificacaoABC = (
    produto: Produto,
    todosProdutos: Produto[]
): 'A' | 'B' | 'C' => {
    // Ordenar produtos por faturamento (preco_venda * quantidade_vendida)
    const produtosComFaturamento = todosProdutos
        .map(p => ({
            id: p.id,
            faturamento: p.preco_venda * (p.quantidade_vendida || 0)
        }))
        .sort((a, b) => b.faturamento - a.faturamento);

    const faturamentoTotal = produtosComFaturamento.reduce((sum, p) => sum + p.faturamento, 0);
    
    if (faturamentoTotal === 0) return 'C';

    let acumulado = 0;
    for (const p of produtosComFaturamento) {
        acumulado += p.faturamento;
        const percentualAcumulado = acumulado / faturamentoTotal;
        
        if (p.id === produto.id) {
            if (percentualAcumulado <= 0.80) return 'A';
            if (percentualAcumulado <= 0.95) return 'B';
            return 'C';
        }
    }
    
    return 'C';
};

/**
 * Calcula status de giro do produto baseado na última venda
 */
export const calcularStatusGiro = (produto: Produto): 'rapido' | 'normal' | 'lento' => {
    if (!produto.ultima_venda) return 'lento';
    
    const hoje = new Date();
    const dataUltimaVenda = new Date(produto.ultima_venda);
    const diasDesdeVenda = Math.floor((hoje.getTime() - dataUltimaVenda.getTime()) / (1000 * 60 * 60 * 24));
    
    if (diasDesdeVenda <= 7) return 'rapido';
    if (diasDesdeVenda <= 30) return 'normal';
    return 'lento';
};

/**
 * Calcula dias desde a última venda
 */
export const calcularDiasParado = (produto: Produto): number | null => {
    if (!produto.ultima_venda) return null;
    
    const hoje = new Date();
    const dataUltimaVenda = new Date(produto.ultima_venda);
    const diasDesdeVenda = Math.floor((hoje.getTime() - dataUltimaVenda.getTime()) / (1000 * 60 * 60 * 24));
    
    return diasDesdeVenda;
};

/**
 * Calcula categoria de margem do produto
 */
export const calcularCategoriaMargem = (produto: Produto): 'alta' | 'media' | 'baixa' => {
    const margem = produto.margem_lucro || 0;
    
    if (margem >= 50) return 'alta';
    if (margem >= 30) return 'media';
    return 'baixa';
};

/**
 * Determina ação necessária para o produto
 */
export const determinarAcaoNecessaria = (produto: Produto): 'repor_urgente' | 'promocao' | 'ajustar_preco' | null => {
    // Prioridade 1: Repor urgente (esgotado ou baixo estoque)
    if (produto.estoque_status === 'esgotado' || produto.estoque_status === 'baixo') {
        return 'repor_urgente';
    }
    
    // Prioridade 2: Fazer promoção (giro lento + estoque alto)
    const giro = calcularStatusGiro(produto);
    if (giro === 'lento' && produto.quantidade > produto.quantidade_minima * 2) {
        return 'promocao';
    }
    
    // Prioridade 3: Ajustar preço (margem muito baixa)
    const margem = produto.margem_lucro || 0;
    if (margem < 20) {
        return 'ajustar_preco';
    }
    
    return null;
};

/**
 * Calcula valor total investido no produto
 */
export const calcularValorInvestido = (produto: Produto): number => {
    return produto.preco_custo * produto.quantidade;
};

/**
 * Calcula lucro potencial se vender todo o estoque
 */
export const calcularLucroPotencial = (produto: Produto): number => {
    const valorVenda = produto.preco_venda * produto.quantidade;
    const valorCusto = produto.preco_custo * produto.quantidade;
    return valorVenda - valorCusto;
};

/**
 * Calcula estatísticas para o painel de filtros estratégicos
 */
export const calcularEstatisticasEstrategicas = (produtos: Produto[]) => {
    const stats = {
        abc: { A: 0, B: 0, C: 0 },
        giro: { rapido: 0, normal: 0, lento: 0 },
        margem: { alta: 0, media: 0, baixa: 0 },
        acao: { repor_urgente: 0, promocao: 0, ajustar_preco: 0 },
        financeiro: {
            capital_investido: 0,
            lucro_potencial: 0,
            margem_media: 0,
        },
        totais: {
            produtos_filtrados: produtos.length,
            produtos_totais: produtos.length,
            alertas_criticos: 0,
        },
    };

    if (produtos.length === 0) return stats;

    let somaMargens = 0;

    produtos.forEach(produto => {
        // ABC
        const abc = calcularClassificacaoABC(produto, produtos);
        stats.abc[abc]++;

        // Giro
        const giro = calcularStatusGiro(produto);
        stats.giro[giro]++;

        // Margem
        const categoriaMargem = calcularCategoriaMargem(produto);
        stats.margem[categoriaMargem]++;

        // Ação necessária
        const acao = determinarAcaoNecessaria(produto);
        if (acao) {
            stats.acao[acao]++;
            if (acao === 'repor_urgente') {
                stats.totais.alertas_criticos++;
            }
        }

        // Financeiro
        stats.financeiro.capital_investido += calcularValorInvestido(produto);
        stats.financeiro.lucro_potencial += calcularLucroPotencial(produto);
        somaMargens += produto.margem_lucro || 0;
    });

    stats.financeiro.margem_media = produtos.length > 0 ? somaMargens / produtos.length : 0;

    return stats;
};

/**
 * Aplica filtros estratégicos aos produtos
 */
export const aplicarFiltrosEstrategicos = (
    produtos: Produto[],
    filtros: {
        abc?: 'A' | 'B' | 'C';
        giro?: 'rapido' | 'normal' | 'lento';
        margem?: 'alta' | 'media' | 'baixa';
        acao?: 'repor_urgente' | 'promocao' | 'ajustar_preco';
    }
): Produto[] => {
    let produtosFiltrados = [...produtos];

    // Filtro ABC
    if (filtros.abc) {
        produtosFiltrados = produtosFiltrados.filter(p => 
            calcularClassificacaoABC(p, produtos) === filtros.abc
        );
    }

    // Filtro Giro
    if (filtros.giro) {
        produtosFiltrados = produtosFiltrados.filter(p => 
            calcularStatusGiro(p) === filtros.giro
        );
    }

    // Filtro Margem
    if (filtros.margem) {
        produtosFiltrados = produtosFiltrados.filter(p => 
            calcularCategoriaMargem(p) === filtros.margem
        );
    }

    // Filtro Ação
    if (filtros.acao) {
        produtosFiltrados = produtosFiltrados.filter(p => 
            determinarAcaoNecessaria(p) === filtros.acao
        );
    }

    return produtosFiltrados;
};
