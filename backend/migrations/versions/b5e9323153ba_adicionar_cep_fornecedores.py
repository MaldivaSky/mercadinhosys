"""adicionar_cep_fornecedores

Revision ID: b5e9323153ba
Revises: d31cf4ee8e85
Create Date: 2026-01-05 21:52:08.461754

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b5e9323153ba'
down_revision = 'd31cf4ee8e85'
branch_labels = None
depends_on = None


def upgrade():
    # Adicionar coluna cep à tabela fornecedores
    with op.batch_alter_table('fornecedores', schema=None) as batch_op:
        batch_op.add_column(sa.Column('cep', sa.String(length=10), nullable=True))


def downgrade():
    # Remover coluna cep da tabela fornecedores
    with op.batch_alter_table('fornecedores', schema=None) as batch_op:
        batch_op.drop_column('cep')
