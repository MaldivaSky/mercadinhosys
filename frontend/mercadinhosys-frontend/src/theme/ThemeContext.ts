// src/theme/ThemeContext.ts
import { createContext } from 'react';

export interface ThemeContextType {
    mode: 'dark' | 'light';
    toggleTheme: () => void;
}

export const ThemeContext = createContext<ThemeContextType>({
    mode: 'dark',
    toggleTheme: () => {},
});