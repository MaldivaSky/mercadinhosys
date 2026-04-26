import React, { useState } from 'react';
import { CreditCard, DollarSign, Smartphone, Trash2, Plus, Tag } from 'lucide-react';
import { formatCurrency } from '../../../utils/formatters';

export interface PagamentoItem {
    id: string;
    forma: string;
    valor: number;
    bandeira?: string;
}

interface MultiPaymentManagerProps {
    totalVenda: number;
    formasDisponiveis: any[];
    pagamentosatuais: PagamentoItem[];
    onAdicionar: (forma: string, valor: number, bandeira?: string) => void;
    onRemover: (id: string) => void;
    onFinalizar?: () => void;
}

const MultiPaymentManager: React.FC<MultiPaymentManagerProps> = ({
    totalVenda,
    formasDisponiveis,
    pagamentosatuais,
    onAdicionar,
    onRemover
}) => {
    const [valorInput, setValorInput] = useState<string>('');
    const [formaSelecionada, setFormaSelecionada] = useState<string>('dinheiro');

    const totalPago = pagamentosatuais.reduce((sum, p) => sum + p.valor, 0);
    const faltante = Math.max(0, totalVenda - totalPago);

    const handleAdicionar = () => {
        const valor = parseFloat(valorInput.replace(',', '.')) || faltante;
        if (valor <= 0) return;

        onAdicionar(formaSelecionada, valor);
        setValorInput('');
    };

    const renderIcon = (tipo: string) => {
        switch (tipo) {
            case 'dinheiro': return <DollarSign className="w-5 h-5" />;
            case 'cartao_credito':
            case 'cartao_debito': return <CreditCard className="w-5 h-5" />;
            case 'pix': return <Smartphone className="w-5 h-5" />;
            default: return <Tag className="w-5 h-5" />;
        }
    };

    return (
        <div className="flex flex-col gap-4">
            {/* 📊 RESUMO DE PAGAMENTO */}
            <div className="grid grid-cols-2 gap-3 mb-2">
                <div className="bg-slate-100 dark:bg-slate-800 p-3 rounded-2xl border border-slate-200 dark:border-slate-700">
                    <span className="text-[10px] font-bold text-slate-400 uppercase block mb-1">Total Pago</span>
                    <span className="text-xl font-black text-blue-600 dark:text-blue-400 tabular-nums">
                        {formatCurrency(totalPago)}
                    </span>
                </div>
                <div className="bg-slate-100 dark:bg-slate-800 p-3 rounded-2xl border border-slate-200 dark:border-slate-700">
                    <span className="text-[10px] font-bold text-slate-400 uppercase block mb-1">Faltante</span>
                    <span className={`text-xl font-black tabular-nums ${faltante > 0 ? 'text-red-500' : 'text-green-500'}`}>
                        {formatCurrency(faltante)}
                    </span>
                </div>
            </div>

            {/* 💸 SELEÇÃO DE FORMA */}
            <div className="grid grid-cols-4 gap-2">
                {formasDisponiveis.map((forma) => (
                    <button
                        key={forma.tipo}
                        onClick={() => setFormaSelecionada(forma.tipo)}
                        className={`p-3 rounded-xl border-2 flex flex-col items-center gap-1 transition-all ${formaSelecionada === forma.tipo
                            ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/20 text-blue-600'
                            : 'border-transparent bg-slate-100 dark:bg-slate-800 text-slate-500'
                            }`}
                    >
                        {renderIcon(forma.tipo)}
                        <span className="text-[9px] font-black uppercase tracking-tight">{forma.label}</span>
                    </button>
                ))}
            </div>

            {/* ⌨️ INPUT DE VALOR */}
            <div className="flex gap-2">
                <div className="flex-1 relative">
                    <input
                        type="text"
                        value={valorInput}
                        onChange={(e) => setValorInput(e.target.value)}
                        placeholder={`Restante: ${faltante.toFixed(2)}`}
                        className="w-full p-4 bg-white dark:bg-slate-900 border-2 border-slate-200 dark:border-slate-800 rounded-2xl text-lg font-bold focus:border-blue-600 outline-none transition-all"
                    />
                    <button
                        onClick={() => setValorInput(faltante.toString())}
                        className="absolute right-3 top-1/2 -translate-y-1/2 p-2 text-[10px] font-black uppercase text-blue-600 hover:bg-blue-50 rounded-lg"
                    >
                        Total
                    </button>
                </div>
                <button
                    onClick={handleAdicionar}
                    disabled={faltante <= 0 && valorInput === ''}
                    className="px-6 bg-blue-600 hover:bg-blue-700 text-white rounded-2xl font-black uppercase text-xs tracking-widest transition-all disabled:opacity-50 disabled:bg-slate-400 shadow-lg shadow-blue-500/20"
                >
                    <Plus className="w-5 h-5 mx-auto" />
                </button>
            </div>

            {/* 📜 LISTA DE PAGAMENTOS ADICIOANDOS */}
            <div className="mt-2 space-y-2 max-h-[150px] overflow-y-auto custom-scrollbar">
                {pagamentosatuais.length === 0 ? (
                    <div className="py-8 text-center border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-3xl opacity-40">
                        <p className="text-xs font-bold uppercase tracking-widest">Nenhum pagamento adicionado</p>
                    </div>
                ) : (
                    pagamentosatuais.map((p) => (
                        <div key={p.id} className="flex items-center justify-between p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-slate-100 dark:bg-slate-800 rounded-lg text-slate-600 dark:text-slate-300">
                                    {renderIcon(p.forma)}
                                </div>
                                <div>
                                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                                        {formasDisponiveis.find(f => f.tipo === p.forma)?.label || p.forma}
                                    </p>
                                    <p className="text-sm font-black text-slate-700 dark:text-slate-200">
                                        {formatCurrency(p.valor)}
                                    </p>
                                </div>
                            </div>
                            <button
                                onClick={() => onRemover(p.id)}
                                className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-xl transition-all"
                            >
                                <Trash2 className="w-4 h-4" />
                            </button>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default MultiPaymentManager;
