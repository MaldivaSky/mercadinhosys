import { toast } from 'react-hot-toast';

export interface CepData {
    cep: string;
    logradouro: string;
    complemento: string;
    bairro: string;
    localidade: string;
    uf: string;
    erro?: boolean;
}

/**
 * Busca dados de endereço a partir do CEP usando a API ViaCEP
 * @param cep - CEP a ser consultado (com ou sem formatação)
 * @returns Dados do endereço ou null em caso de erro
 */
export const buscarCep = async (cep: string): Promise<CepData | null> => {
    const cepLimpo = cep.replace(/\D/g, '');
    
    if (cepLimpo.length !== 8) {
        toast.error('CEP deve conter 8 dígitos');
        return null;
    }

    try {
        const response = await fetch(`https://viacep.com.br/ws/${cepLimpo}/json/`);
        const data: CepData = await response.json();
        
        if (data.erro) {
            toast.error('CEP não encontrado');
            return null;
        }

        toast.success('✅ Endereço preenchido automaticamente!');
        return data;
    } catch (error) {
        console.error('Erro ao buscar CEP:', error);
        toast.error('Erro ao buscar CEP. Verifique sua conexão.');
        return null;
    }
};

/**
 * Formata CEP para o padrão 00000-000
 */
export const formatCep = (value: string): string => {
    const numbers = value.replace(/\D/g, '').slice(0, 8);
    if (numbers.length <= 5) return numbers;
    return `${numbers.slice(0, 5)}-${numbers.slice(5)}`;
};

/**
 * Formata telefone para o padrão (00) 00000-0000
 */
export const formatPhone = (value: string): string => {
    const numbers = value.replace(/\D/g, '').slice(0, 11);
    if (numbers.length <= 2) return numbers;
    if (numbers.length <= 7) return `(${numbers.slice(0, 2)}) ${numbers.slice(2)}`;
    return `(${numbers.slice(0, 2)}) ${numbers.slice(2, 7)}-${numbers.slice(7)}`;
};

/**
 * Formata CNPJ para o padrão 00.000.000/0000-00
 */
export const formatCnpj = (value: string): string => {
    const numbers = value.replace(/\D/g, '').slice(0, 14);
    if (numbers.length <= 2) return numbers;
    if (numbers.length <= 5) return `${numbers.slice(0, 2)}.${numbers.slice(2)}`;
    if (numbers.length <= 8) return `${numbers.slice(0, 2)}.${numbers.slice(2, 5)}.${numbers.slice(5)}`;
    if (numbers.length <= 12) return `${numbers.slice(0, 2)}.${numbers.slice(2, 5)}.${numbers.slice(5, 8)}/${numbers.slice(8)}`;
    return `${numbers.slice(0, 2)}.${numbers.slice(2, 5)}.${numbers.slice(5, 8)}/${numbers.slice(8, 12)}-${numbers.slice(12)}`;
};

/**
 * Formata CPF para o padrão 000.000.000-00
 */
export const formatCpf = (value: string): string => {
    const numbers = value.replace(/\D/g, '').slice(0, 11);
    if (numbers.length <= 3) return numbers;
    if (numbers.length <= 6) return `${numbers.slice(0, 3)}.${numbers.slice(3)}`;
    if (numbers.length <= 9) return `${numbers.slice(0, 3)}.${numbers.slice(3, 6)}.${numbers.slice(6)}`;
    return `${numbers.slice(0, 3)}.${numbers.slice(3, 6)}.${numbers.slice(6, 9)}-${numbers.slice(9)}`;
};
