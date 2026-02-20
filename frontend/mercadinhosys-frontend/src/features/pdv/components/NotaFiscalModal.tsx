import { useEffect, useState } from 'react';
import { Mail, Printer, X, ChevronRight } from 'lucide-react';
import ResponsiveModal from '../../../components/ui/ResponsiveModal';

interface NotaFiscalModalProps {
    mostrar: boolean;
    emailCliente?: string;
    onEnviarEmail: (email: string) => void;
    onVisualizar: () => void;
    onImprimir: () => void;
    onFechar: () => void;
    enviando?: boolean;
}

const NotaFiscalModal = ({
    mostrar,
    emailCliente,
    onEnviarEmail,
    onVisualizar,
    onImprimir,
    onFechar,
    enviando = false
}: NotaFiscalModalProps) => {
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

    return (
        <ResponsiveModal
            isOpen={mostrar}
            onClose={onFechar}
            title="Enviar Nota Fiscal"
            subtitle="Como deseja receber o comprovante?"
            headerIcon={<Mail className="w-6 h-6" />}
            headerColor="blue"
            size="md"
            footer={
                <button
                    onClick={onFechar}
                    disabled={enviando}
                    className="w-full sm:w-auto px-8 py-3 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-white rounded-xl font-bold hover:bg-gray-200 dark:hover:bg-gray-600 transition-all border border-gray-200 dark:border-gray-600 flex items-center justify-center gap-2"
                >
                    <span>Concluir</span>
                    <ChevronRight className="w-5 h-5" />
                </button>
            }
        >
            <div className="space-y-6">
                {/* Opção de Email */}
                <div className="space-y-4">
                    <div className="relative">
                        <label className="block text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1.5 ml-1">
                            Email para envio
                        </label>
                        <div className="flex gap-2">
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => handleEmailChange(e.target.value)}
                                placeholder="cliente@exemplo.com"
                                className={`flex-1 px-4 py-3.5 bg-gray-50 dark:bg-gray-900 border-2 rounded-xl focus:ring-2 transition-all outline-none ${email && !emailValido
                                    ? 'border-red-200 focus:ring-red-500'
                                    : 'border-gray-100 dark:border-gray-700 focus:ring-blue-500'
                                    }`}
                                disabled={enviando}
                            />
                            <button
                                onClick={handleEnviar}
                                disabled={!emailValido || !email || enviando}
                                className={`px-4 rounded-xl font-bold transition-all flex items-center gap-2 ${!emailValido || !email || enviando
                                    ? 'bg-gray-100 dark:bg-gray-800 text-gray-400 cursor-not-allowed'
                                    : 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg shadow-blue-500/20'
                                    }`}
                            >
                                {enviando ? (
                                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                                ) : (
                                    <>
                                        <Mail className="w-5 h-5" />
                                        <span className="hidden sm:inline">Enviar</span>
                                    </>
                                )}
                            </button>
                        </div>
                        {email && !emailValido && (
                            <p className="text-[10px] text-red-500 font-bold mt-1 ml-1 flex items-center gap-1">
                                <X className="w-3 h-3" /> Email inválido
                            </p>
                        )}
                    </div>
                </div>

                <div className="h-px bg-gray-100 dark:bg-gray-700 my-2"></div>

                {/* Opções Físicas e Visualização */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <button
                        onClick={onImprimir}
                        disabled={enviando}
                        className="p-4 bg-white dark:bg-gray-800 border-2 border-gray-100 dark:border-gray-700 rounded-2xl flex items-center gap-3 hover:border-blue-500 hover:bg-blue-50/30 transition-all group"
                    >
                        <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-xl group-hover:bg-blue-600 group-hover:text-white transition-colors">
                            <Printer className="w-6 h-6 text-blue-600 dark:text-blue-400 group-hover:text-white" />
                        </div>
                        <div className="text-left">
                            <p className="font-black text-gray-800 dark:text-white text-sm">Imprimir Ticket</p>
                            <p className="text-[10px] text-gray-500 font-medium">Impressora Térmica 80mm</p>
                        </div>
                    </button>

                    <button
                        onClick={onVisualizar}
                        disabled={enviando}
                        className="p-4 bg-white dark:bg-gray-800 border-2 border-gray-100 dark:border-gray-700 rounded-2xl flex items-center gap-3 hover:border-purple-500 hover:bg-purple-50/30 transition-all group"
                    >
                        <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-xl group-hover:bg-purple-600 group-hover:text-white transition-colors">
                            <Mail className="w-6 h-6 text-purple-600 dark:text-purple-400 group-hover:text-white" />
                        </div>
                        <div className="text-left">
                            <p className="font-black text-gray-800 dark:text-white text-sm">Visualizar</p>
                            <p className="text-[10px] text-gray-500 font-medium">Ver PDF no navegador</p>
                        </div>
                    </button>
                </div>

                <div className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-2xl border border-gray-100 dark:border-gray-800">
                    <p className="text-[10px] text-center text-gray-400 dark:text-gray-500 font-bold uppercase tracking-widest leading-loose">
                        ℹ️ Comprovante de venda para fins de simples conferência. Documento não fiscal.
                    </p>
                </div>
            </div>
        </ResponsiveModal>
    );
};

export default NotaFiscalModal;
