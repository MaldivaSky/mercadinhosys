import toast, { ToastOptions } from 'react-hot-toast';

/**
 * Sistema de notificações profissional — MercadinhoSys
 * Compatível com dark mode (padrão do app).
 */

export const showToast = {
    success: (message: string, options?: ToastOptions) => {
        toast.success(message, {
            duration: 4000,
            position: 'top-right',
            style: {
                background: '#052e16',
                border: '1px solid #16a34a',
                color: '#86efac',
                borderRadius: '10px',
                padding: '14px 18px',
                fontWeight: 600,
                fontSize: '0.9rem',
                maxWidth: '420px',
                boxShadow: '0 0 0 1px rgba(22,163,74,0.2), 0 4px 24px rgba(0,0,0,0.4)',
            },
            iconTheme: {
                primary: '#22c55e',
                secondary: '#052e16',
            },
            ...options,
        });
    },

    error: (message: string, options?: ToastOptions) => {
        toast.error(message, {
            duration: 5000,
            position: 'top-right',
            style: {
                background: '#2d0a0a',
                border: '1px solid #dc2626',
                color: '#fca5a5',
                borderRadius: '10px',
                padding: '14px 18px',
                fontWeight: 600,
                fontSize: '0.9rem',
                maxWidth: '420px',
                boxShadow: '0 0 0 1px rgba(220,38,38,0.2), 0 4px 24px rgba(0,0,0,0.4)',
            },
            iconTheme: {
                primary: '#ef4444',
                secondary: '#2d0a0a',
            },
            ...options,
        });
    },

    warning: (message: string, options?: ToastOptions) => {
        toast(message, {
            duration: 4500,
            position: 'top-right',
            icon: '⚠️',
            style: {
                background: '#1c1407',
                border: '1px solid #d97706',
                color: '#fcd34d',
                borderRadius: '10px',
                padding: '14px 18px',
                fontWeight: 600,
                fontSize: '0.9rem',
                maxWidth: '420px',
                boxShadow: '0 0 0 1px rgba(217,119,6,0.2), 0 4px 24px rgba(0,0,0,0.4)',
            },
            ...options,
        });
    },

    info: (message: string, options?: ToastOptions) => {
        toast(message, {
            duration: 4000,
            position: 'top-right',
            icon: 'ℹ️',
            style: {
                background: '#020c1b',
                border: '1px solid #2563eb',
                color: '#93c5fd',
                borderRadius: '10px',
                padding: '14px 18px',
                fontWeight: 600,
                fontSize: '0.9rem',
                maxWidth: '420px',
                boxShadow: '0 0 0 1px rgba(37,99,235,0.2), 0 4px 24px rgba(0,0,0,0.4)',
            },
            ...options,
        });
    },

    loading: (message: string, options?: ToastOptions) => toast.loading(message, {
        position: 'top-right',
        style: {
            background: '#111827',
            border: '1px solid #374151',
            color: '#d1d5db',
            borderRadius: '10px',
            padding: '14px 18px',
            fontWeight: 600,
            fontSize: '0.9rem',
            maxWidth: '420px',
        },
        ...options,
    }),

    dismiss: (toastId?: string) => toast.dismiss(toastId),
};
