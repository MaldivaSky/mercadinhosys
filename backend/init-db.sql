-- Script de inicialização do banco PostgreSQL
-- Executado automaticamente na primeira vez que o container sobe

-- Criar extensões úteis
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- Para busca full-text

-- Criar schema se necessário
-- CREATE SCHEMA IF NOT EXISTS mercadinhosys;

-- Configurações de performance
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

-- Log de inicialização
DO $$
BEGIN
    RAISE NOTICE 'Database mercadinhosys initialized successfully!';
END $$;
