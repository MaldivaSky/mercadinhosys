import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiClient } from '../api/apiClient';

type Theme = 'light' | 'dark';

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

interface ThemeProviderProps {
  children: ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const [theme, setThemeState] = useState<Theme>(() => {
    const savedTheme = localStorage.getItem('theme') as Theme;
    if (savedTheme) return savedTheme;
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) return 'dark';
    return 'light';
  });

  // Sincronizar com o backend na inicialização
  useEffect(() => {
    const fetchUserPreferences = async () => {
      const token = localStorage.getItem('access_token');
      if (!token || token === 'undefined' || token === 'null') return;

      try {
        const response = await apiClient.get('/configuracao/preferencias');
        if (response.data && response.data.success) {
          const pref = response.data.preferencias;
          if (pref && typeof pref.tema_escuro !== 'undefined') {
            const newTheme = pref.tema_escuro ? 'dark' : 'light';
            setThemeState(newTheme);
            localStorage.setItem('theme', newTheme);
          }
        }
      } catch (error) {
        console.error('Erro ao buscar preferências de tema:', error);
      }
    };

    fetchUserPreferences();
  }, []);

  useEffect(() => {
    // Aplicar tema ao documento
    document.documentElement.setAttribute('data-theme', theme);
    document.body.className = theme === 'dark' ? 'dark-theme' : 'light-theme';

    // Salvar preferência local
    localStorage.setItem('theme', theme);
  }, [theme]);

  const setTheme = async (newTheme: Theme) => {
    setThemeState(newTheme);

    // Salvar no backend se estiver logado
    const token = localStorage.getItem('access_token');
    if (token && token !== 'undefined' && token !== 'null') {
      try {
        await apiClient.put('/configuracao/preferencias', {
          tema_escuro: newTheme === 'dark'
        });
      } catch (error) {
        console.error('Erro ao salvar preferência de tema:', error);
      }
    }
  };

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
  };

  const value = {
    theme,
    toggleTheme,
    setTheme
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

export default ThemeProvider;
