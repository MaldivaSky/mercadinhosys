import React from 'react';
import { Cliente } from '../../../types';
import { IconButton, Tooltip, Skeleton } from '@mui/material';
import { Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material';

interface CustomerTableProps {
  clientes: Cliente[];
  loading?: boolean;
  onRowClick?: (cliente: Cliente) => void;
  onEdit?: (cliente: Cliente) => void;
  onDelete?: (cliente: Cliente) => void;
  selectedClienteId?: number;
}
const CustomerTable: React.FC<CustomerTableProps> = ({ clientes, loading, onRowClick, onEdit, onDelete, selectedClienteId }) => {
  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead className="bg-gray-50 dark:bg-gray-800">
          <tr>
            <th className="px-2 sm:px-4 py-2 text-left text-xs font-semibold text-gray-700 dark:text-gray-200">Nome</th>
            <th className="hidden sm:table-cell px-4 py-2 text-left text-xs font-semibold text-gray-700 dark:text-gray-200">CPF</th>
            <th className="hidden md:table-cell px-4 py-2 text-left text-xs font-semibold text-gray-700 dark:text-gray-200">Telefone</th>
            <th className="hidden lg:table-cell px-4 py-2 text-left text-xs font-semibold text-gray-700 dark:text-gray-200">Email</th>
            <th className="px-2 sm:px-4 py-2 text-center text-xs font-semibold text-gray-700 dark:text-gray-200">Ações</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
          {loading ? (
            // Skeleton loading
            Array.from({ length: 5 }).map((_, index) => (
              <tr key={index}>
                <td className="px-4 py-2"><Skeleton variant="text" width={150} /></td>
                <td className="px-4 py-2"><Skeleton variant="text" width={120} /></td>
                <td className="px-4 py-2"><Skeleton variant="text" width={130} /></td>
                <td className="px-4 py-2"><Skeleton variant="text" width={100} /></td>
                <td className="px-4 py-2 text-center"><Skeleton variant="rectangular" width={80} height={36} /></td>
              </tr>
            ))
          ) : clientes.length === 0 ? (
            <tr>
              <td colSpan={5} className="px-4 py-6 text-center text-gray-500 dark:text-gray-400">
                Nenhum cliente encontrado.
              </td>
            </tr>
          ) : (
            clientes.map((cliente) => (
              <tr
                key={cliente.id}
                className={`transition cursor-pointer ${
                  selectedClienteId === cliente.id
                    ? 'bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500'
                    : 'hover:bg-gray-50 dark:hover:bg-gray-800'
                }`}
                onClick={onRowClick ? () => onRowClick(cliente) : undefined}
              >
                <td className="px-2 sm:px-4 py-2 whitespace-nowrap">
                  <div>
                    <div className="font-medium">{cliente.nome || '-'}</div>
                    <div className="text-xs text-gray-500 sm:hidden">{cliente.cpf || '-'}</div>
                    <div className="text-xs text-gray-500 md:hidden sm:hidden">{cliente.celular || cliente.telefone || '-'}</div>
                  </div>
                </td>
                <td className="hidden sm:table-cell px-4 py-2 whitespace-nowrap">{cliente.cpf || '-'}</td>
                <td className="hidden md:table-cell px-4 py-2 whitespace-nowrap">{cliente.celular || cliente.telefone || '-'}</td>
                <td className="hidden lg:table-cell px-4 py-2 whitespace-nowrap">{cliente.email || '-'}</td>
                <td className="px-2 sm:px-4 py-2 whitespace-nowrap text-center">
                  <div className="flex justify-center space-x-1" onClick={(e) => e.stopPropagation()}>
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
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};

export default CustomerTable;
