"""Add SaaS fields, Lead table and restore stability columns

Revision ID: add_saas_and_leads
Revises: add_margem_lucro_real
Create Date: 2026-02-19

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_saas_and_leads'
down_revision = 'add_margem_lucro_real'
branch_labels = None
depends_on = None

def upgrade():
    # 1. Create Lead table
    op.create_table(
        'leads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=150), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('whatsapp', sa.String(length=30), nullable=False),
        sa.Column('origem', sa.String(length=100), nullable=True, server_default='landing_page'),
        sa.Column('observacao', sa.Text(), nullable=True),
        sa.Column('data_cadastro', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. Add SaaS columns to estabelecimentos
    op.add_column('estabelecimentos', sa.Column('plano', sa.String(length=20), nullable=True, server_default='Basic'))
    op.add_column('estabelecimentos', sa.Column('plano_status', sa.String(length=20), nullable=True, server_default='experimental'))
    op.add_column('estabelecimentos', sa.Column('vencimento_assinatura', sa.DateTime(), nullable=True))
    op.add_column('estabelecimentos', sa.Column('pagarme_id', sa.String(length=100), nullable=True))

    # 3. Restore and Add columns to configuracoes
    op.add_column('configuracoes', sa.Column('logo_base64', sa.Text(), nullable=True))
    op.add_column('configuracoes', sa.Column('tema_escuro', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('configuracoes', sa.Column('impressao_automatica', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('configuracoes', sa.Column('tipo_impressora', sa.String(length=20), nullable=True, server_default='termica_80mm'))
    op.add_column('configuracoes', sa.Column('exibir_preco_tela', sa.Boolean(), nullable=True, server_default='true'))
    op.add_column('configuracoes', sa.Column('permitir_venda_sem_estoque', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('configuracoes', sa.Column('desconto_maximo_percentual', sa.Numeric(precision=5, scale=2), nullable=True, server_default='10.00'))
    op.add_column('configuracoes', sa.Column('arredondamento_valores', sa.Boolean(), nullable=True, server_default='true'))
    op.add_column('configuracoes', sa.Column('formas_pagamento', sa.Text(), nullable=True, server_default='["Dinheiro", "Cartão de Crédito", "Cartão de Débito", "PIX"]'))
    op.add_column('configuracoes', sa.Column('alerta_estoque_minimo', sa.Boolean(), nullable=True, server_default='true'))
    op.add_column('configuracoes', sa.Column('dias_alerta_validade', sa.Integer(), nullable=True, server_default='30'))
    op.add_column('configuracoes', sa.Column('estoque_minimo_padrao', sa.Integer(), nullable=True, server_default='10'))
    op.add_column('configuracoes', sa.Column('tempo_sessao_minutos', sa.Integer(), nullable=True, server_default='30'))
    op.add_column('configuracoes', sa.Column('tentativas_senha_bloqueio', sa.Integer(), nullable=True, server_default='3'))
    op.add_column('configuracoes', sa.Column('alertas_email', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('configuracoes', sa.Column('alertas_whatsapp', sa.Boolean(), nullable=True, server_default='false'))

    # 4. Restore columns to funcionarios
    op.add_column('funcionarios', sa.Column('status', sa.String(length=20), nullable=True, server_default='ativo'))
    op.add_column('funcionarios', sa.Column('data_demissao', sa.Date(), nullable=True))

def downgrade():
    # Remove columns from funcionarios
    op.drop_column('funcionarios', 'data_demissao')
    op.drop_column('funcionarios', 'status')

    # Remove columns from configuracoes
    op.drop_column('configuracoes', 'alertas_whatsapp')
    op.drop_column('configuracoes', 'alertas_email')
    op.drop_column('configuracoes', 'tentativas_senha_bloqueio')
    op.drop_column('configuracoes', 'tempo_sessao_minutos')
    op.drop_column('configuracoes', 'estoque_minimo_padrao')
    op.drop_column('configuracoes', 'dias_alerta_validade')
    op.drop_column('configuracoes', 'alerta_estoque_minimo')
    # op.drop_column('configuracoes', 'formas_pagamento') # Keep if data is critical
    op.drop_column('configuracoes', 'arredondamento_valores')
    op.drop_column('configuracoes', 'desconto_maximo_percentual')
    op.drop_column('configuracoes', 'permitir_venda_sem_estoque')
    op.drop_column('configuracoes', 'exibir_preco_tela')
    op.drop_column('configuracoes', 'tipo_impressora')
    op.drop_column('configuracoes', 'impressao_automatica')
    op.drop_column('configuracoes', 'tema_escuro')
    op.drop_column('configuracoes', 'logo_base64')

    # Remove columns from estabelecimentos
    op.drop_column('estabelecimentos', 'pagarme_id')
    op.drop_column('estabelecimentos', 'vencimento_assinatura')
    op.drop_column('estabelecimentos', 'plano_status')
    op.drop_column('estabelecimentos', 'plano')

    # Drop Lead table
    op.drop_table('leads')
