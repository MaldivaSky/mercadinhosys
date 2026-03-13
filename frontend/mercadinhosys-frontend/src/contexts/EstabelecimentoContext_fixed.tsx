// src/contexts/EstabelecimentoContext.tsx
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiClient } from '../api/apiClient';
import toast from 'react-hot-toast';

interface Estabelecimento {
    id: number;
    nome_fantasia: string;
    razao_social: string;
    cnpj: string;
    cidade: string;
    estado: string;
    plano: string;
    total_funcionarios: number;
    total_produtos: number;
    total_clientes: number;
    faturamento_total: number;
    ultima_venda: string;
}

interface EstabelecimentoContextType {
    estabelecimentoAtual: Estabelecimento | null;
    setEstabelecimentoAtual: (estabelecimento: Estabelecimento | null) => void;
    estabelecimentos: Estabelecimento[];
    setEstabelecimentos: (estabelecimentos: Estabelecimento[]) => void;
    loading: boolean;
    isSuperAdmin: boolean;
    handleSelectEstabelecimento: (estabelecimento: Estabelecimento) => void;
    handleClearEstabelecimento: () => void;
}

const EstabelecimentoContext = createContext<EstabelecimentoContextType | undefined>(undefined);

export const useEstabelecimento = () => {
    const context = useContext(EstabelecimentoContext);
    if (!context) {
        throw new Error('useEstabelecimento deve ser usado dentro de um EstabelecimentoProvider');
    }
    return context;
};

export const EstabelecimentoProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [estabelecimentoAtual, setEstabelecimentoAtual] = useState<Estabelecimento | null>(null);
    const [estabelecimentos, setEstabelecimentos] = useState<Estabelecimento[]>([]);
    const [loading, setLoading] = useState(false);
    const [isSuperAdmin, setIsSuperAdmin] = useState(false);

    // Carregar estabelecimentos ao iniciar
    useEffect(() => {
        carregarDados();
    }, []);

    // Salvar no localStorage quando mudar
    useEffect(() => {
        if (estabelecimentoAtual) {
            localStorage.setItem('estabelecimentoSelecionado', JSON.stringify(estabelecimentoAtual));
            // Disparar evento global para outras páginas saberem
            window.dispatchEvent(new CustomEvent('estabelecimentoAlterado', {
                detail: estabelecimentoAtual
            }));
        }
    }, [estabelecimentoAtual]);

    // Carregar do localStorage ao iniciar
    useEffect(() => {
        const salvo = localStorage.getItem('estabelecimentoSelecionado');
        const userStr = localStorage.getItem('user');

        if (salvo) {
            const estab = JSON.parse(salvo);
            setEstabelecimentoAtual(estab);
        }

        if (userStr) {
            const user = JSON.parse(userStr);
            setIsSuperAdmin(user.is_super_admin || false);
        }
    }, []);

    const carregarDados = async () => {
        try {
            setLoading(true);
            const response = await apiClient.get('/estabelecimentos');
            if (response.data?.success) {
                const estabs = response.data.estabelecimentos || [];
                setEstabelecimentos(estabs);

                // Se não tiver selecionado, selecionar o primeiro
                const salvo = localStorage.getItem('estabelecimentoSelecionado');
                if (!salvo && estabs.length > 0) {
                    setEstabelecimentoAtual(estabs[0]);
                }
            }
        } catch (error) {
            toast.error('Erro ao carregar estabelecimentos');
        } finally {
            setLoading(false);
        }
    };

    const handleSelectEstabelecimento = (estabelecimento: Estabelecimento) => {
        setEstabelecimentoAtual(estabelecimento);
        toast.success(`Estabelecimento ${estabelecimento.nome_fantasia} selecionado`);
    };

    const handleClearEstabelecimento = () => {
        setEstabelecimentoAtual(null);
        localStorage.removeItem('estabelecimentoSelecionado');
        window.dispatchEvent(new CustomEvent('estabelecimentoAlterado', {
            detail: null
        }));
    };

    return (
        <EstabelecimentoContext.Provider value={{
            estabelecimentoAtual,
            setEstabelecimentoAtual,
            estabelecimentos,
            setEstabelecimentos,
            loading,
            isSuperAdmin,
            handleSelectEstabelecimento,
            handleClearEstabelecimento
        }}>
            {children}
        </EstabelecimentoContext.Provider>
    );
};

export default EstabelecimentoContext;
