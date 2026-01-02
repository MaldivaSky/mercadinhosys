// src/theme/ThemeProvider.tsx - VERSÃO FINAL CORRIGIDA
import { createTheme, ThemeProvider as MuiThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { useState, useMemo } from 'react';
import type { ReactNode } from 'react';
import { ThemeContext } from './ThemeContext';

interface ThemeProviderProps {
    children: ReactNode;
    defaultMode?: 'dark' | 'light';
}

export function ThemeProvider({ children, defaultMode = 'dark' }: ThemeProviderProps) {
    const [mode, setMode] = useState<'dark' | 'light'>(defaultMode);

    const toggleTheme = () => {
        setMode((prevMode) => (prevMode === 'light' ? 'dark' : 'light'));
    };

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