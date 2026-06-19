"""add proveedor table with indexes and rls

Revision ID: 000000000005
Revises: 000000000004
Create Date: 2024-06-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "000000000005"
down_revision = "000000000004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create proveedor table
    op.create_table(
        "proveedor",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("empresa_id", sa.Uuid(), nullable=False),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column("cuit", sa.String(), nullable=True),
        sa.Column("telefono", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("direccion", sa.String(), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["empresa_id"],
            ["empresa.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Indexes for proveedor
    op.create_index(
        op.f("ix_proveedor_empresa_id"),
        "proveedor",
        ["empresa_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_proveedor_nombre"),
        "proveedor",
        ["nombre"],
        unique=False,
    )
    op.create_index(
        op.f("ix_proveedor_empresa_id_nombre"),
        "proveedor",
        ["empresa_id", "nombre"],
        unique=False,
    )
    op.create_index(
        op.f("ix_proveedor_cuit"),
        "proveedor",
        ["cuit"],
        unique=False,
    )
    op.create_index(
        op.f("ix_proveedor_activo"),
        "proveedor",
        ["activo"],
        unique=False,
    )

    # Partial unique index on (empresa_id, cuit) where cuit IS NOT NULL
    op.execute(
        "CREATE UNIQUE INDEX ix_proveedor_empresa_id_cuit_unique "
        "ON proveedor (empresa_id, cuit) WHERE cuit IS NOT NULL;"
    )

    # Enable RLS on proveedor
    op.execute("ALTER TABLE proveedor ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY proveedor_empresa_isolation ON proveedor "
        "USING (empresa_id = current_setting('app.current_empresa', true)::uuid "
        "OR current_setting('app.current_empresa', true) = '');"
    )


def downgrade() -> None:
    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS proveedor_empresa_isolation ON proveedor;")
    op.execute("ALTER TABLE proveedor DISABLE ROW LEVEL SECURITY;")

    # Drop indexes
    op.execute("DROP INDEX IF EXISTS ix_proveedor_empresa_id_cuit_unique;")
    op.drop_index(op.f("ix_proveedor_activo"), table_name="proveedor")
    op.drop_index(op.f("ix_proveedor_cuit"), table_name="proveedor")
    op.drop_index(op.f("ix_proveedor_empresa_id_nombre"), table_name="proveedor")
    op.drop_index(op.f("ix_proveedor_nombre"), table_name="proveedor")
    op.drop_index(op.f("ix_proveedor_empresa_id"), table_name="proveedor")

    # Drop table
    op.drop_table("proveedor")
