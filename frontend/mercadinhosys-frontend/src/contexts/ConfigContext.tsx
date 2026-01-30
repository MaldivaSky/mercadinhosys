import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { settingsService, Configuracao } from '../features/settings/settingsService';
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
        }

        // Aplicar tema escuro
        if (config.tema_escuro) {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
    };

    const loadConfig = async () => {
        try {
            setLoading(true);
            const response = await settingsService.getConfiguracoes();
            if (response.success && response.config) {
                setConfig(response.config);
            }
        } catch (error) {
            console.error('Erro ao carregar configurações:', error);
            toast.error('Erro ao carregar configurações do sistema');
        } finally {
            setLoading(false);
        }
    };

    const updateConfig = async (newConfig: Partial<Configuracao>) => {
        try {
            const response = await settingsService.updateConfiguracoes(newConfig);
            if (response.success && response.config) {
                setConfig(response.config);
                toast.success('Configurações atualizadas com sucesso!');
            }
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
