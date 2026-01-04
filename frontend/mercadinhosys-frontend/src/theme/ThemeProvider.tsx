// src/theme/ThemeProvider.tsx - VERSÃO FINAL CORRIGIDA
import { createTheme, ThemeProvider as MuiThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { useState, useMemo, useEffect } from 'react';
import type { ReactNode } from 'react';
import { ThemeContext } from './ThemeContext';

interface ThemeProviderProps {
    children: ReactNode;
    defaultMode?: 'dark' | 'light';
}

export function ThemeProvider({ children, defaultMode = 'dark' }: ThemeProviderProps) {
    // Carregar tema do localStorage ou usar padrão
    const [mode, setMode] = useState<'dark' | 'light'>(() => {
        const savedTheme = localStorage.getItem('theme') as 'dark' | 'light' | null;
        return savedTheme || defaultMode;
    });

    const toggleTheme = () => {
        console.log('🎨 TOGGLE THEME CHAMADO!');
        setMode((prevMode) => {
            const newMode = prevMode === 'light' ? 'dark' : 'light';
            console.log(`🔄 Alterando de ${prevMode} para ${newMode}`);
            
            // Salvar no localStorage
            localStorage.setItem('theme', newMode);
            console.log('💾 Tema salvo no localStorage:', newMode);
            
            // Atualizar a classe no HTML para Tailwind
            if (newMode === 'dark') {
                document.documentElement.classList.add('dark');
                console.log('✅ Classe "dark" ADICIONADA ao <html>');
            } else {
                document.documentElement.classList.remove('dark');
                console.log('❌ Classe "dark" REMOVIDA do <html>');
            }
            
            console.log('📋 Classes atuais no <html>:', document.documentElement.className);
            return newMode;
        });
    };

    // Aplicar classe dark no mount
    useEffect(() => {
        if (mode === 'dark') {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
    }, [mode]);

    const theme = useMemo(() => {
        return createTheme({
            palette: {
                mode,
                primary: {
                    main: mode === 'dark' ? '#90caf9' : '#2563eb',
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
    }, [mode]);

    return (
        <ThemeContext.Provider value={{ mode, toggleTheme }}>
            <MuiThemeProvider theme={theme}>
                <CssBaseline />
                {children}
            </MuiThemeProvider>
        </ThemeContext.Provider>
    );
}