import { Produto } from '../../../types';

/**
 * Calcula classificação ABC baseada em FATURAMENTO (Análise de Pareto)
 * Classe A: Top 20% dos produtos que geram 80% do faturamento
 * Classe B: Próximos 30% dos produtos que geram 15% do faturamento
 * Classe C: Últimos 50% dos produtos que geram 5% do faturamento
 */
export const getClassificacaoABC = (produto: Produto, todosProdutos: Produto[]): 'A' | 'B' | 'C' => {
    const produtosComFaturamento = todosProdutos
        .map(p => ({
            id: p.id,
            faturamento: p.total_vendido || 0
        }))
        .sort((a, b) => b.faturamento - a.faturamento);

    const faturamentoTotal = produtosComFaturamento.reduce((sum, p) => sum + p.faturamento, 0);
    
    if (faturamentoTotal === 0) {
        return 'C';
    }

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
 * Calcula dias desde última venda
 */
export const getDiasDesdeUltimaVenda = (produto: Produto): number | null => {
    if (!produto.ultima_venda) return null;
    
    const hoje = new Date();
    const ultimaVenda = new Date(produto.ultima_venda);
    return Math.floor((hoje.getTime() - ultimaVenda.getTime()) / (1000 * 60 * 60 * 24));
};

/**
 * Aplica filtro rápido aos produtos
 */
export const aplicarFiltroRapido = (produtos: Produto[], filtro: string | null, todosProdutos: Produto[]): Produto[] => {
    if (!filtro) return produtos;

    switch (filtro) {
        case 'classe_a':
            return produtos.filter(p => getClassificacaoABC(p, todosProdutos) === 'A');
        
        case 'classe_c':
            return produtos.filter(p => getClassificacaoABC(p, todosProdutos) === 'C');
        
        case 'giro_rapido': {
            return produtos.filter(p => {
                const dias = getDiasDesdeUltimaVenda(p);
                return dias !== null && dias <= 7;
            });
        }
        
        case 'giro_lento': {
            return produtos.filter(p => {
                const dias = getDiasDesdeUltimaVenda(p);
                return dias === null || dias > 30;
            });
        }
        
        case 'margem_alta':
            return produtos.filter(p => (p.margem_lucro || 0) >= 50);
        
        case 'margem_baixa':
            return produtos.filter(p => (p.margem_lucro || 0) < 30);
        
        case 'repor_urgente':
            return produtos.filter(p => 
                p.estoque_status === 'esgotado' || p.estoque_status === 'baixo'
            );
        
        case 'sem_fornecedor':
            return produtos.filter(p => !p.fornecedor_id);
        
        default:
            return produtos;
    }
};

/**
 * Calcula contadores para os filtros rápidos
 * Usa TODOS os produtos para calcular os contadores corretamente
 */
export const calcularContadoresFiltros = (produtos: Produto[], todosProdutos: Produto[]) => {
    // DEBUG: Diagnóstico completo
    console.log('🔍 DIAGNÓSTICO calcularContadoresFiltros:');
    console.log('  Total produtos recebidos:', produtos.length);
    console.log('  Total produtos para ABC:', todosProdutos.length);
    
    if (todosProdutos.length > 0) {
        const primeiro = todosProdutos[0];
        console.log('  Primeiro produto:', {
            nome: primeiro.nome,
            total_vendido: primeiro.total_vendido,
            quantidade_vendida: primeiro.quantidade_vendida,
            ultima_venda: primeiro.ultima_venda,
            margem_lucro: primeiro.margem_lucro,
        });
    }
    
    console.log('  Produtos com total_vendido > 0:', todosProdutos.filter(p => (p.total_vendido || 0) > 0).length);
    console.log('  Produtos com quantidade_vendida > 0:', todosProdutos.filter(p => (p.quantidade_vendida || 0) > 0).length);
    console.log('  Produtos com ultima_venda:', todosProdutos.filter(p => p.ultima_venda).length);
    console.log('  Produtos com margem_lucro > 0:', todosProdutos.filter(p => (p.margem_lucro || 0) > 0).length);
    
    const produtosComFaturamento = todosProdutos
        .map(p => ({
            id: p.id,
            nome: p.nome,
            faturamento: p.total_vendido || 0
        }))
        .sort((a, b) => b.faturamento - a.faturamento);
    
    const faturamentoTotal = produtosComFaturamento.reduce((sum, p) => sum + p.faturamento, 0);
    console.log('  Faturamento total:', faturamentoTotal.toFixed(2));
    
    if (faturamentoTotal > 0) {
        console.log('  Top 5 produtos por faturamento:', produtosComFaturamento.slice(0, 5));
    }
    
    const contadores = {
        classe_a: produtos.filter(p => getClassificacaoABC(p, todosProdutos) === 'A').length,
        classe_c: produtos.filter(p => getClassificacaoABC(p, todosProdutos) === 'C').length,
        giro_rapido: produtos.filter(p => {
            const dias = getDiasDesdeUltimaVenda(p);
            return dias !== null && dias <= 7;
        }).length,
        giro_lento: produtos.filter(p => {
            const dias = getDiasDesdeUltimaVenda(p);
            return dias === null || dias > 30;
        }).length,
        margem_alta: produtos.filter(p => (p.margem_lucro || 0) >= 50).length,
        margem_baixa: produtos.filter(p => (p.margem_lucro || 0) < 30).length,
        repor_urgente: produtos.filter(p => 
            p.estoque_status === 'esgotado' || p.estoque_status === 'baixo'
        ).length,
        sem_fornecedor: produtos.filter(p => !p.fornecedor_id).length,
    };
    
    console.log('  Contadores calculados:', contadores);
    
    return contadores;
};
