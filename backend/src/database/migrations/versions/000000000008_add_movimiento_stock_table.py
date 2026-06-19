"""add movimiento_stock table with indexes

Revision ID: 000000000008
Revises: 000000000007
Create Date: 2024-06-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "000000000008"
down_revision = "000000000007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "movimiento_stock",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("empresa_id", sa.Uuid(), nullable=False),
        sa.Column("producto_id", sa.Uuid(), nullable=False),
        sa.Column("tipo", sa.String(), nullable=False),
        sa.Column("cantidad_kilos", sa.DECIMAL(19, 3), nullable=False),
        sa.Column("stock_resultante", sa.DECIMAL(19, 3), nullable=False),
        sa.Column("referencia_id", sa.String(), nullable=True),
        sa.Column("referencia_tipo", sa.String(), nullable=True),
        sa.Column("operador_id", sa.Uuid(), nullable=True),
        sa.Column("fecha", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["empresa_id"],
            ["empresa.id"],
        ),
        sa.ForeignKeyConstraint(
            ["producto_id"],
            ["producto.id"],
        ),
        sa.ForeignKeyConstraint(
            ["operador_id"],
            ["usuario.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_movimiento_stock_empresa_id"),
        "movimiento_stock",
        ["empresa_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_movimiento_stock_producto_id"),
        "movimiento_stock",
        ["producto_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_movimiento_stock_empresa_id_producto_id_fecha"),
        "movimiento_stock",
        ["empresa_id", "producto_id", "fecha"],
        unique=False,
    )
    op.create_index(
        op.f("ix_movimiento_stock_tipo"),
        "movimiento_stock",
        ["tipo"],
        unique=False,
    )
    op.create_index(
        op.f("ix_movimiento_stock_referencia_tipo"),
        "movimiento_stock",
        ["referencia_tipo"],
        unique=False,
    )

    # Enable RLS on movimiento_stock
    op.execute("ALTER TABLE movimiento_stock ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY movimiento_stock_empresa_isolation ON movimiento_stock "
        "USING (empresa_id = current_setting('app.current_empresa', true)::uuid "
        "OR current_setting('app.current_empresa', true) = '');"
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS movimiento_stock_empresa_isolation ON movimiento_stock;")
    op.execute("ALTER TABLE movimiento_stock DISABLE ROW LEVEL SECURITY;")
    op.drop_index(op.f("ix_movimiento_stock_referencia_tipo"), table_name="movimiento_stock")
    op.drop_index(op.f("ix_movimiento_stock_tipo"), table_name="movimiento_stock")
    op.drop_index(op.f("ix_movimiento_stock_empresa_id_producto_id_fecha"), table_name="movimiento_stock")
    op.drop_index(op.f("ix_movimiento_stock_producto_id"), table_name="movimiento_stock")
    op.drop_index(op.f("ix_movimiento_stock_empresa_id"), table_name="movimiento_stock")
    op.drop_table("movimiento_stock")
