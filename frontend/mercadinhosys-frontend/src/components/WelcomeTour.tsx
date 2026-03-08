import React, { useState, useEffect } from 'react';
import { X, ChevronRight, CheckCircle, Info } from 'lucide-react';

interface TourStep {
    target: string;
    title: string;
    content: string;
    position: 'top' | 'bottom' | 'left' | 'right' | 'center';
}

const TOUR_STEPS: TourStep[] = [
    {
        target: 'body',
        title: '🌟 Bem-vindo ao MercadinhoSys!',
        content: 'Estamos muito felizes em ter você conosco. Vamos fazer um tour rápido pelas ferramentas que vão transformar seu negócio?',
        position: 'center'
    },
    {
        target: '#nav-pdv',
        title: '💰 Ponto de Venda (PDV)',
        content: 'Aqui é onde a mágica acontece. Nosso PDV é ultra-rápido e funciona até mesmo com oscilações de internet.',
        position: 'bottom'
    },
    {
        target: '#nav-estoque',
        title: '📦 Gestão de Estoque',
        content: 'Cadastre seus produtos, controle validades e receba alertas automáticos de estoque baixo.',
        position: 'right'
    },
    {
        target: '#nav-financeiro',
        title: '📊 Financeiro Inteligente',
        content: 'Acompanhe seu lucro real, fluxo de caixa e despesas de forma automatizada.',
        position: 'right'
    },
    {
        target: 'body',
        title: '🚀 Tudo Pronto!',
        content: 'Agora é com você. Boas vendas e conte conosco para o que precisar!',
        position: 'center'
    }
];

const WelcomeTour: React.FC = () => {
    const [currentStep, setCurrentStep] = useState(-1);
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        // Verifica se é o primeiro acesso (localStorage)
        const hasSeenTour = localStorage.getItem('has_seen_welcome_tour');
        const user = JSON.parse(localStorage.getItem('user_data') || '{}');

        // Só mostra se for o primeiro acesso e NÃO for o Super Admin
        if (!hasSeenTour && user.id && !user.is_super_admin) {
            setTimeout(() => {
                setIsVisible(true);
                setCurrentStep(0);
            }, 2000);
        }
    }, []);

    const handleNext = () => {
        if (currentStep < TOUR_STEPS.length - 1) {
            setCurrentStep(currentStep + 1);
        } else {
            handleClose();
        }
    };

    const handleClose = () => {
        setIsVisible(false);
        localStorage.setItem('has_seen_welcome_tour', 'true');
    };

    if (!isVisible || currentStep === -1) return null;

    const step = TOUR_STEPS[currentStep];

    return (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 backdrop-blur-sm transition-all">
            <div className={`bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full border border-indigo-100 transform transition-all scale-100`}>
                <div className="flex items-start justify-between mb-4">
                    <div className="p-3 bg-indigo-50 rounded-xl text-indigo-600">
                        {currentStep === TOUR_STEPS.length - 1 ? <CheckCircle size={32} /> : <Info size={32} />}
                    </div>
                    <button onClick={handleClose} className="text-gray-400 hover:text-gray-600 transition-colors">
                        <X size={24} />
                    </button>
                </div>

                <div className="space-y-4">
                    <h2 className="text-2xl font-bold text-gray-900">{step.title}</h2>
                    <p className="text-gray-600 leading-relaxed">
                        {step.content}
                    </p>
                </div>

                <div className="mt-8 flex items-center justify-between">
                    <div className="flex gap-1">
                        {TOUR_STEPS.map((_, i) => (
                            <div
                                key={i}
                                className={`h-1.5 rounded-full transition-all ${i === currentStep ? 'w-6 bg-indigo-600' : 'w-1.5 bg-gray-200'}`}
                            />
                        ))}
                    </div>

                    <button
                        onClick={handleNext}
                        className="flex items-center gap-2 bg-indigo-600 text-white px-6 py-2.5 rounded-xl font-semibold hover:bg-indigo-700 transition-all hover:shadow-lg active:scale-95"
                    >
                        {currentStep === TOUR_STEPS.length - 1 ? 'Começar Agora!' : 'Entendi'}
                        {currentStep < TOUR_STEPS.length - 1 && <ChevronRight size={18} />}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default WelcomeTour;
