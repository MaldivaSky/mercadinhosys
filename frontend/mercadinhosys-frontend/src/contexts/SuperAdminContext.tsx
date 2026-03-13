import React, { createContext, useContext, useState, useEffect } from 'react';

type SuperAdminContextType = {
    selectedTenantId: string;
    setSelectedTenantId: (id: string) => void;
    syncStatus: {
        lastSync: Date | null;
        status: 'online' | 'offline' | 'delayed' | 'unknown';
    };
    setSyncStatus: React.Dispatch<React.SetStateAction<{ lastSync: Date | null; status: 'online' | 'offline' | 'delayed' | 'unknown' }>>;
};

const SuperAdminContext = createContext<SuperAdminContextType | undefined>(undefined);

export const SuperAdminProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [selectedTenantId, setSelectedTenantId] = useState<string>(() => {
        return localStorage.getItem('mercadinhosys_superadmin_tenant') || 'all';
    });

    const [syncStatus, setSyncStatus] = useState<SuperAdminContextType['syncStatus']>({
        lastSync: null,
        status: 'unknown',
    });

    useEffect(() => {
        localStorage.setItem('mercadinhosys_superadmin_tenant', selectedTenantId);
    }, [selectedTenantId]);

    return (
        <SuperAdminContext.Provider value={{ selectedTenantId, setSelectedTenantId, syncStatus, setSyncStatus }}>
            {children}
        </SuperAdminContext.Provider>
    );
};

export const useSuperAdmin = () => {
    const context = useContext(SuperAdminContext);
    if (!context) {
        throw new Error('useSuperAdmin must be used within a SuperAdminProvider');
    }
    return context;
};
