import React, { ReactNode } from 'react';
import { X } from 'lucide-react';

interface ResponsiveModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  children: ReactNode;
  footer?: ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  headerIcon?: ReactNode;
  headerColor?: 'blue' | 'green' | 'red' | 'indigo' | 'purple';
  closeButton?: boolean;
}

const ResponsiveModal: React.FC<ResponsiveModalProps> = ({
  isOpen,
  onClose,
  title,
  subtitle,
  children,
  footer,
  size = 'lg',
  headerIcon,
  headerColor = 'blue',
  closeButton = true,
}) => {
  if (!isOpen) return null;

  const sizeClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
    full: 'max-w-6xl',
  };

  const headerColorClasses = {
    blue: 'from-blue-500 to-blue-600',
    green: 'from-green-500 to-green-600',
    red: 'from-red-500 to-red-600',
    indigo: 'from-indigo-500 to-indigo-600',
    purple: 'from-purple-500 to-purple-600',
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-2 sm:p-4 overflow-y-auto">
      <div className={`bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full ${sizeClasses[size]} max-h-[95vh] overflow-hidden flex flex-col my-auto`}>
        {/* Header */}
        <div className={`bg-gradient-to-r ${headerColorClasses[headerColor]} px-4 sm:px-6 py-4 flex justify-between items-center flex-shrink-0`}>
          <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
            {headerIcon && (
              <div className="text-white flex-shrink-0">
                {headerIcon}
              </div>
            )}
            <div className="min-w-0">
              <h2 className="text-lg sm:text-xl font-bold text-white truncate">
                {title}
              </h2>
              {subtitle && (
                <p className="text-xs sm:text-sm text-blue-100 truncate">
                  {subtitle}
                </p>
              )}
            </div>
          </div>
          {closeButton && (
            <button
              onClick={onClose}
              className="p-2 hover:bg-white hover:bg-opacity-20 rounded-lg transition-colors flex-shrink-0 ml-2"
              aria-label="Fechar"
            >
              <X className="w-5 h-5 text-white" />
            </button>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          {children}
        </div>

        {/* Footer */}
        {footer && (
          <div className="border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-750 px-4 sm:px-6 py-4 flex-shrink-0">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
};

export default ResponsiveModal;
