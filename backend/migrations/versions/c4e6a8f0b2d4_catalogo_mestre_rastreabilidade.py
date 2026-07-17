"""catalogo_mestre_rastreabilidade

Rastreabilidade mínima de descoberta no Catálogo Mestre: quem (estabelecimento)
e como (modal/xml) trouxe um item novo pro catálogo global.

Revision ID: c4e6a8f0b2d4
Revises: b8e2c4a9f1d0
Create Date: 2026-07-17

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c4e6a8f0b2d4'
down_revision = 'b8e2c4a9f1d0'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('catalogo_mestre', schema=None) as batch_op:
        batch_op.add_column(sa.Column('descoberto_por_estabelecimento_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('descoberto_via', sa.String(length=20), nullable=True))


def downgrade():
    with op.batch_alter_table('catalogo_mestre', schema=None) as batch_op:
        batch_op.drop_column('descoberto_via')
        batch_op.drop_column('descoberto_por_estabelecimento_id')
