import React from 'react';

interface CardProps {
    title: string;
    children: React.ReactNode;
    className?: string;
    icon?: React.ReactNode;
    footer?: React.ReactNode;
}

const Card: React.FC<CardProps> = ({
    title,
    children,
    className = '',
    icon,
    footer
}) => {
    return (
        <div className={`bg-white rounded-xl shadow-md overflow-hidden ${className}`}>
            {/* Cabeçalho do Card */}
            <div className="px-6 py-4 border-b border-gray-100">
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                        {icon && (
                            <div className="text-azul-principal">
                                {icon}
                            </div>
                        )}
                        <h3 className="text-lg font-semibold text-gray-800">{title}</h3>
                    </div>
                </div>
            </div>

            {/* Corpo do Card */}
            <div className="p-6">
                {children}
            </div>

            {/* Footer do Card (opcional) */}
            {footer && (
                <div className="px-6 py-4 bg-gray-50 border-t border-gray-100">
                    {footer}
                </div>
            )}
        </div>
    );
};

export default Card;