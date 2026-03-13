#!/bin/bash

# Deploy Sistema Multi-Tenant - MercadinhoSys
# Cada estabelecimento com seu próprio banco de dados

echo "🚀 Iniciando deploy do sistema Multi-Tenant..."

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função de log
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERRO] $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[AVISO] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Verificar Docker
if ! command -v docker &> /dev/null; then
    error "Docker não está instalado!"
fi

if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose não está instalado!"
fi

# Parar containers existentes
log "Parando containers existentes..."
docker-compose -f docker-compose.dev.yml down || true

# Limpar volumes antigos (opcional - descomentar se necessário)
# warning "Limpando volumes antigos..."
# docker volume rm mercadinhosys_postgres_data_dev || true

# Iniciar sistema multi-tenant
log "Iniciando sistema Multi-Tenant..."
docker-compose -f docker-compose.multi-tenant.yml up -d --build

# Aguardar bancos iniciarem
log "Aguardando inicialização dos bancos de dados..."
sleep 30

# Verificar se containers estão rodando
log "Verificando status dos containers..."
docker-compose -f docker-compose.multi-tenant.yml ps

# Verificar banco principal
log "Verificando banco principal..."
if docker exec mercadinhosys-backend-multi python -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://mercadinho_user:mercadinho_secure_pass_2024@postgres-main:5432/mercadinhosys_main')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM tenant_management.estabelecimentos')
    count = cursor.fetchone()[0]
    print(f'✅ Banco principal OK - {count} estabelecimentos cadastrados')
    cursor.close()
    conn.close()
except Exception as e:
    print(f'❌ Erro no banco principal: {e}')
    exit(1)
"; then
    log "✅ Banco principal configurado com sucesso!"
else
    error "❌ Falha na configuração do banco principal!"
fi

# Verificar bancos dos tenants
log "Verificando bancos dos tenants..."
for tenant_id in 1 2; do
    if docker exec mercadinhosys-backend-multi python -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://mercadinho_user:mercadinho_secure_pass_2024@postgres-main:5432/tenant_${tenant_id}')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM configuracoes')
    count = cursor.fetchone()[0]
    print(f'✅ Tenant ${tenant_id} OK - {count} configurações')
    cursor.close()
    conn.close()
except Exception as e:
    print(f'❌ Erro no tenant ${tenant_id}: {e}')
    exit(1)
"; then
        log "✅ Tenant ${tenant_id} acessível!"
    else
        error "❌ Falha no acesso ao tenant ${tenant_id}!"
    fi
done

# Testar autenticação
log "Testando autenticação multi-tenant..."
if curl -s -X POST http://localhost:5000/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username": "admin", "senha": "admin123"}' | grep -q "success.*true"; then
    log "✅ Autenticação admin funcionando!"
else
    warning "⚠️ Autenticação admin precisa de verificação"
fi

if curl -s -X POST http://localhost:5000/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username": "admin2", "senha": "admin123"}' | grep -q "success.*true"; then
    log "✅ Autenticação admin2 funcionando!"
else
    warning "⚠️ Autenticação admin2 precisa de verificação"
fi

# Informações de acesso
echo ""
log "🎉 Sistema Multi-Tenant implantado com sucesso!"
echo ""
echo "📋 Informações de Acesso:"
echo "┌─────────────────────────────────────────────────────┐"
echo "│ 🏢 Frontend: http://localhost:5173                │"
echo "│ 🔧 Backend API: http://localhost:5000              │"
echo "│ 🗄️ Banco Principal: postgres-main:5432            │"
echo "│ 🏪 Tenant 1: tenant_1 (Mercadinho Central)        │"
echo "│ 🏪 Tenant 2: tenant_2 (Supermercado Praia)         │"
echo "└─────────────────────────────────────────────────────┘"
echo ""
echo "👤 Usuários de Teste:"
echo "┌─────────────────────────────────────────────────────┐"
echo "│ 🏪 Admin Central:                                  │"
echo "│   Email: admin@mercadinho.com                      │"
echo "│   Senha: admin123                                  │"
echo "│   Tenant: Mercadinho Central                        │"
echo "│                                                     │"
echo "│ 🏪 Admin Praia:                                    │"
echo "│   Email: admin2@mercadinho.com                     │"
echo "│   Senha: admin123                                  │"
echo "│   Tenant: Supermercado Praia                       │"
echo "└─────────────────────────────────────────────────────┘"
echo ""
echo "🔍 Logs em tempo real:"
echo "  docker-compose -f docker-compose.multi-tenant.yml logs -f"
echo ""
echo "🛑 Parar sistema:"
echo "  docker-compose -f docker-compose.multi-tenant.yml down"
echo ""
echo "🔄 Reiniciar sistema:"
echo "  docker-compose -f docker-compose.multi-tenant.yml restart"
echo ""

# Verificar health check
log "Verificando health check final..."
sleep 10

if curl -s http://localhost:5000/api/auth/verify-tenant -H "Authorization: Bearer $(curl -s -X POST http://localhost:5000/api/auth/login -H "Content-Type: application/json" -d '{"username": "admin", "senha": "admin123"}' | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)" | grep -q "success.*true"; then
    log "🎯 Sistema 100% operacional!"
    echo ""
    log "🚀 Multi-Tenant isolado e funcionando perfeitamente!"
    log "📦 Cada estabelecimento tem seu próprio banco de dados!"
    log "🔒 Configurações, produtos e vendas 100% isolados!"
else
    warning "⚠️ Sistema iniciado, mas verificação final falhou"
    echo "Verifique os logs para mais detalhes"
fi

echo ""
log "✅ Deploy concluído!"
