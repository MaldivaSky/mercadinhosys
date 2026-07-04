"""Backfill nivel_acesso com a numeração canônica (1=Admin … 6=Entregador)

A numeração antiga era 3=Caixa, 4=Estoque, 5=RH, 6=Entregador, 7=Vendedor.
A canônica (Regras de Acesso) é 3=RH, 4=Estoque/Caixa, 5=Vendedor, 6=Entregador.
Recalcula a coluna a partir do role, que é a fonte de verdade.

Revision ID: c7d9e1f2a3b4
Revises: a4a7b50ea341
Create Date: 2026-07-03
"""
from alembic import op

revision = 'c7d9e1f2a3b4'
down_revision = 'a4a7b50ea341'
branch_labels = None
depends_on = None

ROLE_TO_NIVEL = {
    "ADMIN": 1, "ADMINISTRADOR": 1, "PROPRIETARIO": 1, "DONO": 1, "MASTER": 1,
    "GERENTE": 2, "SUPERVISOR": 2,
    "RH": 3, "RECURSOS_HUMANOS": 3,
    "CAIXA": 4, "OPERADOR": 4, "ESTOQUE": 4, "ESTOQUISTA": 4,
    "ALMOXARIFE": 4, "ATENDENTE": 4, "FUNCIONARIO": 4,
    "VENDEDOR": 5, "SFA": 5, "SAF": 5,
    "ENTREGADOR": 6, "MOTOBOY": 6, "MOTORISTA": 6,
}


def upgrade():
    conn = op.get_bind()
    for role, nivel in ROLE_TO_NIVEL.items():
        conn.exec_driver_sql(
            "UPDATE funcionarios SET nivel_acesso = %s WHERE UPPER(COALESCE(role, 'FUNCIONARIO')) = %s"
            if conn.dialect.name != "sqlite"
            else "UPDATE funcionarios SET nivel_acesso = ? WHERE UPPER(COALESCE(role, 'FUNCIONARIO')) = ?",
            (nivel, role),
        )
    # Roles desconhecidos caem no fallback 4 (estoque/caixa)
    placeholders = ", ".join(["%s" if conn.dialect.name != "sqlite" else "?"] * len(ROLE_TO_NIVEL))
    conn.exec_driver_sql(
        f"UPDATE funcionarios SET nivel_acesso = 4 WHERE UPPER(COALESCE(role, 'FUNCIONARIO')) NOT IN ({placeholders})",
        tuple(ROLE_TO_NIVEL.keys()),
    )


def downgrade():
    # Sem downgrade: a numeração antiga era inconsistente com o produto.
    pass
