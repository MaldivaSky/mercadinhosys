"""Conformidade logística: documentos (CNH/CRLV) + checklists_veiculo

Revision ID: b4d6f8a0c2e3
Revises: a3c5e7f9b1d2
Create Date: 2026-07-05
"""
from alembic import op
import sqlalchemy as sa

revision = 'b4d6f8a0c2e3'
down_revision = 'a3c5e7f9b1d2'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('motoristas', sa.Column('cnh_documento_url', sa.String(length=500), nullable=True))
    op.add_column('veiculos', sa.Column('crlv_documento_url', sa.String(length=500), nullable=True))

    op.create_table(
        'checklists_veiculo',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('estabelecimento_id', sa.Integer(), sa.ForeignKey('estabelecimentos.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('veiculo_id', sa.Integer(), sa.ForeignKey('veiculos.id', ondelete='CASCADE'), nullable=False),
        sa.Column('motorista_id', sa.Integer(), sa.ForeignKey('motoristas.id'), nullable=True),
        sa.Column('km_atual', sa.Numeric(10, 2), nullable=True),
        sa.Column('itens_json', sa.JSON(), nullable=True),
        sa.Column('aprovado', sa.Boolean(), nullable=True),
        sa.Column('observacoes_gerais', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('sync_uuid', sa.String(length=36), nullable=False, unique=True),
    )
    op.create_index('ix_checklist_veiculo', 'checklists_veiculo', ['veiculo_id'])
    op.create_index('ix_checklist_created', 'checklists_veiculo', ['created_at'])


def downgrade():
    op.drop_index('ix_checklist_created', table_name='checklists_veiculo')
    op.drop_index('ix_checklist_veiculo', table_name='checklists_veiculo')
    op.drop_table('checklists_veiculo')
    op.drop_column('veiculos', 'crlv_documento_url')
    op.drop_column('motoristas', 'cnh_documento_url')
