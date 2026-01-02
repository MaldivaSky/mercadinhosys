import { IconButton, Tooltip } from '@mui/material';
import { Brightness4, Brightness7 } from '@mui/icons-material';
import { useTheme } from '../../theme/ThemeProvider';

export function ThemeToggle() {
    const { mode, toggleTheme } = useTheme();

    return (
        <Tooltip title={`Alternar para tema ${mode === 'dark' ? 'claro' : 'escuro'}`}>
            <IconButton
                onClick={toggleTheme}
                sx={{
                    color: 'inherit',
                    '&:hover': {
                        backgroundColor: 'action.hover',
                    },
                }}
            >
                {mode === 'dark' ? <Brightness7 /> : <Brightness4 />}
            </IconButton>
        </Tooltip>
    );
}