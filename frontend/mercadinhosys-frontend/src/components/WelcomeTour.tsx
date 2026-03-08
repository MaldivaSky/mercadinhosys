import React, { useState, useEffect } from 'react';
import {
    X,
    ChevronRight,
    ChevronLeft,
    ShoppingBag,
    Package,
    LayoutDashboard,
    Settings,
    Rocket
} from 'lucide-react';

interface TourStep {
    title: string;
    description: string;
    targetId: string;
    icon: React.ReactNode;
    position: 'top' | 'bottom' | 'left' | 'right';
}

const steps: TourStep[] = [
    {
        title: "Bem-vindo ao Futuro!",
        description: "Olá! Este é o seu novo painel de controle inteligente. Vamos fazer um tour de 30 segundos para você dominar sua loja?",
        targetId: 'dashboard-main',
        icon: <Rocket className="text-indigo-600" size={24} />,
        position: 'bottom'
    },
    {
        title: "Seu Faturamento em Tempo Real",
        description: "Aqui você acompanha quanto vendeu hoje, seu lucro e a margem bruta. Tudo atualizado no momento da venda.",
        targetId: 'kpi-cards',
        icon: <LayoutDashboard className="text-blue-600" size={24} />,
        position: 'bottom'
    },
    {
        title: "O Coração do Negócio: Vendas",
        description: "Clique aqui para abrir o PDV. É o checkout mais rápido do mercado, integrado com seu estoque e financeiro.",
        targetId: 'nav-vendas',
        icon: <ShoppingBag className="text-green-600" size={24} />,
        position: 'right'
    },
    {
        title: "Gestão de Estoque Inteligente",
        description: "Cadastre produtos, controle validade e receba alertas de reposição automática para nunca perder uma venda.",
        targetId: 'nav-produtos',
        icon: <Package className="text-orange-600" size={24} />,
        position: 'right'
    },
    {
        title: "Personalize sua Marca",
        description: "Configure seu logotipo, dados da empresa e regras de negócio para que o sistema fique com a cara da sua loja.",
        targetId: 'nav-configuracoes',
        icon: <Settings className="text-gray-600" size={24} />,
        position: 'right'
    }
];

const WelcomeTour: React.FC = () => {
    const [currentStep, setCurrentStep] = useState(0);
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        // Verifica se é o primeiro acesso
        const hasSeenTour = localStorage.getItem('mercadinhosys_tour_seen');
        if (!hasSeenTour) {
            const timer = setTimeout(() => setIsVisible(true), 2000); // 2 segundos após carregar
            return () => clearTimeout(timer);
        }
    }, []);

    const handleNext = () => {
        if (currentStep < steps.length - 1) {
            setCurrentStep(currentStep + 1);
        } else {
            completeTour();
        }
    };

    const handlePrev = () => {
        if (currentStep > 0) {
            setCurrentStep(currentStep - 1);
        }
    };

    const completeTour = () => {
        localStorage.setItem('mercadinhosys_tour_seen', 'true');
        setIsVisible(false);
    };

    if (!isVisible) return null;

    const step = steps[currentStep];

    return (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center pointer-events-none">
            <div className="absolute inset-0 bg-black/40 backdrop-blur-sm pointer-events-auto" onClick={completeTour} />

            <div className="relative w-full max-w-md bg-white rounded-[2rem] shadow-2xl p-8 animate-in zoom-in-95 duration-300 border border-white/20 pointer-events-auto">
                <button
                    onClick={completeTour}
                    className="absolute top-6 right-6 p-2 text-gray-400 hover:text-gray-600 transition-colors"
                >
                    <X size={20} />
                </button>

                <div className="flex flex-col items-center text-center space-y-6">
                    <div className="p-4 bg-indigo-50 rounded-2xl shadow-inner mb-2">
                        {step.icon}
                    </div>

                    <div className="space-y-3">
                        <h3 className="text-xl font-black text-gray-900 italic tracking-tight">
                            {step.title}
                        </h3>
                        <p className="text-sm text-gray-500 font-medium leading-relaxed">
                            {step.description}
                        </p>
                    </div>

                    {/* Progress dots */}
                    <div className="flex gap-2">
                        {steps.map((_, i) => (
                            <div
                                key={i}
                                className={`h-1.5 rounded-full transition-all duration-300 ${i === currentStep ? 'w-6 bg-indigo-600' : 'w-1.5 bg-gray-200'}`}
                            />
                        ))}
                    </div>

                    <div className="flex w-full gap-3 pt-4">
                        {currentStep > 0 && (
                            <button
                                onClick={handlePrev}
                                className="flex-1 px-6 py-3 border border-gray-200 rounded-2xl text-xs font-black text-gray-400 hover:bg-gray-50 transition-all flex items-center justify-center gap-2"
                            >
                                <ChevronLeft size={16} />
                                ANTERIOR
                            </button>
                        )}
                        <button
                            onClick={handleNext}
                            className="flex-[2] px-6 py-4 bg-indigo-600 text-white rounded-2xl text-xs font-black italic tracking-widest hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-100 flex items-center justify-center gap-2"
                        >
                            {currentStep === steps.length - 1 ? 'VAMOS COMEÇAR!' : 'PRÓXIMO'}
                            <ChevronRight size={18} />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default WelcomeTour;
