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
  AccountCircleOutlined,
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { showToast } from '../../utils/toast';
import { authService } from './authService';
import logo from '../../../logoprincipal.png';

export function LoginPage() {
  const theme = useTheme();
  const mode = theme.palette.mode;
  const { login: authLogin } = useAuth();

  // Estados do formulário
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showBootstrap, setShowBootstrap] = useState(false);

  // Detectar sucesso vindo do Stripe
  const queryParams = new URLSearchParams(window.location.search);
  const isStripeSuccess = queryParams.get('status') === 'success';
  const [stripeSuccess, setStripeSuccess] = useState(isStripeSuccess);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();

    if (!identifier.trim() || password.length < 6) {
      setError('Preencha o usuário e a senha (mínimo 6 caracteres)');
      return;
    }

    setLoading(true);
    setError('');
    setShowBootstrap(false);

    try {
      const success = await authLogin(identifier, password);

      if (!success) {
        setError('Falha no login. Verifique suas credenciais.');
      }
      // Note: AuthContext.login already handles the redirect to /dashboard on success
    } catch (err: any) {
      console.error('❌ Erro no login:', err);
      let errorMessage = err.response?.data?.error || 'Erro ao fazer login';

      if (err.response?.status === 401 || err.response?.status === 404) {
        setShowBootstrap(true);
      }

      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [identifier, password, authLogin]);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && identifier && password.length >= 6 && !loading) {
      handleSubmit(e as unknown as React.FormEvent);
    }
  };

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
              <Typography variant="h4" gutterBottom sx={{ fontWeight: 900, letterSpacing: '-0.03em' }}>
                Entrar
              </Typography>
              <Typography variant="body1" color="text.secondary" fontWeight="medium">
                Bem-vindo de volta ao seu painel.
              </Typography>
            </Box>

            {stripeSuccess && (
              <Alert
                severity="success"
                sx={{ mb: 3, borderRadius: 2 }}
                onClose={() => setStripeSuccess(false)}
              >
                <strong>Assinatura realizada com sucesso!</strong><br />
                Faça login com seu usuário para começar. <br />
                Sua senha temporária é: <strong>Trocar@123</strong>
              </Alert>
            )}

            {error && (
              <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>
                {error}
              </Alert>
            )}

            <form onSubmit={handleSubmit}>
              <TextField
                fullWidth
                label="Usuário"
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
                      <AccountCircleOutlined color="action" />
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
                      const promise = authService.bootstrapAdmin(identifier, password).then(async bootstrap => {
                        if (bootstrap.success) {
                          const loginOk = await authLogin(identifier, password);
                          // No hard reload here anymore - AuthContext/AppRoutes handle it
                          return loginOk;
                        }
                        throw new Error('Falha ao criar admin');
                      });

                      await showToast.promise(promise, {
                        loading: 'Criando administrador e autenticando...',
                        success: 'Administrador criado com sucesso!',
                        error: 'Falha ao criar administrador inicial'
                      });
                    } catch (e) {
                      console.error(e);
                    } finally {
                      setLoading(false);
                    }
                  }}
                  sx={{ py: 1.5, mb: 2, borderRadius: 2, textTransform: 'none' }}
                >
                  Criar administrador inicial
                </Button>
              )}


            </form>

            <Box sx={{ mt: 4, display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Button
                onClick={() => {
                  localStorage.clear();
                  sessionStorage.clear();
                  window.location.reload();
                }}
                variant="text"
                color="secondary"
                size="small"
                sx={{
                  textTransform: 'none',
                  fontSize: '0.75rem',
                  opacity: 0.6,
                  '&:hover': { opacity: 1 }
                }}
              >
                Limpar Cache e Reiniciar
              </Button>
              <Button
                onClick={() => window.location.href = '/'}
                variant="text"
                sx={{
                  color: 'text.secondary',
                  textTransform: 'none',
                  fontWeight: 600,
                  fontSize: '0.875rem'
                }}
              >
                ← Voltar para o Site
              </Button>
            </Box>
          </Paper>
        </Box>
      </Box>
    </Container>
  );
}
