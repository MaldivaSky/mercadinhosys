import { useState, useCallback, useEffect } from 'react';
import { Produto, Cliente } from '../types';
import { pdvService } from '../features/pdv/pdvService';

interface ItemCarrinho {
    produto: Produto;
    quantidade: number;
    precoUnitario: number;
    desconto: number;
    total: number;
}

interface FormaPagamento {
    tipo: string;
    label: string;
    taxa: number;
    ativo: boolean;
    exigeTroco?: boolean;
    parcelas?: number;
}

export const usePDV = () => {
    const [carrinho, setCarrinho] = useState<ItemCarrinho[]>([]);
    const [cliente, setCliente] = useState<Cliente | null>(null);
    const [formasPagamento, setFormasPagamento] = useState<FormaPagamento[]>([]);
    const [formaPagamentoSelecionada, setFormaPagamentoSelecionada] = useState<string>('dinheiro');
    const [valorRecebido, setValorRecebido] = useState<number>(0);
    const [observacoes, setObservacoes] = useState<string>('');
    const [descontoGeral, setDescontoGeral] = useState<number>(0);
    const [descontoPercentual, setDescontoPercentual] = useState<boolean>(false);

    const carregarFormasPagamento = async () => {
        try {
            const formas = await pdvService.getFormasPagamento();
            const formatadas = Object.entries(formas || {}).map(([tipo, config]: [string, any]) => ({
                tipo,
                label: tipo.replace('_', ' ').toUpperCase(),
                taxa: config.taxa || 0,
                ativo: config.ativo !== false,
                exigeTroco: config.exige_troco,
                parcelas: config.parcelas,
            }));
            setFormasPagamento(formatadas.filter(f => f.ativo));
        } catch (error) {
            console.error('Erro ao carregar formas de pagamento:', error);
        }
    };

    // Carregar formas de pagamento
    useEffect(() => {
        carregarFormasPagamento();
    }, []);

    // Cálculos
    const subtotal = carrinho.reduce((sum, item) => sum + item.total, 0);
    const descontoTotal = descontoPercentual
        ? subtotal * (descontoGeral / 100)
        : descontoGeral;
    const total = subtotal - descontoTotal;
    const troco = valorRecebido > total ? valorRecebido - total : 0;

    // Adicionar produto ao carrinho
    const adicionarProduto = useCallback((produto: Produto, quantidade: number = 1) => {
        setCarrinho(prev => {
            const itemExistente = prev.find(item => item.produto.id === produto.id);

            if (itemExistente) {
                return prev.map(item =>
                    item.produto.id === produto.id
                        ? {
                            ...item,
                            quantidade: item.quantidade + quantidade,
                            total: (item.quantidade + quantidade) * item.precoUnitario - item.desconto,
                        }
                        : item
                );
            } else {
                const novoItem: ItemCarrinho = {
                    produto,
                    quantidade,
                    precoUnitario: produto.preco_venda,
                    desconto: 0,
                    total: produto.preco_venda * quantidade,
                };
                return [...prev, novoItem];
            }
        });
    }, []);

    // Remover produto do carrinho
    const removerProduto = useCallback((produtoId: number) => {
        setCarrinho(prev => prev.filter(item => item.produto.id !== produtoId));
    }, []);

    // Atualizar quantidade
    const atualizarQuantidade = useCallback((produtoId: number, quantidade: number) => {
        if (quantidade <= 0) {
            removerProduto(produtoId);
            return;
        }

        setCarrinho(prev =>
            prev.map(item =>
                item.produto.id === produtoId
                    ? {
                        ...item,
                        quantidade,
                        total: quantidade * item.precoUnitario - item.desconto,
                    }
                    : item
            )
        );
    }, [removerProduto]);

    // Aplicar desconto no item
    const aplicarDescontoItem = useCallback((produtoId: number, desconto: number, percentual: boolean = false) => {
        setCarrinho(prev =>
            prev.map(item => {
                if (item.produto.id === produtoId) {
                    const descontoValor = percentual
                        ? item.precoUnitario * item.quantidade * (desconto / 100)
                        : desconto;

                    return {
                        ...item,
                        desconto: descontoValor,
                        total: item.precoUnitario * item.quantidade - descontoValor,
                    };
                }
                return item;
            })
        );
    }, []);

    // Limpar carrinho
    const limparCarrinho = useCallback(() => {
        setCarrinho([]);
        setCliente(null);
        setValorRecebido(0);
        setDescontoGeral(0);
        setObservacoes('');
    }, []);

    // Finalizar venda
    const finalizarVenda = async () => {
        if (carrinho.length === 0) {
            throw new Error('Adicione produtos ao carrinho');
        }

        if (formaPagamentoSelecionada === 'dinheiro' && valorRecebido < total) {
            throw new Error('Valor recebido insuficiente');
        }

        const vendaData = {
            cliente_id: cliente?.id,
            forma_pagamento: formaPagamentoSelecionada,
            subtotal,
            desconto: descontoTotal,
            total,
            valor_recebido: formaPagamentoSelecionada === 'dinheiro' ? valorRecebido : total,
            troco,
            observacoes,
            itens: carrinho.map(item => ({
                produto_id: item.produto.id,
                quantidade: item.quantidade,
                preco_unitario: item.precoUnitario,
                desconto: item.desconto,
                total_item: item.total,
            })),
        };

        return await pdvService.criarVenda(vendaData);
    };

    return {
        carrinho,
        cliente,
        setCliente,
        formasPagamento,
        formaPagamentoSelecionada,
        setFormaPagamentoSelecionada,
        valorRecebido,
        setValorRecebido,
        observacoes,
        setObservacoes,
        descontoGeral,
        setDescontoGeral,
        descontoPercentual,
        setDescontoPercentual,
        subtotal,
        descontoTotal,
        total,
        troco,
        adicionarProduto,
        removerProduto,
        atualizarQuantidade,
        aplicarDescontoItem,
        limparCarrinho,
        finalizarVenda,
    };
};