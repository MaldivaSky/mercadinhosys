"""
Script de migração: adiciona colunas ausentes ao banco de producao.
Executar: python migrate_schema.py
"""
import os
os.environ['SKIP_DB_SETUP'] = 'true'
os.environ['FLASK_ENV'] = 'development'

from app import create_app, db
from sqlalchemy import text, inspect

app = create_app('development')
with app.app_context():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print('TABELAS EXISTENTES:', tables)
    
    # Colunas a adicionar em estabelecimentos
    novas_estabelecimentos = [
        ('plano', "VARCHAR(20) DEFAULT 'Basic'"),
        ('plano_status', "VARCHAR(20) DEFAULT 'experimental'"),
        ('cep', "VARCHAR(9) DEFAULT '00000-000'"),
        ('logradouro', "VARCHAR(200) DEFAULT 'Nao Informado'"),
        ('numero', "VARCHAR(10) DEFAULT 'S/N'"),
        ('complemento', 'VARCHAR(100)'),
        ('bairro', "VARCHAR(100) DEFAULT 'Centro'"),
        ('cidade', "VARCHAR(100) DEFAULT 'Cidade'"),
        ('estado', "VARCHAR(2) DEFAULT 'SP'"),
        ('pais', "VARCHAR(50) DEFAULT 'Brasil'"),
        ('stripe_customer_id', 'VARCHAR(100)'),
        ('stripe_subscription_id', 'VARCHAR(100)'),
        ('vencimento_assinatura', 'TIMESTAMP'),
        ('pagarme_id', 'VARCHAR(100)'),
    ]
    
    if 'estabelecimentos' in tables:
        existing = [c['name'] for c in inspector.get_columns('estabelecimentos')]
        print('\nCOLUNAS EXISTENTES em estabelecimentos:', existing)
        
        for cname, ctype in novas_estabelecimentos:
            if cname not in existing:
                try:
                    db.session.execute(text(f'ALTER TABLE estabelecimentos ADD COLUMN {cname} {ctype}'))
                    db.session.commit()
                    print(f'  ADICIONADA: {cname}')
                except Exception as e:
                    db.session.rollback()
                    print(f'  ERRO {cname}: {str(e)[:100]}')
            else:
                print(f'  JA EXISTE: {cname}')
    else:
        print('AVISO: tabela estabelecimentos nao existe neste banco')

    # Colunas a adicionar em configuracoes
    novas_configuracoes = [
        ('logo_base64', 'TEXT'),
        ('tema_escuro', 'BOOLEAN DEFAULT FALSE'),
        ('cor_principal', "VARCHAR(7) DEFAULT '#2563eb'"),
        ('emitir_nfe', 'BOOLEAN DEFAULT FALSE'),
        ('emitir_nfce', 'BOOLEAN DEFAULT TRUE'),
        ('impressao_automatica', 'BOOLEAN DEFAULT FALSE'),
        ('tipo_impressora', "VARCHAR(20) DEFAULT 'termica_80mm'"),
        ('exibir_preco_tela', 'BOOLEAN DEFAULT TRUE'),
        ('permitir_venda_sem_estoque', 'BOOLEAN DEFAULT FALSE'),
        ('desconto_maximo_percentual', 'NUMERIC(5,2) DEFAULT 10.00'),
        ('desconto_maximo_funcionario', 'NUMERIC(5,2) DEFAULT 10.00'),
        ('arredondamento_valores', 'BOOLEAN DEFAULT TRUE'),
        ('formas_pagamento', 'TEXT'),
        ('controlar_validade', 'BOOLEAN DEFAULT TRUE'),
        ('alerta_estoque_minimo', 'BOOLEAN DEFAULT TRUE'),
        ('dias_alerta_validade', 'INTEGER DEFAULT 30'),
        ('estoque_minimo_padrao', 'INTEGER DEFAULT 10'),
        ('tempo_sessao_minutos', 'INTEGER DEFAULT 30'),
        ('tentativas_senha_bloqueio', 'INTEGER DEFAULT 3'),
        ('alertas_email', 'BOOLEAN DEFAULT FALSE'),
        ('alertas_whatsapp', 'BOOLEAN DEFAULT FALSE'),
        ('horas_extras_percentual', 'NUMERIC(5,2) DEFAULT 50.00'),
    ]
    
    if 'configuracoes' in tables:
        existing = [c['name'] for c in inspector.get_columns('configuracoes')]
        print('\nCOLUNAS EXISTENTES em configuracoes:', existing)
        
        for cname, ctype in novas_configuracoes:
            if cname not in existing:
                try:
                    db.session.execute(text(f'ALTER TABLE configuracoes ADD COLUMN {cname} {ctype}'))
                    db.session.commit()
                    print(f'  ADICIONADA: {cname}')
                except Exception as e:
                    db.session.rollback()
                    print(f'  ERRO {cname}: {str(e)[:100]}')
            else:
                print(f'  JA EXISTE: {cname}')

    print('\nMIGRACao CONCLUIDA')
