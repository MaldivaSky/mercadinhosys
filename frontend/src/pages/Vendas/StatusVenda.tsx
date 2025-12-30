import React from 'react';
import { CheckCircle, Clock, XCircle, TrendingUp } from 'lucide-react';

export type StatusVendaType = 'pendente' | 'processando' | 'finalizada' | 'cancelada' | 'sucesso';

interface StatusVendaProps {
    status: StatusVendaType;
    tamanho?: 'sm' | 'md' | 'lg';
    mostrarTexto?: boolean;
}

const StatusVenda: React.FC<StatusVendaProps> = ({
    status,
    tamanho = 'md',
    mostrarTexto = true
}) => {
    const config = {
        pendente: {
            icon: Clock,
            texto: 'Pendente',
            cor: 'text-yellow-600',
            bg: 'bg-yellow-100',
            border: 'border-yellow-200'
        },
        processando: {
            icon: TrendingUp,
            texto: 'Processando',
            cor: 'text-blue-600',
            bg: 'bg-blue-100',
            border: 'border-blue-200'
        },
        finalizada: {
            icon: CheckCircle,
            texto: 'Finalizada',
            cor: 'text-green-600',
            bg: 'bg-green-100',
            border: 'border-green-200'
        },
        sucesso: {
            icon: CheckCircle,
            texto: 'Sucesso',
            cor: 'text-green-600',
            bg: 'bg-green-100',
            border: 'border-green-200'
        },
        cancelada: {
            icon: XCircle,
            texto: 'Cancelada',
            cor: 'text-red-600',
            bg: 'bg-red-100',
            border: 'border-red-200'
        }
    };

    const { icon: Icon, texto, cor, bg, border } = config[status];

    const sizeClasses = {
        sm: 'text-xs px-2 py-1',
        md: 'text-sm px-3 py-1.5',
        lg: 'text-base px-4 py-2'
    };

    return (
        <div className={`inline-flex items-center rounded-full border ${sizeClasses[tamanho]} ${bg} ${border}`}>
            <Icon className={`h-4 w-4 mr-2 ${cor}`} />
            {mostrarTexto && <span className={`font-medium ${cor}`}>{texto}</span>}
        </div>
    );
};

// Componente para timeline de status
export const TimelineStatus: React.FC<{ status: StatusVendaType }> = ({ status }) => {
    const etapas = [
        { id: 'pendente', label: 'Iniciada' },
        { id: 'processando', label: 'Processando' },
        { id: 'finalizada', label: 'Finalizada' }
    ];

    const statusIndex = etapas.findIndex(e => e.id === status);

    return (
        <div className="flex items-center justify-between max-w-md mx-auto">
            {etapas.map((etapa, index) => {
                const isActive = index <= statusIndex;
                const isCurrent = etapa.id === status;

                return (
                    <React.Fragment key={etapa.id}>
                        {/* Etapa */}
                        <div className="flex flex-col items-center">
                            <div className={`
                h-10 w-10 rounded-full flex items-center justify-center
                ${isActive ? 'bg-azul-principal text-white' : 'bg-gray-200 text-gray-400'}
                ${isCurrent ? 'ring-4 ring-blue-100' : ''}
              `}>
                                {isActive ? (
                                    <CheckCircle className="h-6 w-6" />
                                ) : (
                                    <div className="h-4 w-4 rounded-full bg-gray-400" />
                                )}
                            </div>
                            <span className={`mt-2 text-sm font-medium ${isActive ? 'text-gray-800' : 'text-gray-400'}`}>
                                {etapa.label}
                            </span>
                        </div>

                        {/* Linha */}
                        {index < etapas.length - 1 && (
                            <div className={`flex-1 h-1 ${index < statusIndex ? 'bg-azul-principal' : 'bg-gray-200'}`} />
                        )}
                    </React.Fragment>
                );
            })}
        </div>
    );
};

export default StatusVenda;