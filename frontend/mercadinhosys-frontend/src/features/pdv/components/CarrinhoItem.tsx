import React, { useState } from 'react';
import { Trash2, Minus, Plus, Percent, Tag } from 'lucide-react';
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
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 mb-3">
            <div className="flex items-start justify-between">
                <div className="flex-1">
                    <div className="flex items-start space-x-3">
                        <div className="w-12 h-12 bg-gray-100 dark:bg-gray-700 rounded flex items-center justify-center">
                            <span className="font-bold text-gray-600 dark:text-gray-300">
                                {quantidade}
                            </span>
                        </div>
                        <div className="flex-1">
                            <h4 className="font-semibold text-gray-800 dark:text-white">
                                {produto.nome}
                            </h4>
                            <p className="text-sm text-gray-500 dark:text-gray-400">
                                {produto.codigo_barras} • {produto.unidade_medida}
                            </p>

                            <div className="flex items-center space-x-4 mt-2">
                                <div className="flex items-center space-x-2">
                                    <button
                                        onClick={() => onAtualizarQuantidade(quantidade - 1)}
                                        className="p-1 bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600"
                                    >
                                        <Minus className="w-4 h-4" />
                                    </button>

                                    <input
                                        type="number"
                                        value={quantidade}
                                        onChange={(e) => onAtualizarQuantidade(parseInt(e.target.value) || 1)}
                                        className="w-16 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded text-center"
                                        min="1"
                                    />

                                    <button
                                        onClick={() => onAtualizarQuantidade(quantidade + 1)}
                                        className="p-1 bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600"
                                    >
                                        <Plus className="w-4 h-4" />
                                    </button>
                                </div>

                                <button
                                    onClick={() => setMostrarDesconto(!mostrarDesconto)}
                                    className="flex items-center space-x-1 text-sm text-yellow-600 dark:text-yellow-400 hover:text-yellow-700 dark:hover:text-yellow-300"
                                >
                                    <Tag className="w-4 h-4" />
                                    <span>Desconto</span>
                                </button>
                            </div>
                        </div>
                    </div>

                    {mostrarDesconto && (
                        <div className="mt-3 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                            <div className="flex items-center space-x-2 mb-2">
                                <button
                                    onClick={() => setTipoDesconto('valor')}
                                    className={`px-3 py-1 rounded text-sm ${tipoDesconto === 'valor'
                                            ? 'bg-yellow-500 text-white'
                                            : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                                        }`}
                                >
                                    R$
                                </button>
                                <button
                                    onClick={() => setTipoDesconto('percentual')}
                                    className={`px-3 py-1 rounded text-sm ${tipoDesconto === 'percentual'
                                            ? 'bg-yellow-500 text-white'
                                            : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                                        }`}
                                >
                                    %
                                </button>
                            </div>

                            <div className="flex space-x-2">
                                <input
                                    type="number"
                                    value={valorDesconto}
                                    onChange={(e) => setValorDesconto(e.target.value)}
                                    placeholder={tipoDesconto === 'valor' ? 'Valor' : 'Percentual'}
                                    className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded"
                                    step="0.01"
                                />
                                <button
                                    onClick={handleAplicarDesconto}
                                    className="px-4 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600"
                                >
                                    Aplicar
                                </button>
                            </div>
                        </div>
                    )}
                </div>

                <div className="text-right">
                    <button
                        onClick={onRemover}
                        className="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg mb-2"
                    >
                        <Trash2 className="w-5 h-5" />
                    </button>

                    <div>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                            {quantidade} × R$ {precoUnitario.toFixed(2)}
                        </p>
                        {desconto > 0 && (
                            <p className="text-sm text-red-500 line-through">
                                -R$ {desconto.toFixed(2)}
                            </p>
                        )}
                        <p className="font-bold text-lg text-gray-800 dark:text-white">
                            R$ {total.toFixed(2)}
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default CarrinhoItem;