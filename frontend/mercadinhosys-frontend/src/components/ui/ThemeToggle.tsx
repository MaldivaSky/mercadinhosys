// src/components/ui/ThemeToggle.tsx
import { IconButton, Tooltip } from '@mui/material';
import { Brightness4, Brightness7 } from '@mui/icons-material';
import { useTheme } from '../../theme/useTheme';

export function ThemeToggle() {
    const { mode, toggleTheme } = useTheme();

    return (
        <Tooltip title={`Alternar para tema ${mode === 'dark' ? 'claro' : 'escuro'}`}>
            <IconButton onClick={toggleTheme} color="inherit">
                {mode === 'dark' ? <Brightness7 /> : <Brightness4 />}
            </IconButton>
        </Tooltip>
    );
};
export default ThemeToggle;