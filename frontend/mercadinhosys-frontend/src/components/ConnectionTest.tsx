// src/components/ConnectionTest.tsx
import { useState } from 'react';

export function ConnectionTest() {
    const [message, setMessage] = useState('');
    const [loading, setLoading] = useState(false);

    const testBackendConnection = async () => {
        setLoading(true);
        setMessage('🔄 Testando conexão com backend...');

        try {
            // Teste 1: Endpoint health básico
            const response = await fetch('http://localhost:5000/api/health');
            const data = await response.json();

            if (response.ok) {
                setMessage(`✅ Backend conectado! Status: ${data.status || 'OK'}`);
            } else {
                setMessage(`⚠️ Backend respondeu com erro: ${data.message || 'Erro desconhecido'}`);
            }
        } catch (error: any) {
            // Teste 2: Endpoint raiz alternativo
            try {
                const altResponse = await fetch('http://localhost:5000/');
                const altData = await altResponse.json();
                setMessage(`✅ Backend conectado (via raiz)! Mensagem: ${altData.message || 'OK'}`);
            } catch (altError) {
                setMessage(`❌ Erro ao conectar com backend: ${error.message}. Verifique se o Flask está rodando na porta 5000.`);
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="card p-6 mb-6">
            <h3 className="text-xl font-semibold mb-4 text-gray-100">
                🔧 Teste de Conexão Backend
            </h3>

            <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4 mb-4">
                <p className="text-blue-300 text-sm">
                    Clique no botão para testar se o frontend consegue acessar o backend Flask
                </p>
            </div>

            <button
                onClick={testBackendConnection}
                disabled={loading}
                className={`w-full py-3 rounded-lg font-medium transition-all ${loading ? 'bg-gray-600 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'}`}
            >
                {loading ? (
                    <span className="flex items-center justify-center">
                        <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                        Testando...
                    </span>
                ) : (
                    '🔄 Testar Conexão Backend'
                )}
            </button>

            {message && (
                <div className={`mt-4 p-3 rounded-lg ${message.includes('✅') ? 'bg-green-900/20 border border-green-500/30' : message.includes('⚠️') ? 'bg-yellow-900/20 border border-yellow-500/30' : 'bg-red-900/20 border border-red-500/30'}`}>
                    <p className={message.includes('✅') ? 'text-green-300' : message.includes('⚠️') ? 'text-yellow-300' : 'text-red-300'}>
                        {message}
                    </p>
                </div>
            )}

            <div className="mt-3 text-sm text-gray-400">
                <strong>Backend esperado:</strong> http://localhost:5000
                <br />
                <strong>Status atual:</strong> {loading ? 'Testando...' : message ? 'Teste realizado' : 'Aguardando teste'}
            </div>
        </div>
    );
}