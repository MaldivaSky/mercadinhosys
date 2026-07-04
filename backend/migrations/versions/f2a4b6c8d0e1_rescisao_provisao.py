"""Cria tabelas rescisoes e provisoes_trabalhistas (motor de folha: verbas
rescisórias CLT + provisões 1/12 avos para custo real)

Revision ID: f2a4b6c8d0e1
Revises: e1f3a4b5c6d7
Create Date: 2026-07-04
"""
from alembic import op
import sqlalchemy as sa

revision = 'f2a4b6c8d0e1'
down_revision = 'e1f3a4b5c6d7'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'rescisoes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('estabelecimento_id', sa.Integer(), sa.ForeignKey('estabelecimentos.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('funcionario_id', sa.Integer(), sa.ForeignKey('funcionarios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('data_demissao', sa.Date(), nullable=False),
        sa.Column('tipo_rescisao', sa.String(length=20), nullable=False),
        sa.Column('verbas_rescisorias_json', sa.JSON(), nullable=True),
        sa.Column('total_proventos', sa.Numeric(19, 4), nullable=True),
        sa.Column('total_descontos', sa.Numeric(19, 4), nullable=True),
        sa.Column('total_liquido', sa.Numeric(19, 4), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('sync_uuid', sa.String(length=36), nullable=False, unique=True),
    )
    op.create_index('ix_rescisao_funcionario', 'rescisoes', ['funcionario_id'])

    op.create_table(
        'provisoes_trabalhistas',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('estabelecimento_id', sa.Integer(), sa.ForeignKey('estabelecimentos.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('funcionario_id', sa.Integer(), sa.ForeignKey('funcionarios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('ano_mes', sa.String(length=7), nullable=False),
        sa.Column('valor_ferias', sa.Numeric(19, 4), nullable=True),
        sa.Column('valor_decimo_terceiro', sa.Numeric(19, 4), nullable=True),
        sa.Column('encargos_provisionados', sa.Numeric(19, 4), nullable=True),
        sa.Column('custo_real', sa.Numeric(19, 4), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('sync_uuid', sa.String(length=36), nullable=False, unique=True),
        sa.UniqueConstraint('funcionario_id', 'ano_mes', name='uq_provisao_func_mes'),
    )
    op.create_index('ix_provisao_funcionario', 'provisoes_trabalhistas', ['funcionario_id'])


def downgrade():
    op.drop_index('ix_provisao_funcionario', table_name='provisoes_trabalhistas')
    op.drop_table('provisoes_trabalhistas')
    op.drop_index('ix_rescisao_funcionario', table_name='rescisoes')
    op.drop_table('rescisoes')
