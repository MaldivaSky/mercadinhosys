import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    CheckCircle,
    ShoppingCart,
    Users,
    Zap,
    ShieldCheck,
    TrendingUp,
    Globe,
    MessageCircle,
    Star,
    Cpu,
    Lock,
    Mail,
    Phone,
    User,
    PlayCircle
} from 'lucide-react';
import { toast } from 'react-hot-toast';

const LandingPage: React.FC = () => {
    const navigate = useNavigate();
    const [leadName, setLeadName] = useState('');
    const [leadEmail, setLeadEmail] = useState('');
    const [leadWhatsApp, setLeadWhatsApp] = useState('');
    const [loadingLead, setLoadingLead] = useState(false);

    const handleLeadSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setLoadingLead(true);
        // Simulação de salvamento de lead
        setTimeout(() => {
            setLoadingLead(false);
            toast.success('Informações enviadas! Entraremos em contato em breve.');
            setLeadName('');
            setLeadEmail('');
            setLeadWhatsApp('');
            // Abrir WhatsApp após cadastro
            window.open('https://wa.me/5511919889233?text=Olá! Acabei de me cadastrar no site e gostaria de saber mais sobre o MercadinhoSys.', '_blank');
        }, 1500);
    };

    const tiers = [
        {
            name: 'Basic',
            price: 'R$ 29,90',
            period: '/mês',
            description: 'Perfeito para quem está começando e quer fugir das planilhas.',
            features: [
                'Até 500 produtos',
                'PDV ultra-rápido',
                'Controle de Estoque Essencial',
                'Relatórios Mensais de Vendas',
                'Suporte via Email'
            ],
            cta: 'Começar Basic',
            highlight: false
        },
        {
            name: 'Advanced',
            price: 'R$ 69,90',
            period: '/mês',
            description: 'A escolha dos especialistas para escalar o faturamento.',
            features: [
                'Produtos Ilimitados',
                'Dashboard Científico (AI Insight)',
                'Gestão de Funcionários & RH',
                'Previsão de Demanda & Estacionalidade',
                'Suporte Prioritário 24/7'
            ],
            cta: 'Assinar Advanced',
            highlight: true
        },
        {
            name: 'Premium',
            price: 'R$ 99,90',
            period: '/mês',
            description: 'Gestão robusta para múltiplas unidades e redes de lojas.',
            features: [
                'Multitenancy (Multi-estabelecimentos)',
                'White Label & Personalização',
                'API Full de Integração',
                'Conciliação Bancária Completa',
                'Painel de Auditoria de Perdas'
            ],
            cta: 'Lançar Premium',
            highlight: false
        }
    ];

    const testimonials = [
        {
            name: "João Pereira",
            role: "Dono do Mercadinho São José",
            comment: "Depois que instalei o MercadinhoSys, parei de perder 20% do meu estoque por validade. A inteligência do dashboard é surreal.",
            stars: 5,
            image: "https://images.unsplash.com/photo-1560250097-0b93528c311a?auto=format&fit=crop&q=80&w=150"
        },
        {
            name: "Maria Silva",
            role: "Gerente Operacional - Grupo Varejo",
            comment: "O PDV é o mais rápido que já usei. Mesmo em dias de black friday, o sistema não travou uma vez sequer. Recomendo para todos.",
            stars: 5,
            image: "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&q=80&w=150"
        },
        {
            name: "Ricardo Mendes",
            role: "Empresário MEI",
            comment: "O plano Basic cabe no bolso e me deu profissionalismo. Meus clientes adoram receber o cupom fiscal direto no WhatsApp.",
            stars: 5,
            image: "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?auto=format&fit=crop&q=80&w=150"
        }
    ];

    return (
        <div className="min-h-screen bg-slate-50 text-gray-900 font-sans selection:bg-blue-200 selection:text-blue-900 overflow-x-hidden">

            {/* WhatsApp Floating Button */}
            <a
                href="https://wa.me/5511919889233"
                target="_blank"
                rel="noreferrer"
                className="fixed bottom-8 right-8 z-[100] bg-emerald-500 text-white p-4 rounded-full shadow-2xl shadow-emerald-200 hover:scale-110 active:scale-95 transition-all flex items-center justify-center group"
            >
                <MessageCircle className="w-8 h-8" />
                <span className="max-w-0 overflow-hidden group-hover:max-w-xs group-hover:ml-2 transition-all duration-500 font-bold whitespace-nowrap">
                    Falar no WhatsApp
                </span>
            </a>

            {/* Navbar */}
            <nav className="fixed top-0 w-full z-50 bg-white/90 backdrop-blur-xl border-b border-gray-100">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center h-20">
                        <div className="flex items-center gap-3 group cursor-pointer" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
                            <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center p-1 shadow-md group-hover:scale-110 transition-transform overflow-hidden">
                                <img
                                    src="/assets/logo.png"
                                    alt="MercadinhoSys Logo"
                                    onError={(e) => {
                                        (e.target as HTMLImageElement).parentElement!.innerHTML = '<div class="w-full h-full bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold">M</div>';
                                    }}
                                    className="w-full h-full object-contain"
                                />
                            </div>
                            <span className="text-2xl font-black text-gray-900 tracking-tighter">
                                Mercadinho<span className="text-blue-600">Sys</span>
                            </span>
                        </div>
                        <div className="hidden lg:flex items-center gap-10">
                            <a href="#features" className="text-sm font-bold text-gray-500 hover:text-blue-600 transition-colors uppercase tracking-widest">Recursos</a>
                            <a href="#testimonials" className="text-sm font-bold text-gray-500 hover:text-blue-600 transition-colors uppercase tracking-widest">Depoimentos</a>
                            <a href="#pricing" className="text-sm font-bold text-gray-500 hover:text-blue-600 transition-colors uppercase tracking-widest">Planos</a>
                            <a href="#contact" className="text-sm font-bold text-gray-500 hover:text-blue-600 transition-colors uppercase tracking-widest">Contato</a>
                            <button
                                onClick={() => navigate('/login')}
                                className="px-8 py-3 bg-gray-900 text-white rounded-xl font-black text-sm hover:bg-black transition-all shadow-xl shadow-gray-200 hover:-translate-y-0.5 active:translate-y-0"
                            >
                                ACESSAR PAINEL
                            </button>
                        </div>
                        <div className="lg:hidden">
                            <button onClick={() => navigate('/login')} className="bg-blue-600 text-white px-5 py-2 rounded-lg font-bold text-sm">LOGIN</button>
                        </div>
                    </div>
                </div>
            </nav>

            {/* HERO SECTION */}
            <section className="relative pt-32 pb-20 lg:pt-52 lg:pb-40 overflow-hidden bg-white">
                <div className="absolute top-0 right-0 -z-10 w-[1000px] h-[1000px] bg-blue-50/50 rounded-full blur-[120px] translate-x-1/3 -translate-y-1/3"></div>

                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="grid lg:grid-cols-2 gap-16 items-center">
                        <div className="text-left">
                            <div className="inline-flex items-center gap-3 px-4 py-2 rounded-full bg-blue-50 text-blue-700 font-bold text-xs mb-8 tracking-widest uppercase border border-blue-100">
                                <img src="/assets/logo.png" className="w-5 h-5 object-contain" alt="mini-logo" />
                                O ERP Nº 1 PARA PEQUENOS VAREJISTAS
                            </div>
                            <h1 className="text-5xl lg:text-8xl font-black text-gray-900 tracking-tight leading-[0.9] mb-8">
                                Transforme seu <br />
                                <span className="text-blue-600">Mercadinho</span> em uma <br />
                                <span className="bg-gradient-to-r from-indigo-600 to-blue-600 bg-clip-text text-transparent underline decoration-blue-200 underline-offset-8">Potência.</span>
                            </h1>
                            <p className="text-xl lg:text-2xl text-gray-600 leading-relaxed mb-12 font-medium max-w-xl">
                                Esqueça as planilhas. Gerencie estoque, vendas e lucro com inteligência artificial e o PDV mais rápido do Brasil.
                            </p>
                            <div className="flex flex-col sm:flex-row items-center gap-6">
                                <button
                                    onClick={() => navigate('/login')}
                                    className="w-full sm:w-auto px-12 py-6 bg-blue-600 text-white rounded-2xl font-black text-xl hover:bg-blue-700 transition-all shadow-2xl shadow-blue-200 flex items-center justify-center gap-3 group"
                                >
                                    GARANTIR MEU LUCRO AGORA
                                    <PlayCircle className="w-6 h-6 group-hover:scale-110 transition-transform" />
                                </button>
                                <a
                                    href="#pricing"
                                    className="w-full sm:w-auto px-12 py-6 bg-white text-gray-900 border-2 border-gray-100 rounded-2xl font-black text-xl hover:border-blue-600 transition-all text-center"
                                >
                                    VER COMPARATIVO
                                </a>
                            </div>
                            <div className="mt-12 flex items-center gap-6 text-sm font-bold text-gray-400">
                                <div className="flex -space-x-3">
                                    {[1, 2, 3, 4].map(i => (
                                        <div key={i} className="w-10 h-10 rounded-full border-2 border-white bg-gray-200 overflow-hidden">
                                            <img src={`https://i.pravatar.cc/100?u=${i}`} alt="user" />
                                        </div>
                                    ))}
                                </div>
                                <p>+1.200 empresários satisfeitos hoje</p>
                            </div>
                        </div>
                        <div className="relative lg:block">
                            <div className="absolute -inset-4 bg-gradient-to-tr from-blue-600/20 to-indigo-600/20 rounded-[3rem] blur-2xl"></div>
                            <div className="relative bg-white border border-gray-100 rounded-[3rem] shadow-2xl p-4 overflow-hidden group">
                                <video
                                    autoPlay
                                    muted
                                    loop
                                    playsInline
                                    className="w-full rounded-[2.5rem] group-hover:scale-105 transition-transform duration-1000"
                                >
                                    <source src="/screenshots/videosys.mp4" type="video/mp4" />
                                    Seu navegador não suporta vídeos.
                                </video>
                                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                                    <div className="w-20 h-20 bg-white/30 backdrop-blur-md rounded-full flex items-center justify-center cursor-pointer hover:scale-110 transition-transform">
                                        <PlayCircle className="w-16 h-16 text-white drop-shadow-lg" />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* PAS SECTION (IDENTIFICANDO A DOR) */}
            <section className="py-24 bg-rose-50/30">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center max-w-3xl mx-auto mb-16">
                        <h2 className="text-rose-600 font-black tracking-widest text-sm uppercase mb-4">O Preço do Amadorismo</h2>
                        <h3 className="text-4xl lg:text-5xl font-black text-gray-900 leading-tight">Quanto custa para o seu bolso <span className="text-rose-600">não ter controle?</span></h3>
                    </div>

                    <div className="grid md:grid-cols-3 gap-8">
                        {[
                            {
                                pain: "Estoque Furado",
                                agit: "Produtos vencendo na prateleira ou sumindo sem você saber. O dinheiro que deveria ser seu está indo pro lixo.",
                                icon: "📉"
                            },
                            {
                                pain: "Filas de Desistência",
                                agit: "Sistema lento que trava no meio da venda. Seu cliente larga o carrinho e vai comprar no vizinho.",
                                icon: "⏳"
                            },
                            {
                                pain: "Lucro Fantasma",
                                agit: "Você fatura muito, mas no fim do mês não vê a cor do dinheiro. Onde estão as taxas e custos?",
                                icon: "👻"
                            }
                        ].map((item, idx) => (
                            <div key={idx} className="bg-white p-10 rounded-[2.5rem] border-2 border-rose-100 shadow-xl hover:shadow-rose-100 transition-all">
                                <span className="text-4xl mb-6 block">{item.icon}</span>
                                <h4 className="text-2xl font-black text-gray-900 mb-4">{item.pain}</h4>
                                <p className="text-gray-600 font-medium leading-relaxed">{item.agit}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* COMPARISON TABLE (POR QUE SOMOS MELHORES) */}
            <section className="py-24 bg-white">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-16">
                        <h2 className="text-blue-600 font-black tracking-widest text-sm uppercase mb-4">Diferenciação Real</h2>
                        <h3 className="text-4xl lg:text-5xl font-black text-gray-900">MercadinhoSys vs. <span className="text-gray-400">Sistemas Antigos</span></h3>
                    </div>

                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-separate border-spacing-y-4">
                            <thead>
                                <tr className="text-gray-400 text-sm font-bold uppercase tracking-widest">
                                    <th className="px-8 pb-4">Funcionalidade</th>
                                    <th className="px-8 pb-4">Sistemas Legados</th>
                                    <th className="px-8 pb-4 text-blue-600">MercadinhoSys (O Futuro)</th>
                                </tr>
                            </thead>
                            <tbody>
                                {[
                                    ["Velocidade de Venda", "Lento, pesado e trava toda hora", "Ultra-rápido, otimizado para o dia a dia"],
                                    ["Inteligência de Dados", "Relatórios complexos que ninguém entende", "IA que te diz onde investir e onde economizar"],
                                    ["Mobilidade", "Preso ao balcão e ao servidor local", "Acesse tudo de onde quiser (Nuvem Real)"],
                                    ["Facilidade de Uso", "Dias de treinamento obrigatório", "Seus funcionários aprendem em 15 minutos"],
                                    ["WhatsApp Integrado", "Não possui ou custa uma fortuna", "Nativo. Cupom e atendimento direto no zap"]
                                ].map((row, i) => (
                                    <tr key={i} className="bg-slate-50/50 rounded-2xl overflow-hidden">
                                        <td className="px-8 py-6 font-black text-gray-700 rounded-l-2xl border-y border-l border-gray-100">{row[0]}</td>
                                        <td className="px-8 py-6 text-gray-400 font-medium border-y border-gray-100">{row[1]}</td>
                                        <td className="px-8 py-6 text-blue-600 font-black rounded-r-2xl border-y border-r border-blue-100 bg-blue-50/50">{row[2]}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </section>

            {/* O SISTEMA EM AÇÃO - GALERIA REAL */}
            <section className="py-24 bg-white overflow-hidden">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center max-w-3xl mx-auto mb-20 whitespace-normal">
                        <h2 className="text-blue-600 font-black tracking-widest text-sm uppercase mb-4">Interface de Alta Performance</h2>
                        <h3 className="text-4xl lg:text-6xl font-black text-gray-900 mb-8">O sistema que seus olhos <span className="text-blue-600">vão amar.</span></h3>
                        <p className="text-xl text-gray-500 font-medium">Capture a essência da modernidade com uma interface limpa, rápida e intuitiva. Abaixo, fotos reais do sistema.</p>
                    </div>

                    <div className="grid md:grid-cols-2 gap-12">
                        {/* Coluna 1 */}
                        <div className="space-y-12">
                            <div className="group">
                                <div className="bg-slate-50 p-6 rounded-[3rem] border border-gray-100 shadow-xl overflow-hidden mb-6 group-hover:shadow-2xl transition-all relative">
                                    <img
                                        src="/screenshots/pdv.png"
                                        alt="Caixa PDV"
                                        onError={(e) => {
                                            (e.target as HTMLImageElement).src = 'https://images.unsplash.com/photo-1556742111-a301076d9d18?auto=format&fit=crop&q=80&w=800';
                                        }}
                                        className="w-full rounded-3xl group-hover:scale-[1.03] transition-transform duration-700"
                                    />
                                </div>
                                <h4 className="text-2xl font-black px-6">Caixa PDV Ultra-Rápido</h4>
                                <p className="text-gray-500 font-bold px-6">Layout focado em produtividade para atendimento imediato.</p>
                            </div>
                            <div className="group">
                                <div className="bg-slate-50 p-6 rounded-[3rem] border border-gray-100 shadow-xl overflow-hidden mb-6 group-hover:shadow-2xl transition-all relative">
                                    <img
                                        src="/screenshots/products.png"
                                        alt="Gestão de Produtos"
                                        onError={(e) => {
                                            (e.target as HTMLImageElement).src = 'https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&q=80&w=800';
                                        }}
                                        className="w-full rounded-3xl group-hover:scale-[1.03] transition-transform duration-700"
                                    />
                                </div>
                                <h4 className="text-2xl font-black px-6">Gestão de Estoque Inteligente</h4>
                                <p className="text-gray-500 font-bold px-6">Painéis de controle com classificação ABC e alertas automáticos.</p>
                            </div>
                        </div>
                        {/* Coluna 2 */}
                        <div className="space-y-12 md:translate-y-20">
                            <div className="group">
                                <div className="bg-slate-50 p-6 rounded-[3rem] border border-gray-100 shadow-xl overflow-hidden mb-6 group-hover:shadow-2xl transition-all relative">
                                    <video
                                        autoPlay
                                        muted
                                        loop
                                        playsInline
                                        className="w-full rounded-3xl group-hover:scale-[1.03] transition-transform duration-700 shadow-lg"
                                    >
                                        <source src="/screenshots/videosys.mp4" type="video/mp4" />
                                        Seu navegador não suporta vídeos.
                                    </video>
                                </div>
                                <h4 className="text-2xl font-black px-6">Central de Inteligência ERP</h4>
                                <p className="text-gray-500 font-bold px-6">Análises detalhadas para uma tomada de decisão baseada em dados.</p>
                            </div>
                            <div className="group">
                                <div className="bg-slate-50 p-6 rounded-[3rem] border border-gray-100 shadow-xl overflow-hidden mb-6 group-hover:shadow-2xl transition-all relative">
                                    <img
                                        src="/screenshots/sales.png"
                                        alt="Análise de Vendas"
                                        onError={(e) => {
                                            (e.target as HTMLImageElement).src = 'https://images.unsplash.com/photo-1551434678-e076c223a692?auto=format&fit=crop&q=80&w=800';
                                        }}
                                        className="w-full rounded-3xl group-hover:scale-[1.03] transition-transform duration-700"
                                    />
                                </div>
                                <h4 className="text-2xl font-black px-6">Painel de Vendas Dinâmico</h4>
                                <p className="text-gray-500 font-bold px-6">Filtros avançados e acompanhamento de metas em tempo real.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* QUOTE / BANNER RÁPIDO */}
            <section className="py-20 bg-gray-900 text-white overflow-hidden relative">
                <div className="absolute top-1/2 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-gray-700 to-transparent"></div>
                <div className="max-w-7xl mx-auto px-4 text-center relative z-10">
                    <p className="text-2xl md:text-4xl font-black italic tracking-tight opacity-90">
                        "O sistema é tão intuitivo que meus funcionários aprenderam em 15 minutos."
                    </p>
                    <p className="mt-4 text-blue-400 font-bold tracking-widest uppercase text-sm">— Rede de Supermercados Smart</p>
                </div>
            </section>

            {/* FEATURES DETALHADAS */}
            <section id="features" className="py-32 bg-slate-50">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center max-w-3xl mx-auto mb-20">
                        <h2 className="text-blue-600 font-black tracking-[0.2em] text-sm uppercase mb-4">O que oferecemos</h2>
                        <h3 className="text-4xl lg:text-6xl font-black text-gray-900 leading-tight">Uma central de comando completa para sua loja.</h3>
                    </div>

                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-10">
                        {[
                            {
                                icon: <ShoppingCart className="w-10 h-10 text-white" />,
                                color: "bg-blue-600",
                                title: "PDV Ultra-Fast 2.0",
                                description: "Interface otimizada para agilidade. Atalhos de teclado, integração com balanças e leitores laser sem atraso."
                            },
                            {
                                icon: <TrendingUp className="w-10 h-10 text-white" />,
                                color: "bg-emerald-600",
                                title: "CFO Virtual (AI)",
                                description: "Consultoria financeira automática. Nosso algoritmo identifica desperdícios e sugere onde investir seu lucro."
                            },
                            {
                                icon: <Zap className="w-10 h-10 text-white" />,
                                color: "bg-amber-500",
                                title: "Smart Inventory",
                                description: "Controle de estoque com curva ABC. Saiba exatamente o que está vendendo e o que está parado."
                            },
                            {
                                icon: <Users className="w-10 h-10 text-white" />,
                                color: "bg-indigo-600",
                                title: "RH & Gestão de Ponto",
                                description: "Controle jornada de trabalho, gere holerites e analise o desempenho de cada colaborador nativamente."
                            },
                            {
                                icon: <ShieldCheck className="w-10 h-10 text-white" />,
                                color: "bg-rose-600",
                                title: "Segurança de Dados",
                                description: "Backups redundantes a cada 1 hora. Seus dados estão protegidos sob criptografia de nível militar (AES-256)."
                            },
                            {
                                icon: <Globe className="w-10 h-10 text-white" />,
                                color: "bg-cyan-600",
                                title: "Multi-Estabelecimento",
                                description: "Gerencie 1 ou 100 lojas de um único lugar. Visão consolidada do seu império comercial."
                            }
                        ].map((feature, idx) => (
                            <div key={idx} className="bg-white p-12 rounded-[3rem] border border-gray-100 hover:shadow-2xl hover:shadow-blue-100 transition-all group lg:odd:-translate-y-4">
                                <div className={`mb-8 w-20 h-20 ${feature.color} rounded-3xl flex items-center justify-center shadow-lg group-hover:rotate-12 transition-transform`}>
                                    {feature.icon}
                                </div>
                                <h4 className="text-2xl font-black text-gray-900 mb-6">{feature.title}</h4>
                                <p className="text-gray-500 leading-relaxed text-lg font-medium">{feature.description}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* SOCIAL PROOF / DEPOIMENTOS */}
            <section id="testimonials" className="py-32 bg-white">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex flex-col lg:flex-row justify-between items-end mb-20 gap-10">
                        <div className="max-w-2xl text-left">
                            <h2 className="text-blue-600 font-black tracking-widest text-sm uppercase mb-4">Social Proof</h2>
                            <h3 className="text-4xl lg:text-6xl font-black text-gray-900 leading-tight">Quem usa, confirma: o lucro aumenta.</h3>
                        </div>
                        <div className="flex items-center gap-4 bg-slate-50 px-8 py-4 rounded-3xl border border-gray-100">
                            <Star className="w-6 h-6 fill-amber-400 text-amber-400" />
                            <span className="text-3xl font-black">4.9/5.0</span>
                            <span className="text-gray-400 font-bold ml-2">Média de satisfação</span>
                        </div>
                    </div>

                    <div className="grid md:grid-cols-3 gap-8">
                        {testimonials.map((t, i) => (
                            <div key={i} className="bg-slate-50 p-10 rounded-[2.5rem] border border-gray-100 relative group">
                                <div className="flex gap-1 mb-6">
                                    {[...Array(t.stars)].map((_, s) => (
                                        <Star key={s} className="w-4 h-4 fill-amber-400 text-amber-400" />
                                    ))}
                                </div>
                                <p className="text-lg font-medium text-gray-700 italic mb-8 leading-relaxed">
                                    "{t.comment}"
                                </p>
                                <div className="flex items-center gap-4">
                                    <img src={t.image} alt={t.name} className="w-14 h-14 rounded-full border-2 border-white shadow-md" />
                                    <div>
                                        <p className="font-black text-gray-900">{t.name}</p>
                                        <p className="text-sm font-bold text-blue-600">{t.role}</p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* TECHNICAL ARCHITECTURE Section */}
            <section className="py-32 bg-gray-900 text-white overflow-hidden">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
                    <div className="grid lg:grid-cols-2 gap-20 items-center">
                        <div>
                            <h2 className="text-blue-400 font-black tracking-widest text-sm uppercase mb-4">Engineering Focus</h2>
                            <h3 className="text-4xl lg:text-6xl font-black mb-10 leading-tight">Tecnologia de ponta para sua tranquilidade.</h3>
                            <div className="space-y-8">
                                <div className="flex gap-6">
                                    <div className="w-14 h-14 rounded-2xl bg-white/10 flex items-center justify-center shrink-0">
                                        <Cpu className="w-7 h-7 text-blue-400" />
                                    </div>
                                    <div>
                                        <h4 className="text-xl font-bold mb-2">Arquitetura de Alta Performance</h4>
                                        <p className="text-gray-400 font-medium">Lógica processada via **FastAPI** e **React 18**, garantindo tempos de resposta sub-milissegundos.</p>
                                    </div>
                                </div>
                                <div className="flex gap-6">
                                    <div className="w-14 h-14 rounded-2xl bg-white/10 flex items-center justify-center shrink-0">
                                        <Lock className="w-7 h-7 text-emerald-400" />
                                    </div>
                                    <div>
                                        <h4 className="text-xl font-bold mb-2">Segurança de Dados Tier-4</h4>
                                        <p className="text-gray-400 font-medium">Infraestrutura hospedada na AWS com isolamento total (Tenant Isolation) por estabelecimento.</p>
                                    </div>
                                </div>
                                <div className="flex gap-6">
                                    <div className="w-14 h-14 rounded-2xl bg-white/10 flex items-center justify-center shrink-0">
                                        <Globe className="w-7 h-7 text-indigo-400" />
                                    </div>
                                    <div>
                                        <h4 className="text-xl font-bold mb-2">Sincronização em Nuvem</h4>
                                        <p className="text-gray-400 font-medium">Acesso multi-plataforma. Seus dados estão sempre com você, em qualquer lugar do mundo.</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div className="relative">
                            <div className="bg-gradient-to-tr from-blue-600 to-indigo-600 rounded-[4rem] p-12 lg:p-20 shadow-2xl relative overflow-hidden group">
                                <div className="absolute -top-10 -right-10 w-64 h-64 bg-white/10 rounded-full blur-3xl group-hover:scale-150 transition-transform duration-1000"></div>
                                <div className="relative z-10 text-center">
                                    <h4 className="text-3xl font-black mb-6">99.98% Uptime</h4>
                                    <p className="text-blue-100 font-medium mb-12">Garantimos estabilidade total ou devolvemos seu dinheiro. Nossa infraestrutura é resiliente a falhas.</p>
                                    <button
                                        onClick={() => navigate('/login')}
                                        className="w-full py-5 bg-white text-blue-900 rounded-2xl font-black text-lg hover:bg-blue-50 transition-all shadow-xl"
                                    >
                                        VER DEMO TÉCNICA
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* PRICING Section */}
            <section id="pricing" className="py-32 bg-slate-50">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center max-w-3xl mx-auto mb-20 whitespace-normal">
                        <h2 className="text-blue-600 font-black tracking-widest text-sm uppercase mb-4">Investimento</h2>
                        <h3 className="text-4xl lg:text-6xl font-black text-gray-900 mb-8">Escolha o motor do seu crescimento.</h3>
                        <p className="text-xl text-gray-500 font-medium">Planos flexíveis para cada estágio do seu negócio varejista.</p>
                    </div>

                    <div className="grid lg:grid-cols-3 gap-8 items-stretch">
                        {tiers.map((tier, idx) => (
                            <div
                                key={idx}
                                className={`relative flex flex-col p-12 rounded-[3.5rem] border-2 transition-all duration-500 hover:shadow-2xl ${tier.highlight
                                    ? 'border-blue-600 bg-white scale-105 z-10'
                                    : 'border-transparent bg-white shadow-lg'
                                    }`}
                            >
                                {tier.highlight && (
                                    <div className="absolute top-0 left-1/2 -track-widest -translate-x-1/2 -translate-y-1/2 bg-blue-600 text-white px-8 py-2 rounded-full text-xs font-black tracking-widest uppercase">
                                        IDEAL PARA VOCÊ
                                    </div>
                                )}
                                <div className="mb-10">
                                    <h4 className="text-2xl font-black text-gray-900 mb-2">{tier.name}</h4>
                                    <div className="flex items-baseline gap-1 mb-6">
                                        <span className="text-5xl font-black text-gray-900 tracking-tight">{tier.price}</span>
                                        <span className="text-gray-400 font-bold">{tier.period}</span>
                                    </div>
                                    <p className="text-gray-500 font-semibold leading-relaxed min-h-[60px]">{tier.description}</p>
                                </div>
                                <div className="space-y-6 mb-12 flex-1">
                                    {tier.features.map((feature, fIdx) => (
                                        <div key={fIdx} className="flex items-start gap-4 group">
                                            <div className="shrink-0 mt-1">
                                                <CheckCircle className={`w-5 h-5 ${tier.highlight ? 'text-blue-600' : 'text-emerald-500'}`} />
                                            </div>
                                            <span className="text-gray-700 font-bold text-sm leading-snug group-hover:text-gray-900 transition-colors">{feature}</span>
                                        </div>
                                    ))}
                                </div>
                                <button
                                    onClick={() => navigate('/login')}
                                    className={`w-full py-5 rounded-3xl font-black text-lg transition-all active:scale-95 ${tier.highlight
                                        ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-xl shadow-blue-200'
                                        : 'bg-gray-900 text-white hover:bg-black'
                                        }`}>
                                    {tier.cta}
                                </button>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* FAQ / OBJEÇÕES Section */}
            <section className="py-24 bg-white">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center max-w-3xl mx-auto mb-20 whitespace-normal">
                        <h2 className="text-blue-600 font-black tracking-widest text-sm uppercase mb-4">Dúvidas Frequentes</h2>
                        <h3 className="text-4xl lg:text-5xl font-black text-gray-900 mb-8">Tudo o que você precisa saber.</h3>
                    </div>

                    <div className="grid md:grid-cols-2 gap-10">
                        {[
                            {
                                q: "Como funciona a migração de dados?",
                                a: "Temos um importador inteligente. Você sobe sua planilha de produtos e o sistema organiza tudo para você em minutos."
                            },
                            {
                                q: "Preciso de internet o tempo todo?",
                                a: "Não. Nosso PDV foi projetado para funcionar mesmo com oscilações. Seus dados são sincronizados assim que a conexão volta."
                            },
                            {
                                q: "O sistema é seguro? Meus dados sumirão?",
                                a: "Hospedagem em nuvem (AWS) com backups automáticos. Seus dados estão mais seguros aqui do que em um computador local que pode quebrar."
                            },
                            {
                                q: "Tem fidelidade ou multa de cancelamento?",
                                a: "Zero. Você paga pelo mês que usar. Se não estiver satisfeito, pode cancelar a qualquer momento sem letras miúdas."
                            },
                            {
                                q: "O suporte é humanizado?",
                                a: "Sim! Nada de robôs travados. Nosso time de especialistas atende via WhatsApp e e-mail para resolver sua dúvida na hora."
                            },
                            {
                                q: "Dá para emitir cupom fiscal?",
                                a: "Com certeza. O sistema está preparado para as normas fiscais brasileiras (NFC-e/SAT) dependendo da sua região."
                            }
                        ].map((faq, idx) => (
                            <div key={idx} className="bg-slate-50 p-8 rounded-[2rem] border border-gray-100 hover:border-blue-100 transition-colors">
                                <h4 className="text-xl font-black text-gray-900 mb-4">{faq.q}</h4>
                                <p className="text-gray-600 font-medium leading-relaxed">{faq.a}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>
            <section id="contact" className="py-32 bg-white">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="bg-gray-900 rounded-[4rem] overflow-hidden shadow-2xl relative">
                        {/* DECOR */}
                        <div className="absolute -bottom-20 -left-20 w-80 h-80 bg-blue-600/20 rounded-full blur-[100px]"></div>

                        <div className="grid lg:grid-cols-2">
                            <div className="p-12 lg:p-24 border-b lg:border-b-0 lg:border-r border-white/10 relative z-10">
                                <h3 className="text-4xl lg:text-6xl font-black text-white mb-8">Fale com um Especialista.</h3>
                                <p className="text-xl text-gray-400 font-medium mb-12 leading-relaxed">
                                    Quer entender como o **MercadinhoSys** pode ser adaptado especificamente para o seu modelo de negócio? Preencha os dados e retornamos em minutos.
                                </p>
                                <div className="space-y-8">
                                    <div className="flex items-center gap-6">
                                        <div className="w-12 h-12 bg-blue-600/20 rounded-xl flex items-center justify-center">
                                            <Phone className="w-6 h-6 text-blue-400" />
                                        </div>
                                        <div>
                                            <p className="text-gray-500 font-bold text-xs uppercase tracking-widest">Ligue agora</p>
                                            <p className="text-xl font-bold text-white">(11) 91988-9233</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-6">
                                        <div className="w-12 h-12 bg-emerald-600/20 rounded-xl flex items-center justify-center">
                                            <Mail className="w-6 h-6 text-emerald-400" />
                                        </div>
                                        <div>
                                            <p className="text-gray-500 font-bold text-xs uppercase tracking-widest">E-mail Comercial</p>
                                            <p className="text-xl font-bold text-white">vendas@mercadinhosys.com.br</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div className="p-12 lg:p-24 bg-white/5 backdrop-blur-sm relative z-10">
                                <form onSubmit={handleLeadSubmit} className="space-y-6">
                                    <div>
                                        <label className="block text-gray-400 text-sm font-bold mb-3 uppercase tracking-widest">Nome Completo</label>
                                        <div className="relative">
                                            <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                                            <input
                                                required
                                                type="text"
                                                placeholder="Seu nome aqui"
                                                value={leadName}
                                                onChange={(e) => setLeadName(e.target.value)}
                                                className="w-full bg-white/10 border border-white/10 rounded-2xl py-5 pl-12 pr-6 text-white font-medium focus:outline-none focus:border-blue-500 transition-all placeholder:text-gray-600"
                                            />
                                        </div>
                                    </div>
                                    <div>
                                        <label className="block text-gray-400 text-sm font-bold mb-3 uppercase tracking-widest">E-mail Corporativo</label>
                                        <div className="relative">
                                            <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                                            <input
                                                required
                                                type="email"
                                                placeholder="exemplo@loja.com"
                                                value={leadEmail}
                                                onChange={(e) => setLeadEmail(e.target.value)}
                                                className="w-full bg-white/10 border border-white/10 rounded-2xl py-5 pl-12 pr-6 text-white font-medium focus:outline-none focus:border-blue-500 transition-all placeholder:text-gray-600"
                                            />
                                        </div>
                                    </div>
                                    <div>
                                        <label className="block text-gray-400 text-sm font-bold mb-3 uppercase tracking-widest">WhatsApp / Celular</label>
                                        <div className="relative">
                                            <Phone className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                                            <input
                                                required
                                                type="tel"
                                                placeholder="(11) 99999-9999"
                                                value={leadWhatsApp}
                                                onChange={(e) => setLeadWhatsApp(e.target.value)}
                                                className="w-full bg-white/10 border border-white/10 rounded-2xl py-5 pl-12 pr-6 text-white font-medium focus:outline-none focus:border-blue-500 transition-all placeholder:text-gray-600"
                                            />
                                        </div>
                                    </div>
                                    <button
                                        type="submit"
                                        disabled={loadingLead}
                                        className="w-full py-6 bg-blue-600 text-white rounded-2xl font-black text-xl hover:bg-blue-700 transition-all shadow-2xl shadow-blue-900/40 flex items-center justify-center"
                                    >
                                        {loadingLead ? <div className="w-8 h-8 border-4 border-white border-t-transparent rounded-full animate-spin"></div> : 'RECEBER CONSULTORIA GRÁTIS'}
                                    </button>
                                    <p className="text-center text-gray-500 text-sm font-medium italic">
                                        Fique tranquilo, não enviamos spam. Seu contato está seguro.
                                    </p>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="py-20 bg-slate-50 border-t border-gray-200">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex flex-col md:flex-row justify-between items-center gap-10">
                        <div className="flex items-center gap-3">
                            <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center p-1 shadow-sm border border-gray-100 overflow-hidden">
                                <img src="/assets/logo.png" alt="Logo Footer" className="w-8 h-8 object-contain" />
                            </div>
                            <span className="text-2xl font-black text-gray-900 tracking-tighter">
                                Mercadinho<span className="text-blue-600">Sys</span>
                            </span>
                        </div>
                        <div className="flex flex-wrap justify-center gap-10 text-sm font-bold text-gray-500 uppercase tracking-widest">
                            <a href="#features" className="hover:text-blue-600">Recursos</a>
                            <a href="#pricing" className="hover:text-blue-600">Planos</a>
                            <a href="/login" className="hover:text-blue-600">Painel do Cliente</a>
                            <a href="#contact" className="hover:text-blue-600">Falar com Consultor</a>
                        </div>
                        <p className="text-gray-400 font-bold text-xs">
                            &copy; {new Date().getFullYear()} MERCADINHOSYS ERP. TODOS OS DIREITOS RESERVADOS.
                        </p>
                    </div>
                </div>
            </footer>
        </div>
    );
};

export default LandingPage;
