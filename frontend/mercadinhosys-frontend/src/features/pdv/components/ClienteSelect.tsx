import React, { useState, useEffect } from 'react';
import { User, UserPlus, X } from 'lucide-react';
import { Cliente } from '../../../types';
import { pdvService } from '../pdvService';

interface ClienteSelectProps {
    cliente: Cliente | null;
    onClienteSelecionado: (cliente: Cliente | null) => void;
}

const ClienteSelect: React.FC<ClienteSelectProps> = ({ cliente, onClienteSelecionado }) => {
    const [query, setQuery] = useState('');
    const [resultados, setResultados] = useState<Cliente[]>([]);
    const [loading, setLoading] = useState(false);
    const [mostrarBusca, setMostrarBusca] = useState(false);

    useEffect(() => {
        const buscarClientes = async () => {
            setLoading(true);
            try {
                const clientes = await pdvService.buscarClientes(query);
                setResultados(clientes.slice(0, 10));
            } catch (error) {
                console.error('Erro ao buscar clientes:', error);
                setResultados([]);
            } finally {
                setLoading(false);
            }
        };

        const debounce = setTimeout(buscarClientes, 200);
        return () => clearTimeout(debounce);
    }, [query]);

    const handleClienteClick = (cliente: Cliente) => {
        onClienteSelecionado(cliente);
        setMostrarBusca(false);
        setQuery('');
        setResultados([]);
    };

    const handleRemoverCliente = () => {
        onClienteSelecionado(null);
    };

    return (
        <div className="relative">
            {cliente ? (
                <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
                                <User className="w-5 h-5 text-white" />
                            </div>
                            <div>
                                <h4 className="font-semibold text-gray-800 dark:text-white">
                                    {cliente.nome}
                                </h4>
                                <p className="text-sm text-gray-500 dark:text-gray-400">
                                    CPF: {cliente.cpf_cnpj} • Total: R$ {cliente.total_compras.toFixed(2)}
                                </p>
                            </div>
                        </div>
                        <button
                            onClick={handleRemoverCliente}
                            className="p-2 text-gray-500 hover:text-red-500"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    </div>
                </div>
            ) : (
                <button
                    onClick={() => setMostrarBusca(true)}
                    className="w-full p-4 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg hover:border-blue-500 dark:hover:border-blue-500 transition-colors"
                >
                    <div className="flex flex-col items-center justify-center">
                        <UserPlus className="w-8 h-8 text-gray-400 mb-2" />
                        <span className="text-gray-600 dark:text-gray-400">Adicionar cliente</span>
                    </div>
                </button>
            )}

            {mostrarBusca && !cliente && (
                <div className="absolute z-50 w-full mt-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg">
                    <div className="p-3 border-b border-gray-200 dark:border-gray-700">
                        <div className="relative">
                            <input
                                type="text"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                placeholder="Buscar cliente por nome, CPF ou telefone..."
                                className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                autoFocus
                            />
                            {loading && (
                                <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="max-h-64 overflow-y-auto">
                        {resultados.length > 0 ? (
                            resultados.map((cliente) => (
                                <div
                                    key={cliente.id}
                                    onClick={() => handleClienteClick(cliente)}
                                    className="p-3 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer border-b border-gray-100 dark:border-gray-700 last:border-b-0"
                                >
                                    <div className="flex items-center space-x-3">
                                        <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
                                            <User className="w-4 h-4 text-blue-500" />
                                        </div>
                                        <div className="flex-1">
                                            <h4 className="font-medium text-gray-800 dark:text-white">
                                                {cliente.nome}
                                            </h4>
                                            <p className="text-sm text-gray-500 dark:text-gray-400">
                                                {cliente.cpf_cnpj} • {cliente.telefone}
                                            </p>
                                        </div>
                                        <div className="text-right">
                                            <p className="text-sm font-medium text-gray-800 dark:text-white">
                                                R$ {cliente.total_compras.toFixed(2)}
                                            </p>
                                            <p className="text-xs text-gray-500 dark:text-gray-400">
                                                {cliente.frequencia_compras} compras
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            ))
                        ) : query.trim() && !loading ? (
                            <div className="p-6 text-center text-gray-500 dark:text-gray-400">
                                <User className="w-12 h-12 mx-auto mb-2 opacity-50" />
                                <p>Nenhum cliente encontrado</p>
                            </div>
                        ) : null}
                    </div>

                    <div className="p-3 border-t border-gray-200 dark:border-gray-700">
                        <button
                            onClick={() => setMostrarBusca(false)}
                            className="w-full px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600"
                        >
                            Cancelar
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ClienteSelect;