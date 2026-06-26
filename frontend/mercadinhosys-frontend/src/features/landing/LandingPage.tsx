import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../auth/authService';
import {
    ShoppingCart,
    Zap,
    ShieldCheck,
    Globe,
    MessageCircle,
    Star,
    Lock,
    Mail,
    Phone,
    User,
    PlayCircle,
    ArrowRight,
    TrendingUp,
    Check,
    CheckCircle,
    Truck,
    Receipt,
    FileUp,
    Award,
    X
} from 'lucide-react';
import { motion } from 'framer-motion';
import { showToast } from '../../utils/toast';
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

    useEffect(() => {
        const token = sessionStorage.getItem('access_token');
        if (token) {
            authService.logout();
        }
    }, []);

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
                showToast.info('Informações enviadas! Entraremos em contato em breve.');
                setLeadName('');
                setLeadEmail('');
                setLeadWhatsApp('');

                setTimeout(() => {
                    window.open(`https://wa.me/5511919889233?text=Olá! Acabei de me cadastrar no site e gostaria de saber mais sobre o MercadinhoSys. Meu e-mail é ${leadEmail}.`, '_blank');
                }, 1000);
            } else {
                showToast.error(result.error || 'Ocorreu um erro ao enviar seus dados.');
            }
        } catch (error) {
            console.error('Erro ao enviar lead:', error);
            showToast.error('Erro de conexão com o servidor.');
        } finally {
            setLoadingLead(false);
        }
    };

    const handlePlanSelect = (tier: { name: string, price: string }) => {
        setSelectedPlan({ name: tier.name, price: tier.price });
        setConversionModalOpen(true);
    };

    const handleCheckout = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoadingCheckout(true);

        try {
            const response = await fetch(`${API_CONFIG.BASE_URL}/billing/public-checkout`, {
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
                showToast.create('Conta criada! Redirecionando para o pagamento...');
                window.location.href = result.checkout_url;
            } else {
                showToast.error(result.message || 'Erro ao iniciar checkout.');
            }
        } catch (error) {
            console.error('Erro no checkout:', error);
            showToast.error('Erro de conexão.');
        } finally {
            setLoadingCheckout(false);
        }
    };

    const handleDemoAccess = async () => {
        try {
            showToast.loading('Preparando ambiente de demonstração...');
            const response = await fetch(`${API_CONFIG.BASE_URL}/auth/demo`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const result = await response.json();

            if (response.ok && result.success) {
                const data = result.data || {};
                const access_token = data.access_token || result.access_token;
                const refresh_token = data.refresh_token || result.refresh_token;
                const user = data.user;
                const estabelecimento = data.estabelecimento;

                if (access_token) sessionStorage.setItem('access_token', access_token);
                if (refresh_token) sessionStorage.setItem('refresh_token', refresh_token);
                if (user) sessionStorage.setItem('user_data', JSON.stringify(user));
                if (estabelecimento) localStorage.setItem('estabelecimento_data', JSON.stringify(estabelecimento));
                
                window.dispatchEvent(new Event('auth-change'));

                showToast.dismiss();
                showToast.info('Entrando no ambiente de demonstração...', { icon: '✨' });

                setTimeout(() => {
                    navigate('/dashboard');
                }, 1000);
            } else {
                showToast.dismiss();
                showToast.error(result.error || 'Erro ao acessar demonstração');
            }
        } catch (error) {
            showToast.dismiss();
            console.error('Erro no demo access:', error);
            showToast.error('Erro de conexão com o servidor demo.');
        }
    };

    const tiers = [
        {
            name: 'Basic',
            price: 'Grátis',
            period: 'Por tempo limitado',
            description: 'O essencial para quem quer profissionalizar a gestão da loja.',
            features: [
                '1 Terminal PDV Offline-First',
                'Gestão de Estoque Simplificada',
                'Importação de XML de Fornecedor',
                'Módulo de Delivery',
                'Suporte Comercial'
            ],
            cta: 'Ativar Plano Grátis',
            highlight: false
        },
        {
            name: 'Premium',
            price: 'R$ 99,90',
            period: '/mês (Tempo Limitado)',
            description: 'Automação fiscal e inteligência de dados para maximizar lucros.',
            features: [
                'Terminais PDV Ilimitados',
                'Emissão de NFe e NFCe nativas (SEFAZ)',
                'Importação de XML de Notas',
                'Módulo de Delivery Completo',
                'Dashboard com IA e Curva ABC',
                'Previsão de Demanda (Forecast)',
                'Sincronização em Nuvem em Tempo Real',
                'Suporte Humanizado (SLA de 1h)'
            ],
            cta: 'Assinar Plano Premium',
            highlight: true
        }
    ];

    const testimonials = [
        {
            name: "João Pereira",
            role: "Dono do Mercadinho São José",
            comment: "O sistema não trava. Mesmo quando a internet cai, o PDV continua vendendo e, quando volta, sincroniza tudo. A emissão de NFCe é quase instantânea.",
            stars: 5,
            image: "https://images.unsplash.com/photo-1560250097-0b93528c311a?auto=format&fit=crop&q=80&w=150"
        },
        {
            name: "Maria Silva",
            role: "Gerente Operacional",
            comment: "Importar as notas dos fornecedores pelo XML salvou horas do meu dia. O estoque atualiza sozinho e eu consigo focar no que importa: atender o cliente.",
            stars: 5,
            image: "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&q=80&w=150"
        },
        {
            name: "Ricardo Mendes",
            role: "Empresário Varejista",
            comment: "O módulo de Delivery organizou nossas entregas por motoboy. As taxas são calculadas direto na venda e o fluxo de caixa bate certinho no fim do dia.",
            stars: 5,
            image: "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?auto=format&fit=crop&q=80&w=150"
        }
    ];

    return (
        <div className="h-screen overflow-y-auto bg-slate-50 text-gray-900 font-sans selection:bg-blue-200 selection:text-blue-900 overflow-x-hidden custom-scrollbar">
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
                            <a href="#fiscal" className="text-sm font-bold text-gray-500 hover:text-blue-600 transition-colors uppercase tracking-widest">Fiscal NFe</a>
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

                <div className={`lg:hidden overflow-hidden transition-all duration-300 bg-white border-b border-gray-100 ${mobileMenuOpen ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'}`}>
                    <div className="px-4 py-6 space-y-4">
                        <a href="#features" onClick={() => setMobileMenuOpen(false)} className="block text-lg font-bold text-gray-600">Recursos</a>
                        <a href="#fiscal" onClick={() => setMobileMenuOpen(false)} className="block text-lg font-bold text-gray-600">Fiscal NFe</a>
                        <a href="#testimonials" onClick={() => setMobileMenuOpen(false)} className="block text-lg font-bold text-gray-600">Depoimentos</a>
                        <a href="#pricing" onClick={() => setMobileMenuOpen(false)} className="block text-lg font-bold text-gray-600">Planos</a>
                        <a href="#contact" onClick={() => setMobileMenuOpen(false)} className="block text-lg font-bold text-gray-600">Contato</a>
                    </div>
                </div>
            </nav>

            {/* HERO SECTION - REALISTIC & HIGH CONVERSION */}
            <section className="relative pt-32 pb-20 lg:pt-52 lg:pb-40 overflow-hidden bg-white">
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
                                O FIM DA FILA NO CAIXA
                            </div>
                            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-black text-gray-900 tracking-tight leading-[1.05] lg:leading-[0.95] mb-10">
                                O ERP focado na <br className="hidden sm:block" />
                                <span className="bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-700 bg-clip-text text-transparent">realidade do varejo.</span>
                            </h1>
                            <p className="text-xl lg:text-2xl text-gray-600 leading-relaxed mb-12 font-medium max-w-xl">
                                PDV ágil que <strong>não para se a internet cair</strong>. Emissão nativa de NFCe, importação de XML de fornecedores em um clique e módulo completo de Delivery.
                            </p>

                            <div className="flex flex-col sm:flex-row items-center gap-6">
                                <motion.button
                                    whileHover={{ scale: 1.05, boxShadow: "0 25px 50px -12px rgba(37, 99, 235, 0.4)" }}
                                    whileTap={{ scale: 0.98 }}
                                    onClick={() => document.getElementById('pricing')?.scrollIntoView({ behavior: 'smooth' })}
                                    className="w-full sm:w-auto px-10 py-6 bg-blue-600 text-white rounded-[2rem] font-black text-xl hover:bg-blue-700 transition-all flex items-center justify-center gap-3 relative group overflow-hidden"
                                >
                                    <span className="relative z-10 uppercase tracking-tighter">CONHECER OS PLANOS</span>
                                    <ArrowRight className="w-6 h-6 group-hover:translate-x-1 transition-transform relative z-10" />
                                </motion.button>

                                <motion.button
                                    whileHover={{ scale: 1.05, borderColor: "#2563eb" }}
                                    whileTap={{ scale: 0.98 }}
                                    onClick={handleDemoAccess}
                                    className="w-full sm:w-auto px-10 py-6 bg-white text-gray-900 border-2 border-gray-100 rounded-[2rem] font-black text-xl hover:bg-slate-50 transition-all text-center flex items-center justify-center gap-3 shadow-xl shadow-gray-200/50"
                                >
                                    VER DEMONSTRAÇÃO
                                    <PlayCircle className="w-6 h-6 text-blue-600" />
                                </motion.button>
                            </div>

                            <div className="mt-14 flex flex-wrap items-center gap-8 text-sm font-bold text-gray-500">
                                <div className="flex items-center gap-2">
                                    <Award className="w-5 h-5 text-amber-500" />
                                    <span>Selo de Qualidade no Suporte</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <ShieldCheck className="w-5 h-5 text-emerald-500" />
                                    <span>NFC-e / NF-e Autorizadas SEFAZ</span>
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

                                <motion.div
                                    animate={{ y: [0, -10, 0] }}
                                    transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                                    className="absolute -bottom-8 -right-8 bg-white p-6 rounded-3xl shadow-2xl border border-gray-100 max-w-[200px] hidden sm:block"
                                >
                                    <div className="flex items-center gap-3 mb-2">
                                        <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                                            <FileUp className="w-5 h-5 text-blue-600" />
                                        </div>
                                        <div className="flex-1">
                                            <div className="h-2 w-full bg-gray-100 rounded-full mb-1"></div>
                                            <div className="h-2 w-2/3 bg-gray-50 rounded-full"></div>
                                        </div>
                                    </div>
                                    <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest">XML Importado com Sucesso</p>
                                </motion.div>
                            </div>
                        </motion.div>
                    </div>
                </div>
            </section>

            {/* SEÇÃO FISCAL NFE/NFCE & XML */}
            <section id="fiscal" className="py-24 lg:py-32 bg-gray-900 border-y border-white/5 relative overflow-hidden">
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
                                        <div className="w-12 h-12 bg-emerald-500 rounded-xl flex items-center justify-center">
                                            <ShieldCheck className="w-6 h-6 text-white" />
                                        </div>
                                        <div>
                                            <p className="text-white font-black">Homologado na SEFAZ</p>
                                            <p className="text-gray-400 text-xs">Autorização direta de NF-e e NFC-e</p>
                                        </div>
                                    </div>
                                </div>

                                <div className="space-y-6">
                                    <div className="flex items-start gap-6">
                                        <motion.div
                                            animate={{ scale: [1, 1.1, 1], rotate: [0, 5, 0] }}
                                            transition={{ duration: 3, repeat: Infinity }}
                                            className="w-16 h-16 bg-white/10 rounded-2xl flex items-center justify-center shrink-0 border border-white/5"
                                        >
                                            <FileUp className="w-8 h-8 text-blue-400" />
                                        </motion.div>
                                        <div>
                                            <h4 className="text-xl font-black text-white mb-2">Entrada de Estoque via XML</h4>
                                            <p className="text-gray-400 leading-relaxed font-medium">
                                                Pare de cadastrar produtos na mão. Importe a nota do seu fornecedor e o sistema cadastra os itens e atualiza o estoque de forma automática.
                                            </p>
                                        </div>
                                    </div>
                                    
                                    <div className="h-[1px] w-full bg-white/10 my-4"></div>

                                    <div className="flex items-start gap-6">
                                        <motion.div
                                            animate={{ scale: [1, 1.1, 1], rotate: [0, 5, 0] }}
                                            transition={{ duration: 3, delay: 1, repeat: Infinity }}
                                            className="w-16 h-16 bg-white/10 rounded-2xl flex items-center justify-center shrink-0 border border-white/5"
                                        >
                                            <Receipt className="w-8 h-8 text-emerald-400" />
                                        </motion.div>
                                        <div>
                                            <h4 className="text-xl font-black text-white mb-2">Cupom ou E-mail, Você Escolhe</h4>
                                            <p className="text-gray-400 leading-relaxed font-medium">
                                                Imprima a nota diretamente na impressora térmica no balcão ou envie por e-mail para o cliente em um clique, sem complicações.
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </motion.div>

                        <div className="text-left">
                            <h2 className="text-blue-400 font-black tracking-widest text-sm uppercase mb-6">Módulo Fiscal Nativo</h2>
                            <h3 className="text-4xl lg:text-6xl font-black text-white leading-tight mb-8">
                                Você em dia com o fisco, <br />
                                <span className="text-gray-500">sem dores de cabeça.</span>
                            </h3>
                            <div className="space-y-8">
                                {[
                                    { title: "Comunicação Direta SEFAZ", desc: "Autorização de notas fiscais diretamente pelos nossos servidores rápidos e seguros." },
                                    { title: "Gerenciador de Contingência Offline", desc: "A internet caiu? O PDV opera normalmente e transmite os cupons pendentes quando a conexão voltar." },
                                    { title: "Certificado A1 Integrado", desc: "Basta vincular seu certificado digital (.pfx) no painel de controle de forma simples." }
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


            {/* DELIVERY / NEW FEATURE SECTION */}
            <section className="py-24 bg-blue-50 relative overflow-hidden">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center max-w-3xl mx-auto mb-20">
                        <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-blue-600 text-white rounded-full text-xs font-black tracking-widest uppercase mb-6 shadow-md animate-bounce">
                            <Truck className="w-4 h-4" />
                            FUNCIONALIDADE COMPLETA
                        </div>
                        <h3 className="text-4xl lg:text-6xl font-black text-gray-900 leading-tight">
                            Gestão de Entregas e <br />
                            <span className="text-blue-600">Módulo Delivery.</span>
                        </h3>
                    </div>

                    <div className="grid lg:grid-cols-2 gap-16 items-center">
                        <div>
                            <h4 className="text-3xl font-black text-gray-900 mb-6">Controle as taxas e motoboys.</h4>
                            <p className="text-xl text-gray-600 leading-relaxed font-medium mb-10">
                                Vende pelo WhatsApp ou telefone? Lance o pedido diretamente no PDV escolhendo a opção Delivery. Inclua a taxa de entrega e saiba exatamente o que o motoboy deve acertar no fim do dia.
                            </p>
                            <ul className="space-y-4 mb-8">
                                <li className="flex items-center gap-3 text-gray-700 font-bold"><CheckCircle className="text-emerald-500 w-5 h-5" /> Tela PDV otimizada: Alterne entre Balcão e Delivery facilmente</li>
                                <li className="flex items-center gap-3 text-gray-700 font-bold"><CheckCircle className="text-emerald-500 w-5 h-5" /> Adição de taxas de entrega customizadas</li>
                                <li className="flex items-center gap-3 text-gray-700 font-bold"><CheckCircle className="text-emerald-500 w-5 h-5" /> Dados do cliente para o entregador diretamente na impressão</li>
                            </ul>
                            <button onClick={() => navigate('/login')} className="px-8 py-4 bg-gray-900 text-white rounded-xl font-black hover:bg-black transition-all">
                                Explorar o PDV de Delivery
                            </button>
                        </div>
                        <div className="relative">
                            <div className="bg-white p-4 rounded-[2rem] border border-gray-200 shadow-2xl rotate-2 hover:rotate-0 transition-transform duration-500">
                                <img src="/screenshots/pdv.png" alt="PDV com Delivery" className="rounded-2xl w-full" onError={(e) => {
                                    (e.target as HTMLImageElement).src = 'https://images.unsplash.com/photo-1620063259966-218ab2b3ee33?auto=format&fit=crop&q=80&w=800';
                                }} />
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* O SISTEMA EM AÇÃO - GALERIA REAL */}
            <section className="py-16 lg:py-24 bg-white overflow-hidden">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center max-w-3xl mx-auto mb-20">
                        <h2 className="text-blue-600 font-black tracking-widest text-sm uppercase mb-4">Design Clean e Focado</h2>
                        <h3 className="text-4xl lg:text-6xl font-black text-gray-900 mb-8">Conheça as Telas <span className="text-blue-600">do Sistema.</span></h3>
                        <p className="text-xl text-gray-500 font-medium">Um layout pensado para quem opera o caixa e para quem faz a gestão. Simples, bonito e funcional.</p>
                    </div>

                    <div className="grid md:grid-cols-2 gap-12">
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
                                <h4 className="text-2xl font-black px-6">Caixa PDV Rápido</h4>
                                <p className="text-gray-500 font-bold px-6">Layout focado em produtividade para atendimento sem filas.</p>
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
                                <h4 className="text-2xl font-black px-6">Gestão de Estoque</h4>
                                <p className="text-gray-500 font-bold px-6">Acompanhe quantidade, curva ABC e receba alertas de produtos vencendo.</p>
                            </div>
                        </div>
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
                                <h4 className="text-2xl font-black px-6">Dashboard Gerencial</h4>
                                <p className="text-gray-500 font-bold px-6">Resumo financeiro, lucro bruto e volume de vendas centralizados.</p>
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
                                <h4 className="text-2xl font-black px-6">Análise de Vendas</h4>
                                <p className="text-gray-500 font-bold px-6">Filtre vendas por data, vendedor e status de forma simples.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* RECURSOS ADICIONAIS Section */}
            <section id="features" className="py-20 lg:py-40 bg-slate-50 relative overflow-hidden">
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1200px] h-[1200px] bg-blue-100/20 rounded-full blur-[150px] -z-10"></div>

                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center max-w-3xl mx-auto mb-24">
                        <div className="inline-block px-4 py-1.5 bg-blue-600/10 text-blue-600 rounded-full text-xs font-black tracking-widest uppercase mb-6">Completo e Fácil</div>
                        <h3 className="text-4xl lg:text-5xl font-black text-gray-900 leading-tight mb-8">
                            Ferramentas pensadas <br />
                            <span className="text-blue-600">no dia a dia do varejo.</span>
                        </h3>
                        <p className="text-xl text-gray-500 font-medium">Desde o cadastro até a emissão da nota, otimizamos todas as pontas da operação.</p>
                    </div>

                    <div className="grid lg:grid-cols-3 gap-10">
                        {[
                            {
                                icon: <Zap className="w-10 h-10 text-white" />,
                                color: "bg-blue-600",
                                title: "PDV Híbrido",
                                description: "Funciona online e offline. A internet caiu? Continue vendendo normalmente, os dados são salvos no navegador e sobem sozinhos quando conectar."
                            },
                            {
                                icon: <FileUp className="w-10 h-10 text-white" />,
                                color: "bg-emerald-500",
                                title: "Importação XML",
                                description: "Suba o arquivo XML da nota de compra do seu fornecedor. O sistema vincula, cria produtos novos e abastece seu estoque automaticamente."
                            },
                            {
                                icon: <Truck className="w-10 h-10 text-white" />,
                                color: "bg-indigo-500",
                                title: "Módulo Delivery",
                                description: "Adicione dados de entrega e taxas de motoboy nas vendas por WhatsApp. Tenha relatórios separados do balcão e gerencie seus entregadores."
                            },
                            {
                                icon: <TrendingUp className="w-10 h-10 text-white" />,
                                color: "bg-purple-600",
                                title: "Análise de Estoque ABC",
                                description: "Entenda quais produtos trazem mais lucro (Curva A) e quais estão encalhados (Curva C), ajustando suas compras de forma inteligente."
                            },
                            {
                                icon: <ShieldCheck className="w-10 h-10 text-white" />,
                                color: "bg-amber-500",
                                title: "Emissão NFe e NFCe",
                                description: "Módulo fiscal homologado. Emita cupons rapidamente para seus clientes, seja na impressora ou via envio de email."
                            },
                            {
                                icon: <Globe className="w-10 h-10 text-white" />,
                                color: "bg-teal-600",
                                title: "Sistema em Nuvem",
                                description: "Acesse os relatórios gerenciais pelo celular ou de casa. Seus dados estão seguros e backupeados em nossos servidores."
                            }
                        ].map((feat, i) => (
                            <motion.div
                                key={i}
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: i * 0.1 }}
                                className="bg-white p-10 rounded-[3rem] border border-gray-100 hover:shadow-xl hover:border-blue-100 transition-all group relative overflow-hidden"
                            >
                                <div className={`w-16 h-16 rounded-2xl ${feat.color} flex items-center justify-center mb-8 shadow-sm transform group-hover:scale-110 transition-transform`}>
                                    {feat.icon}
                                </div>
                                <h4 className="text-xl font-black text-gray-900 mb-4">{feat.title}</h4>
                                <p className="text-gray-500 font-medium leading-relaxed">
                                    {feat.description}
                                </p>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* TESTIMONIALS */}
            <section id="testimonials" className="py-24 lg:py-32 bg-white relative">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-20">
                        <h3 className="text-4xl lg:text-5xl font-black text-gray-900 mb-6">Quem usa, aprova</h3>
                        <p className="text-xl text-gray-500 font-medium">Veja o que donos de negócios locais dizem sobre nossa plataforma.</p>
                    </div>

                    <div className="grid md:grid-cols-3 gap-8">
                        {testimonials.map((t, i) => (
                            <div key={i} className="bg-slate-50 p-10 rounded-[2.5rem] border border-gray-100 relative group hover:shadow-xl transition-all">
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


            {/* PRICING Section - REALISTIC & CLEAR */}
            <section id="pricing" className="py-24 lg:py-40 bg-slate-50 relative overflow-hidden">
                <div className="absolute top-1/2 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-gray-200 to-transparent"></div>

                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
                    <div className="text-center max-w-3xl mx-auto mb-24">
                        <div className="inline-block px-4 py-1.5 bg-blue-600/10 text-blue-600 rounded-full text-xs font-black tracking-widest uppercase mb-6">Assinatura Simples</div>
                        <h3 className="text-4xl lg:text-6xl font-black text-gray-900 mb-8">Planos feitos para o <br /><span className="text-blue-600">seu momento.</span></h3>
                        <p className="text-xl text-gray-500 font-medium leading-relaxed">Assine sem burocracia, cancele quando quiser. Nenhuma taxa surpresa de instalação.</p>
                    </div>

                    <div className="grid md:grid-cols-2 max-w-4xl mx-auto gap-10">
                        {tiers.map((tier, idx) => (
                            <motion.div
                                key={idx}
                                initial={{ opacity: 0, y: 30 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: idx * 0.1 }}
                                className={`relative flex flex-col p-10 md:p-12 rounded-[3rem] border-2 transition-all duration-500 ${tier.highlight
                                    ? 'border-blue-600 bg-white shadow-xl scale-105 z-10'
                                    : 'border-gray-100 bg-white shadow hover:border-blue-200'
                                    }`}
                            >
                                {tier.highlight && (
                                    <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-blue-600 text-white px-6 py-2 rounded-full text-[10px] font-black tracking-widest uppercase shadow-md whitespace-nowrap">
                                        RECOMENDADO (MAIS COMPLETO)
                                    </div>
                                )}
                                <div className="mb-10">
                                    <h4 className="text-3xl font-black text-gray-900 mb-3">{tier.name}</h4>
                                    <div className="flex items-baseline gap-2 mb-4">
                                        <span className="text-5xl font-black text-gray-900 tracking-tighter">{tier.price}</span>
                                        <span className="text-gray-400 font-bold text-lg">{tier.period}</span>
                                    </div>
                                    <p className="text-gray-500 font-medium leading-relaxed">{tier.description}</p>
                                </div>
                                <div className="space-y-4 mb-10 flex-1">
                                    {tier.features.map((feature, fIdx) => (
                                        <div key={fIdx} className="flex items-start gap-3">
                                            <div className="shrink-0 mt-1">
                                                <CheckCircle className={`w-5 h-5 ${tier.highlight ? 'text-blue-600' : 'text-emerald-500'}`} />
                                            </div>
                                            <span className="text-gray-700 font-medium text-sm leading-snug">{feature}</span>
                                        </div>
                                    ))}
                                </div>
                                <button
                                    onClick={() => handlePlanSelect(tier)}
                                    className={`w-full py-5 rounded-[1.5rem] font-bold text-lg transition-all active:scale-95 flex items-center justify-center gap-2 ${tier.highlight
                                        ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-lg shadow-blue-200/50'
                                        : 'bg-white border-2 border-gray-200 text-gray-900 hover:border-gray-900'
                                        }`}>
                                    {tier.cta}
                                </button>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* CONTACT SECTION */}
            <section id="contact" className="py-20 lg:py-32 bg-white">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="bg-gray-900 rounded-[3rem] overflow-hidden shadow-2xl relative">
                        <div className="absolute -bottom-20 -left-20 w-80 h-80 bg-blue-600/20 rounded-full blur-[100px]"></div>

                        <div className="grid lg:grid-cols-2">
                            <div className="p-8 md:p-12 lg:p-20 border-b lg:border-b-0 lg:border-r border-white/10 relative z-10">
                                <h3 className="text-4xl lg:text-5xl font-black text-white mb-8">Fale com nossa equipe comercial.</h3>
                                <p className="text-xl text-gray-400 font-medium mb-12 leading-relaxed">
                                    Tem dúvidas se o <strong>MercadinhoSys</strong> serve para o seu negócio? Deixe seus dados que entraremos em contato rapidamente.
                                </p>
                                <div className="space-y-8">
                                    <div className="flex items-center gap-6">
                                        <div className="w-12 h-12 bg-blue-600/20 rounded-xl flex items-center justify-center">
                                            <Phone className="w-6 h-6 text-blue-400" />
                                        </div>
                                        <div>
                                            <p className="text-gray-500 font-bold text-xs uppercase tracking-widest">WhatsApp Comercial</p>
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
                            <div className="p-8 md:p-12 lg:p-20 bg-white/5 backdrop-blur-sm relative z-10">
                                <form onSubmit={handleLeadSubmit} className="space-y-6">
                                    <div>
                                        <label className="block text-gray-400 text-sm font-bold mb-2">Nome Completo</label>
                                        <div className="relative">
                                            <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                                            <input
                                                required
                                                type="text"
                                                placeholder="Seu nome"
                                                value={leadName}
                                                onChange={(e) => setLeadName(e.target.value)}
                                                className="w-full bg-white/10 border border-white/10 rounded-xl py-4 pl-12 pr-6 text-white font-medium focus:outline-none focus:border-blue-500 transition-all placeholder:text-gray-600"
                                            />
                                        </div>
                                    </div>
                                    <div>
                                        <label className="block text-gray-400 text-sm font-bold mb-2">E-mail</label>
                                        <div className="relative">
                                            <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                                            <input
                                                required
                                                type="email"
                                                placeholder="exemplo@loja.com.br"
                                                value={leadEmail}
                                                onChange={(e) => setLeadEmail(e.target.value)}
                                                className="w-full bg-white/10 border border-white/10 rounded-xl py-4 pl-12 pr-6 text-white font-medium focus:outline-none focus:border-blue-500 transition-all placeholder:text-gray-600"
                                            />
                                        </div>
                                    </div>
                                    <div>
                                        <label className="block text-gray-400 text-sm font-bold mb-2">WhatsApp / Celular</label>
                                        <div className="relative">
                                            <Phone className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                                            <input
                                                required
                                                type="tel"
                                                placeholder="(11) 99999-9999"
                                                value={leadWhatsApp}
                                                onChange={(e) => setLeadWhatsApp(e.target.value)}
                                                className="w-full bg-white/10 border border-white/10 rounded-xl py-4 pl-12 pr-6 text-white font-medium focus:outline-none focus:border-blue-500 transition-all placeholder:text-gray-600"
                                            />
                                        </div>
                                    </div>
                                    <button
                                        type="submit"
                                        disabled={loadingLead}
                                        className="w-full py-4 bg-blue-600 text-white rounded-xl font-bold text-lg hover:bg-blue-700 transition-all flex items-center justify-center"
                                    >
                                        {loadingLead ? <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin"></div> : 'SOLICITAR CONTATO'}
                                    </button>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="py-12 bg-slate-50 border-t border-gray-200">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex flex-col md:flex-row justify-between items-center gap-6">
                        <div className="flex items-center gap-3">
                            <img src="/assets/logo.png" alt="Logo Footer" className="w-8 h-8 object-contain" />
                            <span className="text-xl font-black text-gray-900 tracking-tighter">
                                Mercadinho<span className="text-blue-600">Sys</span>
                            </span>
                        </div>
                        <div className="flex flex-wrap justify-center gap-6 text-sm font-bold text-gray-500">
                            <a href="#features" className="hover:text-blue-600">Recursos</a>
                            <a href="#fiscal" className="hover:text-blue-600">Fiscal NFe/NFCe</a>
                            <a href="#pricing" className="hover:text-blue-600">Planos</a>
                            <a href="/termos" className="hover:text-blue-600">Termos de Uso</a>
                            <a href="/privacidade" className="hover:text-blue-600">Privacidade</a>
                            <a href="/login" className="hover:text-blue-600">Acesso Cliente</a>
                            <a href="/ajuda" className="hover:text-blue-600">Ajuda</a>
                        </div>
                        <p className="text-gray-400 font-medium text-xs">
                            &copy; {new Date().getFullYear()} MercadinhoSys. Todos os direitos reservados.
                        </p>
                    </div>
                </div>
            </footer>
            
            {/* CONVERSION MODAL APRIMORADO */}
            {conversionModalOpen && (
                <div className="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-gray-900/80 backdrop-blur-md overflow-y-auto">
                    <div className="bg-white w-full max-w-5xl rounded-[2rem] shadow-2xl overflow-hidden relative animate-in fade-in zoom-in duration-300 my-8 flex flex-col md:flex-row">
                        <button
                            onClick={() => setConversionModalOpen(false)}
                            className="absolute top-4 right-4 z-10 text-gray-400 hover:text-gray-900 bg-gray-100 hover:bg-gray-200 rounded-full p-2 transition-colors"
                        >
                            <X className="w-5 h-5" />
                        </button>

                        {/* Coluna da Esquerda - Benefícios e Confiança */}
                        <div className="bg-gradient-to-br from-blue-900 to-blue-700 w-full md:w-5/12 p-8 md:p-12 text-white flex flex-col justify-between">
                            <div>
                                <div className="inline-flex items-center gap-2 px-3 py-1 bg-white/20 rounded-full text-sm font-semibold mb-6">
                                    <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
                                    Plano Escolhido
                                </div>
                                <h3 className="text-3xl font-black mb-2">{selectedPlan?.name}</h3>
                                <div className="flex items-baseline gap-1 mb-8">
                                    <span className="text-4xl font-black">{selectedPlan?.price}</span>
                                    <span className="text-blue-200">/mês</span>
                                </div>

                                <ul className="space-y-4 mb-8">
                                    <li className="flex items-start gap-3">
                                        <div className="mt-1 bg-blue-500/30 p-1 rounded-full"><Check className="w-4 h-4 text-blue-100" /></div>
                                        <p className="text-blue-50 font-medium text-sm md:text-base"><strong>Sem fidelidade.</strong> Cancele quando quiser, sem multas.</p>
                                    </li>
                                    <li className="flex items-start gap-3">
                                        <div className="mt-1 bg-blue-500/30 p-1 rounded-full"><Lock className="w-4 h-4 text-blue-100" /></div>
                                        <p className="text-blue-50 font-medium text-sm md:text-base"><strong>Preço travado.</strong> O valor que você assinar hoje não sofrerá reajustes no futuro.</p>
                                    </li>
                                    <li className="flex items-start gap-3">
                                        <div className="mt-1 bg-blue-500/30 p-1 rounded-full"><ShieldCheck className="w-4 h-4 text-blue-100" /></div>
                                        <p className="text-blue-50 font-medium text-sm md:text-base"><strong>Garantia de 7 dias.</strong> Reembolso integral se não gostar do sistema.</p>
                                    </li>
                                </ul>
                            </div>

                            {/* Trust Badges */}
                            <div className="pt-8 border-t border-white/10 flex flex-col gap-4">
                                <div className="flex items-center gap-3 bg-white/10 p-3 rounded-xl backdrop-blur-sm max-w-fit">
                                    <img src="/assets/reclame.png" alt="Selo Reclame Aqui" className="h-12 w-auto object-contain" />
                                </div>
                                <div className="flex items-center gap-3">
                                    <Lock className="w-5 h-5 text-blue-300 flex-shrink-0" />
                                    <p className="text-xs text-blue-200 leading-tight">Ambiente Seguro. Seus dados estão criptografados de ponta a ponta.</p>
                                </div>
                            </div>
                        </div>

                        {/* Coluna da Direita - Formulário */}
                        <div className="w-full md:w-7/12 p-8 md:p-12 bg-white">
                            <div className="mb-8">
                                <h3 className="text-2xl font-bold text-gray-900">Quase lá!</h3>
                                <p className="text-gray-500 mt-2">Crie sua conta para acessar o checkout seguro.</p>
                            </div>

                            <form onSubmit={handleCheckout} className="space-y-5">
                                <div>
                                    <label className="block text-gray-700 text-sm font-bold mb-2">E-mail de Acesso</label>
                                    <div className="relative">
                                        <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                                        <input
                                            required
                                            type="email"
                                            placeholder="seu@email.com"
                                            value={onboardingEmail}
                                            onChange={(e) => setOnboardingEmail(e.target.value)}
                                            className="w-full bg-slate-50 border border-gray-200 rounded-xl py-3.5 pl-12 pr-4 focus:outline-none focus:border-blue-600 focus:ring-4 focus:ring-blue-600/10 transition-all font-medium"
                                        />
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-gray-700 text-sm font-bold mb-2">WhatsApp Corporativo</label>
                                    <div className="relative">
                                        <Phone className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                                        <input
                                            required
                                            type="tel"
                                            placeholder="(11) 99999-9999"
                                            value={onboardingWhatsApp}
                                            onChange={(e) => setOnboardingWhatsApp(e.target.value)}
                                            className="w-full bg-slate-50 border border-gray-200 rounded-xl py-3.5 pl-12 pr-4 focus:outline-none focus:border-blue-600 focus:ring-4 focus:ring-blue-600/10 transition-all font-medium"
                                        />
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-gray-700 text-sm font-bold mb-2">Nome do Estabelecimento</label>
                                    <div className="relative">
                                        <ShoppingCart className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                                        <input
                                            required
                                            type="text"
                                            placeholder="Ex: Mercadinho São José"
                                            value={onboardingStoreName}
                                            onChange={(e) => setOnboardingStoreName(e.target.value)}
                                            className="w-full bg-slate-50 border border-gray-200 rounded-xl py-3.5 pl-12 pr-4 focus:outline-none focus:border-blue-600 focus:ring-4 focus:ring-blue-600/10 transition-all font-medium"
                                        />
                                    </div>
                                </div>

                                <div className="pt-4">
                                    <button
                                        type="submit"
                                        disabled={loadingCheckout}
                                        className="w-full py-4 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl font-bold text-lg hover:from-blue-700 hover:to-blue-800 transition-all shadow-lg shadow-blue-600/30 flex items-center justify-center gap-3 disabled:opacity-70"
                                    >
                                        {loadingCheckout ? 'Preparando Checkout...' : 'Continuar para Pagamento'}
                                        {!loadingCheckout && <ArrowRight className="w-5 h-5" />}
                                    </button>
                                </div>
                            </form>

                            <div className="flex flex-col sm:flex-row items-center justify-center gap-3 mt-8 pt-6 border-t border-gray-100">
                                <span className="text-xs text-gray-400 font-medium">Pagamento seguro processado por</span>
                                <div className="flex items-center justify-center bg-[#F36F21] px-3 py-1.5 rounded-lg shadow-sm">
                                    {/* Logo Efí Bank Oficial - Laranja vibrante com letras brancas */}
                                    <svg viewBox="0 0 100 30" className="h-4 w-auto fill-white">
                                        <path d="M15.5 8.1c-4.2 0-7.3 3-7.3 7.3s3.1 7.3 7.3 7.3c2.7 0 5-1.4 6.2-3.5l-2.4-1.5c-.8 1.4-2.2 2.3-3.8 2.3-2.6 0-4.6-2.1-4.6-4.6h11v-1c0-3.5-2.6-6.3-6.4-6.3zm-4.6 6c.4-1.8 1.9-3.2 3.8-3.2 2 0 3.6 1.4 3.8 3.2h-7.6zM28.4 8.5v2.8h-2.1v11.1h-2.9V11.3h-1.5V8.5h1.5V6.7c0-2.3 1.3-3.5 3.6-3.5h1.4v2.8h-1c-.9 0-1.1.4-1.1 1v1.5h2.1zM34.3 5.3c-1 0-1.8-.8-1.8-1.8s.8-1.8 1.8-1.8 1.8.8 1.8 1.8-.8 1.8-1.8 1.8zm-1.4 3.2h2.9v13.9h-2.9V8.5z"/>
                                        <path d="M47.8 8.1c-3.1 0-5.3 1.7-6 4.3h-2.1V8.5h-2.9v13.9h2.9v-5.8c0-3.1 1.7-5.5 4.9-5.5 1.5 0 2.8.5 3.8 1.4l1.9-2.2c-1.3-1.3-3-2.2-2.5-2.2z"/>
                                    </svg>
                                    <span className="text-white font-black ml-1 text-sm tracking-tighter">efí</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default LandingPage;
