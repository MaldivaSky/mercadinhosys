"""Adiciona jornada_diaria_minutos em configuracoes_horario (CLT: 8h/dia
default; horas trabalhadas além disso viram hora extra)

Revision ID: e1f3a4b5c6d7
Revises: d8e0f2a3b4c5
Create Date: 2026-07-04
"""
from alembic import op
import sqlalchemy as sa

revision = 'e1f3a4b5c6d7'
down_revision = 'd8e0f2a3b4c5'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'configuracoes_horario',
        sa.Column('jornada_diaria_minutos', sa.Integer(), nullable=True, server_default='480'),
    )


def downgrade():
    op.drop_column('configuracoes_horario', 'jornada_diaria_minutos')
