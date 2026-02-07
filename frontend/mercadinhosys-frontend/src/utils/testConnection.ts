/**
 * Script de teste de conectividade com o backend
 * Use no console do navegador: testConnection()
 */

import { apiClient } from '../api/apiClient';
import { API_CONFIG } from '../api/apiConfig';

type TestConnectionConfig = {
    BASE_URL: string;
    IS_DEVELOPMENT: boolean;
    TIMEOUT: number;
    CURRENT_URL: string;
    TOKENS: {
        access_token: string;
        refresh_token: string;
    };
};

type HealthResult =
    | {
          status: number;
          ok: boolean;
          data: unknown;
      }
    | {
          error: string;
          type?: string;
      };

type AuthResult =
    | {
          status: 'authenticated';
          user: unknown;
      }
    | {
          status: 'failed';
          error?: unknown;
          statusCode?: number;
      }
    | {
          status: 'no_token';
      };

type EndpointResult =
    | {
          status: '✅ OK';
          statusCode: number;
          hasData: boolean;
      }
    | {
          status: '❌ ERRO';
          statusCode?: number;
          error?: unknown;
      };

type TestConnectionResults = {
    config: TestConnectionConfig;
    health: HealthResult;
    auth: AuthResult;
    endpoints: Record<string, EndpointResult>;
};

type ApiError = {
    message?: string;
    name?: string;
    response?: {
        data?: unknown;
        status?: number;
    };
};

const getApiError = (error: unknown): ApiError => {
    if (typeof error === 'object' && error !== null) {
        return error as ApiError;
    }
    if (typeof error === 'string') {
        return { message: error };
    }
    return {};
};

export const testConnection = async () => {
    console.log('🔍 Iniciando teste de conectividade...\n');
    
    const results: TestConnectionResults = {
        config: {
            BASE_URL: '',
            IS_DEVELOPMENT: false,
            TIMEOUT: 0,
            CURRENT_URL: '',
            TOKENS: {
                access_token: '',
                refresh_token: '',
            },
        },
        health: {
            status: 0,
            ok: false,
            data: null,
        },
        auth: {
            status: 'no_token',
        },
        endpoints: {},
    };

    // 1. Verificar configuração
    console.log('1️⃣ Verificando configuração...');
    results.config = {
        BASE_URL: API_CONFIG.BASE_URL,
        IS_DEVELOPMENT: API_CONFIG.IS_DEVELOPMENT,
        TIMEOUT: API_CONFIG.TIMEOUT,
        CURRENT_URL: window.location.href,
        TOKENS: {
            access_token: localStorage.getItem('access_token') ? '✅ Presente' : '❌ Ausente',
            refresh_token: localStorage.getItem('refresh_token') ? '✅ Presente' : '❌ Ausente',
        }
    };
    console.log('✅ Configuração:', results.config);

    // 2. Testar endpoint de saúde
    console.log('\n2️⃣ Testando endpoint de saúde...');
    try {
        const response = await fetch(`${API_CONFIG.BASE_URL}/health`);
        const data = await response.json();
        results.health = {
            status: response.status,
            ok: response.ok,
            data: data,
        };
        console.log('✅ Health check:', results.health);
    } catch (error: unknown) {
        const err = getApiError(error);
        results.health = {
            error: err.message || 'Erro desconhecido',
            type: err.name,
        };
        console.error('❌ Health check falhou:', results.health);
    }

    // 3. Testar autenticação (se tiver token)
    if (localStorage.getItem('access_token')) {
        console.log('\n3️⃣ Testando autenticação...');
        try {
            const response = await apiClient.get('/auth/me');
            results.auth = {
                status: 'authenticated',
                user: response.data,
            };
            console.log('✅ Autenticação válida:', results.auth);
        } catch (error: unknown) {
            const err = getApiError(error);
            results.auth = {
                status: 'failed',
                error: err.response?.data || err.message,
                statusCode: err.response?.status,
            };
            console.error('❌ Autenticação falhou:', results.auth);
        }
    } else {
        console.log('\n3️⃣ ⚠️ Sem token de autenticação');
        results.auth = { status: 'no_token' };
    }

    // 4. Testar endpoints principais
    console.log('\n4️⃣ Testando endpoints principais...');
    const endpoints = [
        { name: 'Produtos', url: '/produtos' },
        { name: 'Clientes', url: '/clientes' },
        { name: 'Vendas', url: '/vendas' },
        { name: 'Dashboard', url: '/dashboard/cientifico' },
        { name: 'Funcionários', url: '/funcionarios' },
    ];

    for (const endpoint of endpoints) {
        try {
            const response = await apiClient.get(endpoint.url);
            results.endpoints[endpoint.name] = {
                status: '✅ OK',
                statusCode: response.status,
                hasData: !!response.data,
            };
            console.log(`✅ ${endpoint.name}:`, results.endpoints[endpoint.name]);
        } catch (error: unknown) {
            const err = getApiError(error);
            results.endpoints[endpoint.name] = {
                status: '❌ ERRO',
                statusCode: err.response?.status,
                error:
                    (typeof err.response?.data === 'object' &&
                    err.response?.data !== null &&
                    'message' in err.response.data
                        ? (err.response.data as { message?: string }).message
                        : err.response?.data) || err.message,
            };
            console.error(`❌ ${endpoint.name}:`, results.endpoints[endpoint.name]);
        }
    }

    // 5. Resumo final
    console.log('\n📊 RESUMO DO TESTE:');
    console.log('='.repeat(50));
    console.table(results.endpoints);
    console.log('='.repeat(50));

    // Diagnóstico
    console.log('\n🔍 DIAGNÓSTICO:');
    if (results.health.error) {
        console.error('❌ Backend não está acessível!');
        console.log('Possíveis causas:');
        console.log('  1. Backend offline no Render');
        console.log('  2. URL incorreta:', API_CONFIG.BASE_URL);
        console.log('  3. Problema de CORS');
    } else if (results.auth.status === 'failed') {
        console.error('❌ Problema de autenticação!');
        console.log('Possíveis causas:');
        console.log('  1. Token expirado - faça login novamente');
        console.log('  2. JWT_SECRET_KEY diferente entre ambientes');
    } else {
        const failedEndpoints = Object.entries(results.endpoints)
            .filter(([, v]) => v.status === '❌ ERRO');
        
        if (failedEndpoints.length > 0) {
            console.warn('⚠️ Alguns endpoints falharam:');
            failedEndpoints.forEach(([name, data]) => {
                console.log(`  - ${name}:`, data);
            });
        } else {
            console.log('✅ Todos os testes passaram!');
        }
    }

    return results;
};

// Expor globalmente para uso no console
declare global {
    interface Window {
        testConnection?: () => Promise<TestConnectionResults>;
    }
}

if (typeof window !== 'undefined') {
    window.testConnection = testConnection;
    console.log('💡 Use testConnection() no console para testar a conectividade');
}
