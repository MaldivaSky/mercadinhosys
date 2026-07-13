import React, { useState, useEffect } from 'react';
import { Joyride, STATUS } from 'react-joyride';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';
import { Play } from 'lucide-react';

const TourExecutivo: React.FC = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const { user } = useAuth();
    
    const [run, setRun] = useState(false);
    const [stepIndex, setStepIndex] = useState(0);
    const [showWelcome, setShowWelcome] = useState(false);

    // Evita incomodar o Seed Admin ou quem já fez
    useEffect(() => {
        if (!user) return;
        const hasSeenTour = localStorage.getItem(`mercadinhosys_tour_${user.id}`);
        if (!hasSeenTour) {
            // Usa timeout zero para evitar warning de cascading render no strict mode
            setTimeout(() => setShowWelcome(true), 0);
        }
    }, [user]);

    const handleSkipAll = () => {
        if (user) localStorage.setItem(`mercadinhosys_tour_${user.id}`, 'true');
        setShowWelcome(false);
        setRun(false);
    };

    const handleStartTour = () => {
        if (user) localStorage.setItem(`mercadinhosys_tour_${user.id}`, 'true');
        setShowWelcome(false);
        setStepIndex(0);
        setRun(true);
    };

    const steps: any[] = [
        {
            target: 'body',
            placement: 'center',
            content: (
                <div className="text-left">
                    <div className="w-16 h-16 mb-4 mx-auto">
                        <img src="/logo_alternativa.png" alt="Logo" className="w-full h-full object-contain" />
                    </div>
                    <h3 className="text-xl font-bold mb-2">Bem-vindo ao Nível Executivo!</h3>
                    <p className="text-gray-600 mb-4 text-sm">Este tour vai te mostrar como dominar a ferramenta. Você pode pular qualquer etapa a qualquer momento.</p>
                </div>
            ),
            disableBeacon: true,
        },
        {
            target: '.tour-indicadores',
            content: (
                <div className="text-left">
                    <h3 className="text-lg font-bold mb-1 text-blue-600">Visão de Águia (Dashboard)</h3>
                    <p className="text-sm">Controle sua Receita e descubra na hora quem é o seu Maior Devedor. Inteligência pura de fluxo de caixa.</p>
                </div>
            ),
            placement: 'bottom',
            route: '/dashboard'
        },
        {
            target: '.tour-produtos-upload',
            content: (
                <div className="text-left">
                    <h3 className="text-lg font-bold mb-1 text-blue-600">Importação de Estoque</h3>
                    <p className="text-sm">Não sofra digitando. Arraste sua planilha do Excel aqui e cadastre milhares de produtos em segundos.</p>
                </div>
            ),
            placement: 'bottom',
            route: '/products'
        },
        {
            target: '.tour-clientes-upload',
            content: (
                <div className="text-left">
                    <h3 className="text-lg font-bold mb-1 text-blue-600">Migração do Fiado (Clientes)</h3>
                    <p className="text-sm">Traga a lista de clientes com o saldo devedor deles. O sistema gera automaticamente as contas a receber. Adeus caderninho!</p>
                </div>
            ),
            placement: 'bottom',
            route: '/customers'
        },
        {
            target: '.tour-pdv-leitor',
            content: (
                <div className="text-left">
                    <h3 className="text-lg font-bold mb-1 text-blue-600">O Coração da Loja (PDV)</h3>
                    <p className="text-sm">Bipe rápido. Funciona SEM INTERNET. Suas vendas são sincronizadas sozinhas quando a conexão voltar.</p>
                </div>
            ),
            placement: 'bottom',
            route: '/pdv'
        },
        {
            target: '.tour-vendas-historico',
            content: (
                <div className="text-left">
                    <h3 className="text-lg font-bold mb-1 text-blue-600">Histórico de Vendas</h3>
                    <p className="text-sm">Audite cada cupom emitido, cancele vendas erradas e reimprima comprovantes com 1 clique.</p>
                </div>
            ),
            placement: 'bottom',
            route: '/sales'
        },
        {
            target: '.tour-delivery-visao',
            content: (
                <div className="text-left">
                    <h3 className="text-lg font-bold mb-1 text-blue-600">Gestão de Entregas (Delivery)</h3>
                    <p className="text-sm">Controle os pedidos do WhatsApp, atribua motoristas e monitore as rotas até a casa do cliente.</p>
                </div>
            ),
            placement: 'bottom',
            route: '/delivery'
        },
        {
            target: '.tour-despesas-add',
            content: (
                <div className="text-left">
                    <h3 className="text-lg font-bold mb-1 text-blue-600">Saúde Financeira (Despesas)</h3>
                    <p className="text-sm">Lance todas as contas do mercado (Luz, Água, Fornecedores). Saiba exatamente para onde seu dinheiro vai.</p>
                </div>
            ),
            placement: 'bottom',
            route: '/expenses'
        },
        {
            target: '.tour-compras-visao',
            content: (
                <div className="text-left">
                    <h3 className="text-lg font-bold mb-1 text-blue-600">Gestão de Compras</h3>
                    <p className="text-sm">Faça pedidos aos seus fornecedores, controle prazos de entrega e reabasteça seu estoque sem rupturas.</p>
                </div>
            ),
            placement: 'bottom',
            route: '/compras'
        },
        {
            target: '.tour-relatorios-visao',
            content: (
                <div className="text-left">
                    <h3 className="text-lg font-bold mb-1 text-blue-600">Relatórios Estratégicos</h3>
                    <p className="text-sm">Fechamento de caixa, DRE gerencial, curvas ABC e tudo que você precisa para a contabilidade.</p>
                </div>
            ),
            placement: 'bottom',
            route: '/reports'
        },
        {
            target: '.tour-rh-visao',
            content: (
                <div className="text-left">
                    <h3 className="text-lg font-bold mb-1 text-blue-600">Gestão de Pessoas (RH)</h3>
                    <p className="text-sm">Administre seus funcionários, salários, vales e controle totalmente a sua equipe.</p>
                </div>
            ),
            placement: 'bottom',
            route: '/rh'
        },
        {
            target: '.tour-ponto-bater',
            content: (
                <div className="text-left">
                    <h3 className="text-lg font-bold mb-1 text-blue-600">Controle de Ponto Seguro</h3>
                    <p className="text-sm">Seus funcionários batem o ponto com foto e GPS geolocalizado. Segurança jurídica para o dono da loja.</p>
                </div>
            ),
            placement: 'bottom',
            route: '/ponto'
        }
    ];

    const handleJoyrideCallback = (data: any) => {
        const { action, index, status, type } = data;
        
        // Finaliza o tour se o usuário fechou ou pulou
        if (status === STATUS.FINISHED || status === STATUS.SKIPPED) {
            setRun(false);
            return;
        }

        // Navegação síncrona
        if (type === 'step:after' && action === 'next') {
            const nextIndex = index + 1;
            if (steps[nextIndex] && (steps[nextIndex] as any).route) {
                const nextRoute = (steps[nextIndex] as any).route;
                if (location.pathname !== nextRoute) {
                    navigate(nextRoute);
                    // Damos um tempo minúsculo para a rota renderizar e os elementos aparecerem no DOM
                    setTimeout(() => {
                        setStepIndex(nextIndex);
                    }, 400); 
                    return;
                }
            }
            setStepIndex(nextIndex);
        } else if (type === 'step:after' && action === 'prev') {
            const prevIndex = index - 1;
            if (steps[prevIndex] && (steps[prevIndex] as any).route) {
                const prevRoute = (steps[prevIndex] as any).route;
                if (location.pathname !== prevRoute) {
                    navigate(prevRoute);
                    setTimeout(() => {
                        setStepIndex(prevIndex);
                    }, 400);
                    return;
                }
            }
            setStepIndex(prevIndex);
        }
    };

    return (
        <>
            <AnimatePresence>
                {showWelcome && (
                    <motion.div 
                        initial={{ opacity: 0, y: 50 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 50 }}
                        className="fixed bottom-4 left-4 right-4 sm:left-auto sm:right-6 sm:bottom-6 z-[9999] bg-white dark:bg-slate-800 shadow-2xl rounded-2xl p-5 sm:p-6 border border-gray-200 dark:border-slate-700 sm:w-80"
                    >
                        <div className="flex items-center gap-3 mb-4">
                            <img src="/logo_alternativa.png" alt="Logo" className="w-8 h-8 object-contain" />
                            <h4 className="font-bold text-gray-900 dark:text-white">Bem-vindo(a) CEO!</h4>
                        </div>
                        <p className="text-sm text-gray-600 dark:text-gray-300 mb-6">
                            Quer fazer um Tour Rápido para conhecer o poder de controle do sistema?
                        </p>
                        <div className="flex flex-col gap-2">
                            <button 
                                onClick={handleStartTour}
                                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg flex items-center justify-center gap-2 transition-colors"
                            >
                                <Play className="w-4 h-4" /> Iniciar Tour Profissional
                            </button>
                            <button 
                                onClick={handleSkipAll}
                                className="w-full bg-gray-100 hover:bg-gray-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-gray-700 dark:text-gray-200 font-medium py-2 px-4 rounded-lg transition-colors"
                            >
                                Pular (Já conheço)
                            </button>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            <Joyride
                steps={steps}
                run={run}
                stepIndex={stepIndex}
                continuous
                hideCloseButton={false}
                scrollToFirstStep
                callback={handleJoyrideCallback}
                locale={{
                    back: 'Voltar',
                    close: 'Fechar',
                    last: 'Finalizar',
                    next: 'Próximo',
                    skip: 'Pular esta etapa'
                }}
                styles={{
                    options: {
                        primaryColor: '#2563eb',
                        textColor: '#1f2937',
                        zIndex: 10000,
                        arrowColor: '#ffffff',
                    },
                    tooltip: {
                        borderRadius: '16px',
                        padding: '20px',
                        width: 'calc(100vw - 32px)',
                        maxWidth: '400px',
                        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
                    },
                    tooltipContainer: {
                        textAlign: 'left',
                    },
                    buttonSkip: {
                        color: '#6b7280',
                        fontSize: '14px',
                        padding: '10px 15px',
                        borderRadius: '8px',
                    },
                    buttonNext: {
                        backgroundColor: '#2563eb',
                        fontWeight: 'bold',
                        padding: '10px 20px',
                        borderRadius: '8px',
                    },
                    buttonBack: {
                        color: '#4b5563',
                        marginRight: '10px',
                    }
                } as any}
            />
        </>
    );
};

export default TourExecutivo;
