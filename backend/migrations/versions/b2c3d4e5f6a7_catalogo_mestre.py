"""catalogo mestre global de produtos com EAN real (harvester Cosmos)

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-21 01:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'catalogo_mestre' in inspector.get_table_names():
        return

    op.create_table(
        'catalogo_mestre',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ean', sa.String(length=14), nullable=False),
        sa.Column('nome', sa.String(length=200), nullable=True),
        sa.Column('marca', sa.String(length=100), nullable=True),
        sa.Column('fabricante', sa.String(length=150), nullable=True),
        sa.Column('ncm', sa.String(length=8), nullable=True),
        sa.Column('categoria', sa.String(length=60), nullable=True),
        sa.Column('unidade', sa.String(length=20), nullable=True),
        sa.Column('preco_referencia', sa.Numeric(precision=19, scale=4), nullable=True),
        sa.Column('imagem_url', sa.String(length=500), nullable=True),
        sa.Column('fonte', sa.String(length=20), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('payload_json', sa.Text(), nullable=True),
        sa.Column('consultado_em', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id', name='pk_catalogo_mestre'),
        sa.UniqueConstraint('ean', name='uq_catalogo_mestre_ean'),
    )
    op.create_index('ix_catalogo_mestre_ean', 'catalogo_mestre', ['ean'], unique=True)
    op.create_index('ix_catalogo_status', 'catalogo_mestre', ['status'], unique=False)
    op.create_index('ix_catalogo_categoria', 'catalogo_mestre', ['categoria'], unique=False)


def downgrade():
    op.drop_index('ix_catalogo_categoria', table_name='catalogo_mestre')
    op.drop_index('ix_catalogo_status', table_name='catalogo_mestre')
    op.drop_index('ix_catalogo_mestre_ean', table_name='catalogo_mestre')
    op.drop_table('catalogo_mestre')
