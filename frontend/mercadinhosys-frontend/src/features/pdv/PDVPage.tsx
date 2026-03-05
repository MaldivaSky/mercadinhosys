import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { showToast } from '../../utils/toast';
import {
    ShoppingCart,
    Check,
    CreditCard,
    DollarSign,
    Smartphone,
    User,
    Tag,
    X,
    Plus,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import ProdutoSearch from './components/ProdutoSearch';
import CarrinhoItem from './components/CarrinhoItem';
import ClienteSelect from './components/ClienteSelect';
import CaixaHeader from './components/CaixaHeader';
import NotaFiscalModal from './components/NotaFiscalModal';
import CupomFiscalModal from './components/CupomFiscalModal';
import PesoInputModal from './components/PesoInputModal';
import { usePDV } from '../../hooks/usePDV';
import { formatCurrency } from '../../utils/formatters';
import { pdvService } from './pdvService';
import PDVSkeleton from './components/PDVSkeleton';
import CaixaManager from './components/CaixaManager';

const PDVPage: React.FC = () => {

    const {
        sessoes,
        sessaoAtivaId,
        adicionarSessao,
        alternarSessao,
        removerSessao,
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
        finalizarVenda,
        caixaAberto,
        setCaixaAberto,
    } = usePDV();

    const [formaPagamentoAberta, setFormaPagamentoAberta] = useState(false);
    const [activeSection, setActiveSection] = useState<'cliente' | 'pagamento'>('pagamento');
    const [enviandoEmail, setEnviandoEmail] = useState(false);
    const [mostrarModalNotaFiscal, setMostrarModalNotaFiscal] = useState(false);
    const [vendaFinalizada, setVendaFinalizada] = useState<{ id: number; codigo: string } | null>(null);
    const [managerCaixaAberto, setManagerCaixaAberto] = useState(false);
    const [dataVencimentoFiado, setDataVencimentoFiado] = useState('');  // data prevista pagamento do fiado
    const [cupomModalAberto, setCupomModalAberto] = useState(false);
    const [mostrarModalPeso, setMostrarModalPeso] = useState(false);
    const [produtoPendentePeso, setProdutoPendentePeso] = useState<any>(null);

    const isFiado = formaPagamentoSelecionada === 'fiado';

    const location = useLocation();
    const navigate = useNavigate();

    useEffect(() => {
        const params = new URLSearchParams(location.search);
        if (params.get('manage') === 'true') {
            setManagerCaixaAberto(true);
            // Optionally remove the parameter from the URL so it doesn't stay
            navigate('/pdv', { replace: true });
        }
    }, [location.search, navigate]);

    const handleFinalizarVenda = async () => {
        if (carrinho.length === 0) return showToast.error('Carrinho vazio');
        if (!formaPagamentoSelecionada) {
            showToast.warning('Selecione uma forma de pagamento');
            setActiveSection('pagamento');
            setFormaPagamentoAberta(true);
            return;
        }
        // Validação de Fiado: cliente obrigatório
        if (isFiado && !cliente) {
            showToast.error('Selecione um cliente cadastrado para vender no Fiado!');
            setActiveSection('cliente');
            return;
        }

        try {
            const venda = await showToast.promise(
                finalizarVenda({ data_vencimento_fiado: isFiado && dataVencimentoFiado ? dataVencimentoFiado : undefined }),
                {
                    loading: 'Finalizando venda...',
                    success: 'Venda concluída com sucesso!',
                    error: (err: any) => err.message || 'Erro ao finalizar venda'
                }
            );

            if (venda) {
                setVendaFinalizada(venda);
                setFormaPagamentoAberta(false);
                setMostrarModalNotaFiscal(true);
                setDataVencimentoFiado('');
            }
        } catch (error: any) {
            // 403 com CAIXA_FECHADO → avisar e abrir o gestor de caixa
            const errData = error?.response?.data;
            if (error?.response?.status === 403 && errData?.error === 'CAIXA_FECHADO') {
                showToast.error('⚠️ Caixa fechado! Abra o caixa antes de registrar vendas.', { duration: 6000 });
                setFormaPagamentoAberta(false);
                setManagerCaixaAberto(true);
                return;
            }
            // Outros erros já tratados pelo promise
        }
    };

    const handleLimparCarrinho = () => {
        if (carrinho.length > 0 && confirm('Deseja realmente cancelar esta venda?')) {
            limparCarrinho();
            showToast.warning('Venda cancelada');
        }
    };

    const handleProdutoSelecionado = (p: any) => {
        const aGranel = ['KG', 'G', 'L', 'ML'].includes(p.unidade_medida?.toUpperCase()) || p.tipo === 'granel';

        if (aGranel) {
            setProdutoPendentePeso(p);
            setMostrarModalPeso(true);
        } else {
            adicionarProduto(p, 1);
        }
    };

    const handleConfirmarPeso = (peso: number) => {
        if (produtoPendentePeso) {
            adicionarProduto(produtoPendentePeso, peso);
            setProdutoPendentePeso(null);
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
            <CaixaManager
                caixaAtual={caixaAberto}
                setCaixaAtual={setCaixaAberto}
                isOpen={managerCaixaAberto}
                onClose={() => setManagerCaixaAberto(false)}
            />

            <PesoInputModal
                isOpen={mostrarModalPeso}
                onClose={() => { setMostrarModalPeso(false); setProdutoPendentePeso(null); }}
                onConfirm={handleConfirmarPeso}
                produto={produtoPendentePeso}
            />

            <CaixaHeader
                funcionarioNome={configuracoes?.funcionario.nome}
                funcionarioRole={configuracoes?.funcionario.role}
                onOpenCaixaManager={() => setManagerCaixaAberto(true)}
            />

            <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 overflow-hidden border-t border-slate-200 dark:border-slate-800">
                {/* 🛒 LISTAGEM DE ITENS (FOCO TOTAL) */}
                <div className="lg:col-span-9 flex flex-col bg-white dark:bg-slate-900 overflow-hidden">
                    {/* 📑 TABS DE SESSÃO */}
                    <div className="flex items-center gap-1 px-4 pt-3 bg-slate-200/50 dark:bg-slate-950 border-b border-slate-200 dark:border-slate-800 overflow-x-auto custom-scrollbar">
                        {sessoes.map((sessao: any, index: number) => (
                            <button
                                key={sessao.id}
                                onClick={() => alternarSessao(sessao.id)}
                                className={`flex items-center gap-2 px-4 py-2.5 rounded-t-2xl transition-all ${sessaoAtivaId === sessao.id ? 'bg-white dark:bg-slate-900 shadow-[0_-4px_10px_rgba(0,0,0,0.02)] text-blue-600 dark:text-blue-400 font-black' : 'bg-transparent text-slate-500 hover:bg-slate-300/50 dark:hover:bg-slate-900/50 font-bold'}`}
                            >
                                <span className="text-xs uppercase tracking-wider whitespace-nowrap">Cx. {index + 1}</span>
                                {sessao.carrinho.length > 0 && (
                                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-black ${sessaoAtivaId === sessao.id ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30' : 'bg-slate-300/50 text-slate-600 dark:bg-slate-800'}`}>
                                        {sessao.carrinho.length}
                                    </span>
                                )}
                                {sessoes.length > 1 && (
                                    <div
                                        className={`ml-1 rounded-full p-1 transition-colors ${sessaoAtivaId === sessao.id ? 'hover:bg-red-100 hover:text-red-600' : 'hover:bg-slate-300 hover:text-slate-700'}`}
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            removerSessao(sessao.id);
                                        }}
                                    >
                                        <X className="w-3.5 h-3.5" />
                                    </div>
                                )}
                            </button>
                        ))}
                        <button
                            onClick={adicionarSessao}
                            className="ml-2 mb-1 p-2 bg-slate-300/50 dark:bg-slate-800 hover:bg-blue-600 dark:hover:bg-blue-600 hover:text-white text-slate-500 rounded-xl transition-all shadow-sm"
                            title="Nova Sessão (Caixa Zerado)"
                        >
                            <Plus className="w-4 h-4" />
                        </button>
                    </div>

                    <div className="p-3 bg-slate-50 dark:bg-slate-900/50 border-b border-slate-200 dark:border-slate-800">
                        <div className="bg-white dark:bg-slate-900 p-4 border-b border-slate-200 dark:border-slate-800">
                            <ProdutoSearch onProdutoSelecionado={handleProdutoSelecionado} />
                        </div>
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
                <div className="hidden lg:flex lg:col-span-3 flex-col bg-slate-50 dark:bg-slate-950 border-l border-slate-200 dark:border-slate-800">
                    <div className="flex-1 p-6 flex flex-col justify-end gap-6">
                        <div className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-xl shadow-slate-200/50 dark:shadow-none text-center">
                            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-1">Total a Pagar</span>
                            <span className="text-3xl font-black text-red-600 dark:text-red-400 tabular-nums block truncate">
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
                                                            className={`p-4 rounded-2xl border-2 flex flex-col items-center gap-3 transition-all ${formaPagamentoSelecionada === forma.tipo
                                                                ? forma.tipo === 'fiado' ? 'border-orange-500 bg-orange-50 dark:bg-orange-900/20 shadow-lg' : 'border-blue-600 bg-white dark:bg-slate-900 shadow-lg'
                                                                : 'border-transparent bg-slate-200/50 dark:bg-slate-700/50 hover:bg-slate-200'
                                                                }`}
                                                        >
                                                            <div className={formaPagamentoSelecionada === forma.tipo ? (forma.tipo === 'fiado' ? 'text-orange-500' : 'text-blue-600') : 'text-slate-400'}>
                                                                {forma.tipo === 'fiado' ? <span className="text-2xl">🤝</span> : renderIconPagamento(forma.tipo)}
                                                            </div>
                                                            <span className={`text-[10px] font-black uppercase tracking-wider text-center ${formaPagamentoSelecionada === forma.tipo ? (forma.tipo === 'fiado' ? 'text-orange-500' : 'text-blue-600') : 'text-slate-500'
                                                                }`}>
                                                                {forma.label}
                                                            </span>
                                                        </button>
                                                    ))}
                                                </div>

                                                {/* Campo de Data de Vencimento - Visível apenas para Fiado */}
                                                {formaPagamentoSelecionada === 'fiado' && (
                                                    <div className="mt-4 p-4 bg-orange-50 dark:bg-orange-900/20 rounded-2xl border border-orange-500/20">
                                                        {!cliente && (
                                                            <p className="text-xs text-orange-700 font-bold mb-3 text-center">
                                                                ⚠️ Fiado requer um Cliente cadastrado! Selecione acima.
                                                            </p>
                                                        )}
                                                        <label className="text-[10px] font-bold text-orange-600 uppercase tracking-widest block mb-2">
                                                            📅 Data Prevista de Pagamento
                                                        </label>
                                                        <input
                                                            type="date"
                                                            value={dataVencimentoFiado}
                                                            onChange={e => setDataVencimentoFiado(e.target.value)}
                                                            min={new Date().toISOString().split('T')[0]}
                                                            className="w-full p-3 rounded-xl border border-orange-300 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-orange-400"
                                                        />
                                                        <p className="text-[10px] text-orange-500 mt-1">Opcional. Padrão: 30 dias.</p>
                                                    </div>
                                                )}                               {formasPagamento.find((f: any) => f.tipo === formaPagamentoSelecionada)?.permite_troco && (
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
                            <div className="p-6 border-t border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/50 space-y-6">

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
                emailCliente={cliente?.email || ''}
                onFechar={() => {
                    setMostrarModalNotaFiscal(false);
                    setVendaFinalizada(null);
                    limparCarrinho();
                }}
                onImprimir={async () => {
                    if (!vendaFinalizada) return;
                    setMostrarModalNotaFiscal(false);
                    setCupomModalAberto(true);
                }}
                onEnviarEmail={async (email) => {
                    if (!vendaFinalizada) return;
                    setEnviandoEmail(true);
                    try {
                        await showToast.promise(pdvService.enviarCupomFiscal(vendaFinalizada.id, email), {
                            loading: 'Enviando nota fiscal...',
                            success: 'Nota fiscal enviada por e-mail!',
                            error: (err: any) => err.response?.data?.error || 'Erro ao enviar e-mail'
                        });
                        setMostrarModalNotaFiscal(false);
                        setVendaFinalizada(null);
                        limparCarrinho();
                    } catch (error) {
                        // Erro tratado pelo promise
                    } finally {
                        setEnviandoEmail(false);
                    }
                }}
                enviando={enviandoEmail}
                onVisualizar={async () => {
                    if (!vendaFinalizada) return;
                    setMostrarModalNotaFiscal(false);
                    setCupomModalAberto(true);
                }}
            />

            {/* CUPOM FISCAL PROFISSIONAL */}
            <CupomFiscalModal
                aberto={cupomModalAberto}
                vendaId={vendaFinalizada?.id ?? null}
                onFechar={() => {
                    setCupomModalAberto(false);
                    setVendaFinalizada(null);
                    limparCarrinho();
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
