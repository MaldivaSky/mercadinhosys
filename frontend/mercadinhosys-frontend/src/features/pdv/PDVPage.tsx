import React, { useState } from 'react';
import { showToast } from '../../utils/toast';
import {
    ShoppingCart,
    Check,
    CreditCard,
    DollarSign,
    Smartphone,
    User,
    Tag,
    Mail,
    X,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import ProdutoSearch from './components/ProdutoSearch';
import CarrinhoItem from './components/CarrinhoItem';
import ClienteSelect from './components/ClienteSelect';
import CaixaHeader from './components/CaixaHeader';
import NotaFiscalModal from './components/NotaFiscalModal';
import { usePDV } from '../../hooks/usePDV';
import { formatCurrency } from '../../utils/formatters';
import { pdvService } from './pdvService';
import PDVSkeleton from './components/PDVSkeleton';

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
        configuracoes,
        loading,
        subtotal,
        total,
        troco,
        adicionarProduto,
        removerProduto,
        atualizarQuantidade,
        aplicarDescontoItem,
        limparCarrinho,
        emailRecibo,
        setEmailRecibo,
        finalizarVenda,
    } = usePDV();

    const [formaPagamentoAberta, setFormaPagamentoAberta] = useState(false);
    const [activeSection, setActiveSection] = useState<'cliente' | 'pagamento'>('pagamento');
    const [enviandoEmail, setEnviandoEmail] = useState(false);
    const [mostrarModalNotaFiscal, setMostrarModalNotaFiscal] = useState(false);
    const [vendaFinalizada, setVendaFinalizada] = useState<{ id: number; codigo: string } | null>(null);

    const handleFinalizarVenda = async () => {
        if (carrinho.length === 0) return showToast.error('Carrinho vazio');
        if (!formaPagamentoSelecionada) {
            showToast.warning('Selecione uma forma de pagamento');
            setActiveSection('pagamento');
            setFormaPagamentoAberta(true);
            return;
        }

        try {
            const venda = await finalizarVenda();
            if (venda) {
                setVendaFinalizada(venda);
                showToast.success('Venda concluída!');
                setFormaPagamentoAberta(false);
                setMostrarModalNotaFiscal(true);
            }
        } catch (error: any) {
            showToast.error(error.message || 'Erro ao finalizar venda');
        }
    };

    const handleLimparCarrinho = () => {
        if (carrinho.length > 0 && confirm('Deseja realmente cancelar esta venda?')) {
            limparCarrinho();
            showToast.info('Venda cancelada');
        }
    };

    const renderIconPagamento = (tipo: string) => {
        switch (tipo) {
            case 'dinheiro': return <DollarSign className="w-6 h-6" />;
            case 'cartao_credito':
            case 'cartao_debito': return <CreditCard className="w-6 h-6" />;
            case 'pix': return <Smartphone className="w-6 h-6" />;
            default: return <Tag className="w-6 h-6" />;
        }
    };

    if (loading && !configuracoes) return <PDVSkeleton />;

    return (
        <div className="h-screen bg-slate-50 dark:bg-slate-950 flex flex-col overflow-hidden font-sans text-slate-900 dark:text-slate-100">
            <CaixaHeader
                funcionarioNome={configuracoes?.funcionario.nome}
                funcionarioRole={configuracoes?.funcionario.role}
            />

            <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 overflow-hidden border-t border-slate-200 dark:border-slate-800">
                {/* 🛒 LISTAGEM DE ITENS (FOCO TOTAL) */}
                <div className="lg:col-span-10 flex flex-col bg-white dark:bg-slate-900 overflow-hidden">
                    <div className="p-3 bg-slate-50 dark:bg-slate-900/50 border-b border-slate-200 dark:border-slate-800">
                        <ProdutoSearch onProdutoSelecionado={adicionarProduto} />
                    </div>

                    <div className="flex-1 overflow-y-auto custom-scrollbar">
                        {carrinho.length === 0 ? (
                            <div className="h-full flex flex-col items-center justify-center opacity-20 pointer-events-none">
                                <ShoppingCart className="w-24 h-24 mb-4 text-slate-400" />
                                <h3 className="text-3xl font-black uppercase tracking-tighter">Aguardando Produtos</h3>
                            </div>
                        ) : (
                            <div className="divide-y divide-slate-100 dark:divide-slate-800">
                                {carrinho.map((item: any) => (
                                    <CarrinhoItem
                                        key={item.produto.id}
                                        produto={item.produto}
                                        quantidade={item.quantidade}
                                        precoUnitario={item.precoUnitario}
                                        desconto={item.desconto}
                                        total={item.total}
                                        onAtualizarQuantidade={(qtd) => atualizarQuantidade(item.produto.id, qtd)}
                                        onRemover={() => removerProduto(item.produto.id)}
                                        onAplicarDesconto={(val, perc) => aplicarDescontoItem(item.produto.id, val, perc)}
                                    />
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* 🏷️ RESUMO LATERAL (PROFISSIONAL E SÓBRIO) */}
                <div className="hidden lg:flex lg:col-span-2 flex-col bg-slate-50 dark:bg-slate-950 border-l border-slate-200 dark:border-slate-800">
                    <div className="flex-1 p-6 flex flex-col justify-end gap-6">
                        <div className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-xl shadow-slate-200/50 dark:shadow-none text-center">
                            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-1">Total a Pagar</span>
                            <span className="text-4xl font-black text-red-600 dark:text-red-400 tabular-nums">
                                {formatCurrency(total)}
                            </span>
                        </div>

                        <div className="space-y-3">
                            <button
                                onClick={() => {
                                    setFormaPagamentoAberta(true);
                                    setActiveSection('pagamento');
                                }}
                                className="w-full h-16 bg-red-600 hover:bg-red-700 text-white rounded-2xl flex items-center justify-center gap-3 font-bold uppercase text-xs tracking-widest shadow-lg shadow-red-500/20 active:scale-95 transition-all"
                            >
                                <CreditCard className="w-5 h-5" />
                                <span>Pagar (F4)</span>
                            </button>
                            <button
                                onClick={handleLimparCarrinho}
                                className="w-full py-3 text-slate-400 hover:text-red-500 font-bold text-[10px] uppercase tracking-widest transition-all"
                            >
                                Cancelar Venda
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* 💳 CHECKOUT DRAWER (DESIGN PRÊMIUM E ACESSÍVEL) */}
            <AnimatePresence>
                {formaPagamentoAberta && (
                    <>
                        <motion.div
                            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                            onClick={() => setFormaPagamentoAberta(false)}
                            className="fixed inset-0 bg-slate-900/60 backdrop-blur-md z-[90]"
                        />
                        <motion.div
                            initial={{ x: '100%' }} animate={{ x: 0 }} exit={{ x: '100%' }}
                            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
                            className="fixed top-0 right-0 bottom-0 w-full sm:w-[480px] bg-white dark:bg-slate-900 shadow-2xl z-[100] flex flex-col"
                        >
                            {/* Drawer Header */}
                            <div className="p-6 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 bg-slate-900 dark:bg-white rounded-xl flex items-center justify-center text-white dark:text-slate-900">
                                        <Check className="w-6 h-6" />
                                    </div>
                                    <h3 className="text-xl font-black uppercase tracking-tight text-slate-900 dark:text-white">Checkout</h3>
                                </div>
                                <button
                                    onClick={() => setFormaPagamentoAberta(false)}
                                    className="p-3 bg-slate-50 dark:bg-slate-800 rounded-xl text-slate-400 hover:text-slate-900 dark:hover:text-white transition-all"
                                >
                                    <X className="w-6 h-6" />
                                </button>
                            </div>

                            <div className="flex-1 overflow-y-auto p-6 space-y-6">
                                {/* SEÇÃO: CLIENTE */}
                                <div className="bg-slate-50 dark:bg-slate-800/50 rounded-3xl border border-slate-200 dark:border-slate-800 overflow-hidden">
                                    <button
                                        onClick={() => setActiveSection(activeSection === 'cliente' ? 'pagamento' : 'cliente')}
                                        className="w-full p-5 flex items-center justify-between hover:bg-slate-100 dark:hover:bg-slate-800/80 transition-all"
                                    >
                                        <div className="flex items-center gap-4">
                                            <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${cliente ? 'bg-green-100 text-green-600' : 'bg-slate-200 text-slate-500'}`}>
                                                <User className="w-5 h-5" />
                                            </div>
                                            <div className="text-left">
                                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Identificação</p>
                                                <p className="text-sm font-black text-slate-700 dark:text-slate-200 uppercase">{cliente?.nome || 'Consumidor Final'}</p>
                                            </div>
                                        </div>
                                        <Check className={`w-5 h-5 ${cliente ? 'text-green-500' : 'text-slate-200'}`} />
                                    </button>
                                    <AnimatePresence>
                                        {activeSection === 'cliente' && (
                                            <motion.div
                                                initial={{ height: 0, opacity: 0 }}
                                                animate={{ height: 'auto', opacity: 1 }}
                                                exit={{ height: 0, opacity: 0 }}
                                                className="p-5 pt-0 overflow-visible"
                                            >
                                                <div className="pt-4 border-t border-slate-200 dark:border-slate-700">
                                                    <ClienteSelect cliente={cliente} onClienteSelecionado={(c: any) => { setCliente(c); setActiveSection('pagamento'); }} />
                                                </div>
                                            </motion.div>
                                        )}
                                    </AnimatePresence>
                                </div>

                                {/* SEÇÃO: FORMA DE PAGAMENTO */}
                                <div className="bg-slate-50 dark:bg-slate-800/50 rounded-3xl border border-slate-200 dark:border-slate-800 overflow-hidden">
                                    <button
                                        onClick={() => setActiveSection(activeSection === 'pagamento' ? 'cliente' : 'pagamento')}
                                        className="w-full p-5 flex items-center justify-between hover:bg-slate-100 dark:hover:bg-slate-800/80 transition-all"
                                    >
                                        <div className="flex items-center gap-4">
                                            <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${formaPagamentoSelecionada ? 'bg-blue-100 text-blue-600' : 'bg-slate-200 text-slate-500'}`}>
                                                <CreditCard className="w-5 h-5" />
                                            </div>
                                            <div className="text-left">
                                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Pagamento</p>
                                                <p className="text-sm font-black text-slate-700 dark:text-slate-200 uppercase">
                                                    {formasPagamento.find((f: any) => f.tipo === formaPagamentoSelecionada)?.label || 'Selecione a Forma'}
                                                </p>
                                            </div>
                                        </div>
                                        <Check className={`w-5 h-5 ${formaPagamentoSelecionada ? 'text-green-500' : 'text-slate-200'}`} />
                                    </button>
                                    <AnimatePresence>
                                        {activeSection === 'pagamento' && (
                                            <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }} className="overflow-hidden p-5 pt-0">
                                                <div className="pt-4 border-t border-slate-200 dark:border-slate-700 grid grid-cols-2 gap-3">
                                                    {formasPagamento.map((forma: any) => (
                                                        <button
                                                            key={forma.tipo}
                                                            onClick={() => setFormaPagamentoSelecionada(forma.tipo)}
                                                            className={`p-4 rounded-2xl border-2 flex flex-col items-center gap-3 transition-all ${formaPagamentoSelecionada === forma.tipo ? 'border-blue-600 bg-white dark:bg-slate-900 shadow-lg' : 'border-transparent bg-slate-200/50 dark:bg-slate-700/50 hover:bg-slate-200'}`}
                                                        >
                                                            <div className={formaPagamentoSelecionada === forma.tipo ? 'text-blue-600' : 'text-slate-400'}>
                                                                {renderIconPagamento(forma.tipo)}
                                                            </div>
                                                            <span className={`text-[10px] font-black uppercase tracking-wider text-center ${formaPagamentoSelecionada === forma.tipo ? 'text-blue-600' : 'text-slate-500'}`}>
                                                                {forma.label}
                                                            </span>
                                                        </button>
                                                    ))}
                                                </div>

                                                {formasPagamento.find((f: any) => f.tipo === formaPagamentoSelecionada)?.permite_troco && (
                                                    <div className="mt-6 p-6 bg-white dark:bg-slate-900 rounded-3xl border border-blue-500/10 shadow-2xl">
                                                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3 block">Cédula / Valor Recebido</span>
                                                        <input
                                                            type="number"
                                                            value={valorRecebido || ''}
                                                            onChange={(e) => setValorRecebido(parseFloat(e.target.value) || 0)}
                                                            className="w-full text-5xl font-black text-blue-600 dark:text-blue-400 bg-transparent border-none p-0 outline-none tabular-nums text-right"
                                                            placeholder="0,00"
                                                            autoFocus
                                                        />
                                                        {valorRecebido > 0 && (
                                                            <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800 flex justify-between items-center px-2">
                                                                <span className="text-xs font-black text-slate-400 uppercase">Troco</span>
                                                                <span className="text-3xl font-black text-green-500 tabular-nums">
                                                                    {formatCurrency(troco)}
                                                                </span>
                                                            </div>
                                                        )}
                                                    </div>
                                                )}
                                            </motion.div>
                                        )}
                                    </AnimatePresence>
                                </div>
                            </div>

                            {/* Drawer Footer */}
                            <div className="p-6 border-t border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/50 space-y-5">
                                {/* 📧 ENVIO DE RECIBO (ELITE UX) */}
                                <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
                                    <div className="flex items-center gap-2 mb-2 px-1">
                                        <Mail className="w-4 h-4 text-blue-500" />
                                        <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Enviar Comprovante</span>
                                    </div>
                                    <input
                                        type="email"
                                        value={emailRecibo}
                                        onChange={(e) => setEmailRecibo(e.target.value)}
                                        placeholder="E-mail para envio (Opcional)"
                                        className="w-full h-11 px-4 rounded-xl bg-slate-50 dark:bg-slate-800 border-none text-sm focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                                    />
                                </div>

                                <div className="flex justify-between items-center px-1">
                                    <div className="flex flex-col">
                                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Subtotal</span>
                                        <span className="text-md font-bold text-slate-500 tabular-nums">{formatCurrency(subtotal)}</span>
                                    </div>
                                    <div className="text-right">
                                        <span className="text-[10px] font-black text-red-600 uppercase tracking-widest block mb-1">Total a Pagar</span>
                                        <span className="text-4xl font-black text-slate-900 dark:text-white tabular-nums tracking-tighter leading-none">
                                            {formatCurrency(total)}
                                        </span>
                                    </div>
                                </div>

                                <button
                                    onClick={handleFinalizarVenda}
                                    disabled={carrinho.length === 0 || loading}
                                    className={`w-full h-16 rounded-2xl flex items-center justify-center gap-3 text-lg font-black uppercase tracking-widest shadow-xl transition-all active:scale-[0.98] ${carrinho.length === 0 || loading ? 'bg-slate-200 text-slate-400' : 'bg-red-600 text-white hover:bg-red-700 shadow-red-500/20'}`}
                                >
                                    {loading ? (
                                        <div className="animate-spin rounded-full h-6 w-6 border-2 border-white/20 border-t-white" />
                                    ) : (
                                        <Check className="w-7 h-7" />
                                    )}
                                    <span>Concluir Venda</span>
                                </button>
                            </div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>

            <NotaFiscalModal
                mostrar={mostrarModalNotaFiscal}
                emailCliente={cliente?.email || emailRecibo}
                onFechar={() => {
                    setMostrarModalNotaFiscal(false);
                    setVendaFinalizada(null);
                    limparCarrinho();
                }}
                onImprimir={async () => {
                    if (!vendaFinalizada) return;
                    try {
                        const url = await pdvService.imprimirComprovante(vendaFinalizada.id);
                        window.open(url, '_blank');
                    } catch (error) {
                        showToast.error('Erro ao gerar comprovante');
                    }
                }}
                onEnviarEmail={async (email) => {
                    if (!vendaFinalizada) return;
                    setEnviandoEmail(true);
                    try {
                        await pdvService.enviarCupomFiscal(vendaFinalizada.id, email);
                        showToast.success('Nota fiscal enviada por e-mail!');
                        setMostrarModalNotaFiscal(false);
                        setVendaFinalizada(null);
                        limparCarrinho();
                    } catch (error: any) {
                        showToast.error(error.response?.data?.error || 'Erro ao enviar e-mail');
                    } finally {
                        setEnviandoEmail(false);
                    }
                }}
                enviando={enviandoEmail}
                onVisualizar={async () => {
                    if (!vendaFinalizada) return;
                    try {
                        const url = await pdvService.imprimirComprovante(vendaFinalizada.id);
                        window.open(url, '_blank');
                    } catch (error) {
                        showToast.error('Erro ao abrir comprovante profissional');
                    }
                }}
            />

            {/* MOBILE BAR */}
            <div className="lg:hidden fixed bottom-0 left-0 right-0 p-4 bg-white/90 dark:bg-slate-900/90 backdrop-blur-xl border-t border-slate-100 dark:border-slate-800 flex items-center justify-between z-50">
                <div className="flex flex-col pl-2">
                    <span className="text-[10px] font-bold text-slate-400 uppercase">Total Geral</span>
                    <span className="text-3xl font-black text-red-600 dark:text-red-400 tabular-nums">{formatCurrency(total)}</span>
                </div>
                <button
                    onClick={() => setFormaPagamentoAberta(true)}
                    className="h-14 px-10 bg-red-600 text-white rounded-2xl font-black uppercase text-xs tracking-widest shadow-xl shadow-red-500/20"
                >
                    Pagar
                </button>
            </div>
        </div>
    );
};

export default PDVPage;
