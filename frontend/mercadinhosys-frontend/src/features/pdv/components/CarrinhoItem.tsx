import React, { useState } from 'react';
import { Trash2, Minus, Plus, Tag, Check, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Produto } from '../../../types';
import { formatCurrency } from '../../../utils/formatters';
import { showToast } from '../../../utils/toast';

interface CarrinhoItemProps {
    produto: Produto;
    quantidade: number;
    precoUnitario: number;
    desconto: number;
    total: number;
    onAtualizarQuantidade: (quantidade: number) => void;
    onRemover: () => void;
    onAplicarDesconto: (desconto: number, percentual: boolean) => void;
}

const CarrinhoItem: React.FC<CarrinhoItemProps> = ({
    produto,
    quantidade,
    precoUnitario,
    desconto,
    total,
    onAtualizarQuantidade,
    onRemover,
    onAplicarDesconto,
}) => {
    const isGranel = ['KG', 'L', 'G', 'ML'].includes(produto.unidade_medida?.toUpperCase()) || (produto as any).tipo === 'granel';

    const [mostrarDesconto, setMostrarDesconto] = useState(false);
    const [valorDesconto, setValorDesconto] = useState('');
    const [tipoDesconto, setTipoDesconto] = useState<'valor' | 'percentual'>('percentual');

    const subtotalItem = precoUnitario * quantidade;
    const percentualAplicado = desconto > 0 ? ((desconto / subtotalItem) * 100).toFixed(1) : null;

    const handleAplicarDesconto = () => {
        const valor = parseFloat(valorDesconto.replace(',', '.'));
        if (isNaN(valor) || valor < 0) {
            showToast.error('Informe um valor de desconto válido.');
            return;
        }
        // Validação: desconto em valor não pode superar o subtotal do item
        if (tipoDesconto === 'valor' && valor >= subtotalItem) {
            showToast.error('Desconto não pode ser maior ou igual ao valor do item.');
            return;
        }
        if (tipoDesconto === 'percentual' && valor > 100) {
            showToast.error('Percentual não pode ultrapassar 100%.');
            return;
        }
        onAplicarDesconto(valor, tipoDesconto === 'percentual');
        setValorDesconto('');
        setMostrarDesconto(false);
        showToast.success(`Desconto aplicado em ${produto.nome}`);
    };

    const handleRemoverDesconto = () => {
        onAplicarDesconto(0, false);
        showToast.success('Desconto removido');
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') handleAplicarDesconto();
        if (e.key === 'Escape') { setMostrarDesconto(false); setValorDesconto(''); }
    };

    return (
        <motion.div
            layout
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="bg-white dark:bg-gray-800 border-b border-slate-100 dark:border-slate-800 transition-all duration-150"
        >
            <div className="p-2 sm:p-3">
                <div className="flex items-center gap-3">

                    {/* Quantidade badge */}
                    <div className="w-9 h-9 flex-shrink-0 bg-red-600 dark:bg-red-700 rounded-xl text-white font-black flex items-center justify-center text-base shadow-sm">
                        {quantidade}
                    </div>

                    {/* Nome + preço unitário */}
                    <div className="flex-1 min-w-0">
                        <h4 className="font-bold text-slate-800 dark:text-white text-sm leading-tight uppercase tracking-tight truncate">
                            {produto.nome}
                        </h4>
                        <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                            {produto.codigo_barras && (
                                <span className="text-[9px] font-bold text-slate-400 bg-slate-100 dark:bg-slate-700 px-1.5 py-0.5 rounded uppercase tracking-wide">
                                    {produto.codigo_barras}
                                </span>
                            )}
                            <span className="text-xs font-bold text-slate-500">
                                {formatCurrency(precoUnitario)}<span className="text-[10px] opacity-50">/un</span>
                            </span>
                            {/* Estoque disponível */}
                            {(() => {
                                const estoque = produto.estoque_atual ?? (produto as any).quantidade ?? null;
                                if (estoque === null) return null;
                                const baixo = estoque <= 5;
                                return (
                                    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded uppercase ${baixo
                                        ? 'text-red-600 bg-red-50 dark:bg-red-900/20'
                                        : 'text-slate-400 bg-slate-100 dark:bg-slate-700'
                                        }`}>
                                        Est: {estoque}
                                    </span>
                                );
                            })()}
                            {/* Validade */}
                            {produto.data_validade && (() => {
                                let y: number, m: number, d: number;
                                if (produto.data_validade.includes('-')) {
                                    [y, m, d] = produto.data_validade.split('-').map(Number);
                                } else {
                                    [d, m, y] = produto.data_validade.split('/').map(Number);
                                }
                                const dataVal = new Date(y, m - 1, d);
                                const hoje = new Date(); hoje.setHours(0, 0, 0, 0);
                                const limite = new Date(hoje); limite.setDate(hoje.getDate() + 30);
                                if (dataVal < hoje) {
                                    return <span className="text-[9px] font-black px-1.5 py-0.5 rounded uppercase bg-red-500 text-white animate-pulse">Vencido</span>;
                                } else if (dataVal <= limite) {
                                    const dias = Math.round((dataVal.getTime() - hoje.getTime()) / 86400000);
                                    return <span className="text-[9px] font-black px-1.5 py-0.5 rounded uppercase bg-amber-500 text-white">Vence em {dias}d</span>;
                                } else {
                                    return <span className="text-[9px] font-bold px-1.5 py-0.5 rounded uppercase bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">Val. OK</span>;
                                }
                            })()}
                            {desconto > 0 && (
                                <span className="text-[10px] font-black text-emerald-600 bg-emerald-50 dark:bg-emerald-900/20 px-1.5 py-0.5 rounded-full border border-emerald-200 dark:border-emerald-800">
                                    -{percentualAplicado}%
                                </span>
                            )}
                        </div>

                    </div>

                    {/* Controles de quantidade */}
                    <div className="flex items-center gap-4">
                        <div className="flex items-center bg-slate-100 dark:bg-slate-800 rounded-xl p-1 border border-slate-200 dark:border-slate-700">
                            <button
                                onClick={() => onAtualizarQuantidade(Math.max(0, quantidade - (isGranel ? 0.1 : 1)))}
                                className="w-10 h-10 flex items-center justify-center text-slate-500 hover:text-slate-900 dark:hover:text-white transition-all active:scale-90"
                            >
                                <Minus className="w-5 h-5" />
                            </button>
                            <input
                                type="number"
                                value={quantidade}
                                step={isGranel ? "0.001" : "1"}
                                onChange={(e) => onAtualizarQuantidade(parseFloat(e.target.value) || 0)}
                                className="w-16 text-center bg-transparent border-none font-black text-slate-900 dark:text-white focus:outline-none tabular-nums"
                            />
                            <button
                                onClick={() => onAtualizarQuantidade(quantidade + (isGranel ? 0.1 : 1))}
                                className="w-10 h-10 flex items-center justify-center text-slate-500 hover:text-slate-900 dark:hover:text-white transition-all active:scale-90"
                            >
                                <Plus className="w-5 h-5" />
                            </button>
                        </div>
                        <span className="text-[10px] font-black text-slate-400 border border-slate-200 dark:border-slate-700 px-2 py-1 rounded-lg uppercase tracking-widest">
                            {produto.unidade_medida || 'UN'}
                        </span>
                    </div>

                    {/* Total + ações */}
                    <div className="text-right min-w-[80px]">
                        <p className="text-lg font-black text-red-600 dark:text-red-400 tabular-nums tracking-tighter leading-none">
                            {formatCurrency(total)}
                        </p>
                        {desconto > 0 && (
                            <p className="text-[10px] text-slate-400 line-through tabular-nums">
                                {formatCurrency(subtotalItem)}
                            </p>
                        )}
                    </div>

                    {/* Botões de ação — SEMPRE VISÍVEIS */}
                    <div className="flex flex-col gap-1">
                        <button
                            onClick={() => { setMostrarDesconto(!mostrarDesconto); setValorDesconto(''); }}
                            title="Desconto neste item"
                            className={`w-8 h-8 flex items-center justify-center rounded-lg transition-all ${mostrarDesconto || desconto > 0
                                ? 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400'
                                : 'text-slate-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20'
                                }`}
                        >
                            <Tag className="w-4 h-4" />
                        </button>
                        <button
                            onClick={onRemover}
                            title="Remover item"
                            className="w-8 h-8 flex items-center justify-center rounded-lg text-slate-300 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-all"
                        >
                            <Trash2 className="w-4 h-4" />
                        </button>
                    </div>
                </div>

                {/* ── Painel de Desconto Animado ── */}
                <AnimatePresence>
                    {mostrarDesconto && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.18 }}
                            className="overflow-hidden"
                        >
                            <div className="mt-2 p-3 rounded-2xl border border-blue-200 dark:border-blue-800"
                                style={{ background: 'linear-gradient(135deg, rgba(239,246,255,0.8) 0%, rgba(238,242,255,0.8) 100%)' }}
                            >
                                <div className="flex items-center gap-1 mb-2">
                                    <Tag className="w-3.5 h-3.5 text-blue-600" />
                                    <span className="text-[10px] font-black text-blue-700 uppercase tracking-widest">
                                        Desconto — {produto.nome}
                                    </span>
                                    {desconto > 0 && (
                                        <button onClick={handleRemoverDesconto}
                                            className="ml-auto text-[10px] text-red-500 hover:text-red-700 font-bold flex items-center gap-0.5">
                                            <X className="w-3 h-3" /> Remover desconto
                                        </button>
                                    )}
                                </div>

                                <div className="flex items-center gap-2">
                                    {/* Toggle R$ / % */}
                                    <div className="flex bg-white dark:bg-slate-800 rounded-xl p-0.5 border border-slate-200 dark:border-slate-700 shrink-0">
                                        <button
                                            type="button"
                                            onClick={() => setTipoDesconto('valor')}
                                            className={`px-3 py-1.5 text-[11px] font-black rounded-lg transition-all ${tipoDesconto === 'valor' ? 'bg-blue-600 text-white shadow' : 'text-slate-400'}`}
                                        >R$</button>
                                        <button
                                            type="button"
                                            onClick={() => setTipoDesconto('percentual')}
                                            className={`px-3 py-1.5 text-[11px] font-black rounded-lg transition-all ${tipoDesconto === 'percentual' ? 'bg-blue-600 text-white shadow' : 'text-slate-400'}`}
                                        >%</button>
                                    </div>

                                    {/* Input */}
                                    <input
                                        type="number"
                                        value={valorDesconto}
                                        onChange={e => setValorDesconto(e.target.value)}
                                        onKeyDown={handleKeyDown}
                                        placeholder={tipoDesconto === 'percentual' ? 'Ex: 10' : 'Ex: 5,00'}
                                        className="flex-1 min-w-0 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 rounded-xl px-3 py-2 text-sm font-bold outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:text-white"
                                        autoFocus
                                        step="0.01"
                                        min="0"
                                        max={tipoDesconto === 'percentual' ? 100 : subtotalItem - 0.01}
                                    />

                                    {/* Botão aplicar */}
                                    <button
                                        type="button"
                                        onClick={handleAplicarDesconto}
                                        disabled={!valorDesconto}
                                        className="h-9 w-9 flex items-center justify-center bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white rounded-xl transition-all shrink-0 shadow-lg shadow-blue-500/30"
                                    >
                                        <Check className="w-4 h-4" />
                                    </button>
                                </div>

                                {/* Prévia do desconto */}
                                {valorDesconto && !isNaN(parseFloat(valorDesconto)) && (
                                    <div className="mt-2 flex justify-between text-xs text-blue-700 font-semibold px-1">
                                        <span>Desconto:</span>
                                        <span className="font-black">
                                            {tipoDesconto === 'percentual'
                                                ? `${formatCurrency(subtotalItem * (parseFloat(valorDesconto) / 100))} (${valorDesconto}%)`
                                                : formatCurrency(parseFloat(valorDesconto))
                                            }
                                        </span>
                                    </div>
                                )}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </motion.div>
    );
};

export default CarrinhoItem;