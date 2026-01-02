// src/features/auth/LoginTest.tsx
import { useState } from 'react';
import { authService } from './authService';
import { Button, TextField, Box, Typography } from '@mui/material';

export function LoginTest() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [message, setMessage] = useState('');

    const handleLogin = async () => {
        try {
            const result = await authService.login({ email, password });
            setMessage(`✅ Login realizado! Token: ${result.token ? 'Recebido' : 'Não recebido'}`);
        } catch (error) {
            setMessage('❌ Erro no login');
        }
    };

    const handleTestAPI = async () => {
        try {
            const response = await fetch('http://localhost:5000/api/health');
            const data = await response.json();
            setMessage(`✅ Backend conectado: ${data.message || 'OK'}`);
        } catch {
            setMessage('❌ Backend offline ou erro na conexão');
        }
    };

    return (
        <Box sx={{ p: 3, border: '1px solid #ccc', borderRadius: 2, maxWidth: 400 }}>
            <Typography variant="h6" gutterBottom>
                Teste de Conexão Backend
            </Typography>

            <Button
                variant="contained"
                onClick={handleTestAPI}
                sx={{ mb: 2 }}
                fullWidth
            >
                Testar Conexão Backend
            </Button>

            <TextField
                label="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                fullWidth
                sx={{ mb: 2 }}
            />

            <TextField
                label="Senha"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                fullWidth
                sx={{ mb: 2 }}
            />

            <Button
                variant="contained"
                color="primary"
                onClick={handleLogin}
                fullWidth
            >
                Testar Login
            </Button>

            {message && (
                <Typography sx={{ mt: 2, color: message.includes('✅') ? 'green' : 'red' }}>
                    {message}
                </Typography>
            )}
        </Box>
    );
}