import React, { useState } from 'react';
import { apiClient } from '../api/apiClient';

const ConnectionTest: React.FC = () => {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);

    const testPdvRoutes = async () => {
        setLoading(true);
        setError(null);

        try {
            // Testar busca de produtos
            const produtosRes = await apiClient.get('/produtos?page=1&per_page=5');

            // Testar busca de clientes
            const clientesRes = await apiClient.get('/clientes?page=1&per_page=5');

            // Testar formas de pagamento
            const configRes = await apiClient.get('/configuracao');

            setResult({
                produtos: produtosRes.data,
                clientes: clientesRes.data,
                configuracao: configRes.data,
                timestamp: new Date().toISOString(),
            });

        } catch (err: any) {
            setError(err.message || 'Erro desconhecido');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold mb-4">Teste de Conexão PDV</h1>

            <button
                onClick={testPdvRoutes}
                disabled={loading}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400"
            >
                {loading ? 'Testando...' : 'Testar Rotas do PDV'}
            </button>

            {error && (
                <div className="mt-4 p-4 bg-red-100 text-red-700 rounded">
                    <strong>Erro:</strong> {error}
                </div>
            )}

            {result && (
                <div className="mt-4 p-4 bg-green-100 text-green-700 rounded">
                    <strong>Sucesso!</strong> Todas as rotas respondendo.
                    <pre className="mt-2 text-xs overflow-auto">
                        {JSON.stringify(result, null, 2)}
                    </pre>
                </div>
            )}
        </div>
    );
};

export default ConnectionTest;