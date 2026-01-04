// src/components/DebugRoutes.tsx
import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

const DebugRoutes: React.FC = () => {
    const location = useLocation();

    useEffect(() => {
        console.log('=== DEBUG ROUTES ===');
        console.log('Path atual:', location.pathname);
        console.log('Token existe:', !!localStorage.getItem('access_token'));
        console.log('Token valor:', localStorage.getItem('access_token')?.substring(0, 20) + '...');
        console.log('User data:', localStorage.getItem('user_data'));
        console.log('====================');
    }, [location]);

    return null; // Componente invisível
};

export default DebugRoutes;