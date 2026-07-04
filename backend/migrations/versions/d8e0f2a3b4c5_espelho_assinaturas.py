"""Cria tabela espelho_assinaturas (autoatendimento: funcionário assina o
próprio espelho de ponto do período)

Revision ID: d8e0f2a3b4c5
Revises: c7d9e1f2a3b4
Create Date: 2026-07-03
"""
from alembic import op
import sqlalchemy as sa

revision = 'd8e0f2a3b4c5'
down_revision = 'c7d9e1f2a3b4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'espelho_assinaturas',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('estabelecimento_id', sa.Integer(), sa.ForeignKey('estabelecimentos.id'), nullable=False),
        sa.Column('funcionario_id', sa.Integer(), sa.ForeignKey('funcionarios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('data_inicio', sa.Date(), nullable=False),
        sa.Column('data_fim', sa.Date(), nullable=False),
        sa.Column('assinado_em', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('funcionario_id', 'data_inicio', 'data_fim', name='uq_espelho_func_periodo'),
    )
    op.create_index('ix_espelho_assinaturas_funcionario_id', 'espelho_assinaturas', ['funcionario_id'])


def downgrade():
    op.drop_index('ix_espelho_assinaturas_funcionario_id', table_name='espelho_assinaturas')
    op.drop_table('espelho_assinaturas')
