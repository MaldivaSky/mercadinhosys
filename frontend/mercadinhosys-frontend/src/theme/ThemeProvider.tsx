// src/theme/ThemeProvider.tsx - Sincronizado com ConfigContext
import { createTheme, ThemeProvider as MuiThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { useMemo, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { ThemeContext } from './ThemeContext';
import { useConfig } from '../contexts/ConfigContext';

interface ThemeProviderProps {
    children: ReactNode;
    defaultMode?: 'dark' | 'light';
}

export function ThemeProvider({ children, defaultMode = 'dark' }: ThemeProviderProps) {
    const { config, preferencias, updatePreferencias } = useConfig();

    // 1. Estado local inicial sincronizado com localStorage (Zero Flicker)
    const [mode, setMode] = useState<'dark' | 'light'>(() => {
        const saved = localStorage.getItem('theme') as 'dark' | 'light' | null;
        if (saved) return saved;
        return defaultMode;
    });

    // 2. Sincronização CONTÍNUA com as preferências do backend (ConfigContext)
    useEffect(() => {
        if (preferencias?.tema_escuro !== undefined) {
            const serverMode = preferencias.tema_escuro ? 'dark' : 'light';

            // Sincroniza o estado local apenas se for diferente do servidor
            // Isso garante que mudanças no SettingsPage reflitam aqui imediatamente
            if (serverMode !== mode) {
                setMode(serverMode);
                localStorage.setItem('theme', serverMode);
            }
        }
    }, [preferencias?.tema_escuro]);

    // 3. Aplicação do tema no document root
    useEffect(() => {
        const root = document.documentElement;
        if (mode === 'dark') {
            root.classList.add('dark');
        } else {
            root.classList.remove('dark');
        }
        localStorage.setItem('theme', mode);
    }, [mode]);

    const toggleTheme = async () => {
        const newMode = mode === 'dark' ? 'light' : 'dark';

        // Atualização UI Real-time (Otimista)
        setMode(newMode);
        localStorage.setItem('theme', newMode);

        try {
            // Sincronizar com o backend
            await updatePreferencias({ tema_escuro: newMode === 'dark' });
        } catch (error) {
            console.error('Erro ao salvar preferência de tema no backend:', error);
            // Mantemos o modo local mesmo se o backend falhar, 
            // para não frustrar o usuário com rollback de UI.
        }
    };

    const theme = useMemo(() => {
        const primaryColor = config?.cor_principal || '#2563eb';
        return createTheme({
            palette: {
                mode,
                primary: {
                    main: primaryColor,
                },
                secondary: {
                    main: mode === 'dark' ? '#ce93d8' : '#10b981',
                },
                background: {
                    default: mode === 'dark' ? '#121212' : '#f8fafc',
                    paper: mode === 'dark' ? '#1e1e1e' : '#ffffff',
                },
            },
            // Adicionar transição padrão do MUI para consistência
            components: {
                MuiCssBaseline: {
                    styleOverrides: `
                        body {
                            transition: background-color 0.3s ease, color 0.3s ease;
                        }
                    `,
                },
            },
        });
    }, [mode, config?.cor_principal]);

    return (
        <ThemeContext.Provider value={{ mode, toggleTheme }}>
            <MuiThemeProvider theme={theme}>
                <CssBaseline />
                {children}
            </MuiThemeProvider>
        </ThemeContext.Provider>
    );
}