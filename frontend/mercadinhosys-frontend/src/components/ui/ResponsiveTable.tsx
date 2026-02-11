import React, { ReactNode } from 'react';

interface ResponsiveTableProps {
  headers: string[];
  rows: (string | number | ReactNode)[][];
  compact?: boolean;
  striped?: boolean;
  hoverable?: boolean;
  children?: ReactNode;
}

const ResponsiveTable: React.FC<ResponsiveTableProps> = ({
  headers,
  rows,
  compact = false,
  striped = true,
  hoverable = true,
  children,
}) => {
  return (
    <div className="w-full overflow-x-auto">
      <table className="w-full text-xs sm:text-sm">
        <thead>
          <tr className="bg-gray-100 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600">
            {headers.map((header, idx) => (
              <th
                key={idx}
                className={`text-left font-semibold text-gray-700 dark:text-gray-300 ${
                  compact ? 'px-2 sm:px-4 py-2' : 'px-3 sm:px-6 py-3'
                }`}
              >
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIdx) => (
            <tr
              key={rowIdx}
              className={`border-b border-gray-200 dark:border-gray-700 ${
                striped && rowIdx % 2 === 0
                  ? 'bg-gray-50 dark:bg-gray-800'
                  : 'bg-white dark:bg-gray-750'
              } ${
                hoverable
                  ? 'hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors'
                  : ''
              }`}
            >
              {row.map((cell, cellIdx) => (
                <td
                  key={cellIdx}
                  className={`text-gray-700 dark:text-gray-300 ${
                    compact ? 'px-2 sm:px-4 py-2' : 'px-3 sm:px-6 py-3'
                  }`}
                >
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {children}
    </div>
  );
};

export default ResponsiveTable;
