import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
    CheckCircle,
    ShoppingCart,
    BarChart3,
    Users,
    Zap,
    ShieldCheck,
    TrendingUp,
    ArrowRight,
    LayoutDashboard,
    Globe
} from 'lucide-react';

const LandingPage: React.FC = () => {
    const navigate = useNavigate();

    const tiers = [
        {
            name: 'Básico',
            price: 'R$ 97',
            period: '/mês',
            description: 'Ideal para pequenos negócios e MEIs começando agora.',
            features: [
                'Até 500 produtos',
                'PDV Completo',
                'Controle de Estoque Básico',
                'Relatórios Mensais',
                'Suporte via Email'
            ],
            cta: 'Começar Agora',
            highlight: false
        },
        {
            name: 'Profissional',
            price: 'R$ 197',
            period: '/mês',
            description: 'Para comércios em expansão que precisam de inteligência.',
            features: [
                'Produtos Ilimitados',
                'Dashboard Científico',
                'Gestão de Funcionários & RH',
                'Previsão de Demanda (IA)',
                'Suporte Prioritário'
            ],
            cta: 'Escolher Plano Profissional',
            highlight: true
        },
        {
            name: 'Premium',
            price: 'Sob Consulta',
            period: '',
            description: 'Solução completa para redes de lojas e grandes operações.',
            features: [
                'Multi-lojas (Multitenancy)',
                'Personalização Total',
                'API de Integração',
                'Gerente de Conta Dedicado',
                'Treinamento Presencial'
            ],
            cta: 'Falar com Consultor',
            highlight: false
        }
    ];

    return (
        <div className="min-h-screen bg-white text-gray-900 font-sans selection:bg-blue-100 selection:text-blue-900 overflow-x-hidden">
            {/* Header / Navbar */}
            <nav className="fixed top-0 w-full z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center h-20">
                        <div className="flex items-center gap-2">
                            <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-200">
                                <LayoutDashboard className="text-white w-6 h-6" />
                            </div>
                            <span className="text-2xl font-black text-gray-900 tracking-tight">
                                Mercadinho<span className="text-blue-600">Sys</span>
                            </span>
                        </div>
                        <div className="hidden md:flex items-center gap-8">
                            <a href="#features" className="text-sm font-semibold text-gray-600 hover:text-blue-600 transition-colors">Funcionalidades</a>
                            <a href="#pricing" className="text-sm font-semibold text-gray-600 hover:text-blue-600 transition-colors">Preços</a>
                            <a href="#about" className="text-sm font-semibold text-gray-600 hover:text-blue-600 transition-colors">Sobre</a>
                            <button
                                onClick={() => navigate('/login')}
                                className="px-6 py-2.5 bg-blue-600 text-white rounded-full font-bold text-sm hover:bg-blue-700 transition-all shadow-lg shadow-blue-200 hover:scale-105 active:scale-95"
                            >
                                Acessar Painel
                            </button>
                        </div>
                        <div className="md:hidden">
                            <button onClick={() => navigate('/login')} className="text-blue-600 font-bold text-sm">Entrar</button>
                        </div>
                    </div>
                </div>
            </nav>

            {/* Hero Section */}
            <section className="relative pt-32 pb-20 md:pt-48 md:pb-32 overflow-hidden">
                {/* Background Decor */}
                <div className="absolute top-0 right-0 -z-10 w-[800px] h-[800px] bg-blue-50 rounded-full blur-3xl translate-x-1/2 -translate-y-1/2 opacity-60"></div>
                <div className="absolute bottom-0 left-0 -z-10 w-[600px] h-[600px] bg-indigo-50 rounded-full blur-3xl -translate-x-1/2 translate-y-1/2 opacity-60"></div>

                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
                    <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-blue-50 text-blue-600 font-bold text-xs mb-8 animate-bounce">
                        <Zap className="w-4 h-4" />
                        NOVA VERSÃO 2.0 DISPONÍVEL
                    </div>
                    <h1 className="text-5xl md:text-7xl font-extrabold text-gray-900 tracking-tight leading-[1.1] mb-8">
                        O ERP que transforma seu <br className="hidden md:block" />
                        <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent italic">negócio em inteligência.</span>
                    </h1>
                    <p className="max-w-2xl mx-auto text-xl text-gray-600 leading-relaxed mb-12 font-medium">
                        Gestão de estoque, PDV ultra-rápido e análise preditiva de lucros.
                        Tudo o que seu mercadinho precisa para crescer profissionalmente.
                    </p>
                    <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                        <button
                            onClick={() => navigate('/login')}
                            className="w-full sm:w-auto px-10 py-5 bg-blue-600 text-white rounded-2xl font-bold text-lg hover:bg-blue-700 transition-all shadow-2xl shadow-blue-200 hover:-translate-y-1"
                        >
                            Começar Demo Grátis
                        </button>
                        <button className="w-full sm:w-auto px-10 py-5 bg-white text-blue-600 border-2 border-blue-100 rounded-2xl font-bold text-lg hover:border-blue-600 transition-all">
                            Ver Funcionalidades
                        </button>
                    </div>

                    {/* Mockup Preview */}
                    <div className="mt-20 relative px-4 md:px-12">
                        <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-[2rem] blur opacity-20"></div>
                        <div className="relative bg-white border border-gray-100 rounded-[2rem] shadow-2xl overflow-hidden">
                            <img
                                src="https://images.unsplash.com/photo-1556742044-3c52d6e88c62?auto=format&fit=crop&q=80&w=1200"
                                alt="ERP Dashboard Preview"
                                className="w-full h-auto object-cover opacity-90 hover:scale-105 transition-transform duration-700"
                            />
                            {/* Overlay UI elements can be added here with absolute positioning */}
                        </div>
                    </div>
                </div>
            </section>

            {/* Features Grid */}
            <section id="features" className="py-24 bg-gray-50">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-16">
                        <h2 className="text-blue-600 font-black tracking-widest text-sm uppercase mb-3">Vantagens Competitivas</h2>
                        <h3 className="text-4xl md:text-5xl font-extrabold text-gray-900 tracking-tight">Muito além de um simples caixa.</h3>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {[
                            {
                                icon: <ShoppingCart className="w-8 h-8 text-blue-600" />,
                                title: "PDV Offline & Rápido",
                                description: "Interface intuitiva inspirada nos maiores varejistas. Funciona até com oscilações de internet."
                            },
                            {
                                icon: <BarChart3 className="w-8 h-8 text-indigo-600" />,
                                title: "Análise de Faturamento",
                                description: "Curva ABC, ROI e Ticket Médio calculados em tempo real para sua tomada de decisão."
                            },
                            {
                                icon: <Zap className="w-8 h-8 text-amber-500" />,
                                title: "Cadastro Inteligente",
                                description: "Bipou, cadastrou. Integração com API Cosmos para puxar dados de mais de 1 milhão de produtos."
                            },
                            {
                                icon: <Users className="w-8 h-8 text-emerald-600" />,
                                title: "Gestão de RH Completa",
                                description: "Controle de ponto individual, holerites e gestão de escalas nativa no sistema."
                            },
                            {
                                icon: <ShieldCheck className="w-8 h-8 text-red-600" />,
                                title: "Segurança Bancária",
                                description: "Dados criptografados e backups diários automáticos em nuvem de alta disponibilidade."
                            },
                            {
                                icon: <Globe className="w-8 h-8 text-cyan-600" />,
                                title: "Acesso de Qualquer Lugar",
                                description: "Monitore sua loja pelo celular, tablet ou computador, onde quer que você esteja."
                            }
                        ].map((feature, idx) => (
                            <div key={idx} className="bg-white p-10 rounded-[2.5rem] border border-gray-100 hover:shadow-xl transition-all group hover:-translate-y-2">
                                <div className="mb-6 p-4 bg-gray-50 rounded-2xl w-fit group-hover:scale-110 transition-transform">
                                    {feature.icon}
                                </div>
                                <h4 className="text-2xl font-bold text-gray-900 mb-4">{feature.title}</h4>
                                <p className="text-gray-600 leading-relaxed font-medium">{feature.description}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Pricing Section */}
            <section id="pricing" className="py-24">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-16">
                        <h2 className="text-blue-600 font-black tracking-widest text-sm uppercase mb-3">Planos e Preços</h2>
                        <h3 className="text-4xl md:text-5xl font-extrabold text-gray-900 tracking-tight">O investimento que se paga em lucros.</h3>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        {tiers.map((tier, idx) => (
                            <div
                                key={idx}
                                className={`relative p-10 rounded-[3rem] border-2 transition-all hover:shadow-2xl flex flex-col ${tier.highlight
                                        ? 'border-blue-600 bg-white scale-105 z-10'
                                        : 'border-gray-100 bg-white'
                                    }`}
                            >
                                {tier.highlight && (
                                    <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-blue-600 text-white px-6 py-1.5 rounded-full text-sm font-black tracking-widest uppercase">
                                        MAIS POPULAR
                                    </div>
                                )}
                                <div className="mb-8">
                                    <h4 className="text-2xl font-black text-gray-900 mb-2">{tier.name}</h4>
                                    <div className="flex items-baseline gap-1 mb-4">
                                        <span className="text-4xl font-black text-gray-900">{tier.price}</span>
                                        <span className="text-gray-500 font-semibold">{tier.period}</span>
                                    </div>
                                    <p className="text-gray-600 font-medium leading-relaxed">{tier.description}</p>
                                </div>
                                <div className="space-y-4 mb-10 flex-1">
                                    {tier.features.map((feature, fIdx) => (
                                        <div key={fIdx} className="flex items-center gap-3">
                                            <CheckCircle className={`w-5 h-5 flex-shrink-0 ${tier.highlight ? 'text-blue-600' : 'text-gray-300'}`} />
                                            <span className="text-gray-700 font-semibold text-sm">{feature}</span>
                                        </div>
                                    ))}
                                </div>
                                <button className={`w-full py-4 rounded-2xl font-black transition-all ${tier.highlight
                                        ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-xl shadow-blue-200'
                                        : 'bg-gray-50 text-gray-900 hover:bg-gray-100'
                                    }`}>
                                    {tier.cta}
                                </button>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Testimonials or Stats */}
            <section className="py-20 bg-blue-600">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-white">
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-12">
                        <div>
                            <p className="text-5xl font-black mb-2">+50k</p>
                            <p className="text-blue-100 font-bold tracking-widest uppercase text-xs">Vendas Processadas</p>
                        </div>
                        <div>
                            <p className="text-5xl font-black mb-2">99.9%</p>
                            <p className="text-blue-100 font-bold tracking-widest uppercase text-xs">Uptime do Sistema</p>
                        </div>
                        <div>
                            <p className="text-5xl font-black mb-2">+1k</p>
                            <p className="text-blue-100 font-bold tracking-widest uppercase text-xs">Lojas Ativas</p>
                        </div>
                        <div>
                            <p className="text-5xl font-black mb-2">24h</p>
                            <p className="text-blue-100 font-bold tracking-widest uppercase text-xs">Suporte Técnico</p>
                        </div>
                    </div>
                </div>
            </section>

            {/* CTA Final */}
            <section className="py-24">
                <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="bg-gradient-to-br from-gray-900 to-blue-900 rounded-[3.5rem] p-12 md:p-20 text-center relative overflow-hidden shadow-2xl">
                        {/* Decor */}
                        <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>

                        <h2 className="text-4xl md:text-6xl font-black text-white mb-8 tracking-tight">
                            Pronto para profissionalizar sua gestão?
                        </h2>
                        <p className="text-xl text-blue-100/80 mb-12 max-w-2xl mx-auto font-medium">
                            Junte-se a centenas de empresários que escolheram o MercadinhoSys para automatizar suas rotinas e focar no que importa: vender mais.
                        </p>
                        <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
                            <button
                                onClick={() => navigate('/login')}
                                className="w-full sm:w-auto px-10 py-5 bg-white text-blue-900 rounded-2xl font-black text-lg hover:bg-blue-50 transition-all flex items-center justify-center gap-2"
                            >
                                Criar Minha Conta Grátis
                                <ArrowRight className="w-5 h-5" />
                            </button>
                            <p className="text-blue-200/60 font-medium italic">
                                Sem cartão de crédito necessário
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="py-12 border-t border-gray-100">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row justify-between items-center gap-8">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                            <LayoutDashboard className="text-white w-5 h-5" />
                        </div>
                        <span className="text-xl font-black text-gray-900 tracking-tight">
                            Mercadinho<span className="text-blue-600">Sys</span>
                        </span>
                    </div>
                    <p className="text-gray-500 font-medium text-sm">
                        &copy; {new Date().getFullYear()} MercadinhoSys S.A. Todos os direitos reservados.
                    </p>
                    <div className="flex gap-6">
                        <a href="#" className="text-gray-400 hover:text-blue-600 transition-colors"><Globe className="w-6 h-6" /></a>
                        <a href="#" className="text-gray-400 hover:text-blue-600 transition-colors"><ShieldCheck className="w-6 h-6" /></a>
                        <a href="#" className="text-gray-400 hover:text-blue-600 transition-colors"><TrendingUp className="w-6 h-6" /></a>
                    </div>
                </div>
            </footer>
        </div>
    );
};

export default LandingPage;
