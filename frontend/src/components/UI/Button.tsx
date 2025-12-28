import React from 'react';

interface ButtonProps {
    children: React.ReactNode;
    variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'danger';
    size?: 'sm' | 'md' | 'lg';
    className?: string;
    onClick?: () => void;
    disabled?: boolean;
    icon?: React.ReactNode;
    type?: 'button' | 'submit' | 'reset'; // Adicione esta linha
}

const Button: React.FC<ButtonProps> = ({
    children,
    variant = 'primary',
    size = 'md',
    className = '',
    onClick,
    disabled = false,
    icon,
    type = 'button', // Valor padrão
}) => {
    const variantClasses = {
        primary: 'bg-azul-principal hover:bg-blue-700 text-white',
        secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-800',
        success: 'bg-verde-positivo hover:bg-green-700 text-white',
        warning: 'bg-laranja-alerta hover:bg-orange-700 text-white',
        danger: 'bg-red-600 hover:bg-red-700 text-white',
    };

    const sizeClasses = {
        sm: 'px-3 py-1.5 text-sm',
        md: 'px-4 py-2',
        lg: 'px-6 py-3 text-lg',
    };

    return (
        <button
            type={type} // Adicione esta linha
            onClick={onClick}
            disabled={disabled}
            className={`
        ${variantClasses[variant]}
        ${sizeClasses[size]}
        rounded-lg font-medium
        transition-colors duration-200
        flex items-center justify-center
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        ${className}
      `}
        >
            {icon && <span className="mr-2">{icon}</span>}
            {children}
        </button>
    );
};

export default Button;