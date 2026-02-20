import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    ShoppingCart,
    Zap,
    ShieldCheck,
    Globe,
    MessageCircle,
    Star,
    Cpu,
    Lock,
    Mail,
    Phone,
    User,
    PlayCircle,
    Activity,
    BrainCircuit,
    ArrowRight,
    FileText,
    TrendingUp,
    Check,
    ZapOff,
    HelpCircle,
    ArrowUpRight,
    CheckCircle
} from 'lucide-react';
import { motion } from 'framer-motion';
import { toast } from 'react-hot-toast';
import { API_CONFIG } from '../../api/apiConfig';

const LandingPage: React.FC = () => {
    const navigate = useNavigate();
    const [leadName, setLeadName] = useState('');
    const [leadEmail, setLeadEmail] = useState('');
    const [leadWhatsApp, setLeadWhatsApp] = useState('');
    const [loadingLead, setLoadingLead] = useState(false);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const [conversionModalOpen, setConversionModalOpen] = useState(false);
    const [selectedPlan, setSelectedPlan] = useState<{ name: string, price: string } | null>(null);
    const [onboardingEmail, setOnboardingEmail] = useState('');
    const [onboardingWhatsApp, setOnboardingWhatsApp] = useState('');
    const [onboardingStoreName, setOnboardingStoreName] = useState('');
    const [loadingCheckout, setLoadingCheckout] = useState(false);

    const handleLeadSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoadingLead(true);

        try {
            const response = await fetch(`${API_CONFIG.BASE_URL}/saas/leads/registrar`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    nome: leadName,
                    email: leadEmail,
                    whatsapp: leadWhatsApp,
                    origem: 'landing_page'
                }),
            });

            const result = await response.json();

            if (response.ok && result.success) {
                toast.success('Informações enviadas! Entraremos em contato em breve.');
                setLeadName('');
                setLeadEmail('');
                setLeadWhatsApp('');

                // Pequeno delay antes de abrir o zap para o usuário ler o toast
                setTimeout(() => {
                    window.open(`https://wa.me/5511919889233?text=Olá! Acabei de me cadastrar no site e gostaria de saber mais sobre o MercadinhoSys. Meu e-mail é ${leadEmail}.`, '_blank');
                }, 1000);
            } else {
                toast.error(result.error || 'Ocorreu um erro ao enviar seus dados.');
            }
        } catch (error) {
            console.error('Erro ao enviar lead:', error);
            toast.error('Erro de conexão com o servidor.');
        } finally {
            setLoadingLead(false);
        }
    };

    const handlePlanSelect = (tier: any) => {
        setSelectedPlan({ name: tier.name, price: tier.price });
        setConversionModalOpen(true);
    };

    const handleCheckout = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoadingCheckout(true);

        try {
            const response = await fetch(`${API_CONFIG.BASE_URL}/stripe/public-checkout`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: onboardingEmail,
                    whatsapp: onboardingWhatsApp,
                    nome_loja: onboardingStoreName,
                    plan_name: selectedPlan?.name
                }),
            });

            const result = await response.json();

            if (response.ok && result.checkout_url) {
                toast.success('Conta criada! Redirecionando para o pagamento...');
                window.location.href = result.checkout_url;
            } else {
                toast.error(result.message || 'Erro ao iniciar checkout.');
            }
        } catch (error) {
            console.error('Erro no checkout:', error);
            toast.error('Erro de conexão.');
        } finally {
            setLoadingCheckout(false);
        }
    };

    const handleDemoAccess = async () => {
        try {
            toast.loading('Preparando ambiente de demonstração de elite...', {
                style: {
                    borderRadius: '16px',
                    background: '#1e293b',
                    color: '#fff',
                    fontWeight: 'bold'
                }
            });
            const response = await fetch(`${API_CONFIG.BASE_URL}/auth/demo`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const result = await response.json();

            if (response.ok && result.success && result.data) {
                const { access_token, refresh_token, user, estabelecimento } = result.data;
                localStorage.setItem('access_token', access_token);
                if (refresh_token) localStorage.setItem('refresh_token', refresh_token);
                localStorage.setItem('user_data', JSON.stringify(user));
                localStorage.setItem('estabelecimento_data', JSON.stringify(estabelecimento));
                window.dispatchEvent(new Event('auth-change'));

                toast.dismiss();
                toast.success('Entrando como Convidado Específicio...', { icon: '✨' });

                // Redirecionar para o dashboard após breve delay
                setTimeout(() => {
                    navigate('/dashboard');
                }, 1000);
            } else {
                toast.dismiss();
                toast.error(result.error || 'Erro ao acessar demonstração');
            }
        } catch (error) {
            toast.dismiss();
            console.error('Erro no demo access:', error);
            toast.error('Erro de conexão com o servidor demo.');
        }
    };

    const tiers = [
        {
            name: 'Basic',
            price: 'R$ 49,90',
            period: '/mês',
            description: 'Para quem quer sair do caderno e profissionalizar a gestão.',
            features: [
                'Até 500 produtos ativos',
                'PDV Híbrido (Online/Offline)',
                'Gestão de Estoque Essencial',
                'Relatórios Mensais de Vendas',
                'Suporte Garantido'
            ],
            cta: 'Dominar meu Bairro',
            highlight: false
        },
        {
            name: 'Advanced',
            price: 'R$ 69,90',
            period: '/mês',
            description: 'A potência científica para quem quer dobrar o lucro.',
            features: [
                'Produtos Ilimitados',
                'Dashboard Científico Completo',
                'Análise de Correlação (Vendas vs Horário)',
                'Segmentation RFM de Clientes',
                'Previsão de Demanda para 30 dias (Forecast)',
                'Curva ABC Dinâmica de Estoque'
            ],
            cta: 'Ativar Modo Ciência',
            highlight: true
        },
        {
            name: 'Premium',
            price: 'R$ 99,90',
            period: '/mês',
            description: 'Controle total de redes e grandes volumes de dados.',
            features: [
                'Multi-estabelecimentos (Redes)',
                'Auditoria de Perdas & Furtos',
                'Relatórios de ROI por Categoria',
                'Detecção de Anomalias Financeiras',
                'Plano de Resgate Financeiro Personalizado',
                'Gestão de RH & Holerite Integrado'
            ],
            cta: 'Escalar meu Império',
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
            comment: "O plano Basic cabe no bolso e me deu profissionalismo. Meus clientes adoram receber o cupom fiscal direto no Email.",
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
                className="fixed bottom-8 right-8 z-[100] bg-emerald-500 text-white p-4 rounded-full shadow-2xl shadow-emerald-400/50 hover:scale-110 active:scale-95 transition-all flex items-center justify-center group"
            >
                <MessageCircle className="w-8 h-8" />
                <span className="max-w-0 overflow-hidden group-hover:max-w-xs group-hover:ml-2 transition-all duration-500 font-bold whitespace-nowrap">
                    Dúvidas? Fale Conosco
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
                        <div className="lg:hidden flex items-center gap-4">
                            <button
                                onClick={() => navigate('/login')}
                                className="bg-blue-600 text-white px-4 py-2 rounded-lg font-bold text-xs"
                            >
                                LOGIN
                            </button>
                            <button
                                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                                className="p-2 text-gray-600"
                            >
                                <div className="w-6 h-5 flex flex-col justify-between">
                                    <span className={`h-0.5 w-full bg-current transform transition-all duration-300 ${mobileMenuOpen ? 'rotate-45 translate-y-2' : ''}`}></span>
                                    <span className={`h-0.5 w-full bg-current transition-all duration-300 ${mobileMenuOpen ? 'opacity-0' : ''}`}></span>
                                    <span className={`h-0.5 w-full bg-current transform transition-all duration-300 ${mobileMenuOpen ? '-rotate-45 -translate-y-2' : ''}`}></span>
                                </div>
                            </button>
                        </div>
                    </div>
                </div>

                {/* Mobile Menu Content */}
                <div className={`lg:hidden overflow-hidden transition-all duration-300 bg-white border-b border-gray-100 ${mobileMenuOpen ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'}`}>
                    <div className="px-4 py-6 space-y-4">
                        <a href="#features" onClick={() => setMobileMenuOpen(false)} className="block text-lg font-bold text-gray-600">Recursos</a>
                        <a href="#testimonials" onClick={() => setMobileMenuOpen(false)} className="block text-lg font-bold text-gray-600">Depoimentos</a>
                        <a href="#pricing" onClick={() => setMobileMenuOpen(false)} className="block text-lg font-bold text-gray-600">Planos</a>
                        <a href="#contact" onClick={() => setMobileMenuOpen(false)} className="block text-lg font-bold text-gray-600">Contato</a>
                    </div>
                </div>
            </nav>

            {/* HERO SECTION - ELITE REDESIGN */}
            <section className="relative pt-32 pb-20 lg:pt-52 lg:pb-40 overflow-hidden bg-white">
                {/* Dynamic Background Elements */}
                <div className="absolute top-0 right-0 -z-10 w-[1000px] h-[1000px] bg-blue-50/50 rounded-full blur-[120px] translate-x-1/3 -translate-y-1/3 animate-pulse"></div>
                <div className="absolute bottom-0 left-0 -z-10 w-[600px] h-[600px] bg-indigo-50/40 rounded-full blur-[100px] -translate-x-1/4 translate-y-1/4"></div>

                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="grid lg:grid-cols-2 gap-16 items-center">
                        <motion.div
                            initial={{ opacity: 0, x: -50 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ duration: 0.8, ease: "easeOut" }}
                            className="text-left"
                        >
                            <div className="inline-flex items-center gap-3 px-5 py-2.5 rounded-full bg-blue-600/5 text-blue-700 font-bold text-xs mb-10 tracking-[0.15em] uppercase border border-blue-600/10 shadow-sm backdrop-blur-sm">
                                <Zap className="w-4 h-4 fill-blue-600" />
                                TECNOLOGIA CIENTÍFICA PARA O VAREJO
                            </div>
                            <h1 className="text-5xl sm:text-6xl lg:text-8xl font-black text-gray-900 tracking-tight leading-[1.05] lg:leading-[0.95] mb-10">
                                A Ciência de <br className="hidden sm:block" />
                                <span className="bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-700 bg-clip-text text-transparent">Lucrar Mais.</span>
                            </h1>
                            <p className="text-xl lg:text-2xl text-gray-600 leading-relaxed mb-12 font-medium max-w-xl">
                                O ERP que pensa por você. Automatize a emissão de <span className="text-gray-900 font-black underline decoration-blue-500/30 underline-offset-4">Nota Fiscal via E-mail</span>, domine seu estoque com IA e venda mais rápido do que nunca.
                            </p>

                            <div className="flex flex-col sm:flex-row items-center gap-6">
                                <motion.button
                                    whileHover={{ scale: 1.05, boxShadow: "0 25px 50px -12px rgba(37, 99, 235, 0.4)" }}
                                    whileTap={{ scale: 0.98 }}
                                    onClick={() => document.getElementById('pricing')?.scrollIntoView({ behavior: 'smooth' })}
                                    className="w-full sm:w-auto px-10 py-6 bg-blue-600 text-white rounded-[2rem] font-black text-xl hover:bg-blue-700 transition-all flex items-center justify-center gap-3 relative group overflow-hidden"
                                >
                                    <span className="relative z-10 uppercase tracking-tighter">Garantir meu Lucro</span>
                                    <ArrowRight className="w-6 h-6 group-hover:translate-x-1 transition-transform relative z-10" />
                                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:animate-[shimmer_1.5s_infinite]"></div>
                                </motion.button>

                                <motion.button
                                    whileHover={{ scale: 1.05, borderColor: "#2563eb" }}
                                    whileTap={{ scale: 0.98 }}
                                    onClick={handleDemoAccess}
                                    className="w-full sm:w-auto px-10 py-6 bg-white text-gray-900 border-2 border-gray-100 rounded-[2rem] font-black text-xl hover:bg-slate-50 transition-all text-center flex items-center justify-center gap-3 shadow-xl shadow-gray-200/50"
                                >
                                    ACESSAR DEMO
                                    <PlayCircle className="w-6 h-6 text-blue-600" />
                                </motion.button>
                            </div>

                            <div className="mt-14 flex flex-wrap items-center gap-10 text-sm font-bold text-gray-400">
                                <div className="flex items-center gap-2 px-4 py-2 bg-slate-50 rounded-xl border border-gray-100">
                                    <ShieldCheck className="w-5 h-5 text-emerald-500" />
                                    <span>Segurança Nível Bancário</span>
                                </div>
                                <div className="flex items-center gap-2 px-4 py-2 bg-slate-50 rounded-xl border border-gray-100">
                                    <Lock className="w-5 h-5 text-blue-500" />
                                    <span>Backups a cada 1 hora</span>
                                </div>
                            </div>
                        </motion.div>

                        <motion.div
                            initial={{ opacity: 0, scale: 0.9, y: 50 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            transition={{ duration: 1, delay: 0.2 }}
                            className="relative lg:block"
                        >
                            <div className="absolute -inset-10 bg-gradient-to-tr from-blue-600/10 to-indigo-600/10 rounded-[4rem] blur-3xl"></div>
                            <div className="relative bg-white border border-gray-100/50 rounded-[4rem] shadow-[0_50px_100px_-20px_rgba(0,0,0,0.15)] p-5 overflow-hidden group backdrop-blur-sm">
                                <div className="absolute inset-0 bg-gradient-to-b from-transparent via-white/5 to-white/20 pointer-events-none"></div>
                                <video
                                    autoPlay
                                    muted
                                    loop
                                    playsInline
                                    className="w-full rounded-[3.5rem] shadow-2xl transition-transform duration-1000"
                                >
                                    <source src="/screenshots/videosys.mp4" type="video/mp4" />
                                    Seu navegador não suporta vídeos.
                                </video>

                                {/* Floating Overlay Detail */}
                                <motion.div
                                    animate={{ y: [0, -10, 0] }}
                                    transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                                    className="absolute -bottom-8 -right-8 bg-white p-6 rounded-3xl shadow-2xl border border-gray-100 max-w-[200px] hidden sm:block"
                                >
                                    <div className="flex items-center gap-3 mb-2">
                                        <div className="w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center">
                                            <FileText className="w-5 h-5 text-emerald-600" />
                                        </div>
                                        <div className="flex-1">
                                            <div className="h-2 w-full bg-gray-100 rounded-full mb-1"></div>
                                            <div className="h-2 w-2/3 bg-gray-50 rounded-full"></div>
                                        </div>
                                    </div>
                                    <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Nota Fiscal Enviada!</p>
                                </motion.div>
                            </div>
                        </motion.div>
                    </div>
                </div>
            </section>

            {/* SILENT AUTOMATION SECTION (THE "WOW" FACTOR) */}
            <section className="py-24 lg:py-32 bg-gray-900 border-y border-white/5 relative overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(circle_at_30%_20%,rgba(37,99,235,0.1),transparent)] pointer-events-none"></div>

                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="grid lg:grid-cols-2 gap-20 items-center">
                        <motion.div
                            initial={{ opacity: 0, x: -30 }}
                            whileInView={{ opacity: 1, x: 0 }}
                            viewport={{ once: true }}
                            className="relative"
                        >
                            <div className="absolute -inset-4 bg-blue-600/20 blur-3xl rounded-full"></div>
                            <div className="relative bg-white/5 backdrop-blur-xl border border-white/10 rounded-[3rem] p-10 overflow-hidden shadow-2xl">
                                <div className="flex items-center justify-between mb-8 pb-8 border-b border-white/10">
                                    <div className="flex items-center gap-4">
                                        <div className="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center">
                                            <ShoppingCart className="w-6 h-6 text-white" />
                                        </div>
                                        <div>
                                            <p className="text-white font-black">Venda Finalizada</p>
                                            <p className="text-gray-400 text-xs">Mercadinho Central #1204</p>
                                        </div>
                                    </div>
                                    <div className="px-3 py-1 bg-emerald-500/20 text-emerald-400 rounded-full text-[10px] font-black uppercase tracking-widest">Sucesso</div>
                                </div>

                                <div className="space-y-6">
                                    <motion.div
                                        initial={{ width: 0 }}
                                        whileInView={{ width: "100%" }}
                                        transition={{ duration: 1, delay: 0.5 }}
                                        className="h-1 bg-blue-600 rounded-full"
                                    ></motion.div>

                                    <div className="flex items-start gap-6">
                                        <motion.div
                                            animate={{ scale: [1, 1.1, 1], rotate: [0, 5, 0] }}
                                            transition={{ duration: 3, repeat: Infinity }}
                                            className="w-16 h-16 bg-white/10 rounded-2xl flex items-center justify-center shrink-0 border border-white/5"
                                        >
                                            <Mail className="w-8 h-8 text-blue-400" />
                                        </motion.div>
                                        <div>
                                            <h4 className="text-xl font-black text-white mb-2">NF-e Enviada Automaticamente</h4>
                                            <p className="text-gray-400 leading-relaxed font-medium">
                                                Enquanto você entrega o troco, o sistema já disparou o cupom fiscal PDF e XML para o e-mail do cliente.
                                                <span className="text-blue-400 font-bold block mt-2">Zero cliques. Zero papel. 100% Profissional.</span>
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </motion.div>

                        <div className="text-left">
                            <h2 className="text-blue-400 font-black tracking-widest text-sm uppercase mb-6">Automatização Silenciosa</h2>
                            <h3 className="text-4xl lg:text-6xl font-black text-white leading-tight mb-8">
                                Elimine a burocracia, <br />
                                <span className="text-gray-500">encante o cliente.</span>
                            </h3>
                            <div className="space-y-8">
                                {[
                                    { title: "Emissão em Milissegundos", desc: "Integração direta com SEFAZ através de nossa infraestrutura de alta disponibilidade." },
                                    { title: "Eco-Friendly & Redução de Custo", desc: "Economize milhares de reais por ano com bobinas térmicas e manutenção de impressoras." },
                                    { title: "Fidelização Automática", desc: "Ao receber a nota no e-mail, o cliente entra no seu ecossistema digital para futuras ofertas." }
                                ].map((item, i) => (
                                    <div key={i} className="flex gap-6 group">
                                        <div className="w-8 h-8 rounded-full border border-blue-600/50 flex items-center justify-center shrink-0 group-hover:bg-blue-600 transition-colors">
                                            <Check className="w-4 h-4 text-blue-400 group-hover:text-white" />
                                        </div>
                                        <div>
                                            <h4 className="text-lg font-black text-white mb-1">{item.title}</h4>
                                            <p className="text-gray-400 font-medium">{item.desc}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </section>


            {/* ELITE COMPARISON (BATTLE OF SYSTEMS) */}
            <section className="py-24 lg:py-32 bg-white relative">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-24">
                        <div className="inline-block px-4 py-1.5 bg-blue-600/10 text-blue-600 rounded-full text-xs font-black tracking-widest uppercase mb-6">Diferenciação Tecnológica</div>
                        <h3 className="text-4xl lg:text-6xl font-black text-gray-900 leading-tight">
                            MercadinhoSys vs <br />
                            <span className="text-gray-400 italic">Sistemas Legados.</span>
                        </h3>
                    </div>

                    <div className="grid lg:grid-cols-2 gap-10">
                        {/* LEGACY COLUMN */}
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            whileInView={{ opacity: 1, scale: 1 }}
                            viewport={{ once: true }}
                            className="p-12 rounded-[4rem] bg-slate-50 border border-gray-100 relative group"
                        >
                            <div className="flex items-center gap-4 mb-12">
                                <div className="w-14 h-14 bg-gray-200 rounded-2xl flex items-center justify-center shrink-0">
                                    <ZapOff className="w-7 h-7 text-gray-400" />
                                </div>
                                <h4 className="text-2xl font-black text-gray-400">Software Legado</h4>
                            </div>

                            <div className="space-y-8">
                                {[
                                    "Lento, pesado e trava toda hora",
                                    "Relatórios em PDF que ninguém lê",
                                    "Gestão baseada em 'achismo'",
                                    "Cálculos manuais em planilhas Excel",
                                    "Vendas estagnadas por falta de dados"
                                ].map((item, i) => (
                                    <div key={i} className="flex items-center gap-4 opacity-50">
                                        <div className="w-1.5 h-1.5 bg-gray-300 rounded-full"></div>
                                        <span className="text-gray-500 font-bold">{item}</span>
                                    </div>
                                ))}
                            </div>
                        </motion.div>

                        {/* MERCADINHOSYS COLUMN (ELITE) */}
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            whileInView={{ opacity: 1, scale: 1 }}
                            viewport={{ once: true }}
                            transition={{ delay: 0.1 }}
                            className="p-12 rounded-[4rem] bg-blue-600 text-white relative group shadow-2xl shadow-blue-400/30 overflow-hidden"
                        >
                            <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>

                            <div className="flex items-center gap-4 mb-12 relative z-10">
                                <div className="w-14 h-14 bg-white rounded-2xl flex items-center justify-center shrink-0 shadow-lg">
                                    <Zap className="w-7 h-7 text-blue-600 fill-blue-600" />
                                </div>
                                <h4 className="text-2xl font-black">MercadinhoSys</h4>
                            </div>

                            <div className="space-y-8 relative z-10">
                                {[
                                    "PDV Híbrido: Venda em <100ms",
                                    "Correlação de Pearson em Tempo Real",
                                    "ROI Automatizado e Previsão de Ruptura",
                                    "Curva ABC Nativa: Capital Identificado",
                                    "RFM: Recuperação de Clientes em 1 Clique"
                                ].map((item, i) => (
                                    <div key={i} className="flex items-center gap-4 group/item">
                                        <motion.div
                                            whileInView={{ scale: [1, 1.3, 1] }}
                                            className="w-5 h-5 bg-white rounded-full flex items-center justify-center shrink-0"
                                        >
                                            <Check className="w-3 h-3 text-blue-600" />
                                        </motion.div>
                                        <span className="font-black text-lg group-hover/item:translate-x-1 transition-transform">{item}</span>
                                    </div>
                                ))}
                            </div>
                        </motion.div>
                    </div>
                </div>
            </section>


            {/* O SISTEMA EM AÇÃO - GALERIA REAL */}
            <section className="py-16 lg:py-24 bg-white overflow-hidden">
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

            {/* CÉREBRO CIENTÍFICO Section */}
            <section id="features" className="py-20 lg:py-40 bg-slate-50 relative overflow-hidden">
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1200px] h-[1200px] bg-blue-100/20 rounded-full blur-[150px] -z-10"></div>

                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center max-w-3xl mx-auto mb-24">
                        <div className="inline-block px-4 py-1.5 bg-blue-600/10 text-blue-600 rounded-full text-xs font-black tracking-widest uppercase mb-6">Inteligência de Vanguarda</div>
                        <h3 className="text-4xl lg:text-7xl font-black text-gray-900 leading-tight mb-8">
                            A tecnologia do <br />
                            <span className="text-blue-600 italic">Itaú & Ambev</span> <br />
                            <span className="text-gray-400">no seu PDV.</span>
                        </h3>
                        <p className="text-xl text-gray-500 font-medium">Não é apenas um cadastro de produtos. É um motor estatístico que busca lucro em cada milissegundo de operação.</p>
                    </div>

                    <div className="grid lg:grid-cols-3 gap-10">
                        {[
                            {
                                icon: <TrendingUp className="w-10 h-10 text-white" />,
                                color: "bg-gradient-to-br from-blue-600 to-indigo-700",
                                title: "CÉREBRO CIENTÍFICO",
                                description: "Analisamos a **Correlação de Pearson** entre Horários e Vendas. O sistema sugere reposições e promoções baseadas no comportamento real do seu público.",
                                badge: "IA Nativa"
                            },
                            {
                                icon: <BrainCircuit className="w-10 h-10 text-white" />,
                                color: "bg-gradient-to-br from-emerald-500 to-teal-700",
                                title: "FORECAST DE DEMANDA",
                                description: "Previsões precisas para os próximos 30 dias. Identifique rupturas de estoque antes que elas aconteçam e otimize seu fluxo de caixa.",
                                badge: "Estatística"
                            },
                            {
                                icon: <Zap className="w-10 h-10 text-white" />,
                                color: "bg-gradient-to-br from-amber-500 to-orange-600",
                                title: "PDV SUPERSONIC",
                                description: "Processamento de cupom em menos de 100ms. Tecnologia híbrida que garante vendas mesmo sem internet, com sincronia atômica posterior.",
                                badge: "Hybrid Cloud"
                            },
                            {
                                icon: <Activity className="w-10 h-10 text-white" />,
                                color: "bg-gradient-to-br from-indigo-500 to-blue-700",
                                title: "SEGMENTAÇÃO RFM",
                                description: "Recupere clientes inativos e fidelize seus 'Campeões' com campanhas automáticas baseadas em Recência, Frequência e Valor.",
                                badge: "Data Science"
                            },
                            {
                                icon: <ShieldCheck className="w-10 h-10 text-white" />,
                                color: "bg-gradient-to-br from-rose-500 to-red-700",
                                title: "AUDITORIA ANTIFRAUDE",
                                description: "Detecção de anomalias em cancelamentos e descontos. Proteja seu lucro contra erros operacionais ou desvios em tempo real.",
                                badge: "Segurança"
                            },
                            {
                                icon: <Globe className="w-10 h-10 text-white" />,
                                color: "bg-gradient-to-br from-cyan-500 to-blue-600",
                                title: "GESTÃO DE REDES",
                                description: "Visão consolidada para quem quer crescer. Gerencie 1 ou 100 lojas com a mesma facilidade e relatórios comparativos automáticos.",
                                badge: "Enterprise"
                            }
                        ].map((feature, idx) => (
                            <motion.div
                                key={idx}
                                whileHover={{ y: -10 }}
                                className="bg-white p-12 rounded-[4rem] border border-gray-100 shadow-xl shadow-gray-200/50 hover:shadow-2xl hover:shadow-blue-200/30 transition-all group relative overflow-hidden"
                            >
                                <div className="absolute top-8 right-8 text-[10px] font-black text-blue-600 bg-blue-50 px-3 py-1 rounded-full uppercase tracking-widest">{feature.badge}</div>
                                <div className={`mb-10 w-20 h-20 ${feature.color} rounded-[2rem] flex items-center justify-center shadow-lg group-hover:rotate-6 transition-transform`}>
                                    {feature.icon}
                                </div>
                                <h4 className="text-2xl font-black text-gray-900 mb-6">{feature.title}</h4>
                                <p className="text-gray-500 leading-relaxed text-lg font-medium">
                                    {feature.description.split('**').map((text, i) => i % 2 === 1 ? <span key={i} className="text-gray-900 font-black">{text}</span> : text)}
                                </p>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* SOCIAL PROOF / DEPOIMENTOS */}
            <section id="testimonials" className="py-20 lg:py-32 bg-white">
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

            {/* TECHNICAL ARCHITECTURE Section - ELITE POLISH */}
            <section className="py-24 lg:py-40 bg-gray-900 border-t border-white/5 relative overflow-hidden">
                <div className="absolute bottom-0 right-0 w-[800px] h-[800px] bg-blue-600/10 rounded-full blur-[120px] translate-x-1/2 translate-y-1/2"></div>

                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
                    <div className="grid lg:grid-cols-2 gap-24 items-center">
                        <motion.div
                            initial={{ opacity: 0, x: -30 }}
                            whileInView={{ opacity: 1, x: 0 }}
                            viewport={{ once: true }}
                        >
                            <div className="inline-block px-4 py-1.5 bg-blue-500/10 text-blue-400 rounded-full text-xs font-black tracking-widest uppercase mb-6 border border-blue-500/20">Infraestrutura Crítica</div>
                            <h3 className="text-4xl lg:text-7xl font-black text-white mb-12 leading-tight">Engenharia de <br /><span className="text-blue-500 italic">Alta Disponibilidade.</span></h3>

                            <div className="space-y-10">
                                {[
                                    { icon: <Cpu className="w-7 h-7 text-blue-400" />, title: "Backend Reativo Fast API", desc: "Lógica processada em servidores de ultra-baixa latência para respostas sub-milissegundos." },
                                    { icon: <Lock className="w-7 h-7 text-emerald-400" />, title: "Segurança de Dados Tier-4", desc: "Seus dados são criptografados com padrões bancários (AES-256) e isolados por estabelecimento." },
                                    { icon: <Globe className="w-7 h-7 text-indigo-400" />, title: "Escalabilidade Atômica", desc: "Hospedagem em AWS Lambda/Edge, garantindo que o sistema nunca fique fora do ar, não importa o volume." }
                                ].map((item, i) => (
                                    <div key={i} className="flex gap-8 group">
                                        <div className="w-16 h-16 rounded-[1.5rem] bg-white/5 border border-white/10 flex items-center justify-center shrink-0 group-hover:bg-blue-600/20 transition-all shadow-xl">
                                            {item.icon}
                                        </div>
                                        <div>
                                            <h4 className="text-xl font-black text-white mb-2">{item.title}</h4>
                                            <p className="text-gray-400 font-medium leading-relaxed">{item.desc}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </motion.div>

                        <div className="relative">
                            <motion.div
                                initial={{ opacity: 0, scale: 0.9 }}
                                whileInView={{ opacity: 1, scale: 1 }}
                                viewport={{ once: true }}
                                className="bg-gradient-to-tr from-blue-600 to-indigo-800 rounded-[4rem] p-12 lg:p-24 shadow-2xl relative overflow-hidden group border border-white/10"
                            >
                                <div className="absolute -top-10 -right-10 w-80 h-80 bg-white/10 rounded-full blur-3xl group-hover:scale-150 transition-transform duration-1000"></div>
                                <div className="relative z-10 text-center">
                                    <div className="w-24 h-24 bg-white/20 backdrop-blur-md rounded-full flex items-center justify-center mx-auto mb-10 border border-white/30">
                                        <ShieldCheck className="w-12 h-12 text-white" />
                                    </div>
                                    <h4 className="text-5xl font-black text-white mb-6 tracking-tighter">99.99% Uptime</h4>
                                    <p className="text-blue-100 font-bold mb-14 text-lg leading-relaxed">Garantia sob contrato (SLA). Nossa infraestrutura é auditada para suportar picos de 10.000 requisições/segundo.</p>
                                    <button
                                        onClick={() => navigate('/login')}
                                        className="w-full py-6 bg-white text-blue-900 rounded-[2rem] font-black text-xl hover:bg-blue-50 transition-all shadow-2xl active:scale-95"
                                    >
                                        VER STATUS EM TEMPO REAL
                                    </button>
                                </div>
                            </motion.div>
                        </div>
                    </div>
                </div>
            </section>

            {/* PRICING Section - ELITE REDESIGN */}
            <section id="pricing" className="py-24 lg:py-40 bg-white relative overflow-hidden">
                <div className="absolute top-1/2 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-gray-200 to-transparent"></div>

                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
                    <div className="text-center max-w-3xl mx-auto mb-24">
                        <div className="inline-block px-4 py-1.5 bg-blue-600/10 text-blue-600 rounded-full text-xs font-black tracking-widest uppercase mb-6">Investimento & ROI</div>
                        <h3 className="text-4xl lg:text-7xl font-black text-gray-900 mb-8">O motor do seu <br /><span className="text-blue-600 italic">Crescimento Executivo.</span></h3>
                        <p className="text-xl text-gray-500 font-medium leading-relaxed">Planos desenhados para escalar seu lucro através de ciência de dados e automação extrema.</p>
                    </div>

                    <div className="grid lg:grid-cols-3 gap-8 items-stretch">
                        {tiers.map((tier, idx) => (
                            <motion.div
                                key={idx}
                                initial={{ opacity: 0, y: 30 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: idx * 0.1 }}
                                className={`relative flex flex-col p-10 md:p-14 rounded-[4rem] border-2 transition-all duration-500 ${tier.highlight
                                    ? 'border-blue-600 bg-white shadow-[0_50px_100px_-20px_rgba(37,99,235,0.2)] scale-105 z-10'
                                    : 'border-gray-100 bg-white shadow-xl shadow-gray-200/50 hover:border-blue-200'
                                    }`}
                            >
                                {tier.highlight && (
                                    <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-blue-600 text-white px-8 py-2.5 rounded-full text-[10px] font-black tracking-[0.2em] uppercase shadow-lg">
                                        RECOMENDADO PARA VOCÊ
                                    </div>
                                )}
                                <div className="mb-12">
                                    <h4 className="text-2xl font-black text-gray-900 mb-3">{tier.name}</h4>
                                    <div className="flex items-baseline gap-2 mb-8">
                                        <span className="text-6xl font-black text-gray-900 tracking-tighter">{tier.price}</span>
                                        <span className="text-gray-400 font-bold text-lg">{tier.period}</span>
                                    </div>
                                    <p className="text-gray-500 font-bold leading-relaxed min-h-[60px]">{tier.description}</p>
                                </div>
                                <div className="space-y-6 mb-14 flex-1">
                                    {tier.features.map((feature, fIdx) => (
                                        <div key={fIdx} className="flex items-start gap-4 group/item">
                                            <div className="shrink-0 mt-1">
                                                <CheckCircle className={`w-5 h-5 ${tier.highlight ? 'text-blue-600' : 'text-emerald-500'}`} />
                                            </div>
                                            <span className="text-gray-700 font-black text-sm leading-snug group-hover/item:text-blue-600 transition-colors">{feature}</span>
                                        </div>
                                    ))}
                                </div>
                                <button
                                    onClick={() => handlePlanSelect(tier)}
                                    className={`w-full py-6 rounded-[2rem] font-black text-xl transition-all active:scale-95 group flex items-center justify-center gap-3 ${tier.highlight
                                        ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-2xl shadow-blue-200'
                                        : 'bg-gray-900 text-white hover:bg-black'
                                        }`}>
                                    {tier.cta}
                                    <ArrowUpRight className="w-5 h-5 group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
                                </button>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* FAQ / OBJEÇÕES Section - ELITE POLISH */}
            <section className="py-24 lg:py-40 bg-slate-50 relative overflow-hidden">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
                    <div className="flex flex-col lg:flex-row gap-20">
                        <div className="lg:w-1/3">
                            <div className="inline-block px-4 py-1.5 bg-blue-600/10 text-blue-600 rounded-full text-xs font-black tracking-widest uppercase mb-6">Expertise & Suporte</div>
                            <h3 className="text-4xl lg:text-6xl font-black text-gray-900 mb-8 leading-tight">Perguntas <br /><span className="text-blue-600 italic">Frequentes.</span></h3>
                            <p className="text-lg text-gray-500 font-bold leading-relaxed mb-10">Ainda tem dúvidas? Nossa equipe de engenheiros de vendas está pronta para lhe atender via WhatsApp.</p>
                            <button className="flex items-center gap-3 text-blue-600 font-black text-xl group whitespace-nowrap">
                                Falar com suporte humano
                                <ArrowRight className="w-6 h-6 group-hover:translate-x-2 transition-transform" />
                            </button>
                        </div>

                        <div className="lg:w-2/3 grid md:grid-cols-1 gap-6">
                            {[
                                {
                                    q: "Como funciona a emissão automática de NF-e?",
                                    a: "Após configurar seu certificado digital (A1), cada venda fechada no PDV é enviada para o SEFAZ. O retorno positivo dispara um e-mail com o PDF e XML para o cliente instantaneamente."
                                },
                                {
                                    q: "O que é exatamente o 'Cérebro Científico'?",
                                    a: "É nossa engine proprietária que utiliza cálculos de correlação estatística para identificar produtos que vendem juntos, horários de pico reais e sugestões de promoções para queima de estoque."
                                },
                                {
                                    q: "O sistema funciona offline em períodos de queda de internet?",
                                    a: "Sim. O PDV Supersonic trabalha localmente e sincroniza toda a base de dados em nuvem assim que detecta conectividade estável, garantindo que você nunca perca uma venda."
                                },
                                {
                                    q: "Qual a segurança dos meus dados financeiros?",
                                    a: "Utilizamos infraestrutura AWS (Amazon Web Services) com criptografia AES-256 e backups horários redundantes em 3 regiões diferentes."
                                }
                            ].map((faq, idx) => (
                                <motion.div
                                    key={idx}
                                    initial={{ opacity: 0, y: 10 }}
                                    whileInView={{ opacity: 1, y: 0 }}
                                    className="bg-white p-10 rounded-[3rem] border border-gray-100 shadow-lg shadow-gray-200/30 hover:shadow-xl transition-all group"
                                >
                                    <div className="flex items-start gap-6">
                                        <div className="w-12 h-12 rounded-2xl bg-blue-50 flex items-center justify-center shrink-0 group-hover:bg-blue-600 transition-colors">
                                            <HelpCircle className="w-6 h-6 text-blue-600 group-hover:text-white" />
                                        </div>
                                        <div>
                                            <h4 className="text-xl font-black text-gray-900 mb-4">{faq.q}</h4>
                                            <p className="text-gray-600 font-bold leading-relaxed">{faq.a}</p>
                                        </div>
                                    </div>
                                </motion.div>
                            ))}
                        </div>
                    </div>
                </div>
            </section>
            <section id="contact" className="py-20 lg:py-32 bg-white">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="bg-gray-900 rounded-[4rem] overflow-hidden shadow-2xl relative">
                        {/* DECOR */}
                        <div className="absolute -bottom-20 -left-20 w-80 h-80 bg-blue-600/20 rounded-full blur-[100px]"></div>

                        <div className="grid lg:grid-cols-2">
                            <div className="p-8 md:p-12 lg:p-24 border-b lg:border-b-0 lg:border-r border-white/10 relative z-10">
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
                            <div className="p-8 md:p-12 lg:p-24 bg-white/5 backdrop-blur-sm relative z-10">
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
            {/* CONVERSION MODAL */}
            {conversionModalOpen && (
                <div className="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-gray-900/80 backdrop-blur-md">
                    <div className="bg-white w-full max-w-lg rounded-[3rem] shadow-2xl overflow-hidden p-8 md:p-12 relative animate-in fade-in zoom-in duration-300">
                        <button
                            onClick={() => setConversionModalOpen(false)}
                            className="absolute top-8 right-8 text-gray-400 hover:text-gray-900"
                        >
                            <Lock className="w-6 h-6" />
                        </button>

                        <div className="text-center mb-10">
                            <div className="w-20 h-20 bg-blue-50 rounded-3xl flex items-center justify-center mx-auto mb-6">
                                <Zap className="w-10 h-10 text-blue-600" />
                            </div>
                            <h3 className="text-3xl font-black text-gray-900 mb-2">Quase lá!</h3>
                            <p className="text-gray-500 font-bold tracking-tight">
                                Você selecionou o plano <span className="text-blue-600 uppercase">{selectedPlan?.name}</span> ({selectedPlan?.price}/mês).
                            </p>
                        </div>

                        <form onSubmit={handleCheckout} className="space-y-6">
                            <div>
                                <label className="block text-gray-400 text-xs font-black uppercase tracking-[0.2em] mb-3">E-mail para Acesso</label>
                                <div className="relative">
                                    <Mail className="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                                    <input
                                        required
                                        type="email"
                                        placeholder="seu@email.com"
                                        value={onboardingEmail}
                                        onChange={(e) => setOnboardingEmail(e.target.value)}
                                        className="w-full bg-slate-50 border border-gray-100 rounded-2xl py-5 pl-14 pr-6 font-bold focus:outline-none focus:border-blue-600 transition-all"
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-gray-400 text-xs font-black uppercase tracking-[0.2em] mb-3">WhatsApp de Negócios</label>
                                <div className="relative">
                                    <Phone className="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                                    <input
                                        required
                                        type="tel"
                                        placeholder="(11) 99999-9999"
                                        value={onboardingWhatsApp}
                                        onChange={(e) => setOnboardingWhatsApp(e.target.value)}
                                        className="w-full bg-slate-50 border border-gray-100 rounded-2xl py-5 pl-14 pr-6 font-bold focus:outline-none focus:border-blue-600 transition-all"
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-gray-400 text-xs font-black uppercase tracking-[0.2em] mb-3">Nome da Loja</label>
                                <div className="relative">
                                    <ShoppingCart className="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                                    <input
                                        required
                                        type="text"
                                        placeholder="Ex: Mercadinho do Bairro"
                                        value={onboardingStoreName}
                                        onChange={(e) => setOnboardingStoreName(e.target.value)}
                                        className="w-full bg-slate-50 border border-gray-100 rounded-2xl py-5 pl-14 pr-6 font-bold focus:outline-none focus:border-blue-600 transition-all"
                                    />
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={loadingCheckout}
                                className="w-full py-6 bg-blue-600 text-white rounded-2xl font-black text-xl hover:bg-blue-700 transition-all shadow-xl shadow-blue-200 flex items-center justify-center gap-3 disabled:opacity-50"
                            >
                                {loadingCheckout ? 'PROCESSANDO...' : 'PROSSEGUIR PARA O PAGAMENTO'}
                                {!loadingCheckout && <Zap className="w-6 h-6 text-white" />}
                            </button>
                        </form>

                        <p className="text-center mt-8 text-xs text-gray-400 font-bold">
                            Ambiente de checkout seguro processado pela <strong>Stripe</strong>.
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
};

export default LandingPage;
