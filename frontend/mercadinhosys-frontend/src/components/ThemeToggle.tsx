import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '../theme/useTheme';

const ThemeToggle: React.FC = () => {
  const { mode, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className="theme-toggle"
      title={mode === 'light' ? 'Ativar modo escuro' : 'Ativar modo claro'}
      aria-label={mode === 'light' ? 'Ativar modo escuro' : 'Ativar modo claro'}
    >
      {mode === 'light' ? (
        <Moon className="w-5 h-5" />
      ) : (
        <Sun className="w-5 h-5" />
      )}
    </button>
  );
};

export default ThemeToggle;
