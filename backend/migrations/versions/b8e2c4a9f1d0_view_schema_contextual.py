"""view_schema_contextual

Motor de Renderização Contextual:
- estabelecimentos.segmento (nível Tenant da cascata)
- produtos.tipo_item / controlar_estoque / atributos_json (nível Produto)
- view_registry (nível Global: catálogo de campos e métricas por segmento)

Revision ID: b8e2c4a9f1d0
Revises: d73ed9f4ed75
Create Date: 2026-07-16

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b8e2c4a9f1d0'
down_revision = 'd73ed9f4ed75'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('estabelecimentos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('segmento', sa.String(length=30), nullable=True,
                                      server_default='mercearia'))

    with op.batch_alter_table('produtos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tipo_item', sa.String(length=10), nullable=True,
                                      server_default='produto'))
        batch_op.add_column(sa.Column('controlar_estoque', sa.Boolean(), nullable=True,
                                      server_default=sa.true()))
        batch_op.add_column(sa.Column('atributos_json', sa.Text(), nullable=True))

    op.create_table(
        'view_registry',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('escopo', sa.String(length=10), nullable=False),
        sa.Column('chave', sa.String(length=50), nullable=False),
        sa.Column('definicao_json', sa.Text(), nullable=False),
        sa.Column('segmentos_json', sa.Text(), nullable=False),
        sa.Column('ordem', sa.Integer(), nullable=True),
        sa.Column('ativo', sa.Boolean(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_view_registry')),
        sa.UniqueConstraint('escopo', 'chave', name='uq_view_registry_escopo_chave'),
    )
    with op.batch_alter_table('view_registry', schema=None) as batch_op:
        batch_op.create_index('ix_view_registry_escopo', ['escopo'], unique=False)

    # Backfill explícito p/ linhas antigas (server_default cobre bancos que o aplicam
    # no ALTER, mas SQLite antigo e drift manual não).
    op.execute("UPDATE estabelecimentos SET segmento = 'mercearia' WHERE segmento IS NULL")
    op.execute("UPDATE produtos SET tipo_item = 'produto' WHERE tipo_item IS NULL")
    op.execute("UPDATE produtos SET controlar_estoque = TRUE WHERE controlar_estoque IS NULL")


def downgrade():
    with op.batch_alter_table('view_registry', schema=None) as batch_op:
        batch_op.drop_index('ix_view_registry_escopo')
    op.drop_table('view_registry')

    with op.batch_alter_table('produtos', schema=None) as batch_op:
        batch_op.drop_column('atributos_json')
        batch_op.drop_column('controlar_estoque')
        batch_op.drop_column('tipo_item')

    with op.batch_alter_table('estabelecimentos', schema=None) as batch_op:
        batch_op.drop_column('segmento')
