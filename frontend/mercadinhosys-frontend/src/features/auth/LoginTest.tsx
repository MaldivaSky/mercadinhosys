// src/features/auth/LoginTest.tsx
import { useState } from 'react';
import { authService } from './authService';
import { Button, TextField, Box, Typography, CircularProgress } from '@mui/material';

export function LoginTest() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [message, setMessage] = useState('');
    const [loading, setLoading] = useState(false);

    const handleLogin = async () => {
        setLoading(true);
        try {
            const result = await authService.login(email, password);
            setMessage(`✅ Login realizado! Token: ${result.data?.access_token ? 'Recebido' : 'Não recebido'}`);
        } catch (error: any) {
            setMessage(`❌ Erro no login: ${error.response?.data?.message || error.message || 'Erro desconhecido'}`);
        } finally {
            setLoading(false);
        }
    };

    const handleTestAPI = async () => {
        setLoading(true);
        setMessage('🔄 Testando conexão com backend...');
        
        try {
            const response = await fetch('http://localhost:5000/api/health');
            const data = await response.json();
            setMessage(`✅ Backend conectado: ${data.message || data.status || 'OK'}`);
        } catch (error: any) {
            setMessage(`❌ Backend offline ou erro na conexão: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Box 
            sx={{ 
                p: 3, 
                border: '1px solid', 
                borderColor: 'divider',
                borderRadius: 2, 
                maxWidth: 400,
                bgcolor: 'background.paper'
            }}
        >
            <Typography variant="h6" gutterBottom>
                🔐 Teste de Autenticação
            </Typography>

            <Button
                variant="outlined"
                onClick={handleTestAPI}
                sx={{ mb: 2 }}
                fullWidth
                disabled={loading}
                startIcon={loading ? <CircularProgress size={20} /> : null}
            >
                Testar Conexão Backend
            </Button>

            <TextField
                label="Email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                fullWidth
                sx={{ mb: 2 }}
                disabled={loading}
                placeholder="admin@mercadinho.com"
            />

            <TextField
                label="Senha"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                fullWidth
                sx={{ mb: 2 }}
                disabled={loading}
                placeholder="senha123"
            />

            <Button
                variant="contained"
                color="primary"
                onClick={handleLogin}
                fullWidth
                disabled={loading || !email || !password}
                startIcon={loading ? <CircularProgress size={20} /> : null}
            >
                {loading ? 'Testando...' : 'Testar Login'}
            </Button>

            {message && (
                <Box 
                    sx={{ 
                        mt: 2, 
                        p: 2, 
                        borderRadius: 1,
                        bgcolor: message.includes('✅') 
                            ? 'success.dark' 
                            : message.includes('🔄')
                            ? 'info.dark'
                            : 'error.dark',
                        color: 'white'
                    }}
                >
                    <Typography variant="body2">
                        {message}
                    </Typography>
                </Box>
            )}
        </Box>
    );
}