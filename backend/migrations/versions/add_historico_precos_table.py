"""Add historico_precos table for price audit trail

Revision ID: add_historico_precos
Revises: bbdd8b77db20
Create Date: 2026-02-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_historico_precos'
down_revision = 'bbdd8b77db20'
branch_labels = None
depends_on = None


def upgrade():
    # Create historico_precos table
    op.create_table(
        'historico_precos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('estabelecimento_id', sa.Integer(), nullable=False),
        sa.Column('produto_id', sa.Integer(), nullable=False),
        sa.Column('funcionario_id', sa.Integer(), nullable=False),
        sa.Column('preco_custo_anterior', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('preco_venda_anterior', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('margem_anterior', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('preco_custo_novo', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('preco_venda_novo', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('margem_nova', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('motivo', sa.String(length=100), nullable=False),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.Column('data_alteracao', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['estabelecimento_id'], ['estabelecimentos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['funcionario_id'], ['funcionarios.id'], ),
        sa.ForeignKeyConstraint(['produto_id'], ['produtos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better query performance
    op.create_index('idx_historico_produto', 'historico_precos', ['produto_id'])
    op.create_index('idx_historico_data', 'historico_precos', ['data_alteracao'])
    op.create_index('idx_historico_estabelecimento', 'historico_precos', ['estabelecimento_id'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_historico_estabelecimento', table_name='historico_precos')
    op.drop_index('idx_historico_data', table_name='historico_precos')
    op.drop_index('idx_historico_produto', table_name='historico_precos')
    
    # Drop table
    op.drop_table('historico_precos')
