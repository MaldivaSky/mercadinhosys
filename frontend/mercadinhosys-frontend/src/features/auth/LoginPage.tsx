import { useState, useCallback } from 'react';
import {
  Box,
  Button,
  TextField,
  Typography,
  Paper,
  Alert,
  CircularProgress,
  InputAdornment,
  IconButton,
  Container,
  useTheme,
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  LockOutlined,
  EmailOutlined,
} from '@mui/icons-material';
import { authService } from './authService';
import { LoginApiResponse } from '../../types';
import logo from '../../../logoprincipal.png';

export function LoginPage() {
  const theme = useTheme();
  const mode = theme.palette.mode;

  // Estados do formulário
  const [identifier, setIdentifier] = useState('admin');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showBootstrap, setShowBootstrap] = useState(false);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();

    if (!identifier.trim() || password.length < 6) {
      setError('Preencha email/usuário e senha (mínimo 6 caracteres)');
      return;
    }

    setLoading(true);
    setError('');
    setShowBootstrap(false);

    try {
      const response: LoginApiResponse = await authService.login(identifier, password);

      if (!response.success) {
        throw new Error(response.error || 'Falha no login');
      }

      if (response.data) {
        const { access_token, refresh_token, user } = response.data;
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);
        localStorage.setItem('user_data', JSON.stringify(user));
        window.dispatchEvent(new Event('auth-change'));
      }
    } catch (err: any) {
      console.error('❌ Erro no login:', err);
      let errorMessage = 'Erro ao fazer login';
      if (err.response?.status === 401) {
        errorMessage = 'Credenciais inválidas';
        setShowBootstrap(true);
      } else if (err.response?.status === 404) {
        errorMessage = 'Usuário não encontrado';
        setShowBootstrap(true);
      }
      setError(errorMessage);
      authService.logout();
    } finally {
      setLoading(false);
    }
  }, [identifier, password]);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && identifier && password.length >= 6 && !loading) {
      handleSubmit(e as unknown as React.FormEvent);
    }
  };

  const handleDemoLogin = useCallback(() => {
    setIdentifier('admin');
    setPassword('admin123');
    setTimeout(() => {
      const fakeEvent = { preventDefault: () => { } } as React.FormEvent;
      handleSubmit(fakeEvent);
    }, 100);
  }, [handleSubmit]);

  const isFormValid = identifier.trim().length > 0 && password.length >= 6;

  return (
    <Container maxWidth={false} sx={{ minHeight: '100vh', p: 0 }}>
      <Box
        sx={{
          display: 'flex',
          minHeight: '100vh',
          background: mode === 'dark'
            ? 'linear-gradient(135deg, #121212 0%, #1a1a2e 50%, #16213e 100%)'
            : 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 50%, #cbd5e1 100%)',
        }}
      >
        {/* Lado esquerdo - Branding */}
        <Box
          sx={{
            display: { xs: 'none', md: 'flex' },
            flex: 1,
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            p: 8,
            color: mode === 'dark' ? 'white' : '#1e293b',
          }}
        >
          <img src={logo} alt="Logo" style={{ height: 120, marginBottom: 32, borderRadius: 12, boxShadow: '0 2px 12px #0002' }} />
          <Typography variant="h4" fontWeight="black" sx={{ mb: 2, tracking: '-0.02em' }}>
            Mercadinho<span style={{ color: '#3b82f6' }}>Sys</span>
          </Typography>
          <Typography variant="h6" sx={{ opacity: 0.7, textAlign: 'center', maxWidth: 400 }}>
            A inteligência que seu comércio merece para crescer com escala.
          </Typography>
        </Box>

        {/* Lado direito - Login Form */}
        <Box
          sx={{
            display: 'flex',
            flex: { xs: 1, md: 0.8 },
            justifyContent: 'center',
            alignItems: 'center',
            p: { xs: 2, sm: 4 },
          }}
        >
          <Paper
            elevation={24}
            sx={{
              p: { xs: 3, sm: 6 },
              width: '100%',
              maxWidth: 450,
              borderRadius: 4,
              background: mode === 'dark' ? 'rgba(30, 30, 30, 0.8)' : 'rgba(255, 255, 255, 0.95)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255,255,255,0.1)',
            }}
          >
            <Box sx={{ textAlign: 'center', mb: 5 }}>
              <Typography variant="h4" fontWeight="900" gutterBottom tracking="-0.03em">
                Entrar
              </Typography>
              <Typography variant="body1" color="text.secondary" fontWeight="medium">
                Bem-vindo de volta ao seu painel.
              </Typography>
            </Box>

            {error && (
              <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }} onClose={() => setError('')}>
                {error}
              </Alert>
            )}

            <form onSubmit={handleSubmit}>
              <TextField
                fullWidth
                label="Usuário ou Email"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                onKeyPress={handleKeyPress}
                margin="normal"
                variant="outlined"
                required
                disabled={loading}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <EmailOutlined color="action" />
                    </InputAdornment>
                  ),
                }}
                sx={{ mb: 3 }}
              />

              <TextField
                fullWidth
                label="Senha"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyPress={handleKeyPress}
                margin="normal"
                variant="outlined"
                required
                disabled={loading}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <LockOutlined color="action" />
                    </InputAdornment>
                  ),
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton onClick={() => setShowPassword(!showPassword)} edge="end" disabled={loading}>
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
                sx={{ mb: 4 }}
              />

              <Button
                fullWidth
                type="submit"
                variant="contained"
                size="large"
                disabled={!isFormValid || loading}
                sx={{
                  py: 2,
                  mb: 2,
                  borderRadius: 2,
                  fontWeight: 'bold',
                  fontSize: '1rem',
                  textTransform: 'none',
                  boxShadow: '0 10px 20px -5px rgba(59, 130, 246, 0.5)',
                  background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
                }}
              >
                {loading ? <CircularProgress size={26} color="inherit" /> : 'Entrar no Painel'}
              </Button>

              {showBootstrap && !loading && (
                <Button
                  fullWidth
                  variant="outlined"
                  size="large"
                  onClick={async () => {
                    setLoading(true);
                    setError('');
                    try {
                      const bootstrap = await authService.bootstrapAdmin(identifier, password);
                      if (bootstrap.success) {
                        await authService.login(identifier, password);
                        window.dispatchEvent(new Event('auth-change'));
                        return;
                      }
                      const response: LoginApiResponse = await authService.login(identifier, password);
                      if (response.success) window.dispatchEvent(new Event('auth-change'));
                    } catch (e) {
                      setError('Credenciais inválidas');
                    } finally {
                      setLoading(false);
                    }
                  }}
                  sx={{ py: 1.5, mb: 2, borderRadius: 2, textTransform: 'none' }}
                >
                  Criar administrador inicial
                </Button>
              )}

              {import.meta.env.DEV && (
                <Button
                  fullWidth
                  variant="text"
                  onClick={handleDemoLogin}
                  disabled={loading}
                  sx={{ py: 1, color: '#10b981', fontWeight: 'bold' }}
                >
                  Acesso Rápido (Demo Admin)
                </Button>
              )}
            </form>

            <Box sx={{ mt: 6, textAlign: 'center', borderTop: '1px solid rgba(0,0,0,0.05)', pt: 4 }}>
              <Button
                onClick={() => window.location.href = '/'}
                variant="text"
                sx={{ color: 'text.secondary', textTransform: 'none', fontWeight: 'bold' }}
              >
                ← Voltar para o Site Principal
              </Button>
            </Box>
          </Paper>
        </Box>
      </Box>
    </Container>
  );
}
