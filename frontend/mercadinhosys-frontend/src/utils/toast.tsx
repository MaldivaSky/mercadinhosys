import toast, { ToastOptions } from 'react-hot-toast';
import { CheckCircle2, XCircle, AlertTriangle, Info } from 'lucide-react';

/* 
 * Professional Toast Utility 
 * Wraps react-hot-toast with consistent styling and icons.
 */

const TOAST_DURATION = 4000;
const TOAST_POSITION = 'top-right';

const defaultStyle = {
    padding: '16px',
    borderRadius: '12px',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    fontWeight: 500,
    fontSize: '0.95rem',
    maxWidth: '400px',
};

export const showToast = {
    success: (message: string, options?: ToastOptions) => {
        toast.success(message, {
            duration: TOAST_DURATION,
            position: TOAST_POSITION,
            style: {
                ...defaultStyle,
                background: '#ECFDF5', // green-50
                border: '1px solid #10B981', // green-500
                color: '#065F46', // green-800
            },
            icon: <CheckCircle2 className="w-5 h-5 text-green-600" />,
            ...options,
        });
    },

    error: (message: string, options?: ToastOptions) => {
        toast.error(message, {
            duration: 5000,
            position: TOAST_POSITION,
            style: {
                ...defaultStyle,
                background: '#FEF2F2', // red-50
                border: '1px solid #EF4444', // red-500
                color: '#991B1B', // red-800
            },
            icon: <XCircle className="w-5 h-5 text-red-600" />,
            ...options,
        });
    },

    warning: (message: string, options?: ToastOptions) => {
        toast(message, {
            duration: TOAST_DURATION,
            position: TOAST_POSITION,
            style: {
                ...defaultStyle,
                background: '#FFFBEB', // amber-50
                border: '1px solid #F59E0B', // amber-500
                color: '#92400E', // amber-800
            },
            icon: <AlertTriangle className="w-5 h-5 text-amber-600" />,
            ...options,
        });
    },

    info: (message: string, options?: ToastOptions) => {
        toast(message, {
            duration: TOAST_DURATION,
            position: TOAST_POSITION,
            style: {
                ...defaultStyle,
                background: '#EFF6FF', // blue-50
                border: '1px solid #3B82F6', // blue-500
                color: '#1E40AF', // blue-800
            },
            icon: <Info className="w-5 h-5 text-blue-600" />,
            ...options,
        });
    },

    // Default loading
    loading: (message: string) => toast.loading(message, {
        style: { ...defaultStyle, background: '#fff', color: '#333' }
    }),

    // Dismiss
    dismiss: (toastId?: string) => toast.dismiss(toastId),
};
