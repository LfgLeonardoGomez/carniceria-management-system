"""add gasto table

Revision ID: 000000000013
Revises: 000000000012
Create Date: 2026-06-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "000000000013"
down_revision = "000000000012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "gasto",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("empresa_id", sa.Uuid(), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("categoria", sa.String(), nullable=False),
        sa.Column("descripcion", sa.String(), nullable=True),
        sa.Column("importe", sa.Numeric(precision=19, scale=2), nullable=False),
        sa.Column("medio_pago", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresa.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_gasto_empresa_id"), "gasto", ["empresa_id"], unique=False)
    op.create_index(op.f("ix_gasto_fecha"), "gasto", ["fecha"], unique=False)
    op.create_index(op.f("ix_gasto_categoria"), "gasto", ["categoria"], unique=False)
    op.create_index(op.f("ix_gasto_empresa_id_fecha"), "gasto", ["empresa_id", "fecha"], unique=False)
    op.create_index(op.f("ix_gasto_empresa_id_categoria"), "gasto", ["empresa_id", "categoria"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_gasto_empresa_id_categoria"), table_name="gasto")
    op.drop_index(op.f("ix_gasto_empresa_id_fecha"), table_name="gasto")
    op.drop_index(op.f("ix_gasto_categoria"), table_name="gasto")
    op.drop_index(op.f("ix_gasto_fecha"), table_name="gasto")
    op.drop_index(op.f("ix_gasto_empresa_id"), table_name="gasto")
    op.drop_table("gasto")
