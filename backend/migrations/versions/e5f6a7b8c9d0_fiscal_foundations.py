"""fundações fiscais (NFC-e/NF-e) em estabelecimentos e produtos

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-06-23

Adiciona configuração fiscal por estabelecimento (ambiente, gateway, CSC, séries,
numeração) e campos tributários por produto (CEST, CFOP, CST/CSOSN, alíquotas).
Idempotente coluna a coluna.
"""
from alembic import op
import sqlalchemy as sa


revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


_ESTAB_COLS = [
    ("fiscal_ambiente", sa.String(length=15), "homologacao"),
    ("fiscal_gateway", sa.String(length=30), "simulado"),
    ("fiscal_token", sa.String(length=255), None),
    ("fiscal_csc", sa.String(length=64), None),
    ("fiscal_csc_id", sa.String(length=10), None),
    ("serie_nfce", sa.Integer(), "1"),
    ("serie_nfe", sa.Integer(), "1"),
    ("proximo_numero_nfce", sa.Integer(), "1"),
    ("proximo_numero_nfe", sa.Integer(), "1"),
]

_PROD_COLS = [
    ("cest", sa.String(length=7), None),
    ("cfop_padrao", sa.String(length=4), "5102"),
    ("cst_icms", sa.String(length=3), None),
    ("csosn", sa.String(length=3), "102"),
    ("unidade_tributavel", sa.String(length=6), None),
    ("icms_aliquota", sa.Numeric(5, 2), "0"),
    ("pis_aliquota", sa.Numeric(5, 2), "0"),
    ("cofins_aliquota", sa.Numeric(5, 2), "0"),
]


def _add_missing(table, cols):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = {c["name"] for c in inspector.get_columns(table)}
    for name, coltype, default in cols:
        if name not in existing:
            kwargs = {"nullable": True}
            if default is not None:
                kwargs["server_default"] = sa.text(default) if str(default).isdigit() else default
            op.add_column(table, sa.Column(name, coltype, **kwargs))


def upgrade():
    _add_missing("estabelecimentos", _ESTAB_COLS)
    _add_missing("produtos", _PROD_COLS)


def downgrade():
    for name, _, _ in _PROD_COLS:
        try:
            op.drop_column("produtos", name)
        except Exception:
            pass
    for name, _, _ in _ESTAB_COLS:
        try:
            op.drop_column("estabelecimentos", name)
        except Exception:
            pass
