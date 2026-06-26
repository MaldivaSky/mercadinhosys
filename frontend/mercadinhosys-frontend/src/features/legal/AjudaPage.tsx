import React, { useState } from 'react';
import {
    ShoppingCart, Package, Users, BarChart3, FileText, Wallet, Clock, WifiOff,
    ChevronDown, Mail, MessageCircle, LogIn,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import LegalLayout from './LegalLayout';
import { legalInfo, whatsappLink } from './legalInfo';

const recursos = [
    { Icon: ShoppingCart, titulo: 'Frente de caixa (PDV)', desc: 'Venda rápida por código de barras, múltiplas formas de pagamento e cupom.' },
    { Icon: WifiOff, titulo: 'Funciona offline', desc: 'Continue vendendo sem internet; o sistema sincroniza sozinho quando a conexão volta.' },
    { Icon: Package, titulo: 'Estoque e produtos', desc: 'Controle de estoque, custo médio, lotes, validade e curva ABC.' },
    { Icon: Users, titulo: 'Clientes e fiado', desc: 'Cadastro de clientes, histórico de compras e controle de fiado.' },
    { Icon: FileText, titulo: 'Fiscal (NFC-e / NF-e)', desc: 'Importe o XML de compra (cadastra fornecedor e produto) e emita NFC-e.' },
    { Icon: Wallet, titulo: 'Financeiro', desc: 'Contas a pagar, despesas e visão do caixa do dia.' },
    { Icon: Clock, titulo: 'Funcionários e ponto', desc: 'Cadastro de equipe e registro de ponto.' },
    { Icon: BarChart3, titulo: 'Relatórios e painel', desc: 'Dashboard com vendas, lucro e os produtos que mais (e menos) vendem.' },
];

const faq = [
    {
        q: 'Preciso de internet para usar?',
        a: 'O caixa (PDV) funciona mesmo sem internet: você continua vendendo normalmente e o sistema sincroniza automaticamente quando a conexão volta. Os relatórios e o painel precisam de conexão para carregar os dados mais recentes.',
    },
    {
        q: 'O sistema emite nota fiscal (NFC-e)?',
        a: 'Sim. O sistema importa o XML das notas de compra (cadastrando fornecedor e produto automaticamente) e emite NFC-e. Para emitir com valor fiscal, o estabelecimento precisa de CNPJ ativo, certificado digital próprio e parâmetros tributários validados pelo contador. Há um modo de homologação/teste, sem valor fiscal, para conferência.',
    },
    {
        q: 'Meus dados ficam seguros?',
        a: 'Os dados ficam em servidores em nuvem com controle de acesso, criptografia em trânsito e backups. Tratamos os dados conforme a LGPD — veja a Política de Privacidade.',
    },
    {
        q: 'Consigo acessar pelo celular?',
        a: 'Sim. O sistema é uma aplicação web responsiva (PWA), que funciona no computador, no tablet e no celular pelo navegador.',
    },
    {
        q: 'Como começo a usar?',
        a: 'Você cria a conta do seu estabelecimento, cadastra (ou importa) seus produtos e já pode abrir o caixa e vender. Nossa equipe ajuda na configuração inicial e no treinamento.',
    },
    {
        q: 'Posso cancelar quando quiser?',
        a: 'Sim. A assinatura pode ser cancelada a qualquer momento; o cancelamento encerra as renovações futuras. Detalhes nos Termos de Uso.',
    },
];

const AjudaPage: React.FC = () => {
    const [aberta, setAberta] = useState<number | null>(0);
    const wa = whatsappLink('Olá! Preciso de ajuda com o MercadinhoSys.');

    return (
        <LegalLayout
            titulo="Central de Ajuda"
            subtitulo={`Tudo o que o ${legalInfo.produto} faz e respostas para as dúvidas mais comuns.`}
            mostrarData={false}
        >
            {/* O que o sistema faz */}
            <section>
                <h2 className="text-xl font-extrabold text-slate-900 mb-4">O que o sistema faz</h2>
                <div className="grid sm:grid-cols-2 gap-3">
                    {recursos.map(({ Icon, titulo, desc }) => (
                        <div key={titulo} className="flex gap-3 rounded-xl border border-slate-200 p-4 hover:border-blue-300 transition">
                            <div className="shrink-0 w-10 h-10 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
                                <Icon className="w-5 h-5" />
                            </div>
                            <div>
                                <p className="font-bold text-slate-800 text-sm">{titulo}</p>
                                <p className="text-sm text-slate-500">{desc}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            {/* FAQ */}
            <section>
                <h2 className="text-xl font-extrabold text-slate-900 mb-4">Perguntas frequentes</h2>
                <div className="space-y-2">
                    {faq.map((item, i) => {
                        const open = aberta === i;
                        return (
                            <div key={i} className="rounded-xl border border-slate-200 overflow-hidden">
                                <button
                                    onClick={() => setAberta(open ? null : i)}
                                    className="w-full flex items-center justify-between gap-3 px-4 py-3.5 text-left font-bold text-slate-800 hover:bg-slate-50 transition"
                                    aria-expanded={open}
                                >
                                    <span>{item.q}</span>
                                    <ChevronDown className={`w-5 h-5 text-slate-400 shrink-0 transition-transform ${open ? 'rotate-180' : ''}`} />
                                </button>
                                {open && (
                                    <div className="px-4 pb-4 text-sm text-slate-600 leading-relaxed">{item.a}</div>
                                )}
                            </div>
                        );
                    })}
                </div>
            </section>

            {/* Contato / Suporte */}
            <section>
                <h2 className="text-xl font-extrabold text-slate-900 mb-4">Fale com o suporte</h2>
                <div className="grid sm:grid-cols-2 gap-3">
                    <a
                        href={`mailto:${legalInfo.emailContato}`}
                        className="flex items-center gap-3 rounded-xl border border-slate-200 p-4 hover:border-blue-300 hover:bg-blue-50/40 transition"
                    >
                        <div className="w-10 h-10 rounded-lg bg-blue-600 text-white flex items-center justify-center"><Mail className="w-5 h-5" /></div>
                        <div>
                            <p className="font-bold text-slate-800 text-sm">E-mail</p>
                            <p className="text-sm text-slate-500">{legalInfo.emailContato}</p>
                        </div>
                    </a>
                    {wa && (
                        <a
                            href={wa}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-3 rounded-xl border border-slate-200 p-4 hover:border-emerald-300 hover:bg-emerald-50/40 transition"
                        >
                            <div className="w-10 h-10 rounded-lg bg-emerald-600 text-white flex items-center justify-center"><MessageCircle className="w-5 h-5" /></div>
                            <div>
                                <p className="font-bold text-slate-800 text-sm">WhatsApp</p>
                                <p className="text-sm text-slate-500">Atendimento rápido</p>
                            </div>
                        </a>
                    )}
                </div>

                <div className="mt-4 flex flex-wrap gap-3 text-sm">
                    <Link to="/login" className="inline-flex items-center gap-1.5 font-semibold text-blue-600 hover:underline">
                        <LogIn className="w-4 h-4" /> Acessar o sistema
                    </Link>
                    <span className="text-slate-300">•</span>
                    <Link to="/termos" className="font-semibold text-slate-500 hover:text-blue-600">Termos de Uso</Link>
                    <span className="text-slate-300">•</span>
                    <Link to="/privacidade" className="font-semibold text-slate-500 hover:text-blue-600">Política de Privacidade</Link>
                </div>
            </section>
        </LegalLayout>
    );
};

export default AjudaPage;
