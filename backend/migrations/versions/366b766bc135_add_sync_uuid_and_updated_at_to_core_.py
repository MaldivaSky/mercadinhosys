"""add sync_uuid and updated_at to core models

Revision ID: 366b766bc135
Revises: 
Create Date: 2026-03-25 23:45:13.891706

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '366b766bc135'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    # Lista de modelos solicitados
    core_tables = ['funcionarios', 'clientes', 'fornecedores', 'produtos', 'vendas']
    
    for table in core_tables:
        if table in tables:
            columns = [c['name'] for c in inspector.get_columns(table)]
            with op.batch_alter_table(table, schema=None) as batch_op:
                if 'sync_uuid' not in columns:
                    print(f"Adding sync_uuid to {table}")
                    batch_op.add_column(sa.Column('sync_uuid', sa.String(length=36), nullable=True))
                    # Gerar UUIDs para registros existentes (se houver)
                    # No SQLite de simulação, o user_id/sync_uuid geralmente é preenchido via app
                if 'updated_at' not in columns:
                    print(f"Adding updated_at to {table}")
                    batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=True))

def downgrade():
    for table in ['funcionarios', 'clientes', 'fornecedores', 'produtos', 'vendas']:
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.drop_column('sync_uuid')
            batch_op.drop_column('updated_at')
