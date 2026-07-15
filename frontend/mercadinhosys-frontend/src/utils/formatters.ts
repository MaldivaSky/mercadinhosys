const DATE_ONLY_RE = /^\d{4}-\d{2}-\d{2}$/;

export const parseDatePreservingLocalDay = (date: string | Date | null | undefined): Date | null => {
    if (!date) return null;
    if (date instanceof Date) return date;

    const raw = String(date).trim();
    if (DATE_ONLY_RE.test(raw)) {
        const [year, month, day] = raw.split('-').map(Number);
        // Meio-dia local evita o recuo/avanço de dia causado por UTC.
        return new Date(year, month - 1, day, 12, 0, 0, 0);
    }

    const parsed = new Date(raw);
    return isNaN(parsed.getTime()) ? null : parsed;
};

export const localDateInputValue = (date = new Date()): string => {
    const local = new Date(date);
    local.setMinutes(local.getMinutes() - local.getTimezoneOffset());
    return local.toISOString().slice(0, 10);
};

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
        const d = parseDatePreservingLocalDay(date);
        if (!d) return '---';
        return new Intl.DateTimeFormat('pt-BR').format(d);
    } catch (e) {
        return '---';
    }
};

export const formatDateTime = (date: string | Date | null | undefined): string => {
    if (!date) return '---';
    try {
        const d = parseDatePreservingLocalDay(date);
        if (!d) return '---';
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

/**
 * Corrige URLs de imagem que utilizam o serviço via.placeholder.com (que está instável/fora do ar)
 * substituindo pelo serviço placehold.co.
 */
export const fixImageUrl = (url: string | null | undefined): string | undefined => {
    if (!url) return undefined;
    if (url.includes('via.placeholder.com')) {
        return url.replace('via.placeholder.com', 'placehold.co');
    }
    return url;
};
