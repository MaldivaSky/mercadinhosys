/**
 * Script de teste de conectividade com o backend
 * Use no console do navegador: testConnection()
 */

import { apiClient } from '../api/apiClient';
import { API_CONFIG } from '../api/apiConfig';

export const testConnection = async () => {
    console.log('🔍 Iniciando teste de conectividade...\n');
    
    const results = {
        config: {} as any,
        health: {} as any,
        auth: {} as any,
        endpoints: {} as any,
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
    } catch (error: any) {
        results.health = {
            error: error.message,
            type: error.name,
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
        } catch (error: any) {
            results.auth = {
                status: 'failed',
                error: error.response?.data || error.message,
                statusCode: error.response?.status,
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
        } catch (error: any) {
            results.endpoints[endpoint.name] = {
                status: '❌ ERRO',
                statusCode: error.response?.status,
                error: error.response?.data?.message || error.message,
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
            .filter(([_, v]: any) => v.status === '❌ ERRO');
        
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
if (typeof window !== 'undefined') {
    (window as any).testConnection = testConnection;
    console.log('💡 Use testConnection() no console para testar a conectividade');
}
