"""pin_cancelamento como hash (VARCHAR 255)

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-06-23

Garante que funcionarios.pin_cancelamento exista e comporte o hash do PIN
(de 4 a 6 dígitos numéricos). Idempotente: cria a coluna se não existir ou
amplia de VARCHAR(4) para VARCHAR(255) caso já exista.
"""
from alembic import op
import sqlalchemy as sa


revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"]: c for c in inspector.get_columns("funcionarios")}
    if "pin_cancelamento" not in cols:
        op.add_column("funcionarios", sa.Column("pin_cancelamento", sa.String(length=255), nullable=True))
    else:
        op.alter_column(
            "funcionarios",
            "pin_cancelamento",
            type_=sa.String(length=255),
            existing_type=sa.String(length=4),
            existing_nullable=True,
        )


def downgrade():
    # Mantém a coluna ampliada; reduzir poderia truncar hashes. No-op seguro.
    pass
