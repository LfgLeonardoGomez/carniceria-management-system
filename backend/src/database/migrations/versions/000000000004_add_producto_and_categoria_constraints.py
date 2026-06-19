"""add producto table and categoria_producto constraints

Revision ID: 000000000004
Revises: 000000000003
Create Date: 2024-06-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import func

# revision identifiers, used by Alembic.
revision = "000000000004"
down_revision = "000000000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create producto table
    op.create_table(
        "producto",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("empresa_id", sa.Uuid(), nullable=False),
        sa.Column("plu", sa.String(), nullable=False),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column("categoria_id", sa.Uuid(), nullable=True),
        sa.Column("precio_publico", sa.Numeric(19, 4), nullable=False),
        sa.Column("precio_mayorista", sa.Numeric(19, 4), nullable=False),
        sa.Column("costo_por_kilo", sa.Numeric(19, 4), nullable=False),
        sa.Column("margen", sa.Numeric(19, 4), nullable=False),
        sa.Column("stock_actual", sa.Numeric(19, 4), nullable=False),
        sa.Column("stock_minimo", sa.Numeric(19, 4), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["empresa_id"],
            ["empresa.id"],
        ),
        sa.ForeignKeyConstraint(
            ["categoria_id"],
            ["categoria_producto.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("empresa_id", "plu", name="uq_producto_empresa_plu"),
    )

    # Indexes for producto
    op.create_index(
        op.f("ix_producto_empresa_id"),
        "producto",
        ["empresa_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_producto_categoria_id"),
        "producto",
        ["categoria_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_producto_nombre_lower"),
        "producto",
        [sa.text("lower(nombre)")],
        unique=False,
    )
    op.create_index(
        op.f("ix_producto_activo"),
        "producto",
        ["activo"],
        unique=False,
    )

    # Add unique constraint to categoria_producto
    op.create_unique_constraint(
        "uq_categoria_producto_empresa_nombre",
        "categoria_producto",
        ["empresa_id", "nombre"],
    )

    # Add index on empresa_id for categoria_producto
    op.create_index(
        op.f("ix_categoria_producto_empresa_id"),
        "categoria_producto",
        ["empresa_id"],
        unique=False,
    )

    # Enable RLS on producto
    op.execute("ALTER TABLE producto ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY producto_empresa_isolation ON producto "
        "USING (empresa_id = current_setting('app.current_empresa', true)::uuid "
        "OR current_setting('app.current_empresa', true) = '');"
    )

    # Enable RLS on categoria_producto
    op.execute("ALTER TABLE categoria_producto ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY categoria_producto_empresa_isolation ON categoria_producto "
        "USING (empresa_id = current_setting('app.current_empresa', true)::uuid "
        "OR current_setting('app.current_empresa', true) = '');"
    )


def downgrade() -> None:
    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS categoria_producto_empresa_isolation ON categoria_producto;")
    op.execute("ALTER TABLE categoria_producto DISABLE ROW LEVEL SECURITY;")
    op.execute("DROP POLICY IF EXISTS producto_empresa_isolation ON producto;")
    op.execute("ALTER TABLE producto DISABLE ROW LEVEL SECURITY;")

    # Drop indexes and constraints
    op.drop_index(op.f("ix_categoria_producto_empresa_id"), table_name="categoria_producto")
    op.drop_constraint("uq_categoria_producto_empresa_nombre", table_name="categoria_producto")

    op.drop_index(op.f("ix_producto_activo"), table_name="producto")
    op.drop_index(op.f("ix_producto_nombre_lower"), table_name="producto")
    op.drop_index(op.f("ix_producto_categoria_id"), table_name="producto")
    op.drop_index(op.f("ix_producto_empresa_id"), table_name="producto")
    op.drop_table("producto")
