import React, { useState } from 'react';
import { Trash2, Minus, Plus, Tag } from 'lucide-react';
import { Produto } from '../../../types';

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
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-3 sm:p-4 mb-3 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex flex-col sm:flex-row items-start justify-between gap-4">
                <div className="flex-1 w-full min-w-0">
                    <div className="flex items-start space-x-3">
                        <div className="flex-shrink-0 w-10 h-10 sm:w-12 sm:h-12 bg-blue-50 dark:bg-blue-900/20 rounded-lg flex items-center justify-center">
                            <span className="font-bold text-blue-600 dark:text-blue-400">
                                {quantidade}x
                            </span>
                        </div>
                        <div className="flex-1 min-w-0">
                            <h4 className="font-bold text-gray-800 dark:text-white text-base sm:text-lg leading-tight break-words" title={produto.nome}>
                                {produto.nome}
                            </h4>
                            <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 mt-0.5 truncate">
                                {produto.codigo_barras || 'Sem código'} • {produto.unidade_medida || 'UN'}
                            </p>

                            <div className="flex flex-wrap items-center gap-3 mt-3">
                                <div className="flex items-center bg-gray-50 dark:bg-gray-700/50 rounded-lg p-1 border border-gray-100 dark:border-gray-600">
                                    <button
                                        onClick={() => onAtualizarQuantidade(Math.max(1, quantidade - 1))}
                                        className="p-1.5 text-gray-500 hover:text-blue-500 hover:bg-white dark:hover:bg-gray-600 rounded-md transition-all"
                                    >
                                        <Minus className="w-3.5 h-3.5" />
                                    </button>

                                    <input
                                        type="number"
                                        value={quantidade}
                                        onChange={(e) => onAtualizarQuantidade(parseInt(e.target.value) || 1)}
                                        className="w-10 sm:w-12 px-1 text-sm font-bold border-none text-center bg-transparent text-gray-800 dark:text-white focus:ring-0"
                                        min="1"
                                    />

                                    <button
                                        onClick={() => onAtualizarQuantidade(quantidade + 1)}
                                        className="p-1.5 text-gray-500 hover:text-blue-500 hover:bg-white dark:hover:bg-gray-600 rounded-md transition-all"
                                    >
                                        <Plus className="w-3.5 h-3.5" />
                                    </button>
                                </div>

                                <button
                                    onClick={() => setMostrarDesconto(!mostrarDesconto)}
                                    className={`flex items-center space-x-1 px-2 py-1 rounded-md text-xs font-medium transition-colors ${desconto > 0
                                            ? 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400'
                                            : 'bg-yellow-50 dark:bg-yellow-900/20 text-yellow-600 dark:text-yellow-400'
                                        }`}
                                >
                                    <Tag className="w-3.5 h-3.5" />
                                    <span>{desconto > 0 ? 'Ajustar Desc.' : 'Add Desconto'}</span>
                                </button>
                            </div>
                        </div>
                    </div>

                    {mostrarDesconto && (
                        <div className="mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/10 rounded-xl border border-yellow-100 dark:border-yellow-900/30">
                            <div className="flex items-center space-x-2 mb-2">
                                <button
                                    onClick={() => setTipoDesconto('valor')}
                                    className={`flex-1 py-1.5 rounded-lg text-xs font-bold transition-all ${tipoDesconto === 'valor'
                                        ? 'bg-yellow-500 text-white shadow-sm'
                                        : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400'
                                        }`}
                                >
                                    R$ Fixo
                                </button>
                                <button
                                    onClick={() => setTipoDesconto('percentual')}
                                    className={`flex-1 py-1.5 rounded-lg text-xs font-bold transition-all ${tipoDesconto === 'percentual'
                                        ? 'bg-yellow-500 text-white shadow-sm'
                                        : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400'
                                        }`}
                                >
                                    % Percentual
                                </button>
                            </div>

                            <div className="flex space-x-2">
                                <input
                                    type="number"
                                    value={valorDesconto}
                                    onChange={(e) => setValorDesconto(e.target.value)}
                                    placeholder={tipoDesconto === 'valor' ? 'R$ 0,00' : '0 %'}
                                    className="flex-1 px-3 py-2 text-sm border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-white"
                                    step="0.01"
                                />
                                <button
                                    onClick={handleAplicarDesconto}
                                    className="px-4 py-2 bg-yellow-500 text-white text-sm font-bold rounded-lg hover:bg-yellow-600 transition-colors shadow-sm"
                                >
                                    Ok
                                </button>
                            </div>
                        </div>
                    )}
                </div>

                <div className="flex flex-row sm:flex-col items-center sm:items-end justify-between w-full sm:w-auto sm:min-w-[140px] border-t sm:border-t-0 pt-3 sm:pt-0 mt-1 sm:mt-0">
                    <button
                        onClick={onRemover}
                        className="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors order-2 sm:order-1"
                        title="Remover item"
                    >
                        <Trash2 className="w-5 h-5" />
                    </button>

                    <div className="text-left sm:text-right order-1 sm:order-2">
                        <p className="text-[10px] sm:text-xs text-gray-500 dark:text-gray-400 tabular-nums">
                            {quantidade} × {precoUnitario.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                        </p>
                        {desconto > 0 && (
                            <p className="text-xs sm:text-sm text-red-500 font-medium tabular-nums">
                                -{desconto.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                            </p>
                        )}
                        <p className="font-black text-xl sm:text-2xl text-blue-600 dark:text-blue-400 tabular-nums leading-none">
                            {total.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default CarrinhoItem;