import React, { useState, useEffect } from 'react';
import {
    ShoppingCart,
    Printer,
    X,
    Check,
    CreditCard,
    DollarSign,
    Smartphone,
    TrendingUp
} from 'lucide-react';
import ProdutoSearch from './components/ProdutoSearch';
import CarrinhoItem from './components/CarrinhoItem';
import ClienteSelect from './components/ClienteSelect';
import { usePDV } from '../../hooks/usePDV';
import { Produto } from '../../types';
import { formatCurrency } from '../../utils/formatters';

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
    } = usePDV();

    const [loading, setLoading] = useState(false);
    const [mensagem, setMensagem] = useState<{ tipo: 'success' | 'error'; texto: string } | null>(null);
    const [formaPagamentoAberta, setFormaPagamentoAberta] = useState(false);

    const handleProdutoSelecionado = (produto: Produto) => {
        if (produto.quantidade_estoque <= 0) {
            setMensagem({ tipo: 'error', texto: 'Produto sem estoque disponível' });
            return;
        }
        adicionarProduto(produto);
        setMensagem({ tipo: 'success', texto: `${produto.nome} adicionado ao carrinho` });
    };

    const handleFinalizarVenda = async () => {
        try {
            setLoading(true);
            const venda = await finalizarVenda();

            setMensagem({
                tipo: 'success',
                texto: `Venda ${venda.codigo} finalizada com sucesso! Total: ${formatCurrency(venda.total)}`
            });

            // Limpar carrinho após sucesso
            setTimeout(() => {
                limparCarrinho();
                setMensagem(null);
            }, 3000);

        } catch (error: any) {
            setMensagem({
                tipo: 'error',
                texto: error.message || 'Erro ao finalizar venda'
            });
        } finally {
            setLoading(false);
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
                {/* Cabeçalho */}
                <div className="flex items-center justify-between mb-8">
                    <div className="flex items-center space-x-4">
                        <div className="p-3 bg-blue-500 rounded-lg">
                            <ShoppingCart className="w-8 h-8 text-white" />
                        </div>
                        <div>
                            <h1 className="text-2xl font-bold text-gray-800 dark:text-white">
                                Ponto de Venda (PDV)
                            </h1>
                            <p className="text-gray-600 dark:text-gray-400">
                                Sistema de vendas integrado
                            </p>
                        </div>
                    </div>

                    <div className="flex items-center space-x-4">
                        <button
                            onClick={limparCarrinho}
                            className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 flex items-center space-x-2"
                            disabled={carrinho.length === 0}
                        >
                            <X className="w-5 h-5" />
                            <span>Cancelar Venda</span>
                        </button>
                    </div>
                </div>

                {/* Mensagens */}
                {mensagem && (
                    <div className={`mb-6 p-4 rounded-lg ${mensagem.tipo === 'success'
                            ? 'bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-300'
                            : 'bg-red-100 dark:bg-red-900/20 text-red-800 dark:text-red-300'
                        }`}>
                        <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-2">
                                {mensagem.tipo === 'success' ? (
                                    <Check className="w-5 h-5" />
                                ) : (
                                    <X className="w-5 h-5" />
                                )}
                                <span>{mensagem.texto}</span>
                            </div>
                            <button onClick={() => setMensagem(null)}>
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                    </div>
                )}

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
                                <div className="flex justify-between">
                                    <span className="text-gray-600 dark:text-gray-400">Subtotal</span>
                                    <span className="font-medium text-gray-800 dark:text-white">
                                        {formatCurrency(subtotal)}
                                    </span>
                                </div>

                                <div className="border-t border-gray-200 dark:border-gray-700 pt-3">
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-gray-600 dark:text-gray-400">Desconto Geral</span>
                                        <div className="flex items-center space-x-2">
                                            <button
                                                onClick={() => setDescontoPercentual(!descontoPercentual)}
                                                className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 rounded"
                                            >
                                                {descontoPercentual ? '%' : 'R$'}
                                            </button>
                                            <input
                                                type="number"
                                                value={descontoGeral}
                                                onChange={(e) => setDescontoGeral(parseFloat(e.target.value) || 0)}
                                                className="w-24 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded text-right"
                                                step="0.01"
                                                min="0"
                                            />
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <span className="text-red-500">
                                            -{formatCurrency(descontoTotal)}
                                        </span>
                                    </div>
                                </div>

                                <div className="border-t border-gray-200 dark:border-gray-700 pt-3">
                                    <div className="flex justify-between">
                                        <span className="text-lg font-semibold text-gray-800 dark:text-white">
                                            Total
                                        </span>
                                        <span className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                                            {formatCurrency(total)}
                                        </span>
                                    </div>
                                </div>
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
                                    className="text-sm text-blue-500 hover:text-blue-600"
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
                                            }}
                                            className={`w-full p-3 rounded-lg flex items-center justify-between ${formaPagamentoSelecionada === forma.tipo
                                                    ? 'bg-blue-50 dark:bg-blue-900/20 border border-blue-500'
                                                    : 'border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700'
                                                }`}
                                        >
                                            <div className="flex items-center space-x-3">
                                                {renderIconPagamento(forma.tipo)}
                                                <span className="font-medium">{forma.label}</span>
                                            </div>
                                            {forma.taxa > 0 && (
                                                <span className="text-sm text-gray-500">
                                                    Taxa: {forma.taxa}%
                                                </span>
                                            )}
                                        </button>
                                    ))}
                                </div>
                            ) : (
                                <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center space-x-3">
                                            {renderIconPagamento(formaPagamentoSelecionada)}
                                            <span className="font-medium">
                                                {formasPagamento.find(f => f.tipo === formaPagamentoSelecionada)?.label || formaPagamentoSelecionada}
                                            </span>
                                        </div>
                                        {formasPagamento.find(f => f.tipo === formaPagamentoSelecionada)?.taxa > 0 && (
                                            <span className="text-sm text-gray-500">
                                                Taxa: {formasPagamento.find(f => f.tipo === formaPagamentoSelecionada)?.taxa}%
                                            </span>
                                        )}
                                    </div>
                                </div>
                            )}

                            {formaPagamentoSelecionada === 'dinheiro' && (
                                <div className="mt-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                        Valor Recebido
                                    </label>
                                    <input
                                        type="number"
                                        value={valorRecebido}
                                        onChange={(e) => setValorRecebido(parseFloat(e.target.value) || 0)}
                                        className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                        step="0.01"
                                        min="0"
                                    />
                                    {troco > 0 && (
                                        <div className="mt-2 text-center">
                                            <span className="text-sm text-gray-500">Troco:</span>
                                            <span className="ml-2 font-bold text-green-600 dark:text-green-400">
                                                {formatCurrency(troco)}
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
                                    disabled={carrinho.length === 0 || loading}
                                    className={`w-full py-4 rounded-lg font-semibold flex items-center justify-center space-x-3 ${carrinho.length === 0 || loading
                                            ? 'bg-gray-300 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'
                                            : 'bg-green-500 hover:bg-green-600 text-white'
                                        }`}
                                >
                                    {loading ? (
                                        <>
                                            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                                            <span>Processando...</span>
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
                                        onClick={limparCarrinho}
                                        disabled={carrinho.length === 0}
                                        className={`py-3 rounded-lg font-medium flex items-center justify-center space-x-2 ${carrinho.length === 0
                                                ? 'bg-gray-200 dark:bg-gray-700 text-gray-400 dark:text-gray-500 cursor-not-allowed'
                                                : 'bg-red-500 hover:bg-red-600 text-white'
                                            }`}
                                    >
                                        <X className="w-5 h-5" />
                                        <span>Cancelar</span>
                                    </button>

                                    <button
                                        onClick={() => {
                                            // TODO: Implementar impressão
                                            setMensagem({ tipo: 'success', texto: 'Função de impressão em desenvolvimento' });
                                        }}
                                        disabled={carrinho.length === 0}
                                        className={`py-3 rounded-lg font-medium flex items-center justify-center space-x-2 ${carrinho.length === 0
                                                ? 'bg-gray-200 dark:bg-gray-700 text-gray-400 dark:text-gray-500 cursor-not-allowed'
                                                : 'bg-blue-500 hover:bg-blue-600 text-white'
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
            </div>
        </div>
    );
};

export default PDVPage;