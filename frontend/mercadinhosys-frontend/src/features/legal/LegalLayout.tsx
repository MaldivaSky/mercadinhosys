import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { legalInfo } from './legalInfo';

interface LegalLayoutProps {
    titulo: string;
    subtitulo?: string;
    /** Mostra a tarja de "última atualização" no topo. */
    mostrarData?: boolean;
    children: React.ReactNode;
}

/**
 * Moldura comum às páginas públicas institucionais (Termos, Privacidade, Ajuda).
 * Cabeçalho com a marca + voltar, conteúdo legível e rodapé com navegação cruzada.
 */
const LegalLayout: React.FC<LegalLayoutProps> = ({ titulo, subtitulo, mostrarData = true, children }) => {
    return (
        <div className="min-h-screen bg-white text-slate-800">
            {/* Cabeçalho */}
            <header className="border-b border-slate-200 bg-white/90 backdrop-blur sticky top-0 z-10">
                <div className="max-w-3xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
                    <Link to="/" className="flex items-center gap-2 group">
                        <img src="/assets/logo.png" alt="MercadinhoSys" className="w-8 h-8 object-contain" />
                        <span className="text-lg font-black tracking-tighter text-slate-900">
                            Mercadinho<span className="text-blue-600">Sys</span>
                        </span>
                    </Link>
                    <Link
                        to="/"
                        className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-500 hover:text-blue-600 transition"
                    >
                        <ArrowLeft className="w-4 h-4" /> Voltar ao site
                    </Link>
                </div>
            </header>

            {/* Conteúdo */}
            <main className="max-w-3xl mx-auto px-4 sm:px-6 py-10 sm:py-14">
                <h1 className="text-3xl sm:text-4xl font-black tracking-tight text-slate-900">{titulo}</h1>
                {subtitulo && <p className="mt-2 text-slate-500">{subtitulo}</p>}
                {mostrarData && (
                    <p className="mt-3 text-xs font-medium text-slate-400">
                        Última atualização: {legalInfo.ultimaAtualizacao}
                    </p>
                )}

                <div className="legal-prose mt-8 space-y-6 leading-relaxed text-[15px]">
                    {children}
                </div>
            </main>

            {/* Rodapé com navegação cruzada */}
            <footer className="border-t border-slate-200 bg-slate-50">
                <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8 flex flex-col sm:flex-row items-center justify-between gap-4">
                    <p className="text-xs text-slate-400 font-medium">
                        &copy; {new Date().getFullYear()} {legalInfo.produto}. Todos os direitos reservados.
                    </p>
                    <nav className="flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-sm font-semibold text-slate-500">
                        <Link to="/ajuda" className="hover:text-blue-600">Ajuda</Link>
                        <Link to="/termos" className="hover:text-blue-600">Termos de Uso</Link>
                        <Link to="/privacidade" className="hover:text-blue-600">Privacidade</Link>
                        <Link to="/login" className="hover:text-blue-600">Acessar</Link>
                    </nav>
                </div>
            </footer>
        </div>
    );
};

export default LegalLayout;

/** Subtítulo de seção padronizado para as páginas legais. */
export const SecaoTitulo: React.FC<{ numero?: number; children: React.ReactNode }> = ({ numero, children }) => (
    <h2 className="text-xl font-extrabold text-slate-900 pt-2">
        {numero != null && <span className="text-blue-600">{numero}. </span>}
        {children}
    </h2>
);
