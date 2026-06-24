"""venda.offline_uuid (idempotência do PDV offline)

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-06-24
"""
from alembic import op
import sqlalchemy as sa


revision = "d0e1f2a3b4c5"
down_revision = "c9d0e1f2a3b4"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = {c["name"] for c in insp.get_columns("vendas")}
    if "offline_uuid" not in cols:
        op.add_column("vendas", sa.Column("offline_uuid", sa.String(length=36), nullable=True))
    uqs = {c["name"] for c in insp.get_unique_constraints("vendas")}
    if "uq_venda_estab_offline_uuid" not in uqs:
        # NULLs não conflitam no Postgres → vendas sem offline_uuid coexistem
        op.create_unique_constraint(
            "uq_venda_estab_offline_uuid", "vendas", ["estabelecimento_id", "offline_uuid"]
        )


def downgrade():
    op.drop_constraint("uq_venda_estab_offline_uuid", "vendas", type_="unique")
    op.drop_column("vendas", "offline_uuid")
