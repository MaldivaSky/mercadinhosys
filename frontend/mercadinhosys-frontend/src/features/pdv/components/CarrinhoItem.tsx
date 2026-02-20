import React, { useState } from 'react';
import { Trash2, Minus, Plus, Tag } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Produto } from '../../../types';
import { formatCurrency } from '../../../utils/formatters';

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
    const [mostrarDesconto, setMostrarDesconto] = useState(false);
    const [valorDesconto, setValorDesconto] = useState('');
    const [tipoDesconto, setTipoDesconto] = useState<'valor' | 'percentual'>('valor');

    const handleAplicarDesconto = () => {
        const valor = parseFloat(valorDesconto);
        if (!isNaN(valor) && valor >= 0) {
            onAplicarDesconto(valor, tipoDesconto === 'percentual');
            setValorDesconto('');
            setMostrarDesconto(false);
        }
    };

    return (
        <motion.div
            layout
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="group bg-white dark:bg-gray-800 border-b border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-all duration-150"
        >
            <div className="p-2 sm:p-3">
                <div className="flex flex-col sm:flex-row items-center gap-4">

                    {/* Qtd & Name: Compacted but sharp */}
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                        <div className="w-10 h-10 flex-shrink-0 bg-red-600 dark:bg-red-700 rounded-xl text-white font-black flex items-center justify-center text-lg shadow-sm">
                            {quantidade}
                        </div>
                        <div className="flex-1 min-w-0">
                            <h4 className="font-bold text-slate-800 dark:text-white text-base sm:text-lg leading-tight uppercase tracking-tight truncate">
                                {produto.nome}
                            </h4>
                            <div className="flex items-center gap-2 mt-0.5">
                                <span className="text-[9px] font-bold text-slate-400 bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded uppercase">
                                    {produto.codigo_barras || 'SEM EAN'}
                                </span>
                                <span className="text-xs font-bold text-slate-500">
                                    {formatCurrency(precoUnitario)} <span className="text-[10px] opacity-50">/un</span>
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* Interactive Controls & Price Breakdown */}
                    <div className="flex items-center justify-between w-full sm:w-auto gap-4">
                        {/* Quantity Adjusters - Compacted */}
                        <div className="flex items-center bg-slate-100 dark:bg-slate-800 rounded-lg p-0.5">
                            <button
                                onClick={() => onAtualizarQuantidade(Math.max(1, quantidade - 1))}
                                className="w-8 h-8 flex items-center justify-center text-slate-500 hover:text-blue-600 hover:bg-white dark:hover:bg-slate-700 rounded-md transition-all"
                            >
                                <Minus className="w-4 h-4" />
                            </button>
                            <input
                                type="number"
                                value={quantidade}
                                onChange={(e) => onAtualizarQuantidade(parseInt(e.target.value) || 1)}
                                className="w-10 text-center bg-transparent border-none focus:ring-0 text-sm font-bold text-slate-900 dark:text-white"
                            />
                            <button
                                onClick={() => {
                                    const estoqueMax = produto.estoque_atual ?? 0;
                                    if (quantidade < estoqueMax) {
                                        onAtualizarQuantidade(quantidade + 1);
                                    }
                                }}
                                disabled={quantidade >= (produto.estoque_atual ?? 0)}
                                className={`w-8 h-8 flex items-center justify-center rounded-md transition-all ${quantidade >= (produto.estoque_atual ?? 0)
                                        ? 'text-slate-300 cursor-not-allowed opacity-50'
                                        : 'text-slate-500 hover:text-blue-600 hover:bg-white dark:hover:bg-slate-700'
                                    }`}
                            >
                                <Plus className="w-4 h-4" />
                            </button>
                        </div>

                        {/* Totals Section: High impact, less height */}
                        <div className="text-right min-w-[100px]">
                            <p className="text-xl sm:text-2xl font-black text-red-600 dark:text-red-400 tabular-nums tracking-tighter leading-none">
                                {formatCurrency(total)}
                            </p>
                            <div className="flex items-center justify-end gap-1 mt-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                {desconto > 0 && (
                                    <span className="text-[9px] font-black text-red-500 bg-red-50 dark:bg-red-900/10 px-1.5 py-0.5 rounded uppercase">
                                        -{formatCurrency(desconto)}
                                    </span>
                                )}
                                <button
                                    onClick={() => setMostrarDesconto(!mostrarDesconto)}
                                    className="p-1.5 text-slate-400 hover:text-blue-600 transition-colors"
                                    title="Desconto"
                                >
                                    <Tag className="w-4 h-4" />
                                </button>
                                <button
                                    onClick={onRemover}
                                    className="p-1.5 text-slate-300 hover:text-red-500 transition-colors"
                                    title="Remover"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Animated Compact Discount Panel */}
                <AnimatePresence>
                    {mostrarDesconto && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="overflow-hidden"
                        >
                            <div className="mt-3 flex items-center gap-2 bg-slate-50 dark:bg-slate-900/50 p-2 rounded-xl border border-slate-200 dark:border-slate-800">
                                <div className="flex bg-white dark:bg-slate-800 p-0.5 rounded-lg border border-slate-200 dark:border-slate-700">
                                    <button
                                        onClick={() => setTipoDesconto('valor')}
                                        className={`px-3 py-1.5 text-[10px] font-black rounded-md transition-all ${tipoDesconto === 'valor' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-400'}`}
                                    >R$</button>
                                    <button
                                        onClick={() => setTipoDesconto('percentual')}
                                        className={`px-3 py-1.5 text-[10px] font-black rounded-md transition-all ${tipoDesconto === 'percentual' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-400'}`}
                                    >%</button>
                                </div>
                                <input
                                    type="number"
                                    value={valorDesconto}
                                    onChange={(e) => setValorDesconto(e.target.value)}
                                    placeholder="0,00"
                                    className="flex-1 min-w-0 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-2 text-sm font-bold outline-none focus:border-blue-500"
                                    autoFocus
                                />
                                <button
                                    onClick={handleAplicarDesconto}
                                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-[10px] font-bold rounded-lg transition-all uppercase tracking-widest"
                                >Aplicar</button>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </motion.div>
    );
};

export default CarrinhoItem;