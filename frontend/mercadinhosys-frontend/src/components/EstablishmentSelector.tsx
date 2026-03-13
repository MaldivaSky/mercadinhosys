import React, { useState, useEffect } from 'react';
import { Building, ChevronDown, CheckCircle2 } from 'lucide-react';
import { apiClient } from '../api/apiClient';
import toast from 'react-hot-toast';

interface Establishment {
  id: number;
  nome_fantasia: string;
  cidade: string;
  estado: string;
  plano: string;
  plano_status: string;
}

interface EstablishmentSelectorProps {
  className?: string;
  selectedEstablishment?: number | null;
  onEstablishmentChange?: (id: number) => void;
}

const EstablishmentSelector: React.FC<EstablishmentSelectorProps> = ({
  className = "",
  selectedEstablishment,
  onEstablishmentChange
}) => {
  const [establishments, setEstablishments] = useState<Establishment[]>([]);
  const [loading, setLoading] = useState(true);
  const [isOpen, setIsOpen] = useState(false);
  const [internalSelectedId, setInternalSelectedId] = useState<number | null>(() => {
    const stored = localStorage.getItem('selected_establishment_id');
    return stored ? parseInt(stored) : null;
  });

  // Use either the controlled prop or the internal state
  const selectedId = selectedEstablishment !== undefined ? selectedEstablishment : internalSelectedId;

  useEffect(() => {
    fetchEstablishments();
  }, []);

  const fetchEstablishments = async () => {
    try {
      setLoading(true);
      // Endpoint que retorna todos os estabelecimentos para o Super-Admin
      const response = await apiClient.get('/saas/monitor/estabelecimentos');

      if (response.data?.success) {
        setEstablishments(response.data.estabelecimentos);
      } else {
        // Fallback para endpoint alternativo se o acima falhar
        const fb = await apiClient.get('/configuracao/estabelecimentos');
        if (fb.data?.success) {
          setEstablishments(fb.data.estabelecimentos);
        }
      }
    } catch (error) {
      console.error('Erro ao buscar estabelecimentos:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelection = (id: number) => {
    if (onEstablishmentChange) {
      onEstablishmentChange(id);
    } else {
      setInternalSelectedId(id);
      localStorage.setItem('selected_establishment_id', id.toString());
      toast.success('Contexto de auditoria alterado');

      // Forçar recarregamento apenas para modo não-controlado
      setTimeout(() => {
        window.location.reload();
      }, 500);
    }
    setIsOpen(false);
  };

  const selectedData = establishments.find(est => est.id === selectedId);

  if (loading && establishments.length === 0) {
    return (
      <div className={`flex items-center space-x-2 px-3 py-1.5 border border-gray-200 rounded-md bg-white/50 animate-pulse ${className}`}>
        <div className="w-3 h-3 bg-gray-300 rounded-full"></div>
        <div className="h-3 w-20 bg-gray-200 rounded"></div>
      </div>
    );
  }

  // Se não houver estabelecimentos (ex: erro na API), não renderiza nada
  if (establishments.length === 0) return null;

  return (
    <div className={`relative ${className}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center space-x-2 px-3 py-1.5 border border-blue-200 rounded-md bg-blue-50/50 hover:bg-blue-100/50 transition-all duration-200 ${isOpen ? 'ring-2 ring-blue-500/20' : ''}`}
        title="Seletor de Contexto (Super-Admin)"
      >
        <Building className="w-4 h-4 text-blue-600" />
        <span className="text-sm font-medium text-blue-900 max-w-[150px] truncate">
          {selectedData ? selectedData.nome_fantasia : 'Selecionar Unidade'}
        </span>
        <ChevronDown className={`w-3 h-3 text-blue-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-[1300]" onClick={() => setIsOpen(false)} />
          <div className="absolute top-full right-0 mt-2 w-72 bg-white border border-gray-200 rounded-lg shadow-xl z-[1301] overflow-hidden">
            <div className="px-4 py-2 bg-gray-50 border-b border-gray-200">
              <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Modo Auditoria Master</span>
            </div>
            <div className="max-h-80 overflow-y-auto">
              {establishments.map((est) => (
                <button
                  key={est.id}
                  onClick={() => handleSelection(est.id)}
                  className={`w-full flex items-start justify-between p-3 hover:bg-blue-50 transition-colors text-left border-b border-gray-100 last:border-0 ${selectedId === est.id ? 'bg-blue-50/50' : ''}`}
                >
                  <div className="flex-1 min-w-0">
                    <div className="font-semibold text-gray-900 text-sm truncate">{est.nome_fantasia}</div>
                    <div className="text-xs text-gray-500 truncate">{est.cidade}, {est.estado}</div>
                  </div>
                  {selectedId === est.id && (
                    <CheckCircle2 className="w-4 h-4 text-green-500 ml-2 mt-0.5" />
                  )}
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default EstablishmentSelector;
