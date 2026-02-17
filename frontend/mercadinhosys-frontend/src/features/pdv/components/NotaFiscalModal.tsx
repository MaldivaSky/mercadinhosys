import React, { useEffect, useState } from 'react';
import { Mail, Printer, X } from 'lucide-react';

interface NotaFiscalModalProps {
    mostrar: boolean;
    emailCliente?: string;
    onEnviarEmail: (email: string) => void;
    onVisualizar: () => void;
    onImprimir: () => void;
    onFechar: () => void;
    enviando?: boolean;
}

const NotaFiscalModal: React.FC<NotaFiscalModalProps> = ({
    mostrar,
    emailCliente,
    onEnviarEmail,
    onVisualizar,
    onImprimir,
    onFechar,
    enviando = false
}) => {
    const [email, setEmail] = useState(emailCliente || '');
    const [emailValido, setEmailValido] = useState(!!emailCliente);

    const validarEmail = (valor: string) => {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return regex.test(valor);
    };

    useEffect(() => {
        const emailInicial = emailCliente || '';
        setEmail(emailInicial);
        setEmailValido(!!emailInicial && validarEmail(emailInicial));
    }, [emailCliente, mostrar]);

    const handleEmailChange = (valor: string) => {
        setEmail(valor);
        setEmailValido(validarEmail(valor));
    };

    const handleEnviar = () => {
        if (emailValido && email) {
            onEnviarEmail(email);
        }
    };

    if (!mostrar) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 animate-fadeIn">
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-md w-full p-6 relative animate-scaleIn">
                {/* Botão Fechar */}
                <button
                    onClick={onFechar}
                    className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition"
                >
                    <X className="w-5 h-5" />
                </button>

                {/* Header */}
                <div className="text-center mb-6">
                    <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg">
                        <Mail className="w-8 h-8 text-white" />
                    </div>
                    <h3 className="text-2xl font-bold text-gray-800 dark:text-white mb-2">
                        Enviar Nota Fiscal
                    </h3>
                    <p className="text-gray-600 dark:text-gray-400">
                        Como deseja receber o comprovante?
                    </p>
                </div>

                {/* Input de Email */}
                <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        📧 Email para envio:
                    </label>
                    <input
                        type="email"
                        value={email}
                        onChange={(e) => handleEmailChange(e.target.value)}
                        placeholder="cliente@exemplo.com"
                        className={`w-full px-4 py-3 rounded-lg border-2 transition focus:outline-none focus:ring-2 ${
                            email && !emailValido
                                ? 'border-red-300 focus:border-red-500 focus:ring-red-200'
                                : 'border-gray-300 dark:border-gray-600 focus:border-blue-500 focus:ring-blue-200'
                        } bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400`}
                        disabled={enviando}
                    />
                    {email && !emailValido && (
                        <p className="text-red-500 text-sm mt-1">⚠️ Email inválido</p>
                    )}
                    {!emailCliente && (
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                            💡 Deixe em branco se não quiser enviar por email
                        </p>
                    )}
                </div>

                {/* Botões de Ação */}
                <div className="grid grid-cols-3 gap-3 mb-3">
                    <button
                        onClick={handleEnviar}
                        disabled={!emailValido || !email || enviando}
                        className="px-6 py-3 rounded-lg font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed
                            bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 
                            text-white shadow-lg hover:shadow-xl transform hover:scale-105 active:scale-95
                            flex items-center justify-center space-x-2"
                    >
                        {enviando ? (
                            <>
                                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                                <span>Enviando...</span>
                            </>
                        ) : (
                            <>
                                <Mail className="w-5 h-5" />
                                <span>Enviar Email</span>
                            </>
                        )}
                    </button>

                    <button
                        onClick={onImprimir}
                        disabled={enviando}
                        className="px-6 py-3 rounded-lg font-semibold transition
                            bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 
                            text-white shadow-lg hover:shadow-xl transform hover:scale-105 active:scale-95
                            flex items-center justify-center space-x-2 disabled:opacity-50"
                    >
                        <Printer className="w-5 h-5" />
                        <span>Imprimir</span>
                    </button>

                    <button
                        onClick={onVisualizar}
                        disabled={enviando}
                        className="px-6 py-3 rounded-lg font-semibold transition
                            bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700
                            text-white shadow-lg hover:shadow-xl transform hover:scale-105 active:scale-95
                            flex items-center justify-center space-x-2 disabled:opacity-50"
                    >
                        <span>Visualizar</span>
                    </button>
                </div>

                {/* Botão Pular */}
                <button
                    onClick={onFechar}
                    disabled={enviando}
                    className="w-full px-6 py-2.5 rounded-lg font-medium transition
                        bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 
                        text-gray-700 dark:text-gray-300 disabled:opacity-50"
                >
                    Pular e Finalizar
                </button>

                {/* Info */}
                <p className="text-xs text-center text-gray-500 dark:text-gray-400 mt-4">
                    ℹ️ A nota fiscal é um documento não fiscal para controle interno
                </p>
            </div>
        </div>
    );
};

export default NotaFiscalModal;
