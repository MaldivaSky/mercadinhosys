"""Adiciona coluna forma_pagamento ao modelo e tabela rescisoes

Revision ID: f3b5a7c9d1e2
Revises: c4e6a8f0b2d4
Create Date: 2026-07-22
"""
from alembic import op
import sqlalchemy as sa


revision = 'f3b5a7c9d1e2'
down_revision = 'c4e6a8f0b2d4'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('rescisoes', sa.Column('forma_pagamento', sa.String(length=50), nullable=True))


def downgrade():
    op.drop_column('rescisoes', 'forma_pagamento')
