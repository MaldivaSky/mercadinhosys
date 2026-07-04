"""Cria configuracoes_folha (parâmetros de folha configuráveis por loja:
hora extra, FGTS, multa, VT e tabelas progressivas de INSS/IRRF)

Revision ID: a3c5e7f9b1d2
Revises: f2a4b6c8d0e1
Create Date: 2026-07-04
"""
from alembic import op
import sqlalchemy as sa

revision = 'a3c5e7f9b1d2'
down_revision = 'f2a4b6c8d0e1'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'configuracoes_folha',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('estabelecimento_id', sa.Integer(), sa.ForeignKey('estabelecimentos.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('divisor_horas_mensais', sa.Integer(), nullable=True),
        sa.Column('percentual_hora_extra', sa.Numeric(6, 2), nullable=True),
        sa.Column('percentual_adicional_noturno', sa.Numeric(6, 2), nullable=True),
        sa.Column('fgts_percentual', sa.Numeric(6, 2), nullable=True),
        sa.Column('multa_fgts_dispensa', sa.Numeric(6, 2), nullable=True),
        sa.Column('multa_fgts_acordo', sa.Numeric(6, 2), nullable=True),
        sa.Column('desconto_vt_percentual', sa.Numeric(6, 2), nullable=True),
        sa.Column('deducao_por_dependente', sa.Numeric(19, 4), nullable=True),
        sa.Column('inss_faixas', sa.JSON(), nullable=True),
        sa.Column('irrf_faixas', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('sync_uuid', sa.String(length=36), nullable=False, unique=True),
        sa.UniqueConstraint('estabelecimento_id', name='uq_config_folha_estab'),
    )


def downgrade():
    op.drop_table('configuracoes_folha')
