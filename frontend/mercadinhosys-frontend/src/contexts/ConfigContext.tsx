import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import settingsService, { Configuracao } from '../features/settings/settingsService';
import { toast } from 'react-hot-toast';

interface ConfigContextType {
    config: Configuracao | null;
    loading: boolean;
    updateConfig: (newConfig: Partial<Configuracao>) => Promise<void>;
    refreshConfig: () => Promise<void>;
    applyTheme: () => void;
}

const ConfigContext = createContext<ConfigContextType | undefined>(undefined);

export const ConfigProvider = ({ children }: { children: ReactNode }) => {
    const [config, setConfig] = useState<Configuracao | null>(null);
    const [loading, setLoading] = useState(true);

    const applyTheme = () => {
        if (!config) return;

        const root = document.documentElement;
        
        // Aplicar cor principal
        if (config.cor_principal) {
            root.style.setProperty('--color-primary', config.cor_principal);
            
            // Gerar variações da cor principal
            const hex = config.cor_principal.replace('#', '');
            const r = parseInt(hex.substring(0, 2), 16);
            const g = parseInt(hex.substring(2, 4), 16);
            const b = parseInt(hex.substring(4, 6), 16);
            
            // Cor mais escura (hover)
            root.style.setProperty('--color-primary-dark', `rgb(${Math.max(0, r - 30)}, ${Math.max(0, g - 30)}, ${Math.max(0, b - 30)})`);
            
            // Cor mais clara (backgrounds)
            root.style.setProperty('--color-primary-light', `rgba(${r}, ${g}, ${b}, 0.1)`);
            
            // Aplicar em elementos específicos
            const buttons = document.querySelectorAll('.btn-primary, button[class*="bg-blue"], button[class*="bg-primary"]');
            buttons.forEach((btn) => {
                (btn as HTMLElement).style.backgroundColor = config.cor_principal;
            });
        }

        // Aplicar tema escuro
        if (config.tema_escuro) {
            document.documentElement.classList.add('dark');
            localStorage.setItem('theme', 'dark');
        } else {
            document.documentElement.classList.remove('dark');
            localStorage.setItem('theme', 'light');
        }
    };

    const loadConfig = async () => {
        try {
            setLoading(true);
            
            // Verificar se tem token antes de tentar carregar
            const token = localStorage.getItem('access_token');
            if (!token) {
                console.log('Sem token, usando configurações padrão');
                setConfig({
                    id: 0,
                    estabelecimento_id: 1,
                    cor_principal: '#2563eb',
                    tema_escuro: false,
                    logo_url: undefined,
                    emitir_nfe: false,
                    emitir_nfce: true,
                    impressao_automatica: false,
                    tipo_impressora: 'termica_80mm',
                    exibir_preco_tela: true,
                    permitir_venda_sem_estoque: false,
                    desconto_maximo_percentual: 10,
                    desconto_maximo_funcionario: 10,
                    arredondamento_valores: true,
                    formas_pagamento: ['Dinheiro', 'Cartão de Crédito', 'Cartão de Débito', 'PIX'],
                    controlar_validade: true,
                    alerta_estoque_minimo: true,
                    dias_alerta_validade: 30,
                    estoque_minimo_padrao: 10,
                    tempo_sessao_minutos: 30,
                    tentativas_senha_bloqueio: 3,
                    alertas_email: false,
                    alertas_whatsapp: false
                });
                setLoading(false);
                return;
            }

            const response = await settingsService.getConfig();
            setConfig(response);
        } catch (error) {
            console.error('Erro ao carregar configurações:', error);
            // Usar configurações padrão em caso de erro
            setConfig({
                id: 0,
                estabelecimento_id: 1,
                cor_principal: '#2563eb',
                tema_escuro: false,
                logo_url: undefined,
                emitir_nfe: false,
                emitir_nfce: true,
                impressao_automatica: false,
                tipo_impressora: 'termica_80mm',
                exibir_preco_tela: true,
                permitir_venda_sem_estoque: false,
                desconto_maximo_percentual: 10,
                desconto_maximo_funcionario: 10,
                arredondamento_valores: true,
                formas_pagamento: ['Dinheiro', 'Cartão de Crédito', 'Cartão de Débito', 'PIX'],
                controlar_validade: true,
                alerta_estoque_minimo: true,
                dias_alerta_validade: 30,
                estoque_minimo_padrao: 10,
                tempo_sessao_minutos: 30,
                tentativas_senha_bloqueio: 3,
                alertas_email: false,
                alertas_whatsapp: false
            });
        } finally {
            setLoading(false);
        }
    };

    const updateConfig = async (newConfig: Partial<Configuracao>) => {
        try {
            const response = await settingsService.updateConfig(newConfig);
            setConfig(response);
            toast.success('Configurações atualizadas com sucesso!');
            
            // Forçar aplicação do tema imediatamente
            setTimeout(() => {
                applyTheme();
            }, 100);
        } catch (error) {
            console.error('Erro ao atualizar configurações:', error);
            toast.error('Erro ao atualizar configurações');
            throw error;
        }
    };

    const refreshConfig = async () => {
        await loadConfig();
    };

    useEffect(() => {
        loadConfig();
    }, []);

    useEffect(() => {
        applyTheme();
    }, [config]);

    return (
        <ConfigContext.Provider value={{ config, loading, updateConfig, refreshConfig, applyTheme }}>
            {children}
        </ConfigContext.Provider>
    );
};

export const useConfig = () => {
    const context = useContext(ConfigContext);
    if (!context) {
        throw new Error('useConfig must be used within ConfigProvider');
    }
    return context;
};
