export const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    }).format(value);
};

export const formatDate = (date: string | Date | null | undefined): string => {
    if (!date) return '---';
    try {
        const d = new Date(date);
        if (isNaN(d.getTime())) return '---';
        return new Intl.DateTimeFormat('pt-BR').format(d);
    } catch (e) {
        return '---';
    }
};

export const formatDateTime = (date: string | Date | null | undefined): string => {
    if (!date) return '---';
    try {
        const d = new Date(date);
        if (isNaN(d.getTime())) return '---';
        return new Intl.DateTimeFormat('pt-BR', {
            dateStyle: 'short',
            timeStyle: 'short',
        }).format(d);
    } catch (e) {
        return '---';
    }
};

export const formatCPF = (cpf: string): string => {
    return cpf.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
};

export const formatPhone = (phone: string): string => {
    return phone.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
};