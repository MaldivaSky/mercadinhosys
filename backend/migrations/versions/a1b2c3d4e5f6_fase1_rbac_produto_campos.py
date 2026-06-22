"""fase1: nivel_acesso em funcionarios, data_compra e data_recebimento em produtos

Revision ID: a1b2c3d4e5f6
Revises: 366b766bc135
Create Date: 2026-06-21 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = '366b766bc135'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # ── funcionarios: adicionar nivel_acesso ──────────────────────────────
    cols_func = [c['name'] for c in inspector.get_columns('funcionarios')]

    if 'nivel_acesso' not in cols_func:
        with op.batch_alter_table('funcionarios', schema=None) as batch_op:
            batch_op.add_column(sa.Column('nivel_acesso', sa.Integer(), nullable=True, server_default='3'))

    # Preenche nivel_acesso a partir de role existente
    op.execute("""
        UPDATE funcionarios SET nivel_acesso = CASE
            WHEN UPPER(role) IN ('ADMIN','ADMINISTRADOR','PROPRIETARIO','DONO','MASTER') THEN 1
            WHEN UPPER(role) IN ('GERENTE','SUPERVISOR') THEN 2
            WHEN UPPER(role) IN ('CAIXA','OPERADOR') THEN 3
            WHEN UPPER(role) IN ('ESTOQUE','ALMOXARIFE') THEN 4
            WHEN UPPER(role) IN ('RH','RECURSOS_HUMANOS') THEN 5
            WHEN UPPER(role) IN ('ENTREGADOR','MOTOBOY','MOTORISTA') THEN 6
            ELSE 3
        END
        WHERE nivel_acesso IS NULL OR nivel_acesso = 0
    """)

    # ── produtos: adicionar data_compra, data_recebimento, ampliar imagem_url ──
    cols_prod = [c['name'] for c in inspector.get_columns('produtos')]

    with op.batch_alter_table('produtos', schema=None) as batch_op:
        if 'data_compra' not in cols_prod:
            batch_op.add_column(sa.Column('data_compra', sa.Date(), nullable=True))
        if 'data_recebimento' not in cols_prod:
            batch_op.add_column(sa.Column('data_recebimento', sa.Date(), nullable=True))


def downgrade():
    with op.batch_alter_table('funcionarios', schema=None) as batch_op:
        batch_op.drop_column('nivel_acesso')

    with op.batch_alter_table('produtos', schema=None) as batch_op:
        batch_op.drop_column('data_recebimento')
        batch_op.drop_column('data_compra')
