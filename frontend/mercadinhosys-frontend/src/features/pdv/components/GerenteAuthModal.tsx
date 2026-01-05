import React, { useState } from 'react';
import { ShieldCheck, Lock, X, AlertTriangle } from 'lucide-react';
import { pdvService } from '../pdvService';

interface GerenteAuthModalProps {
    acao: 'desconto' | 'cancelamento';
    valorDesconto?: number;
    onAutorizado: () => void;
    onCancelar: () => void;
}

const GerenteAuthModal: React.FC<GerenteAuthModalProps> = ({
    acao,
    valorDesconto,
    onAutorizado,
    onCancelar,
}) => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [erro, setErro] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setErro(null);
        setLoading(true);

        try {
            const autorizado = await pdvService.autorizarGerente({
                username,
                password,
                acao,
                valor_desconto: valorDesconto,
            });

            if (autorizado) {
                onAutorizado();
            } else {
                setErro('Usuário sem permissão para esta ação');
            }
        } catch (error: any) {
            setErro(error.response?.data?.error || 'Credenciais inválidas');
        } finally {
            setLoading(false);
        }
    };

    const getTitulo = () => {
        switch (acao) {
            case 'desconto':
                return 'Autorização Necessária - Desconto';
            case 'cancelamento':
                return 'Autorização Necessária - Cancelamento';
            default:
                return 'Autorização de Gerente';
        }
    };

    const getDescricao = () => {
        switch (acao) {
            case 'desconto':
                return `Desconto de R$ ${valorDesconto?.toFixed(2)} requer autorização de gerente`;
            case 'cancelamento':
                return 'Cancelamento de venda requer autorização de gerente';
            default:
                return 'Esta ação requer autorização';
        }
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-md w-full">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
                    <div className="flex items-center space-x-3">
                        <div className="p-3 bg-orange-100 dark:bg-orange-900 rounded-lg">
                            <ShieldCheck className="w-6 h-6 text-orange-600 dark:text-orange-400" />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-gray-800 dark:text-white">
                                {getTitulo()}
                            </h2>
                            <p className="text-sm text-gray-500 dark:text-gray-400">
                                Credenciais de gerente necessárias
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={onCancelar}
                        className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition"
                    >
                        <X className="w-6 h-6 text-gray-600 dark:text-gray-400" />
                    </button>
                </div>

                {/* Alerta */}
                <div className="p-6 bg-orange-50 dark:bg-orange-900/20 border-b border-orange-200 dark:border-orange-800">
                    <div className="flex items-start space-x-3">
                        <AlertTriangle className="w-5 h-5 text-orange-600 dark:text-orange-400 mt-0.5" />
                        <div>
                            <h4 className="font-medium text-orange-800 dark:text-orange-300 mb-1">
                                Autorização Requerida
                            </h4>
                            <p className="text-sm text-orange-700 dark:text-orange-400">
                                {getDescricao()}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Form */}
                <form onSubmit={handleSubmit} className="p-6 space-y-4">
                    {erro && (
                        <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                            <div className="flex items-center space-x-2">
                                <X className="w-5 h-5 text-red-600 dark:text-red-400" />
                                <p className="text-sm text-red-700 dark:text-red-400">{erro}</p>
                            </div>
                        </div>
                    )}

                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Usuário do Gerente
                        </label>
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            placeholder="Digite o username"
                            className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-800 dark:text-white"
                            required
                            autoFocus
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Senha
                        </label>
                        <div className="relative">
                            <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="Digite a senha"
                                className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-800 dark:text-white"
                                required
                            />
                        </div>
                    </div>

                    {/* Informações */}
                    <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                        <h4 className="font-medium text-blue-800 dark:text-blue-300 mb-2 text-sm">
                            👤 Quem pode autorizar?
                        </h4>
                        <ul className="text-sm text-blue-700 dark:text-blue-400 space-y-1">
                            <li>✅ Gerente da loja</li>
                            <li>✅ Dono do estabelecimento</li>
                            <li>✅ Funcionários com permissão específica</li>
                        </ul>
                    </div>

                    {/* Botões */}
                    <div className="flex space-x-3 pt-4">
                        <button
                            type="button"
                            onClick={onCancelar}
                            className="flex-1 py-3 px-4 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-white rounded-lg font-medium hover:bg-gray-300 dark:hover:bg-gray-600 transition"
                        >
                            Cancelar
                        </button>
                        <button
                            type="submit"
                            disabled={loading || !username || !password}
                            className={`flex-1 py-3 px-4 rounded-lg font-medium flex items-center justify-center space-x-2 transition ${
                                loading || !username || !password
                                    ? 'bg-gray-300 dark:bg-gray-700 text-gray-500 cursor-not-allowed'
                                    : 'bg-orange-500 hover:bg-orange-600 text-white'
                            }`}
                        >
                            {loading ? (
                                <>
                                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                                    <span>Verificando...</span>
                                </>
                            ) : (
                                <>
                                    <ShieldCheck className="w-5 h-5" />
                                    <span>Autorizar</span>
                                </>
                            )}
                        </button>
                    </div>
                </form>

                {/* Footer */}
                <div className="p-4 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 rounded-b-xl">
                    <p className="text-xs text-center text-gray-500 dark:text-gray-400">
                        🔒 Todas as autorizações são registradas no sistema para auditoria
                    </p>
                </div>
            </div>
        </div>
    );
};

export default GerenteAuthModal;
