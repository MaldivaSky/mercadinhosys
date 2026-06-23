"""tabela notas_fiscais_entrada (importação de XML de compra)

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-06-23
"""
from alembic import op
import sqlalchemy as sa


revision = "f6a7b8c9d0e1"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "notas_fiscais_entrada" in inspector.get_table_names():
        return
    op.create_table(
        "notas_fiscais_entrada",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("estabelecimento_id", sa.Integer(), nullable=False),
        sa.Column("fornecedor_id", sa.Integer(), nullable=True),
        sa.Column("funcionario_id", sa.Integer(), nullable=True),
        sa.Column("chave_acesso", sa.String(length=44), nullable=False),
        sa.Column("modelo", sa.String(length=2), nullable=True),
        sa.Column("numero", sa.String(length=15), nullable=True),
        sa.Column("serie", sa.String(length=5), nullable=True),
        sa.Column("natureza_operacao", sa.String(length=120), nullable=True),
        sa.Column("emitente_cnpj", sa.String(length=14), nullable=True),
        sa.Column("emitente_nome", sa.String(length=150), nullable=True),
        sa.Column("data_emissao", sa.DateTime(), nullable=True),
        sa.Column("valor_total", sa.Numeric(19, 4), nullable=True),
        sa.Column("qtd_itens", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("xml_content", sa.Text(), nullable=True),
        sa.Column("itens_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["estabelecimento_id"], ["estabelecimentos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["fornecedor_id"], ["fornecedores.id"]),
        sa.ForeignKeyConstraint(["funcionario_id"], ["funcionarios.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("estabelecimento_id", "chave_acesso", name="uq_nfe_entrada_estab_chave"),
    )
    op.create_index("ix_nfe_entrada_chave", "notas_fiscais_entrada", ["chave_acesso"])
    op.create_index("ix_nfe_entrada_data", "notas_fiscais_entrada", ["data_emissao"])


def downgrade():
    op.drop_table("notas_fiscais_entrada")
