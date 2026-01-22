import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import {
    ShoppingCart,
    Printer,
    X,
    Check,
    CreditCard,
    DollarSign,
    Smartphone,
    TrendingUp,
    Tag,
    AlertTriangle,
    Mail
} from 'lucide-react';
import ProdutoSearch from './components/ProdutoSearch';
import CarrinhoItem from './components/CarrinhoItem';
import ClienteSelect from './components/ClienteSelect';
import CaixaHeader from './components/CaixaHeader';
import GerenteAuthModal from './components/GerenteAuthModal';
import { usePDV } from '../../hooks/usePDV';
import { Produto } from '../../types';
import { formatCurrency } from '../../utils/formatters';
import { pdvService } from './pdvService';

const PDVPage: React.FC = () => {
    const {
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
        subtotal,
        descontoItens,
        descontoGeralCalculado,
        descontoTotal,
        total,
        troco,
        adicionarProduto,
        removerProduto,
        atualizarQuantidade,
        aplicarDescontoItem,
        validarDescontoPermitido,
        limparCarrinho,
        finalizarVenda,
    } = usePDV();

    const [formaPagamentoAberta, setFormaPagamentoAberta] = useState(false);
    const [mostrarAutorizacao, setMostrarAutorizacao] = useState(false);
    const [descontoAprovado, setDescontoAprovado] = useState(false);
    const [ultimaVendaId, setUltimaVendaId] = useState<number | null>(null);
    const [enviandoEmail, setEnviandoEmail] = useState(false);
    const [mostrarModalEmail, setMostrarModalEmail] = useState(false);

    // Validar desconto ao alterar
    useEffect(() => {
        if (descontoGeral > 0 && !descontoAprovado) {
            const permitido = validarDescontoPermitido(descontoGeralCalculado);
            if (!permitido) {
                toast(
                    `Desconto de ${formatCurrency(descontoGeralCalculado)} requer autorização de gerente`,
                    {
                        icon: '⚠️',
                        duration: 4000,
                        style: {
                            background: '#f59e0b',
                            color: '#fff',
                        },
                    }
                );
            }
        }
    }, [descontoGeral, descontoGeralCalculado, descontoAprovado, validarDescontoPermitido]);

    const handleProdutoSelecionado = (produto: Produto) => {
        if (!produto.quantidade_estoque || produto.quantidade_estoque <= 0) {
            toast.error(`📦 ${produto.nome} está sem estoque!`, {
                duration: 5000,
            });
            return;
        }
        adicionarProduto(produto);
        toast.success(`✅ ${produto.nome} adicionado ao carrinho`);
    };

    const handleAplicarDesconto = () => {
        if (descontoGeral > 0) {
            const permitido = validarDescontoPermitido(descontoGeralCalculado);
            
            if (!permitido && !descontoAprovado) {
                setMostrarAutorizacao(true);
            }
        }
    };

    const handleAutorizacaoAprovada = () => {
        setDescontoAprovado(true);
        setMostrarAutorizacao(false);
        toast.success('Desconto autorizado pelo gerente', {
            icon: '✅',
        });
    };

    const handleFinalizarVenda = async () => {
        try {
            // Validar desconto antes de finalizar
            if (descontoGeral > 0) {
                const permitido = validarDescontoPermitido(descontoGeralCalculado);
                if (!permitido && !descontoAprovado) {
                    setMostrarAutorizacao(true);
                    return;
                }
            }

            const venda = await finalizarVenda();
            setUltimaVendaId(venda.id);

            toast.success(
                `🎉 Venda ${venda.codigo} finalizada com sucesso! Total: ${formatCurrency(venda.total)}`,
                { duration: 6000 }
            );

            setDescontoAprovado(false);

            // Perguntar se deseja enviar email ao cliente
            if (cliente?.email) {
                setMostrarModalEmail(true);
            } else {
                // Se não tem email, limpar automaticamente após 2 segundos
                setTimeout(() => {
                    limparCarrinho();
                    setUltimaVendaId(null);
                }, 2000);
            }

        } catch (error: any) {
            console.error('❌ ERRO AO FINALIZAR:', error);
            toast.error(
                error.response?.data?.error || error.message || 'Erro ao finalizar venda',
                {
                    icon: '❌',
                    duration: 6000,
                }
            );
        }
    };

    const handleEnviarEmail = async (enviar: boolean) => {
        setMostrarModalEmail(false);

        if (!enviar) {
            // Cliente não quer email, limpar PDV
            setTimeout(() => {
                limparCarrinho();
                setUltimaVendaId(null);
            }, 1000);
            return;
        }

        if (!ultimaVendaId || !cliente?.email) {
            // Limpar mesmo sem email
            setTimeout(() => {
                limparCarrinho();
                setUltimaVendaId(null);
            }, 1000);
            return;
        }

        try {
            setEnviandoEmail(true);
            await pdvService.enviarCupomEmail(ultimaVendaId);
            
            toast.success(`📧 Cupom fiscal enviado para ${cliente.email}`, {
                duration: 6000,
            });

            // Limpar após envio bem-sucedido
            setTimeout(() => {
                limparCarrinho();
                setUltimaVendaId(null);
            }, 2000);

        } catch (error: any) {
            console.error('❌ ERRO AO ENVIAR EMAIL:', error);
            toast.error(error.response?.data?.error || '❌ Erro ao enviar email', {
                duration: 6000,
            });
            
            // Limpar mesmo com erro no email
            setTimeout(() => {
                limparCarrinho();
                setUltimaVendaId(null);
            }, 2000);
        } finally {
            setEnviandoEmail(false);
        }
    };

    // const handleNovaVenda = () => {
    //     limparCarrinho();
    //     setUltimaVendaId(null);
    //     setDescontoAprovado(false);
    //     toast.success('Nova venda iniciada', {
    //         icon: '🛒',
    //     });
    // };

    const handleLimparCarrinho = () => {
        if (carrinho.length > 0) {
            if (confirm('Tem certeza que deseja cancelar esta venda?')) {
                limparCarrinho();
                setDescontoAprovado(false);
                toast.success('Venda cancelada', {
                    icon: '🗑️',
                });
            }
        }
    };

    const renderIconPagamento = (tipo: string) => {
        switch (tipo) {
            case 'dinheiro':
                return <DollarSign className="w-5 h-5" />;
            case 'cartao_credito':
            case 'cartao_debito':
                return <CreditCard className="w-5 h-5" />;
            case 'pix':
                return <Smartphone className="w-5 h-5" />;
            default:
                return <TrendingUp className="w-5 h-5" />;
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
            <div className="max-w-7xl mx-auto">
                {/* Header com informações do caixa */}
                <CaixaHeader
                    funcionarioNome={configuracoes?.funcionario.nome}
                    funcionarioRole={configuracoes?.funcionario.role}
                />

                {/* Layout Principal */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Coluna 1: Busca e Carrinho */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* Busca de Produtos */}
                        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
                            <h2 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">
                                Buscar Produtos
                            </h2>
                            <ProdutoSearch onProdutoSelecionado={handleProdutoSelecionado} />
                        </div>

                        {/* Carrinho */}
                        <div className="bg-white dark:bg-gray-800 rounded-xl shadow">
                            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                                <div className="flex items-center justify-between">
                                    <h2 className="text-lg font-semibold text-gray-800 dark:text-white">
                                        Carrinho de Vendas
                                    </h2>
                                    <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-300 rounded-full">
                                        {carrinho.length} {carrinho.length === 1 ? 'item' : 'itens'}
                                    </span>
                                </div>
                            </div>

                            <div className="p-6">
                                {carrinho.length === 0 ? (
                                    <div className="text-center py-12">
                                        <ShoppingCart className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
                                        <p className="text-gray-500 dark:text-gray-400">
                                            Nenhum produto no carrinho
                                        </p>
                                        <p className="text-sm text-gray-400 dark:text-gray-500 mt-2">
                                            Busque e adicione produtos para começar uma venda
                                        </p>
                                    </div>
                                ) : (
                                    <div className="space-y-4">
                                        {carrinho.map((item) => (
                                            <CarrinhoItem
                                                key={item.produto.id}
                                                produto={item.produto}
                                                quantidade={item.quantidade}
                                                precoUnitario={item.precoUnitario}
                                                desconto={item.desconto}
                                                total={item.total}
                                                onAtualizarQuantidade={(qtd) =>
                                                    atualizarQuantidade(item.produto.id, qtd)
                                                }
                                                onRemover={() => removerProduto(item.produto.id)}
                                                onAplicarDesconto={(desc, perc) =>
                                                    aplicarDescontoItem(item.produto.id, desc, perc)
                                                }
                                            />
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Coluna 2: Resumo e Pagamento */}
                    <div className="space-y-6">
                        {/* Cliente */}
                        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
                            <h2 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">
                                Cliente
                            </h2>
                            <ClienteSelect
                                cliente={cliente}
                                onClienteSelecionado={setCliente}
                            />
                        </div>

                        {/* Resumo da Venda */}
                        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
                            <h2 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">
                                Resumo da Venda
                            </h2>

                            <div className="space-y-3">
                                <div className="flex justify-between text-gray-600 dark:text-gray-400">
                                    <span>Subtotal</span>
                                    <span className="font-medium text-gray-800 dark:text-white">
                                        {formatCurrency(subtotal)}
                                    </span>
                                </div>

                                {descontoItens > 0 && (
                                    <div className="flex justify-between text-sm">
                                        <span className="text-yellow-600 dark:text-yellow-400">Desconto em itens</span>
                                        <span className="text-yellow-600 dark:text-yellow-400">
                                            -{formatCurrency(descontoItens)}
                                        </span>
                                    </div>
                                )}

                                <div className="border-t border-gray-200 dark:border-gray-700 pt-3">
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-gray-600 dark:text-gray-400">Desconto Geral</span>
                                        <div className="flex items-center space-x-2">
                                            <button
                                                onClick={() => setDescontoPercentual(!descontoPercentual)}
                                                className={`px-3 py-1 text-xs rounded transition ${
                                                    descontoPercentual
                                                        ? 'bg-blue-500 text-white'
                                                        : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                                                }`}
                                            >
                                                {descontoPercentual ? '%' : 'R$'}
                                            </button>
                                            <input
                                                type="number"
                                                value={descontoGeral}
                                                onChange={(e) => setDescontoGeral(parseFloat(e.target.value) || 0)}
                                                onBlur={handleAplicarDesconto}
                                                className="w-24 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded text-right bg-white dark:bg-gray-700 text-gray-800 dark:text-white"
                                                step="0.01"
                                                min="0"
                                                max={descontoPercentual ? "100" : subtotal.toString()}
                                            />
                                        </div>
                                    </div>
                                    {descontoGeralCalculado > 0 && (
                                        <div className="text-right">
                                            <span className="text-sm text-red-500">
                                                -{formatCurrency(descontoGeralCalculado)}
                                            </span>
                                            {descontoAprovado && (
                                                <span className="ml-2 text-xs px-2 py-0.5 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded">
                                                    ✓ Aprovado
                                                </span>
                                            )}
                                        </div>
                                    )}
                                </div>

                                {descontoTotal > 0 && (
                                    <div className="flex justify-between text-sm font-medium text-red-600 dark:text-red-400">
                                        <span>Total em Descontos</span>
                                        <span>-{formatCurrency(descontoTotal)}</span>
                                    </div>
                                )}

                                <div className="border-t border-gray-200 dark:border-gray-700 pt-3">
                                    <div className="flex justify-between items-center">
                                        <span className="text-lg font-semibold text-gray-800 dark:text-white">
                                            Total a Pagar
                                        </span>
                                        <span className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                                            {formatCurrency(total)}
                                        </span>
                                    </div>
                                </div>

                                {/* Indicador de permissões */}
                                {configuracoes && (
                                    <div className={`mt-4 p-3 rounded-lg ${
                                        configuracoes.funcionario.role === 'ADMIN' 
                                            ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
                                            : 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800'
                                    }`}>
                                        <div className="flex items-center justify-between text-xs">
                                            <div className="flex items-center space-x-2">
                                                <Tag className="w-4 h-4" />
                                                <span className={
                                                    configuracoes.funcionario.role === 'ADMIN'
                                                        ? 'text-green-700 dark:text-green-300 font-semibold'
                                                        : 'text-blue-700 dark:text-blue-300'
                                                }>
                                                    {configuracoes.funcionario.role === 'ADMIN' 
                                                        ? '👑 Admin - Desconto Ilimitado'
                                                        : `Limite de desconto: ${configuracoes.funcionario.limite_desconto}%`
                                                    }
                                                </span>
                                            </div>
                                            {configuracoes.funcionario.role === 'ADMIN' && (
                                                <span className="px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full text-xs font-bold">
                                                    ✓ Sem Limite
                                                </span>
                                            )}
                                        </div>
                                        {configuracoes.funcionario.role !== 'ADMIN' && descontoGeralCalculado > 0 && (
                                            <div className="mt-2">
                                                <div className="flex justify-between text-xs mb-1">
                                                    <span className="text-gray-600 dark:text-gray-400">
                                                        Desconto usado: {((descontoGeralCalculado / subtotal) * 100).toFixed(1)}%
                                                    </span>
                                                    <span className={`font-semibold ${
                                                        ((descontoGeralCalculado / subtotal) * 100) > configuracoes.funcionario.limite_desconto
                                                            ? 'text-red-600 dark:text-red-400'
                                                            : 'text-green-600 dark:text-green-400'
                                                    }`}>
                                                        {((descontoGeralCalculado / subtotal) * 100) > configuracoes.funcionario.limite_desconto
                                                            ? '⚠️ Requer autorização'
                                                            : '✓ Dentro do limite'
                                                        }
                                                    </span>
                                                </div>
                                                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                                                    <div
                                                        className={`h-2 rounded-full transition-all ${
                                                            ((descontoGeralCalculado / subtotal) * 100) > configuracoes.funcionario.limite_desconto
                                                                ? 'bg-red-500'
                                                                : 'bg-green-500'
                                                        }`}
                                                        style={{
                                                            width: `${Math.min(100, ((descontoGeralCalculado / subtotal) * 100 / configuracoes.funcionario.limite_desconto) * 100)}%`
                                                        }}
                                                    ></div>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Forma de Pagamento */}
                        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-lg font-semibold text-gray-800 dark:text-white">
                                    Forma de Pagamento
                                </h2>
                                <button
                                    onClick={() => setFormaPagamentoAberta(!formaPagamentoAberta)}
                                    className="text-sm text-blue-500 hover:text-blue-600 font-medium"
                                >
                                    {formaPagamentoAberta ? 'Fechar' : 'Alterar'}
                                </button>
                            </div>

                            {formaPagamentoAberta ? (
                                <div className="space-y-2">
                                    {formasPagamento.map((forma) => (
                                        <button
                                            key={forma.tipo}
                                            onClick={() => {
                                                setFormaPagamentoSelecionada(forma.tipo);
                                                setFormaPagamentoAberta(false);
                                                if (!forma.permite_troco) {
                                                    setValorRecebido(0);
                                                }
                                            }}
                                            className={`w-full p-4 rounded-lg flex items-center justify-between transition ${
                                                formaPagamentoSelecionada === forma.tipo
                                                    ? 'bg-blue-50 dark:bg-blue-900/20 border-2 border-blue-500'
                                                    : 'border-2 border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700'
                                            }`}
                                        >
                                            <div className="flex items-center space-x-3">
                                                {renderIconPagamento(forma.tipo)}
                                                <span className="font-medium text-gray-800 dark:text-white">
                                                    {forma.label}
                                                </span>
                                            </div>
                                            {forma.taxa > 0 && (
                                                <span className="text-sm text-gray-500 dark:text-gray-400">
                                                    Taxa: {forma.taxa}%
                                                </span>
                                            )}
                                        </button>
                                    ))}
                                </div>
                            ) : (
                                <div className="p-4 bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-lg border border-blue-200 dark:border-blue-800">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center space-x-3">
                                            <div className="p-2 bg-blue-500 rounded-lg">
                                                {renderIconPagamento(formaPagamentoSelecionada)}
                                                <span className="sr-only">Ícone</span>
                                            </div>
                                            <div>
                                                <span className="font-semibold text-gray-800 dark:text-white block">
                                                    {formasPagamento.find(f => f.tipo === formaPagamentoSelecionada)?.label || formaPagamentoSelecionada}
                                                </span>
                                                {formasPagamento.find(f => f.tipo === formaPagamentoSelecionada)?.permite_troco && (
                                                    <span className="text-xs text-blue-600 dark:text-blue-400">
                                                        Aceita troco
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                        {(() => {
                                            const forma = formasPagamento.find(f => f.tipo === formaPagamentoSelecionada);
                                            return forma && forma.taxa > 0 ? (
                                                <span className="text-sm px-3 py-1 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 rounded-full">
                                                    Taxa: {forma.taxa}%
                                                </span>
                                            ) : null;
                                        })()}
                                    </div>
                                </div>
                            )}

                            {/* Campo de Valor Recebido para Dinheiro */}
                            {formasPagamento.find(f => f.tipo === formaPagamentoSelecionada)?.permite_troco && (
                                <div className="mt-4 p-4 bg-gradient-to-r from-yellow-50 to-yellow-100 dark:from-yellow-900/20 dark:to-yellow-800/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                        💵 Valor Recebido
                                    </label>
                                    <input
                                        type="number"
                                        value={valorRecebido}
                                        onChange={(e) => setValorRecebido(parseFloat(e.target.value) || 0)}
                                        className="w-full px-4 py-3 border-2 border-yellow-300 dark:border-yellow-700 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-transparent font-bold text-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-white"
                                        step="0.01"
                                        min="0"
                                        placeholder="0.00"
                                    />
                                    {troco > 0 && (
                                        <div className="mt-3 p-3 bg-green-100 dark:bg-green-900/30 rounded-lg border border-green-300 dark:border-green-700">
                                            <div className="flex items-center justify-between">
                                                <span className="text-sm font-medium text-green-700 dark:text-green-300">
                                                    Troco a devolver:
                                                </span>
                                                <span className="text-xl font-bold text-green-600 dark:text-green-400">
                                                    {formatCurrency(troco)}
                                                </span>
                                            </div>
                                        </div>
                                    )}
                                    {valorRecebido > 0 && valorRecebido < total && (
                                        <div className="mt-2 text-sm text-red-600 dark:text-red-400 flex items-center space-x-1">
                                            <AlertTriangle className="w-4 h-4" />
                                            <span>
                                                Faltam {formatCurrency(total - valorRecebido)}
                                            </span>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>

                        {/* Observações */}
                        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
                            <h2 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">
                                Observações
                            </h2>
                            <textarea
                                value={observacoes}
                                onChange={(e) => setObservacoes(e.target.value)}
                                placeholder="Observações sobre a venda..."
                                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent min-h-[100px]"
                                rows={3}
                            />
                        </div>

                        {/* Botões de Ação */}
                        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
                            <div className="space-y-4">
                                <button
                                    onClick={handleFinalizarVenda}
                                    disabled={carrinho.length === 0 || loading || enviandoEmail}
                                    className={`w-full py-4 rounded-lg font-bold text-lg flex items-center justify-center space-x-3 transition shadow-lg ${
                                        carrinho.length === 0 || loading || enviandoEmail
                                            ? 'bg-gray-300 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'
                                            : 'bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white'
                                    }`}
                                >
                                    {loading || enviandoEmail ? (
                                        <>
                                            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>
                                            <span>{enviandoEmail ? 'Enviando email...' : 'Processando...'}</span>
                                        </>
                                    ) : (
                                        <>
                                            <Check className="w-6 h-6" />
                                            <span>FINALIZAR VENDA</span>
                                        </>
                                    )}
                                </button>

                                <div className="grid grid-cols-2 gap-3">
                                    <button
                                        onClick={handleLimparCarrinho}
                                        disabled={carrinho.length === 0 || loading || enviandoEmail}
                                        className={`py-3 rounded-lg font-medium flex items-center justify-center space-x-2 transition ${
                                            carrinho.length === 0 || loading || enviandoEmail
                                                ? 'bg-gray-200 dark:bg-gray-700 text-gray-400 dark:text-gray-500 cursor-not-allowed'
                                                : 'bg-red-50 dark:bg-red-900/30 hover:bg-red-100 dark:hover:bg-red-900/50 text-red-600 dark:text-red-400'
                                        }`}
                                    >
                                        <X className="w-5 h-5" />
                                        <span>Cancelar</span>
                                    </button>

                                    <button
                                        disabled={carrinho.length === 0}
                                        className={`py-3 rounded-lg font-medium flex items-center justify-center space-x-2 transition ${
                                            carrinho.length === 0
                                                ? 'bg-gray-200 dark:bg-gray-700 text-gray-400 dark:text-gray-500 cursor-not-allowed'
                                                : 'bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300'
                                        }`}
                                    >
                                        <Printer className="w-5 h-5" />
                                        <span>Imprimir</span>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Modal de Autorização de Gerente */}
                {mostrarAutorizacao && (
                    <GerenteAuthModal
                        acao="desconto"
                        valorDesconto={descontoGeralCalculado}
                        onAutorizado={handleAutorizacaoAprovada}
                        onCancelar={() => {
                            setMostrarAutorizacao(false);
                            setDescontoGeral(0);
                        }}
                    />
                )}

                {/* Modal de Confirmação de Envio de Email */}
                {mostrarModalEmail && (
                    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-md w-full p-6 animate-fadeIn">
                            <div className="text-center mb-6">
                                <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                                    <Mail className="w-8 h-8 text-blue-600 dark:text-blue-400" />
                                </div>
                                <h3 className="text-xl font-bold text-gray-800 dark:text-white mb-2">
                                    Enviar Cupom Fiscal por Email?
                                </h3>
                                <p className="text-gray-600 dark:text-gray-400">
                                    Deseja enviar o cupom fiscal para o email do cliente?
                                </p>
                                <p className="text-sm font-medium text-blue-600 dark:text-blue-400 mt-2">
                                    📧 {cliente?.email}
                                </p>
                            </div>

                            <div className="grid grid-cols-2 gap-3">
                                <button
                                    onClick={() => handleEnviarEmail(false)}
                                    disabled={enviandoEmail}
                                    className="px-6 py-3 rounded-lg font-medium transition bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 disabled:opacity-50"
                                >
                                    Não, obrigado
                                </button>
                                <button
                                    onClick={() => handleEnviarEmail(true)}
                                    disabled={enviandoEmail}
                                    className="px-6 py-3 rounded-lg font-medium transition bg-blue-500 hover:bg-blue-600 text-white disabled:opacity-50 flex items-center justify-center space-x-2"
                                >
                                    {enviandoEmail ? (
                                        <>
                                            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                                            <span>Enviando...</span>
                                        </>
                                    ) : (
                                        <>
                                            <Mail className="w-5 h-5" />
                                            <span>Sim, enviar</span>
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default PDVPage;