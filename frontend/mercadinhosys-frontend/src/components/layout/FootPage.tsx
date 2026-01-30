import React from 'react';
import { Phone, Mail } from 'lucide-react';

const FootPage: React.FC = () => {
    const year = new Date().getFullYear();
    return (
        <footer className="w-full border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex flex-col sm:flex-row items-center justify-between gap-2">
                <div className="flex flex-col sm:flex-row items-center sm:items-start gap-1 sm:gap-3">
                    <div className="text-xs sm:text-sm text-gray-700 dark:text-gray-200 font-medium">
                        MaldivaSky Tech Solutions - Sistema ERP -
                    </div>
                    <div className="text-xs sm:text-sm text-gray-600 dark:text-gray-300">
                        © {year} • Todos os direitos reservados
                    </div>
                </div>
                <div className="flex items-center gap-3 text-xs sm:text-sm">
                    <a 
                        href="https://wa.me/5511919889233" 
                        target="_blank" 
                        rel="noopener noreferrer" 
                        className="inline-flex items-center gap-1.5 text-green-600 dark:text-green-400 hover:text-green-700 dark:hover:text-green-300 transition-colors"
                        aria-label="Abrir WhatsApp"
                    >
                        <Phone className="w-4 h-4" />
                        <span>WhatsApp</span>
                    </a>
                    <span className="hidden sm:inline text-gray-400">•</span>
                    <a 
                        href="mailto:rafaelmaldivas@gmail.com" 
                        className="inline-flex items-center gap-1.5 text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors"
                        aria-label="Enviar e-mail"
                    >
                        <Mail className="w-4 h-4" />
                        <span>Email</span>
                    </a>
                    <span className="hidden sm:inline text-gray-400">•</span>
                    <a href="/settings" className="text-blue-600 dark:text-blue-400 hover:underline">Configurações</a>
                    <span className="hidden sm:inline text-gray-400">•</span>
                    <a href="/reports" className="text-blue-600 dark:text-blue-400 hover:underline">Relatórios</a>
                    <span className="hidden sm:inline text-gray-400">•</span>
                    <span className="text-gray-500 dark:text-gray-400">v1.0</span>
                </div>
            </div>
        </footer>
    );
};

export default FootPage;
