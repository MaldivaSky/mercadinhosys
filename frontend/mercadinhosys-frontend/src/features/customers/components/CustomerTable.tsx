import React from 'react';
import { Cliente } from '../../../types';
import { IconButton, Tooltip, Skeleton, Chip } from '@mui/material';
import { Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material';
import HandshakeIcon from '@mui/icons-material/Handshake';

interface CustomerTableProps {
  clientes: Cliente[];
  loading?: boolean;
  onRowClick?: (cliente: Cliente) => void;
  onEdit?: (cliente: Cliente) => void;
  onDelete?: (cliente: Cliente) => void;
  onReceberFiado?: (cliente: Cliente) => void;
  selectedClienteId?: number;
  rfmData?: any;
}
const CustomerTable: React.FC<CustomerTableProps> = ({ clientes, loading, onRowClick, onEdit, onDelete, onReceberFiado, selectedClienteId, rfmData }) => {
  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead className="bg-gray-50 dark:bg-gray-800">
          <tr>
            <th className="px-2 sm:px-4 py-2 text-left text-xs font-semibold text-gray-700 dark:text-gray-200">Nome</th>
            <th className="hidden sm:table-cell px-4 py-2 text-left text-xs font-semibold text-gray-700 dark:text-gray-200">CPF</th>
            <th className="hidden md:table-cell px-4 py-2 text-left text-xs font-semibold text-gray-700 dark:text-gray-200">Telefone</th>
            <th className="hidden lg:table-cell px-4 py-2 text-left text-xs font-semibold text-gray-700 dark:text-gray-200">Email</th>
            <th className="px-4 py-2 text-left text-xs font-semibold text-gray-700 dark:text-gray-200">Fiado</th>
            <th className="px-4 py-2 text-left text-xs font-semibold text-gray-700 dark:text-gray-200">Segmento</th>
            <th className="px-2 sm:px-4 py-2 text-center text-xs font-semibold text-gray-700 dark:text-gray-200">Ações</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
          {loading ? (
            Array.from({ length: 5 }).map((_, index) => (
              <tr key={index}>
                <td className="px-4 py-2"><Skeleton variant="text" width={150} /></td>
                <td className="px-4 py-2"><Skeleton variant="text" width={120} /></td>
                <td className="px-4 py-2"><Skeleton variant="text" width={130} /></td>
                <td className="px-4 py-2"><Skeleton variant="text" width={100} /></td>
                <td className="px-4 py-2"><Skeleton variant="text" width={80} /></td>
                <td className="px-4 py-2 text-center"><Skeleton variant="rectangular" width={100} height={36} /></td>
              </tr>
            ))
          ) : clientes.length === 0 ? (
            <tr>
              <td colSpan={6} className="px-4 py-6 text-center text-gray-500 dark:text-gray-400">
                Nenhum cliente encontrado.
              </td>
            </tr>
          ) : (
            clientes.map((cliente) => {
              const temFiado = (cliente.saldo_devedor ?? 0) > 0;
              return (
                <tr
                  key={cliente.id}
                  className={`transition cursor-pointer ${selectedClienteId === cliente.id
                      ? 'bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500'
                      : temFiado
                        ? 'bg-orange-50 dark:bg-orange-900/10 hover:bg-orange-100 dark:hover:bg-orange-900/20'
                        : 'hover:bg-gray-50 dark:hover:bg-gray-800'
                    }`}
                  onClick={onRowClick ? () => onRowClick(cliente) : undefined}
                >

                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-10 w-10 flex items-center justify-center rounded-full bg-blue-100 text-blue-600 font-bold shadow-sm">
                        {cliente.nome ? cliente.nome.charAt(0).toUpperCase() : '?'}
                      </div>
                      <div className="ml-3">
                        <div className="text-sm font-bold text-gray-900 dark:text-white">
                          {cliente.nome}
                        </div>
                        <div className="text-xs text-gray-500 flex items-center mt-0.5">
                          {cliente.cpf ? `CPF: ${cliente.cpf}` : 'Sem documento'}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="hidden sm:table-cell px-4 py-2 whitespace-nowrap">{cliente.cpf || '-'}</td>
                  <td className="hidden md:table-cell px-4 py-3 whitespace-nowrap">
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      {cliente.celular || cliente.telefone || <span className="text-gray-400 font-normal italic">Não informado</span>}
                    </span>
                  </td>
                  <td className="hidden lg:table-cell px-4 py-3 whitespace-nowrap">
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      {cliente.email || <span className="text-gray-400 italic">Não informado</span>}
                    </div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    {temFiado ? (
                      <Chip
                        label={(cliente.saldo_devedor ?? 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                        size="small"
                        icon={<HandshakeIcon style={{ fontSize: 14 }} />}
                        sx={{
                          bgcolor: '#fff3e0',
                          color: '#e65100',
                          fontWeight: 700,
                          border: '1px solid #ffcc80',
                          fontSize: '0.75rem',
                          boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
                        }}
                      />
                    ) : (
                      <span className="text-xs font-medium text-gray-400 bg-gray-50 px-2 py-1 rounded-md border border-gray-100">Sem fiado</span>
                    )}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                     {rfmData && rfmData.customers && rfmData.customers.find((c: any) => c.cliente_id === cliente.id) ? (
                        <Chip
                           label={rfmData.customers.find((c: any) => c.cliente_id === cliente.id).segment}
                           size="small"
                           sx={{
                             fontWeight: 700,
                             fontSize: '0.7rem',
                             letterSpacing: 0.5,
                             textTransform: 'uppercase',
                             bgcolor: rfmData.customers.find((c: any) => c.cliente_id === cliente.id).segment === 'Campeão' ? '#e8f5e9' : 
                                      rfmData.customers.find((c: any) => c.cliente_id === cliente.id).segment === 'Fiel' ? '#e3f2fd' : 
                                      rfmData.customers.find((c: any) => c.cliente_id === cliente.id).segment === 'Perdido' ? '#ffebee' : '#f3e5f5',
                             color: rfmData.customers.find((c: any) => c.cliente_id === cliente.id).segment === 'Campeão' ? '#2e7d32' : 
                                      rfmData.customers.find((c: any) => c.cliente_id === cliente.id).segment === 'Fiel' ? '#1565c0' : 
                                      rfmData.customers.find((c: any) => c.cliente_id === cliente.id).segment === 'Perdido' ? '#c62828' : '#7b1fa2',
                             border: '1px solid',
                             borderColor: rfmData.customers.find((c: any) => c.cliente_id === cliente.id).segment === 'Campeão' ? '#c8e6c9' : 
                                      rfmData.customers.find((c: any) => c.cliente_id === cliente.id).segment === 'Fiel' ? '#bbdefb' : 
                                      rfmData.customers.find((c: any) => c.cliente_id === cliente.id).segment === 'Perdido' ? '#ffcdd2' : '#e1bee7',
                           }}
                        />
                     ) : <span className="text-xs text-gray-400">—</span>}
                  </td>
                  <td className="px-2 sm:px-4 py-3 whitespace-nowrap text-center">
                    <div className="flex justify-center space-x-1" onClick={(e) => e.stopPropagation()}>
                      {temFiado && onReceberFiado && (
                        <Tooltip title="Receber Fiado">
                          <IconButton size="small" onClick={() => onReceberFiado(cliente)} sx={{ color: '#f57c00' }}>
                            <HandshakeIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                      {onEdit && (
                        <Tooltip title="Editar">
                          <IconButton size="small" onClick={() => onEdit(cliente)} color="primary">
                            <EditIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                      {onDelete && (
                        <Tooltip title="Excluir">
                          <IconButton size="small" onClick={() => onDelete(cliente)} color="error">
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
};

export default CustomerTable;
