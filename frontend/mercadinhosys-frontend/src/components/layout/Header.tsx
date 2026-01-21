import React from 'react';
import { AppBar, Toolbar, Typography, Avatar, IconButton, Menu, MenuItem, Box } from '@mui/material';
import { Logout, Brightness4, Brightness7 } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import logo from '../../../logoprincipal.png';

const Header: React.FC = () => {
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const navigate = useNavigate();

  // Busca dados do usuário do localStorage
  const user = React.useMemo(() => {
    try {
      return JSON.parse(localStorage.getItem('user_data') || '{}');
    } catch {
      return {};
    }
  }, []);

  const handleMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_data');
    window.dispatchEvent(new Event('auth-change'));
    navigate('/login');
  };

  // Tema: claro/escuro (persistido em localStorage)
  const [isDark, setIsDark] = React.useState<boolean>(() => {
    try {
      const stored = localStorage.getItem('theme');
      if (stored) return stored === 'dark';
      return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    } catch {
      return false;
    }
  });

  React.useEffect(() => {
    try {
      if (isDark) {
        document.documentElement.classList.add('dark');
        localStorage.setItem('theme', 'dark');
      } else {
        document.documentElement.classList.remove('dark');
        localStorage.setItem('theme', 'light');
      }
      window.dispatchEvent(new Event('theme-change'));
    } catch {
      // ignore
    }
  }, [isDark]);

  const handleToggleTheme = () => setIsDark((s) => !s);

  // Avatar: foto se existir, senão inicial do nome
  const avatarContent = user.foto_url ? (
    <Avatar src={user.foto_url} alt={user.nome} />
  ) : (
    <Avatar>{user.nome ? user.nome[0].toUpperCase() : '?'}</Avatar>
  );

  return (
    <AppBar position="static" color="default" elevation={1} sx={{ zIndex: 1201 }}>
      <Toolbar>
        <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
          <img src={logo} alt="Logo MercadinhoSys" style={{ height: 40, marginRight: 12, borderRadius: 6, width:'auto' }} />
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="body1" sx={{ fontWeight: 500, mr: 1 }}>
            {user.nome || 'Usuário'}
          </Typography>
          <IconButton size="large" color="inherit" onClick={handleToggleTheme} title="Alternar tema">
            {isDark ? <Brightness7 /> : <Brightness4 />}
          </IconButton>
          <IconButton onClick={handleMenu} size="large" sx={{ p: 0 }}>
            {avatarContent}
          </IconButton>
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleClose}
            anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
            transformOrigin={{ vertical: 'top', horizontal: 'right' }}
          >
            <MenuItem onClick={handleLogout}>
              <Logout fontSize="small" sx={{ mr: 1 }} /> Sair
            </MenuItem>
          </Menu>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;