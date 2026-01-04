// src/components/DebugAuth.tsx (opcional)
import React, { useEffect } from 'react';

export const DebugAuth: React.FC = () => {
    useEffect(() => {
        console.group('=== DEBUG AUTENTICAÇÃO ===');
        console.log('Token:', localStorage.getItem('access_token'));
        console.log('Refresh Token:', localStorage.getItem('refresh_token'));
        console.log('User Data:', localStorage.getItem('user_data'));
        console.log('App URL:', window.location.href);
        console.log('Pathname:', window.location.pathname);
        console.groupEnd();
    }, []);

    return null; // Componente invisível
};