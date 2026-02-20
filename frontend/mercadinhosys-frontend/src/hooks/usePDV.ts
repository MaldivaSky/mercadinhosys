import { useState, useCallback, useEffect } from 'react';
import { Produto, Cliente } from '../types';
import { pdvService, ConfiguracoesPDV } from '../features/pdv/pdvService';

interface ItemCarrinho {
    produto: Produto;
    quantidade: number;
    precoUnitario: number;
    desconto: number;
    descontoPercentual: boolean;
    total: number;
}

interface FormaPagamento {
    tipo: string;
    label: string;
    taxa: number;
    permite_troco: boolean;
}

export const usePDV = () => {
    // Estado do PDV
    const [carrinho, setCarrinho] = useState<ItemCarrinho[]>([]);
    const [cliente, setCliente] = useState<Cliente | null>(null);
    const [formasPagamento, setFormasPagamento] = useState<FormaPagamento[]>([]);
    const [formaPagamentoSelecionada, setFormaPagamentoSelecionada] = useState<string>('dinheiro');
    const [valorRecebido, setValorRecebido] = useState<number>(0);
    const [observacoes, setObservacoes] = useState<string>('');
    const [descontoGeral, setDescontoGeral] = useState<number>(0);
    const [descontoPercentual, setDescontoPercentual] = useState<boolean>(false);

    // Configurações e permissões
    const [configuracoes, setConfiguracoes] = useState<ConfiguracoesPDV | null>(null);
    const [loading, setLoading] = useState(false);

    // Carregar configurações do PDV
    useEffect(() => {
        const carregarConfiguracoes = async () => {
            try {
                const config = await pdvService.getConfiguracoes();
                setConfiguracoes(config);
                setFormasPagamento(config.formas_pagamento);
            } catch (error) {
                console.error('Erro ao carregar configurações do PDV:', error);
            }
        };

        carregarConfiguracoes();
    }, []);
    // Help: Precisão decimal rigorosa
    const round = (val: number) => Math.round((val + Number.EPSILON) * 100) / 100;

    // Cálculos em tempo real
    const subtotal = round(carrinho.reduce((sum, item) => {
        return sum + (item.precoUnitario * item.quantidade);
    }, 0));

    const descontoItens = round(carrinho.reduce((sum, item) => sum + item.desconto, 0));

    const descontoGeralCalculado = round(descontoPercentual
        ? (subtotal - descontoItens) * (descontoGeral / 100)
        : descontoGeral);

    const descontoTotal = round(descontoItens + descontoGeralCalculado);
    const total = Math.max(0, round(subtotal - descontoTotal));

    const formaPagamento = formasPagamento.find(f => f.tipo === formaPagamentoSelecionada);
    const troco = (formaPagamento?.permite_troco && valorRecebido > total)
        ? round(valorRecebido - total)
        : 0;

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
                const preco = (produto as { preco_venda_efetivo?: number }).preco_venda_efetivo ?? produto.preco_venda;
                const novoItem: ItemCarrinho = {
                    produto,
                    quantidade,
                    precoUnitario: preco,
                    desconto: 0,
                    descontoPercentual: false,
                    total: preco * quantidade,
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
                        descontoPercentual: percentual,
                        total: item.precoUnitario * item.quantidade - descontoValor,
                    };
                }
                return item;
            })
        );
    }, []);

    // Validar permissão de desconto
    const validarDescontoPermitido = useCallback((valorDesconto: number): boolean => {
        if (!configuracoes) return false;

        // ✅ ADMIN sempre pode dar desconto sem autorização
        if (configuracoes.funcionario.role === 'ADMIN') {
            return true;
        }

        const percentualDesconto = (valorDesconto / subtotal) * 100;
        const limiteDesconto = configuracoes.funcionario.limite_desconto || 0;

        // Se exceder o limite, precisa de autorização
        if (percentualDesconto > limiteDesconto) {
            return false;
        }

        return true;
    }, [configuracoes, subtotal]);

    // Limpar carrinho
    const limparCarrinho = useCallback(() => {
        setCarrinho([]);
        setCliente(null);
        setValorRecebido(0);
        setDescontoGeral(0);
        setDescontoPercentual(false);
        setObservacoes('');
        setFormaPagamentoSelecionada('dinheiro');
    }, []);

    // Finalizar venda
    const finalizarVenda = async () => {
        if (carrinho.length === 0) {
            throw new Error('Adicione produtos ao carrinho');
        }

        if (!configuracoes?.permite_venda_sem_cliente && !cliente) {
            throw new Error('Selecione um cliente para continuar');
        }

        const formaPg = formasPagamento.find(f => f.tipo === formaPagamentoSelecionada);

        // Se permite troco (dinheiro), valida valor recebido
        if (formaPg?.permite_troco) {
            if (valorRecebido < total) {
                throw new Error(`Valor recebido insuficiente. Faltam R$ ${(total - valorRecebido).toFixed(2)}`);
            }
        } else {
            // Se não permite troco (cartão/pix), assume valor exato se não informado
            if (valorRecebido <= 0) {
                // Opcional: setValorRecebido(total) aqui não funcionaria pois é state, 
                // mas podemos considerar o valor recebido como total para fins de registro
            }
        }

        setLoading(true);

        try {
            const vendaData = {
                items: carrinho.map(item => ({
                    id: item.produto.id,
                    quantity: item.quantidade,
                    discount: item.desconto,
                })),
                subtotal,
                desconto: descontoTotal,
                total,
                paymentMethod: formaPagamentoSelecionada,
                valor_recebido: formaPg?.permite_troco ? valorRecebido : total,
                troco,
                cliente_id: cliente?.id,
                observacoes: observacoes.trim() || undefined,
            };

            const venda = await pdvService.finalizarVenda(vendaData);
            return venda;
        } finally {
            setLoading(false);
        }
    };

    return {
        // Estado
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
        configuracoes,
        loading,

        // Cálculos
        subtotal,
        descontoItens,
        descontoGeralCalculado,
        descontoTotal,
        total,
        troco,

        // Ações
        adicionarProduto,
        removerProduto,
        atualizarQuantidade,
        aplicarDescontoItem,
        validarDescontoPermitido,
        limparCarrinho,
        finalizarVenda,
    };
};