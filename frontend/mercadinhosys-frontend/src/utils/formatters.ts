export const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL',
    }).format(value);
};

export const formatDate = (date: string | Date): string => {
    return new Intl.DateTimeFormat('pt-BR').format(new Date(date));
};

export const formatDateTime = (date: string | Date): string => {
    return new Intl.DateTimeFormat('pt-BR', {
        dateStyle: 'short',
        timeStyle: 'short',
    }).format(new Date(date));
};

export const formatCPF = (cpf: string): string => {
    return cpf.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
};

export const formatPhone = (phone: string): string => {
    return phone.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
};