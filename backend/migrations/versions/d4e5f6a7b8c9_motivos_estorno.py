"""motivos_estorno configuráveis em configuracoes

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-06-23

Adiciona a coluna configuracoes.motivos_estorno (lista JSON em texto) usada pelo
admin para pré-definir os motivos de cancelamento/estorno de venda.
"""
from alembic import op
import sqlalchemy as sa


revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None

_DEFAULT = '["Erro de digitação", "Desistência do cliente", "Produto avariado", "Cobrança duplicada", "Treinamento/Teste"]'


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"] for c in inspector.get_columns("configuracoes")}
    if "motivos_estorno" not in cols:
        op.add_column(
            "configuracoes",
            sa.Column("motivos_estorno", sa.Text(), nullable=True, server_default=_DEFAULT),
        )


def downgrade():
    op.drop_column("configuracoes", "motivos_estorno")
