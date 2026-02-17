import React from 'react';
import toast, { ToastOptions } from 'react-hot-toast';

/*
 * MercadinhoSys — Toast Profissional
 * Design adaptado para dark mode (padrão do sistema).
 * Cores sólidas, alto contraste, ícones SVG inline sem dependência de classes Tailwind.
 */

// ─── Estilos base ─────────────────────────────────────────────────────────────
const base: React.CSSProperties = {
    padding: '14px 18px',
    borderRadius: '10px',
    fontFamily: 'system-ui, -apple-system, sans-serif',
    fontSize: '14px',
    fontWeight: 500,
    lineHeight: '1.4',
    maxWidth: '420px',
    minWidth: '280px',
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    boxShadow: '0 8px 24px rgba(0,0,0,0.35)',
    border: '1px solid',
};

const themes = {
    success: {
        style: {
            ...base,
            background: '#0f4c2a',
            color: '#86efac',
            borderColor: '#166534',
        },
        iconColor: '#4ade80',
    },
    error: {
        style: {
            ...base,
            background: '#4c0f0f',
            color: '#fca5a5',
            borderColor: '#7f1d1d',
        },
        iconColor: '#f87171',
    },
    warning: {
        style: {
            ...base,
            background: '#4a3000',
            color: '#fde68a',
            borderColor: '#78350f',
        },
        iconColor: '#fbbf24',
    },
    info: {
        style: {
            ...base,
            background: '#0f2f4c',
            color: '#93c5fd',
            borderColor: '#1e3a5f',
        },
        iconColor: '#60a5fa',
    },
    loading: {
        style: {
            ...base,
            background: '#1e293b',
            color: '#cbd5e1',
            borderColor: '#334155',
        },
        iconColor: '#94a3b8',
    },
};

// ─── Ícones SVG inline (sem Tailwind) ─────────────────────────────────────────
const Icon = {
    success: (c: string) => (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
            <path d="M20 6L9 17l-5-5" />
        </svg>
    ),
    error: (c: string) => (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
            <circle cx="12" cy="12" r="10" />
            <line x1="15" y1="9" x2="9" y2="15" />
            <line x1="9" y1="9" x2="15" y2="15" />
        </svg>
    ),
    warning: (c: string) => (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
            <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
    ),
    info: (c: string) => (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
    ),
};

// ─── API pública ───────────────────────────────────────────────────────────────
export const showToast = {
    success: (message: string, options?: ToastOptions) => {
        const t = themes.success;
        toast.success(message, {
            duration: 3500,
            style: t.style as React.CSSProperties,
            icon: Icon.success(t.iconColor),
            ...options,
        });
    },

    error: (message: string, options?: ToastOptions) => {
        const t = themes.error;
        toast.error(message, {
            duration: 5000,
            style: t.style as React.CSSProperties,
            icon: Icon.error(t.iconColor),
            ...options,
        });
    },

    warning: (message: string, options?: ToastOptions) => {
        const t = themes.warning;
        toast(message, {
            duration: 4500,
            style: t.style as React.CSSProperties,
            icon: Icon.warning(t.iconColor),
            ...options,
        });
    },

    info: (message: string, options?: ToastOptions) => {
        const t = themes.info;
        toast(message, {
            duration: 3500,
            style: t.style as React.CSSProperties,
            icon: Icon.info(t.iconColor),
            ...options,
        });
    },

    loading: (message: string, options?: ToastOptions) => {
        return toast.loading(message, {
            style: themes.loading.style as React.CSSProperties,
            ...options,
        });
    },

    dismiss: (toastId?: string) => toast.dismiss(toastId),

    promise: <T,>(
        promise: Promise<T>,
        msgs: { loading: string; success: string; error: string },
        options?: ToastOptions
    ) => {
        return toast.promise(promise, msgs, {
            style: themes.loading.style as React.CSSProperties,
            success: { style: themes.success.style as React.CSSProperties, icon: Icon.success(themes.success.iconColor) },
            error: { style: themes.error.style as React.CSSProperties, icon: Icon.error(themes.error.iconColor) },
            ...options,
        });
    },
};
