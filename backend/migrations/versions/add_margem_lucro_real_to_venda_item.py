"""Add margem_lucro_real to venda_itens for real-time profit tracking

Revision ID: add_margem_lucro_real
Revises: add_historico_precos
Create Date: 2026-02-08

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_margem_lucro_real'
down_revision = 'add_historico_precos'
branch_labels = None
depends_on = None


def upgrade():
    # Add margem_lucro_real column to venda_itens table
    # This field stores the real profit: (sale_price - current_cost) * quantity
    # Uses CMP (Custo Médio Ponderado) at the moment of sale
    op.add_column(
        'venda_itens',
        sa.Column('margem_lucro_real', sa.Numeric(precision=10, scale=2), nullable=True)
    )


def downgrade():
    # Remove margem_lucro_real column
    op.drop_column('venda_itens', 'margem_lucro_real')
