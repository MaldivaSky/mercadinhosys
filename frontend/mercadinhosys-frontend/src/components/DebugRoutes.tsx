// src/components/DebugRoutes.tsx
import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

const DebugRoutes: React.FC = () => {
    const location = useLocation();

    useEffect(() => {
        // Apenas em desenvolvimento — zero overhead em produção
        if (!import.meta.env.DEV) return;
        console.log(`[Route] ${location.pathname}`);
    }, [location.pathname]);

    return null;
};

export default DebugRoutes;