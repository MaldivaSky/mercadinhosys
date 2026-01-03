// src/features/auth/LoginPage.tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
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

export function LoginPage() {
  const navigate = useNavigate();
  const theme = useTheme();
  const mode = theme.palette.mode;
  
  // Estados do formulário
  const [identifier, setIdentifier] = useState(''); // Aceita email ou username
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Validação simples
  const isFormValid = identifier.length > 0 && password.length >= 6;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isFormValid) return;
    
    setLoading(true);
    setError('');
    
    try {
      await authService.login(identifier, password);
      navigate('/dashboard'); // Redirecionar após login
    } catch (err: any) {
      setError(err.response?.data?.message || 'Erro ao fazer login. Verifique suas credenciais.');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setIdentifier('demo@mercadinhosys.com');
    setPassword('demo123');
  };

  

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
        {/* Lado esquerdo - Ilustração/Logo */}
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
            Sistema de Gestão Comercial Completo
          </Typography>
          <Box sx={{ mt: 6, textAlign: 'center' }}>
            <Typography variant="body1" sx={{ mb: 2 }}>
              🚀 PDV Integrado
            </Typography>
            <Typography variant="body1" sx={{ mb: 2 }}>
              📊 Dashboard em Tempo Real
            </Typography>
            <Typography variant="body1">
              📱 Totalmente Responsivo
            </Typography>
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
            elevation={mode === 'dark' ? 0 : 3}
            sx={{
              p: { xs: 3, sm: 5 },
              width: '100%',
              maxWidth: 450,
              borderRadius: 3,
              border: mode === 'dark' ? '1px solid #333' : 'none',
              background: mode === 'dark' 
                ? 'rgba(30, 30, 30, 0.9)' 
                : 'rgba(255, 255, 255, 0.95)',
              backdropFilter: 'blur(10px)',
            }}
          >
            <Box sx={{ textAlign: 'center', mb: 4 }}>
              <LockOutlined 
                sx={{ 
                  fontSize: 50, 
                  color: '#3b82f6',
                  mb: 2,
                }} 
              />
              <Typography variant="h4" fontWeight="bold" gutterBottom>
                Acessar Sistema
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Entre com suas credenciais para acessar o painel
              </Typography>
            </Box>

            {error && (
              <Alert 
                severity="error" 
                sx={{ mb: 3, borderRadius: 2 }}
                onClose={() => setError('')}
              >
                {error}
              </Alert>
            )}

            <form onSubmit={handleSubmit}>
              <TextField
                fullWidth
                label="Email ou Usuário"
                type="text"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                margin="normal"
                variant="outlined"
                required
                placeholder="Digite seu email ou nome de usuário"
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
                margin="normal"
                variant="outlined"
                required
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
                  onClick={() => alert('Funcionalidade em desenvolvimento')}
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
                  'Entrar no Sistema'
                )}
              </Button>

              <Button
                fullWidth
                variant="outlined"
                size="large"
                onClick={handleDemoLogin}
                sx={{
                  py: 1.5,
                  borderRadius: 2,
                  borderColor: '#10b981',
                  color: '#10b981',
                  '&:hover': {
                    borderColor: '#059669',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                  },
                }}
              >
                Usar Credenciais de Demonstração
              </Button>
            </form>

            <Box sx={{ mt: 4, textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                © {new Date().getFullYear()} MercadinhoSys • v1.0.0
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                Ambiente de Desenvolvimento • Backend: localhost:5000
              </Typography>
            </Box>
          </Paper>
        </Box>
      </Box>
    </Container>
  );
}