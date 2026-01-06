import React from 'react';
import { Cliente } from '../../../types';
import { Button } from '@mui/material';

interface CustomerTableProps {
  clientes: Cliente[];
  onEdit: (cliente: Cliente) => void;
  onDelete: (cliente: Cliente) => void;
  loading?: boolean;
}

const CustomerTable: React.FC<CustomerTableProps> = ({ clientes, onEdit, onDelete, loading }) => {
  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead className="bg-gray-50 dark:bg-gray-800">
          <tr>
            <th className="px-4 py-2 text-left text-xs font-semibold text-gray-700 dark:text-gray-200">Nome</th>
            <th className="px-4 py-2 text-left text-xs font-semibold text-gray-700 dark:text-gray-200">CPF/CNPJ</th>
            <th className="px-4 py-2 text-left text-xs font-semibold text-gray-700 dark:text-gray-200">Telefone</th>
            <th className="px-4 py-2 text-left text-xs font-semibold text-gray-700 dark:text-gray-200">Email</th>
            <th className="px-4 py-2 text-left text-xs font-semibold text-gray-700 dark:text-gray-200">Total Compras</th>
            <th className="px-4 py-2 text-left text-xs font-semibold text-gray-700 dark:text-gray-200">Última Compra</th>
            <th className="px-4 py-2 text-center text-xs font-semibold text-gray-700 dark:text-gray-200">Ações</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
          {clientes.length === 0 && (
            <tr>
              <td colSpan={7} className="px-4 py-6 text-center text-gray-500 dark:text-gray-400">
                {loading ? 'Carregando clientes...' : 'Nenhum cliente encontrado.'}
              </td>
            </tr>
          )}
          {clientes.map((cliente) => (
            <tr key={cliente.id} className="hover:bg-gray-50 dark:hover:bg-gray-800 transition">
              <td className="px-4 py-2 whitespace-nowrap">{cliente.nome || '-'}</td>
              <td className="px-4 py-2 whitespace-nowrap">{cliente.cpf_cnpj || '-'}</td>
              <td className="px-4 py-2 whitespace-nowrap">{cliente.telefone || '-'}</td>
              <td className="px-4 py-2 whitespace-nowrap">{cliente.email || '-'}</td>
              <td className="px-4 py-2 whitespace-nowrap">{typeof cliente.total_compras === 'number' ? `R$ ${cliente.total_compras.toFixed(2)}` : '-'}</td>
              <td className="px-4 py-2 whitespace-nowrap">{cliente.ultima_compra ? new Date(cliente.ultima_compra).toLocaleDateString() : '-'}</td>
              <td className="px-4 py-2 whitespace-nowrap text-center">
                <Button size="small" variant="outlined" color="primary" onClick={() => onEdit(cliente)} style={{marginRight: 8}}>Editar</Button>
                <Button size="small" variant="outlined" color="error" onClick={() => onDelete(cliente)}>Excluir</Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default CustomerTable;
