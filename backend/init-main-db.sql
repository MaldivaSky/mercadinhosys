-- Banco principal para gerenciamento de tenants
-- Este banco armazena apenas informações dos estabelecimentos

-- Schema para gerenciamento de tenants
CREATE SCHEMA IF NOT EXISTS tenant_management;

-- Tabela de estabelecimentos (tenants)
CREATE TABLE IF NOT EXISTS tenant_management.estabelecimentos (
    id SERIAL PRIMARY KEY,
    nome_fantasia VARCHAR(255) NOT NULL,
    razao_social VARCHAR(255) NOT NULL,
    cnpj VARCHAR(20) UNIQUE NOT NULL,
    database_name VARCHAR(100) UNIQUE NOT NULL, -- Nome do banco de dados do tenant
    status VARCHAR(20) DEFAULT 'active', -- active, inactive, suspended
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de usuários do sistema (autenticação global)
CREATE TABLE IF NOT EXISTS tenant_management.usuarios (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    senha_hash VARCHAR(255) NOT NULL,
    estabelecimento_id INTEGER REFERENCES tenant_management.estabelecimentos(id),
    role VARCHAR(50) DEFAULT 'user', -- admin, gerente, caixa, user
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Função para criar banco de dados para novo tenant
CREATE OR REPLACE FUNCTION tenant_management.criar_banco_tenant(estabelecimento_id INTEGER)
RETURNS VOID AS $$
DECLARE
    estabelecimento_record RECORD;
    db_name TEXT;
BEGIN
    -- Buscar informações do estabelecimento
    SELECT e.nome_fantasia, e.database_name 
    INTO estabelecimento_record
    FROM tenant_management.estabelecimentos e 
    WHERE e.id = estabelecimento_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Estabelecimento % não encontrado', estabelecimento_id;
    END IF;
    
    db_name := estabelecimento_record.database_name;
    
    -- Criar banco de dados do tenant
    EXECUTE format('CREATE DATABASE %I', db_name);
    
    -- Conectar ao banco do tenant e criar schema
    EXECUTE format('
        -- Criar schema principal
        CREATE SCHEMA IF NOT EXISTS public;
        
        -- Tabela de produtos
        CREATE TABLE IF NOT EXISTS produtos (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            descricao TEXT,
            preco_venda DECIMAL(10,2) NOT NULL,
            preco_custo DECIMAL(10,2),
            estoque_atual INTEGER DEFAULT 0,
            estoque_minimo INTEGER DEFAULT 10,
            codigo_barras VARCHAR(50),
            categoria VARCHAR(100),
            unidade_medida VARCHAR(20) DEFAULT ''UN'',
            ativo BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Tabela de configurações do estabelecimento
        CREATE TABLE IF NOT EXISTS configuracoes (
            id SERIAL PRIMARY KEY,
            estabelecimento_id INTEGER DEFAULT 1,
            cor_principal VARCHAR(20) DEFAULT ''#2563eb'',
            tema_escuro BOOLEAN DEFAULT false,
            logo_url TEXT,
            logo_base64 TEXT,
            emitir_nfe BOOLEAN DEFAULT false,
            emitir_nfce BOOLEAN DEFAULT true,
            impressao_automatica BOOLEAN DEFAULT false,
            tipo_impressora VARCHAR(50) DEFAULT ''termica_80mm'',
            exibir_preco_tela BOOLEAN DEFAULT true,
            permitir_venda_sem_estoque BOOLEAN DEFAULT false,
            desconto_maximo_percentual DECIMAL(5,2) DEFAULT 10.00,
            desconto_maximo_funcionario DECIMAL(5,2) DEFAULT 10.00,
            arredondamento_valores BOOLEAN DEFAULT true,
            formas_pagamento TEXT DEFAULT ''["Dinheiro", "Cartão de Crédito", "Cartão de Débito", "PIX"]'',
            controlar_validade BOOLEAN DEFAULT true,
            alerta_estoque_minimo BOOLEAN DEFAULT true,
            dias_alerta_validade INTEGER DEFAULT 30,
            estoque_minimo_padrao INTEGER DEFAULT 10,
            tempo_sessao_minutos INTEGER DEFAULT 30,
            tentativas_senha_bloqueio INTEGER DEFAULT 3,
            alertas_email BOOLEAN DEFAULT false,
            alertas_whatsapp BOOLEAN DEFAULT false,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Inserir configuração padrão
        INSERT INTO configuracoes (estabelecimento_id) VALUES (1)
        ON CONFLICT DO NOTHING;
        
        -- Tabela de vendas
        CREATE TABLE IF NOT EXISTS vendas (
            id SERIAL PRIMARY KEY,
            numero_cupom VARCHAR(50) UNIQUE NOT NULL,
            data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            valor_total DECIMAL(10,2) NOT NULL,
            valor_desconto DECIMAL(10,2) DEFAULT 0,
            forma_pagamento VARCHAR(50),
            cliente_cpf VARCHAR(20),
            status VARCHAR(20) DEFAULT ''concluida'',
            usuario_id INTEGER,
            itens JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Tabela de clientes
        CREATE TABLE IF NOT EXISTS clientes (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            cpf VARCHAR(20) UNIQUE,
            telefone VARCHAR(20),
            email VARCHAR(255),
            endereco TEXT,
            data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ativo BOOLEAN DEFAULT true
        );
        
        -- Índices para performance
        CREATE INDEX IF NOT EXISTS idx_produtos_ativos ON produtos(ativo) WHERE ativo = true;
        CREATE INDEX IF NOT EXISTS idx_produtos_estoque ON produtos(estoque_atual);
        CREATE INDEX IF NOT EXISTS idx_vendas_data ON vendas(data_hora);
        CREATE INDEX IF NOT EXISTS idx_clientes_cpf ON clientes(cpf);
        
        -- Grant permissions
        GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mercadinho_user;
        GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mercadinho_user;
    ', db_name);
    
    -- Log de criação
    RAISE NOTICE 'Banco de dados % criado com sucesso para estabelecimento % (%)', 
                 db_name, estabelecimento_id, estabelecimento_record.nome_fantasia;
END;
$$ LANGUAGE plpgsql;

-- Inserir estabelecimentos de exemplo
INSERT INTO tenant_management.estabelecimentos (nome_fantasia, razao_social, cnpj, database_name) VALUES
('Mercadinho Central', 'Central Comércio de Alimentos Ltda', '12.345.678/0001-90', 'tenant_1'),
('Supermercado Praia', 'Praia Comércio de Alimentos Ltda', '98.765.432/0001-10', 'tenant_2')
ON CONFLICT (cnpj) DO NOTHING;

-- Inserir usuários de exemplo
INSERT INTO tenant_management.usuarios (nome, email, senha_hash, estabelecimento_id, role) VALUES
('Administrador Central', 'admin@mercadinho.com', '$2b$12$rQZ8qK4KqKqKqKqKqKqK.O0KqKqKqKqKqKqKqKqKqKqKqKqKqKqKqKqK', 1, 'admin'),
('Administrador Praia', 'admin2@mercadinho.com', '$2b$12$rQZ8qK4KqKqKqKqKqKqK.O0KqKqKqKqKqKqKqKqKqKqKqKqKqKqKqKqK', 2, 'admin')
ON CONFLICT (email) DO NOTHING;

-- Criar bancos para os tenants existentes
SELECT tenant_management.criar_banco_tenant(1);
SELECT tenant_management.criar_banco_tenant(2);

COMMIT;
