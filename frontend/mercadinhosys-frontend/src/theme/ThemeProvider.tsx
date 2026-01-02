import { createTheme, ThemeProvider as MuiThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { useState, useMemo } from 'react';
import type { ReactNode } from 'react';
import { ThemeContext } from './ThemeContext';

// Cores para tema escuro
const darkPalette = {
    primary: {
        main: '#90caf9', // Azul suave
        light: '#e3f2fd',
        dark: '#42a5f5',
    },
    secondary: {
        main: '#ce93d8', // Roxo suave
        light: '#f3e5f5',
        dark: '#ab47bc',
    },
    background: {
        default: '#121212',
        paper: '#1e1e1e',
    },
    text: {
        primary: '#ffffff',
        secondary: '#b0b0b0',
    },
    divider: 'rgba(255, 255, 255, 0.12)',
};

// Cores para tema claro
const lightPalette = {
    primary: {
        main: '#2563eb',
        light: '#60a5fa',
        dark: '#1d4ed8',
    },
    secondary: {
        main: '#10b981',
        light: '#34d399',
        dark: '#059669',
    },
    background: {
        default: '#f8fafc',
        paper: '#ffffff',
    },
    text: {
        primary: '#111827',
        secondary: '#6b7280',
    },
    divider: 'rgba(0, 0, 0, 0.12)',
};

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
        const palette = mode === 'dark' ? darkPalette : lightPalette;

        return createTheme({
            palette: {
                mode,
                ...palette,
            },
            typography: {
                fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
                h1: {
                    fontSize: '2.5rem',
                    fontWeight: 700,
                },
                h2: {
                    fontSize: '2rem',
                    fontWeight: 600,
                },
                h3: {
                    fontSize: '1.75rem',
                    fontWeight: 600,
                },
                button: {
                    textTransform: 'none',
                    fontWeight: 600,
                },
            },
            shape: {
                borderRadius: 8,
            },
            components: {
                MuiButton: {
                    styleOverrides: {
                        root: {
                            textTransform: 'none',
                            fontWeight: 600,
                        },
                    },
                },
                MuiCard: {
                    styleOverrides: {
                        root: {
                            backgroundImage: 'none', // Remove gradiente padrão no modo escuro
                        },
                    },
                },
                MuiAppBar: {
                    styleOverrides: {
                        root: {
                            backgroundImage: 'none',
                        },
                    },
                },
                MuiDrawer: {
                    styleOverrides: {
                        paper: {
                            backgroundImage: 'none',
                        },
                    },
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