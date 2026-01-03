export const validators = {
    required: (value: any) => {
        if (!value && value !== 0) return 'Campo obrigatório';
        return '';
    },

    email: (value: string) => {
        if (!value) return '';
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) return 'Email inválido';
        return '';
    },

    cpf: (value: string) => {
        if (!value) return '';
        const cpfRegex = /^\d{3}\.\d{3}\.\d{3}-\d{2}$/;
        if (!cpfRegex.test(value)) return 'CPF inválido';
        return '';
    },

    minLength: (min: number) => (value: string) => {
        if (value.length < min) return `Mínimo ${min} caracteres`;
        return '';
    },

    maxLength: (max: number) => (value: string) => {
        if (value.length > max) return `Máximo ${max} caracteres`;
        return '';
    },

    number: (value: any) => {
        if (isNaN(Number(value))) return 'Deve ser um número';
        return '';
    },

    positive: (value: number) => {
        if (value < 0) return 'Deve ser positivo';
        return '';
    },
};