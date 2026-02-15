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
    const { config, updateConfig } = useConfig();

    // Mode vem do ConfigContext (API) quando disponível, senão localStorage
    const mode: 'dark' | 'light' = useMemo(() => {
        if (config !== null) {
            return config.tema_escuro ? 'dark' : 'light';
        }
        const saved = localStorage.getItem('theme') as 'dark' | 'light' | null;
        return saved || defaultMode;
    }, [config, defaultMode]);

    const toggleTheme = async () => {
        try {
            const newMode = mode === 'light' ? 'dark' : 'light';
            await updateConfig({ tema_escuro: newMode === 'dark' });
        } catch {
            // Fallback local se API falhar (ex: sem token)
            const fallback = mode === 'light' ? 'dark' : 'light';
            localStorage.setItem('theme', fallback);
            if (fallback === 'dark') {
                document.documentElement.classList.add('dark');
            } else {
                document.documentElement.classList.remove('dark');
            }
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