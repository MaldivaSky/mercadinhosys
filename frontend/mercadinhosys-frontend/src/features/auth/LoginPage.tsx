// src/features/auth/LoginPage.tsx
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
  Storefront,
} from '@mui/icons-material';
import { authService } from './authService';
import { LoginApiResponse } from '../../types';

export function LoginPage() {
  const theme = useTheme();
  const mode = theme.palette.mode;

  // Estados do formulário
  const [identifier, setIdentifier] = useState('admin'); // ← Valor inicial 'admin'
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [debugInfo, setDebugInfo] = useState('');

  // Função de login com useCallback para evitar recriação
  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();

    // Validação básica
    if (!identifier.trim() || password.length < 6) {
      setError('Preencha email/usuário e senha (mínimo 6 caracteres)');
      return;
    }

    setLoading(true);
    setError('');

    try {
      console.log('🔐 Tentando login:', identifier);
      const response: LoginApiResponse = await authService.login(identifier, password);

      if (!response.success) {
        throw new Error(response.error || 'Falha no login');
      }

      if (!response.data) {
        throw new Error('Dados de login não retornados');
      }

      const { access_token, refresh_token, user } = response.data;

      // ✅ Salva no localStorage
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      localStorage.setItem('user_data', JSON.stringify(user));

      console.log('✅ Login bem-sucedido para:', user.nome);

      // Dispara evento - AppRoutes detectará e redirecionará
      window.dispatchEvent(new Event('auth-change'));

    } catch (err: unknown) {
      console.error('❌ Erro no login:', err);

      let errorMessage = 'Erro ao fazer login';

      if (err && typeof err === 'object' && 'response' in err) {
        const axiosError = err as { response?: { status?: number }; request?: unknown };
        if (axiosError.response?.status === 401) {
          errorMessage = 'Credenciais inválidas';
        } else if (axiosError.response?.status === 404) {
          errorMessage = 'Usuário não encontrado';
        } else if (axiosError.request) {
          errorMessage = 'Servidor não respondeu. Verifique se o backend está rodando.';
        }
      }

      setError(errorMessage);
      authService.logout(); // Limpa tokens inválidos

    } finally {
      setLoading(false);
    }
  }, [identifier, password]);

  // ✅ Handle de teclas corrigido
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && identifier && password.length >= 6 && !loading) {
      handleSubmit(e as unknown as React.FormEvent);
    }
  };

  // ✅ Login demo simplificado
  const handleDemoLogin = useCallback(() => {
    // Login demo sempre disponível em desenvolvimento
    setIdentifier('admin');
    setPassword('admin123');

      // Dispara login após preencher campos
      setTimeout(() => {
        const fakeEvent = { preventDefault: () => { } } as React.FormEvent;
        handleSubmit(fakeEvent);
      }, 100);
  }, [handleSubmit]);

  // ✅ Teste de conexão corrigido
  const testBackendConnection = async () => {
    try {
      setDebugInfo('Testando conexão...');
      const response = await fetch('http://localhost:5000/api/auth/health', {
        method: 'GET',
      });
      setDebugInfo(`✅ Backend respondeu: ${response.status} ${response.statusText}`);
    } catch {
      setDebugInfo('❌ Backend offline. Execute: cd backend && npm start');
    }
  };

  // ✅ Validação de formulário
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
        {/* Lado esquerdo - Logo */}
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
          <Storefront sx={{ fontSize: 120, mb: 4, color: '#3b82f6' }} />
          <Typography variant="h2" fontWeight="bold" gutterBottom>
            MercadinhoSys
          </Typography>
          <Typography variant="h5" sx={{ opacity: 0.8, textAlign: 'center' }}>
            Sistema de Gestão Comercial
          </Typography>

          {/* Informações de debug */}
          <Box sx={{ mt: 4, p: 3, bgcolor: 'rgba(0,0,0,0.1)', borderRadius: 2, width: '80%' }}>
            <Typography variant="body2" fontWeight="bold" gutterBottom>
              🔧 Informações Técnicas:
            </Typography>
            <Typography variant="caption" sx={{ display: 'block' }}>
              • Backend: http://localhost:5000
            </Typography>
            <Typography variant="caption" sx={{ display: 'block' }}>
              • Rota de login: POST /api/auth/login
            </Typography>
            <Typography variant="caption" sx={{ display: 'block' }}>
              • Credenciais teste: admin / admin123
            </Typography>

            <Button
              size="small"
              variant="outlined"
              onClick={testBackendConnection}
              sx={{ mt: 2 }}
            >
              Testar Conexão Backend
            </Button>

            {debugInfo && (
              <Alert severity="info" sx={{ mt: 2 }}>
                <Typography variant="caption">{debugInfo}</Typography>
              </Alert>
            )}
          </Box>
        </Box>

        {/* Lado direito - Formulário */}
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
            elevation={3}
            sx={{
              p: { xs: 3, sm: 5 },
              width: '100%',
              maxWidth: 450,
              borderRadius: 3,
              background: mode === 'dark'
                ? 'rgba(30, 30, 30, 0.95)'
                : 'rgba(255, 255, 255, 0.98)',
            }}
          >
            <Box sx={{ textAlign: 'center', mb: 4 }}>
              <LockOutlined sx={{ fontSize: 50, color: '#3b82f6', mb: 2 }} />
              <Typography variant="h4" fontWeight="bold" gutterBottom>
                Acessar Sistema
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Use seu email ou nome de usuário
              </Typography>
            </Box>

            {error && (
              <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
                {error}
              </Alert>
            )}

            <form onSubmit={handleSubmit}>
              <TextField
                fullWidth
                label="Email ou Usuário *"
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
                label="Senha *"
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
                      <IconButton
                        onClick={() => setShowPassword(!showPassword)}
                        edge="end"
                        disabled={loading}
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
                sx={{ mb: 1 }}
              />

              <Box sx={{ textAlign: 'right', mb: 3 }}>
                <Button
                  size="small"
                  sx={{ textTransform: 'none' }}
                  onClick={() => alert('Contate o administrador do sistema')}
                  disabled={loading}
                >
                  Esqueceu a senha?
                </Button>
              </Box>

              <Button
                fullWidth
                type="submit"
                variant="contained"
                size="large"
                disabled={!isFormValid || loading}
                sx={{
                  py: 1.5,
                  mb: 2,
                  borderRadius: 2,
                  background: 'linear-gradient(90deg, #3b82f6 0%, #1d4ed8 100%)',
                  '&:hover': {
                    background: 'linear-gradient(90deg, #1d4ed8 0%, #1e40af 100%)',
                  },
                }}
              >
                {loading ? (
                  <CircularProgress size={24} color="inherit" />
                ) : (
                  'ENTRAR NO SISTEMA'
                )}
              </Button>

              {/* Login demo sempre disponível */}
              {import.meta.env.DEV && (
                <Button
                  fullWidth
                  variant="outlined"
                  size="large"
                  onClick={handleDemoLogin}
                  disabled={loading}
                  sx={{
                    py: 1.5,
                    borderRadius: 2,
                    borderColor: '#10b981',
                    color: '#10b981',
                    '&:hover': {
                      borderColor: '#059669',
                      backgroundColor: 'rgba(16, 185, 129, 0.08)',
                    },
                  }}
                >
                  Login Automático (Admin)
                </Button>
              )}
            </form>

            <Box sx={{ mt: 4, textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                <strong>Instruções:</strong>
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                • Email ou usuário: admin
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                • Senha padrão: admin123
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                • Certifique-se que o backend está rodando na porta 5000
              </Typography>
            </Box>
          </Paper>
        </Box>
      </Box>
    </Container>
  );
}