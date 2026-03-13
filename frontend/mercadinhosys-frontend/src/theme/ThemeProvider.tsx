// src/theme/ThemeProvider.tsx - Sincronizado com ConfigContext
import { createTheme, ThemeProvider as MuiThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { useMemo, useEffect } from 'react';
import type { ReactNode } from 'react';
import { ThemeContext } from './ThemeContext';
import { useConfig } from '../contexts/ConfigContext';

interface ThemeProviderProps {
    children: ReactNode;
    defaultMode?: 'dark' | 'light';
}

export function ThemeProvider({ children, defaultMode = 'dark' }: ThemeProviderProps) {
    const { config, preferencias, updatePreferencias } = useConfig();
    const defaultThemeMode = defaultMode || 'dark';

    // O ConfigContext é o cérebro. ThemeProvider é o músculo (MUI).
    // Senior Mode: Blindagem absoluta contra propriedades undefined
    const mode: 'dark' | 'light' = useMemo(() => {
        // Se temos preferências carregadas, elas mandam
        if (preferencias?.tema_escuro !== undefined) {
            return preferencias.tema_escuro ? 'dark' : 'light';
        }

        // Se o config do estabelecimento carregou, usamos como segundo fallback
        if (config?.tema_escuro !== undefined) {
            return config.tema_escuro ? 'dark' : 'light';
        }

        // Caso contrário, respeitamos o cache ou o padrão do sistema
        const saved = localStorage.getItem('theme') as 'dark' | 'light' | null;
        return saved || defaultThemeMode;
    }, [preferencias?.tema_escuro, config?.tema_escuro, defaultThemeMode]);

    const toggleTheme = async () => {
        try {
            // Unificação Sênior: Usar o toggle central do ConfigContext
            const currentIsDark = mode === 'dark';
            await updatePreferencias({ tema_escuro: !currentIsDark });
        } catch {
            // Fallback local redundante para segurança máxima
            const fallback = mode === 'light' ? 'dark' : 'light';
            localStorage.setItem('theme', fallback);
            document.documentElement.classList.toggle('dark', fallback === 'dark');
        }
    };

    useEffect(() => {
        if (mode === 'dark') {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
    }, [mode]);

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