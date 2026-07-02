import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../auth/authService';
import {
    ShoppingCart,
    ShieldCheck,
    MessageCircle,
    Star,
    Mail,
    Phone,
    User,
    ArrowRight,
    TrendingUp,
    Check,
    Truck,
    Receipt,
    FileUp,
    X,
    DollarSign,
    Zap,
    Globe
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
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nome: leadName, email: leadEmail, whatsapp: leadWhatsApp, origem: 'landing_page' }),
            });
            const result = await response.json();
            if (response.ok && result.success) {
                showToast.info('Informações enviadas! Entraremos em contato em breve.');
                setLeadName(''); setLeadEmail(''); setLeadWhatsApp('');
                setTimeout(() => {
                    window.open(`https://wa.me/5511919889233?text=Olá! Acabei de me cadastrar no site e gostaria de saber mais sobre o MercadinhoSys. Meu e-mail é ${leadEmail}.`, '_blank');
                }, 1000);
            } else {
                showToast.error(result.error || 'Ocorreu um erro ao enviar seus dados.');
            }
        } catch (error) {
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
                headers: { 'Content-Type': 'application/json' },
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
                headers: { 'Content-Type': 'application/json' }
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
                setTimeout(() => { window.location.href = '/dashboard'; }, 500);
            } else {
                showToast.dismiss();
                showToast.error(result.error || 'Erro ao acessar demonstração');
            }
        } catch (error) {
            showToast.dismiss();
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

    return (
        <div className="h-screen overflow-y-auto overflow-x-hidden bg-[#0A1220] font-['Space_Grotesk',sans-serif] text-[#DCE8F7] selection:bg-[#2E9BFF] selection:text-[#06101F] custom-scrollbar relative">
            {/* WhatsApp Floating Button */}
            <a
                href="https://wa.me/5511919889233"
                target="_blank"
                rel="noreferrer"
                className="fixed bottom-8 right-8 z-[100] bg-emerald-500 text-white p-4 rounded-full shadow-2xl shadow-emerald-400/30 hover:scale-110 active:scale-95 transition-all flex items-center justify-center group"
            >
                <MessageCircle className="w-8 h-8" />
                <span className="max-w-0 overflow-hidden group-hover:max-w-xs group-hover:ml-2 transition-all duration-500 font-bold whitespace-nowrap">
                    Dúvidas? Fale Conosco
                </span>
            </a>

            {/* Navbar */}
            <nav className="fixed top-0 w-full z-50 bg-[#0A1220]/80 backdrop-blur-xl border-b border-[#24344F]">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center h-20">
                        <div className="flex items-center gap-3 group cursor-pointer" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
                            <div className="w-12 h-12 bg-[#0A1220] rounded-xl flex items-center justify-center p-1 border border-[#24344F] group-hover:border-[#2E9BFF] transition-all overflow-hidden">
                                <img src="/assets/logo.png" alt="MercadinhoSys Logo" className="w-full h-full object-contain" />
                            </div>
                            <span className="text-2xl font-bold text-white tracking-tighter">
                                Mercadinho<span className="text-[#FF6A5C]">Sys</span>
                            </span>
                        </div>
                        <div className="hidden lg:flex items-center gap-10">
                            <a href="#features" className="text-sm font-bold text-[#8FA3C0] hover:text-[#2E9BFF] transition-colors uppercase tracking-widest">Recursos</a>
                            <a href="#fiscal" className="text-sm font-bold text-[#8FA3C0] hover:text-[#2E9BFF] transition-colors uppercase tracking-widest">Fiscal</a>
                            <a href="#testimonials" className="text-sm font-bold text-[#8FA3C0] hover:text-[#2E9BFF] transition-colors uppercase tracking-widest">Depoimentos</a>
                            <a href="#pricing" className="text-sm font-bold text-[#8FA3C0] hover:text-[#2E9BFF] transition-colors uppercase tracking-widest">Planos</a>
                            <button
                                onClick={() => navigate('/login')}
                                className="px-8 py-3 bg-transparent border border-[#2E9BFF] text-[#6FCBFF] rounded-xl font-bold text-sm hover:bg-[#2E9BFF]/10 transition-all shadow-[0_0_15px_rgba(46,155,255,0.15)]"
                            >
                                ACESSAR PAINEL
                            </button>
                        </div>
                        <div className="lg:hidden flex items-center gap-4">
                            <button onClick={() => navigate('/login')} className="bg-transparent border border-[#2E9BFF] text-[#6FCBFF] px-4 py-2 rounded-lg font-bold text-xs">LOGIN</button>
                            <button onClick={() => setMobileMenuOpen(!mobileMenuOpen)} className="p-2 text-[#8FA3C0]">
                                <div className="w-6 h-5 flex flex-col justify-between">
                                    <span className={`h-0.5 w-full bg-current transform transition-all duration-300 ${mobileMenuOpen ? 'rotate-45 translate-y-2' : ''}`}></span>
                                    <span className={`h-0.5 w-full bg-current transition-all duration-300 ${mobileMenuOpen ? 'opacity-0' : ''}`}></span>
                                    <span className={`h-0.5 w-full bg-current transform transition-all duration-300 ${mobileMenuOpen ? '-rotate-45 -translate-y-2' : ''}`}></span>
                                </div>
                            </button>
                        </div>
                    </div>
                </div>

                <div className={`lg:hidden overflow-hidden transition-all duration-300 bg-[#101C31] border-b border-[#24344F] ${mobileMenuOpen ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'}`}>
                    <div className="px-4 py-6 space-y-4">
                        <a href="#features" onClick={() => setMobileMenuOpen(false)} className="block text-lg font-bold text-[#DCE8F7]">Recursos</a>
                        <a href="#fiscal" onClick={() => setMobileMenuOpen(false)} className="block text-lg font-bold text-[#DCE8F7]">Fiscal</a>
                        <a href="#pricing" onClick={() => setMobileMenuOpen(false)} className="block text-lg font-bold text-[#DCE8F7]">Planos</a>
                    </div>
                </div>
            </nav>

            {/* HERO SECTION - FUTURO DO BAIRRO + SÉRIO E JUSTO + Slogan */}
            <section className="relative pt-32 pb-20 lg:pt-52 lg:pb-32 overflow-hidden">
                <div className="absolute top-0 right-0 -z-10 w-[800px] h-[800px] bg-[#1D4ED8]/20 rounded-full blur-[120px] translate-x-1/3 -translate-y-1/3"></div>
                <div className="absolute bottom-0 left-0 -z-10 w-[600px] h-[600px] bg-[#2E9BFF]/10 rounded-full blur-[100px] -translate-x-1/4 translate-y-1/4"></div>

                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
                    <div className="grid lg:grid-cols-2 gap-16 items-center">
                        <motion.div
                            initial={{ opacity: 0, x: -50 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ duration: 0.8, ease: "easeOut" }}
                            className="text-left"
                        >
                            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight leading-[1.1] lg:leading-[1.05] mb-8 text-white">
                                A gente cuida da sua loja <br className="hidden sm:block" />
                                <span className="bg-gradient-to-r from-[#2E9BFF] to-[#6FCBFF] bg-clip-text text-transparent">com você.</span>
                            </h1>
                            <p className="text-xl lg:text-2xl text-[#8FA3C0] leading-relaxed mb-8 font-medium max-w-xl">
                                <span className="text-white font-bold">ERP completo. R$ 99,90. Sem pegadinha.</span><br/>
                                PDV, estoque, nota fiscal e financeiro. Num app só. A tecnologia dos grandes supermercados agora no seu balcão.
                            </p>

                            <div className="flex flex-col sm:flex-row items-center gap-6">
                                <motion.button
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.98 }}
                                    onClick={() => document.getElementById('pricing')?.scrollIntoView({ behavior: 'smooth' })}
                                    className="w-full sm:w-auto px-10 py-5 bg-gradient-to-r from-[#2E9BFF] to-[#1D4ED8] text-white rounded-[10px] font-bold text-xl hover:brightness-110 transition-all flex items-center justify-center shadow-[0_0_28px_rgba(46,155,255,0.45)]"
                                >
                                    ENTRAR NO FUTURO
                                </motion.button>

                                <motion.button
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.98 }}
                                    onClick={handleDemoAccess}
                                    className="w-full sm:w-auto px-10 py-5 bg-[#101C31] text-[#DCE8F7] border border-[#24344F] rounded-[10px] font-bold text-xl hover:bg-[#24344F] transition-all text-center flex items-center justify-center gap-3"
                                >
                                    TESTAR AGORA
                                </motion.button>
                            </div>
                        </motion.div>

                        <motion.div
                            initial={{ opacity: 0, scale: 0.9, y: 50 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            transition={{ duration: 1, delay: 0.2 }}
                            className="relative lg:block hidden"
                        >
                            <div className="relative w-full max-w-[500px] mx-auto rounded-[24px] shadow-[0_0_50px_rgba(46,155,255,0.15)] border border-[#24344F] overflow-hidden group bg-[#0A1220]">
                                <div className="absolute inset-0 bg-gradient-to-t from-[#0A1220] via-transparent to-transparent z-10 pointer-events-none"></div>
                                <video 
                                    src="/assets/vídeo marketing.mp4" 
                                    autoPlay 
                                    loop 
                                    muted 
                                    playsInline 
                                    className="w-full h-auto object-cover transform group-hover:scale-105 transition-transform duration-700"
                                />
                                <div className="absolute bottom-6 left-6 right-6 z-20 flex justify-between items-end">
                                    <div className="flex flex-col gap-2">
                                        <div className="border border-[#2E9BFF]/50 text-[#6FCBFF] font-bold text-xs tracking-wider uppercase rounded-full px-4 py-1.5 w-max bg-[#101C31]/80 backdrop-blur-md">Veja na prática</div>
                                        <div className="text-white font-bold text-2xl drop-shadow-md">A central de comando <br/>da sua loja.</div>
                                    </div>
                                    <div className="w-12 h-12 rounded-full bg-[#2E9BFF] flex items-center justify-center shadow-lg shadow-[#2E9BFF]/50 animate-pulse">
                                        <div className="w-0 h-0 border-t-8 border-t-transparent border-l-12 border-l-white border-b-8 border-b-transparent ml-1"></div>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    </div>
                </div>
            </section>

            {/* SEÇÃO FISCAL NFE/NFCE & XML */}
            <section id="fiscal" className="py-24 bg-[#101C31] border-y border-[#24344F] relative overflow-hidden">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="grid lg:grid-cols-2 gap-20 items-center">
                        <motion.div
                            initial={{ opacity: 0, x: -30 }}
                            whileInView={{ opacity: 1, x: 0 }}
                            viewport={{ once: true }}
                            className="relative"
                        >
                            <div className="bg-[#0A1220] border border-[#24344F] rounded-[20px] p-10 overflow-hidden shadow-2xl">
                                <div className="flex items-center justify-between mb-8 pb-8 border-b border-[#24344F]">
                                    <div className="flex items-center gap-4">
                                        <div className="w-12 h-12 bg-[#2E9BFF]/20 border border-[#2E9BFF]/50 rounded-xl flex items-center justify-center">
                                            <ShieldCheck className="w-6 h-6 text-[#6FCBFF]" />
                                        </div>
                                        <div>
                                            <p className="text-white font-bold">Homologado na SEFAZ</p>
                                            <p className="text-[#8FA3C0] text-sm">Autorização direta de NF-e e NFC-e</p>
                                        </div>
                                    </div>
                                </div>

                                <div className="space-y-6">
                                    <div className="flex items-start gap-6">
                                        <div className="w-14 h-14 bg-[#101C31] rounded-2xl flex items-center justify-center shrink-0 border border-[#24344F]">
                                            <FileUp className="w-7 h-7 text-[#2E9BFF]" />
                                        </div>
                                        <div>
                                            <h4 className="text-xl font-bold text-white mb-2">Entrada via XML</h4>
                                            <p className="text-[#8FA3C0] leading-relaxed">Importe a nota do seu fornecedor. O sistema vincula e abastece seu estoque automaticamente.</p>
                                        </div>
                                    </div>
                                    
                                    <div className="flex items-start gap-6">
                                        <div className="w-14 h-14 bg-[#101C31] rounded-2xl flex items-center justify-center shrink-0 border border-[#24344F]">
                                            <Receipt className="w-7 h-7 text-[#FF6A5C]" />
                                        </div>
                                        <div>
                                            <h4 className="text-xl font-bold text-white mb-2">Cupom ou E-mail</h4>
                                            <p className="text-[#8FA3C0] leading-relaxed">Imprima a nota diretamente na térmica do balcão ou envie por e-mail em um clique.</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </motion.div>

                        <div className="text-left">
                            <h2 className="text-[#8FA3C0] font-bold tracking-[1.5px] text-xs uppercase mb-6">Módulo Fiscal Nativo</h2>
                            <h3 className="text-4xl lg:text-5xl font-bold text-white leading-tight mb-8">
                                Você em dia com o fisco, <br />
                                <span className="bg-gradient-to-r from-[#FF6A5C] to-[#FFA79E] bg-clip-text text-transparent">sem dores de cabeça.</span>
                            </h3>
                            <div className="space-y-6">
                                <div className="flex gap-4">
                                    <Check className="w-6 h-6 text-[#2E9BFF] shrink-0 mt-1" />
                                    <div>
                                        <h4 className="text-lg font-bold text-white">Comunicação Direta SEFAZ</h4>
                                        <p className="text-[#8FA3C0]">Autorização de notas fiscais diretamente pelos nossos servidores rápidos e seguros.</p>
                                    </div>
                                </div>
                                <div className="flex gap-4">
                                    <Check className="w-6 h-6 text-[#2E9BFF] shrink-0 mt-1" />
                                    <div>
                                        <h4 className="text-lg font-bold text-white">Nota fiscal emitida em 8 segundos</h4>
                                        <p className="text-[#8FA3C0]">A internet caiu? O PDV opera normalmente e transmite os cupons pendentes quando a conexão voltar.</p>
                                    </div>
                                </div>
                                <div className="flex gap-4">
                                    <Check className="w-6 h-6 text-[#2E9BFF] shrink-0 mt-1" />
                                    <div>
                                        <h4 className="text-lg font-bold text-white">Certificado A1 Integrado</h4>
                                        <p className="text-[#8FA3C0]">Basta vincular seu certificado digital no painel de controle de forma simples.</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* RECURSOS ADICIONAIS Section */}
            <section id="features" className="py-20 lg:py-32 bg-[#0A1220] relative overflow-hidden">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center max-w-3xl mx-auto mb-20">
                        <div className="inline-block px-4 py-2 border border-[#24344F] bg-[#101C31] text-[#DCE8F7] rounded-full text-xs font-bold tracking-widest uppercase mb-6">Controle Total</div>
                        <h3 className="text-4xl lg:text-5xl font-bold text-white leading-tight mb-6">
                            Dashboard em tempo real.
                        </h3>
                        <p className="text-xl text-[#8FA3C0]">O que o supermercado grande sabe, agora você também sabe. Curva ABC, RFM e DRE — na tela do seu celular.</p>
                    </div>

                    <div className="grid lg:grid-cols-3 gap-6">
                        {[
                            {
                                icon: <Zap className="w-8 h-8 text-[#2E9BFF]" />,
                                title: "Fecha o caixa num toque",
                                description: "Chega de perder venda por falta de troco no caderno. Receba as vendas e feche o turno sem matemática."
                            },
                            {
                                icon: <ShoppingCart className="w-8 h-8 text-[#FF6A5C]" />,
                                title: "Estoque sob controle. Sempre.",
                                description: "Quanto sua loja perde sem controle de validade? Receba alertas de vencimento por lote antes de perder dinheiro."
                            },
                            {
                                icon: <Truck className="w-8 h-8 text-[#6FCBFF]" />,
                                title: "Delivery Integrado",
                                description: "Adicione dados de entrega e taxas de motoboy nas vendas por WhatsApp. Tenha relatórios separados do balcão."
                            },
                            {
                                icon: <TrendingUp className="w-8 h-8 text-emerald-400" />,
                                title: "Curva ABC de Lucro",
                                description: "Entenda quais produtos trazem mais lucro (Curva A) e quais estão encalhados (Curva C)."
                            },
                            {
                                icon: <Globe className="w-8 h-8 text-indigo-400" />,
                                title: "Sincronização em Nuvem",
                                description: "Seu balcão virou central de comando. Acesse os relatórios gerenciais pelo celular ou de casa."
                            },
                            {
                                icon: <DollarSign className="w-8 h-8 text-amber-400" />,
                                title: "Gestão de Fiado",
                                description: "Controle o limite de crédito de clientes e evite prejuízos, acompanhando as contas a receber com facilidade."
                            }
                        ].map((feat, i) => (
                            <motion.div
                                key={i}
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: i * 0.1 }}
                                className="bg-[#101C31] p-8 rounded-[16px] border border-[#24344F] hover:border-[#2E9BFF] transition-all group"
                            >
                                <div className="mb-6">{feat.icon}</div>
                                <h4 className="text-xl font-bold text-white mb-3">{feat.title}</h4>
                                <p className="text-[#8FA3C0] text-sm leading-relaxed">{feat.description}</p>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* PRICING SECTION - SÉRIO E JUSTO */}
            <section id="pricing" className="py-24 bg-[#101C31] border-t border-[#24344F]">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center max-w-3xl mx-auto mb-16">
                        <h2 className="text-[#8FA3C0] font-bold tracking-[1.5px] text-xs uppercase mb-4">Investimento</h2>
                        <h3 className="text-4xl lg:text-5xl font-bold text-white mb-6">Tecnologia de gigante pelo preço de bairro.</h3>
                        <p className="text-xl text-[#8FA3C0]">Sério, justo e transparente. Cancele quando quiser.</p>
                    </div>

                    <div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto">
                        {tiers.map((tier, i) => (
                            <motion.div
                                key={i}
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                className={`bg-[#0A1220] rounded-[20px] p-10 border ${tier.highlight ? 'border-[#2E9BFF] shadow-[0_0_30px_rgba(46,155,255,0.15)] relative' : 'border-[#24344F]'}`}
                            >
                                {tier.highlight && (
                                    <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-[#2E9BFF] text-white px-4 py-1 rounded-full text-xs font-bold uppercase tracking-wide">
                                        Mais Escolhido
                                    </div>
                                )}
                                <h4 className="text-2xl font-bold text-white mb-2">{tier.name}</h4>
                                <p className="text-[#8FA3C0] h-12">{tier.description}</p>
                                
                                <div className="my-8">
                                    <span className="text-5xl font-bold text-white">{tier.price}</span>
                                    <span className="text-[#8FA3C0] ml-2">{tier.period}</span>
                                </div>

                                <ul className="space-y-4 mb-10 min-h-[280px]">
                                    {tier.features.map((feature, idx) => (
                                        <li key={idx} className="flex items-start gap-3">
                                            <Check className={`w-5 h-5 shrink-0 mt-0.5 ${tier.highlight ? 'text-[#2E9BFF]' : 'text-gray-500'}`} />
                                            <span className="text-[#DCE8F7]">{feature}</span>
                                        </li>
                                    ))}
                                </ul>

                                <button
                                    onClick={() => handlePlanSelect(tier)}
                                    className={`w-full py-4 rounded-[10px] font-bold text-lg transition-all ${
                                        tier.highlight 
                                        ? 'bg-gradient-to-r from-[#2E9BFF] to-[#1D4ED8] text-white hover:brightness-110'
                                        : 'bg-transparent border border-[#24344F] text-white hover:bg-[#24344F]'
                                    }`}>
                                    {tier.cta}
                                </button>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* CONTACT SECTION */}
            <section id="contact" className="py-20 lg:py-32 bg-[#0A1220]">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="bg-[#101C31] rounded-[24px] border border-[#24344F] overflow-hidden">
                        <div className="grid lg:grid-cols-2">
                            <div className="p-10 lg:p-16 border-b lg:border-b-0 lg:border-r border-[#24344F]">
                                <h3 className="text-4xl font-bold text-white mb-6">A gente configura tudo pra você começar hoje.</h3>
                                <p className="text-[#8FA3C0] font-medium mb-10 leading-relaxed">
                                    Deixe seus dados e nossa equipe te ajuda a montar a sua base de produtos e notas sem complicação.
                                </p>
                                <div className="space-y-6">
                                    <div className="flex items-center gap-4">
                                        <div className="w-12 h-12 bg-[#0A1220] border border-[#24344F] rounded-xl flex items-center justify-center">
                                            <Phone className="w-5 h-5 text-[#2E9BFF]" />
                                        </div>
                                        <div>
                                            <p className="text-[#8FA3C0] text-xs uppercase tracking-widest">WhatsApp Comercial</p>
                                            <p className="text-lg font-bold text-white">(11) 91988-9233</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        <div className="w-12 h-12 bg-[#0A1220] border border-[#24344F] rounded-xl flex items-center justify-center">
                                            <Mail className="w-5 h-5 text-[#FF6A5C]" />
                                        </div>
                                        <div>
                                            <p className="text-[#8FA3C0] text-xs uppercase tracking-widest">E-mail Comercial</p>
                                            <p className="text-lg font-bold text-white">vendas@mercadinhosys.com.br</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div className="p-10 lg:p-16">
                                <form onSubmit={handleLeadSubmit} className="space-y-5">
                                    <div>
                                        <label className="block text-[#8FA3C0] text-sm font-bold mb-2">Nome Completo</label>
                                        <div className="relative">
                                            <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#8FA3C0]" />
                                            <input required type="text" placeholder="Seu nome" value={leadName} onChange={(e) => setLeadName(e.target.value)}
                                                className="w-full bg-[#0A1220] border border-[#24344F] rounded-[10px] py-3.5 pl-12 pr-4 text-white focus:outline-none focus:border-[#2E9BFF] transition-all"
                                            />
                                        </div>
                                    </div>
                                    <div>
                                        <label className="block text-[#8FA3C0] text-sm font-bold mb-2">E-mail</label>
                                        <div className="relative">
                                            <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#8FA3C0]" />
                                            <input required type="email" placeholder="exemplo@loja.com.br" value={leadEmail} onChange={(e) => setLeadEmail(e.target.value)}
                                                className="w-full bg-[#0A1220] border border-[#24344F] rounded-[10px] py-3.5 pl-12 pr-4 text-white focus:outline-none focus:border-[#2E9BFF] transition-all"
                                            />
                                        </div>
                                    </div>
                                    <div>
                                        <label className="block text-[#8FA3C0] text-sm font-bold mb-2">WhatsApp / Celular</label>
                                        <div className="relative">
                                            <Phone className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#8FA3C0]" />
                                            <input required type="tel" placeholder="(11) 99999-9999" value={leadWhatsApp} onChange={(e) => setLeadWhatsApp(e.target.value)}
                                                className="w-full bg-[#0A1220] border border-[#24344F] rounded-[10px] py-3.5 pl-12 pr-4 text-white focus:outline-none focus:border-[#2E9BFF] transition-all"
                                            />
                                        </div>
                                    </div>
                                    <button type="submit" disabled={loadingLead} className="w-full py-4 bg-gradient-to-r from-[#2E9BFF] to-[#1D4ED8] text-white rounded-[10px] font-bold text-lg hover:brightness-110 transition-all flex items-center justify-center mt-4">
                                        {loadingLead ? <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin"></div> : 'SOLICITAR CONTATO'}
                                    </button>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="py-12 bg-[#0A1220] border-t border-[#24344F]">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex flex-col md:flex-row justify-between items-center gap-6">
                        <div className="flex items-center gap-3">
                            <img src="/assets/logo.png" alt="Logo Footer" className="w-8 h-8 rounded-md" />
                            <span className="text-xl font-bold text-white tracking-tighter">
                                Mercadinho<span className="text-[#FF6A5C]">Sys</span>
                            </span>
                        </div>
                        <div className="flex flex-wrap justify-center gap-6 text-sm font-bold text-[#8FA3C0]">
                            <a href="#features" className="hover:text-[#2E9BFF]">Recursos</a>
                            <a href="#fiscal" className="hover:text-[#2E9BFF]">Fiscal</a>
                            <a href="#pricing" className="hover:text-[#2E9BFF]">Planos</a>
                            <a href="/termos" className="hover:text-[#2E9BFF]">Termos de Uso</a>
                            <a href="/privacidade" className="hover:text-[#2E9BFF]">Privacidade</a>
                            <a href="/login" className="hover:text-[#2E9BFF]">Acesso Cliente</a>
                        </div>
                        <p className="text-[#4F6A8F] text-xs">
                            &copy; {new Date().getFullYear()} MercadinhoSys. Todos os direitos reservados.
                        </p>
                    </div>
                </div>
            </footer>
            
            {/* CONVERSION MODAL */}
            {conversionModalOpen && (
                <div className="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-[#0A1220]/90 backdrop-blur-md overflow-y-auto">
                    <div className="bg-[#101C31] border border-[#24344F] w-full max-w-5xl rounded-[20px] shadow-2xl overflow-hidden relative flex flex-col md:flex-row">
                        <button onClick={() => setConversionModalOpen(false)} className="absolute top-4 right-4 z-10 text-[#8FA3C0] hover:text-white bg-[#0A1220] rounded-full p-2 border border-[#24344F]">
                            <X className="w-5 h-5" />
                        </button>

                        <div className="bg-[#0A1220] border-r border-[#24344F] w-full md:w-5/12 p-10 flex flex-col justify-between">
                            <div>
                                <div className="inline-flex items-center gap-2 px-3 py-1 bg-[#101C31] border border-[#24344F] text-[#DCE8F7] rounded-full text-sm font-bold mb-6">
                                    <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" /> Plano Escolhido
                                </div>
                                <h3 className="text-3xl font-bold text-white mb-2">{selectedPlan?.name}</h3>
                                <div className="flex items-baseline gap-1 mb-8">
                                    <span className="text-4xl font-bold text-[#2E9BFF]">{selectedPlan?.price}</span>
                                    <span className="text-[#8FA3C0]">/mês</span>
                                </div>

                                <ul className="space-y-4 mb-8">
                                    <li className="flex items-start gap-3">
                                        <Check className="w-5 h-5 text-[#2E9BFF] shrink-0 mt-0.5" />
                                        <p className="text-[#DCE8F7] text-sm"><strong>Sem fidelidade.</strong> Cancele quando quiser.</p>
                                    </li>
                                    <li className="flex items-start gap-3">
                                        <Check className="w-5 h-5 text-[#2E9BFF] shrink-0 mt-0.5" />
                                        <p className="text-[#DCE8F7] text-sm"><strong>Preço travado.</strong> O valor não sofrerá reajustes.</p>
                                    </li>
                                    <li className="flex items-start gap-3">
                                        <ShieldCheck className="w-5 h-5 text-[#2E9BFF] shrink-0 mt-0.5" />
                                        <p className="text-[#DCE8F7] text-sm"><strong>Garantia de 7 dias.</strong> Reembolso integral.</p>
                                    </li>
                                </ul>
                            </div>
                        </div>

                        <div className="w-full md:w-7/12 p-10 bg-[#101C31]">
                            <h3 className="text-2xl font-bold text-white mb-2">Quase lá!</h3>
                            <p className="text-[#8FA3C0] mb-8">Crie sua conta para acessar o checkout seguro.</p>

                            <form onSubmit={handleCheckout} className="space-y-5">
                                <div>
                                    <label className="block text-[#8FA3C0] text-sm font-bold mb-2">E-mail de Acesso</label>
                                    <div className="relative">
                                        <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#8FA3C0]" />
                                        <input required type="email" placeholder="seu@email.com" value={onboardingEmail} onChange={(e) => setOnboardingEmail(e.target.value)}
                                            className="w-full bg-[#0A1220] border border-[#24344F] rounded-[10px] py-3.5 pl-12 pr-4 text-white focus:outline-none focus:border-[#2E9BFF]"
                                        />
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-[#8FA3C0] text-sm font-bold mb-2">WhatsApp</label>
                                    <div className="relative">
                                        <Phone className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#8FA3C0]" />
                                        <input required type="tel" placeholder="(11) 99999-9999" value={onboardingWhatsApp} onChange={(e) => setOnboardingWhatsApp(e.target.value)}
                                            className="w-full bg-[#0A1220] border border-[#24344F] rounded-[10px] py-3.5 pl-12 pr-4 text-white focus:outline-none focus:border-[#2E9BFF]"
                                        />
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-[#8FA3C0] text-sm font-bold mb-2">Nome do Estabelecimento</label>
                                    <div className="relative">
                                        <ShoppingCart className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#8FA3C0]" />
                                        <input required type="text" placeholder="Ex: Mercadinho São José" value={onboardingStoreName} onChange={(e) => setOnboardingStoreName(e.target.value)}
                                            className="w-full bg-[#0A1220] border border-[#24344F] rounded-[10px] py-3.5 pl-12 pr-4 text-white focus:outline-none focus:border-[#2E9BFF]"
                                        />
                                    </div>
                                </div>

                                <div className="pt-4">
                                    <button type="submit" disabled={loadingCheckout} className="w-full py-4 bg-gradient-to-r from-[#2E9BFF] to-[#1D4ED8] text-white rounded-[10px] font-bold text-lg hover:brightness-110 flex items-center justify-center gap-3">
                                        {loadingCheckout ? 'Preparando Checkout...' : 'Continuar para Pagamento'}
                                        {!loadingCheckout && <ArrowRight className="w-5 h-5" />}
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default LandingPage;
