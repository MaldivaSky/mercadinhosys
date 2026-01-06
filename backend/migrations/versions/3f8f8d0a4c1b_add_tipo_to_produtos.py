"""add tipo to produtos

Revision ID: 3f8f8d0a4c1b
Revises: 2b2c732fc099
Create Date: 2026-01-05 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "3f8f8d0a4c1b"
down_revision = "2b2c732fc099"
branch_labels = None
depends_on = None


def upgrade():
    # Add column with a temporary default to backfill existing rows
    op.add_column(
        "produtos",
        sa.Column("tipo", sa.String(length=30), server_default="unidade"),
    )

    # Optional: normalize existing data explicitly (keeps idempotent)
    op.execute("UPDATE produtos SET tipo = 'unidade' WHERE tipo IS NULL")

    # Remove the server default after backfill so ORM default is used
    op.alter_column("produtos", "tipo", server_default=None)


def downgrade():
    op.drop_column("produtos", "tipo")
