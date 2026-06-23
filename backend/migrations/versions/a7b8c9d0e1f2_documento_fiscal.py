"""tabela documentos_fiscais (emissão NFC-e/NF-e)

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-06-23
"""
from alembic import op
import sqlalchemy as sa


revision = "a7b8c9d0e1f2"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "documentos_fiscais" in inspector.get_table_names():
        return
    op.create_table(
        "documentos_fiscais",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("estabelecimento_id", sa.Integer(), nullable=False),
        sa.Column("venda_id", sa.Integer(), nullable=True),
        sa.Column("funcionario_id", sa.Integer(), nullable=True),
        sa.Column("tipo", sa.String(length=10), nullable=True),
        sa.Column("modelo", sa.String(length=2), nullable=True),
        sa.Column("ambiente", sa.String(length=15), nullable=True),
        sa.Column("gateway", sa.String(length=30), nullable=True),
        sa.Column("referencia", sa.String(length=60), nullable=False),
        sa.Column("numero", sa.String(length=15), nullable=True),
        sa.Column("serie", sa.String(length=5), nullable=True),
        sa.Column("chave_acesso", sa.String(length=44), nullable=True),
        sa.Column("protocolo", sa.String(length=30), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("motivo_rejeicao", sa.Text(), nullable=True),
        sa.Column("valor_total", sa.Numeric(19, 4), nullable=True),
        sa.Column("danfe_url", sa.String(length=500), nullable=True),
        sa.Column("xml_url", sa.String(length=500), nullable=True),
        sa.Column("xml_content", sa.Text(), nullable=True),
        sa.Column("qr_code", sa.Text(), nullable=True),
        sa.Column("justificativa_cancelamento", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("autorizado_em", sa.DateTime(), nullable=True),
        sa.Column("cancelado_em", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["estabelecimento_id"], ["estabelecimentos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["venda_id"], ["vendas.id"]),
        sa.ForeignKeyConstraint(["funcionario_id"], ["funcionarios.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("estabelecimento_id", "referencia", name="uq_docfiscal_estab_ref"),
    )
    op.create_index("ix_docfiscal_venda", "documentos_fiscais", ["venda_id"])
    op.create_index("ix_docfiscal_status", "documentos_fiscais", ["status"])
    op.create_index("ix_docfiscal_chave", "documentos_fiscais", ["chave_acesso"])


def downgrade():
    op.drop_table("documentos_fiscais")
