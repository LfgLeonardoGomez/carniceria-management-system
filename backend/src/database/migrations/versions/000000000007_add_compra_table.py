"""add compra table with indexes and rls

Revision ID: 000000000007
Revises: 000000000006
Create Date: 2024-06-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "000000000007"
down_revision = "000000000006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create compra table
    op.create_table(
        "compra",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("empresa_id", sa.Uuid(), nullable=False),
        sa.Column("proveedor_id", sa.Uuid(), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("cantidad_medias_reses", sa.Integer(), nullable=False),
        sa.Column("peso_total", sa.DECIMAL(19, 3), nullable=False),
        sa.Column("costo_total", sa.DECIMAL(19, 3), nullable=False),
        sa.Column("costo_por_kilo", sa.DECIMAL(19, 3), nullable=False),
        sa.Column(
            "costo_promedio_historico",
            sa.DECIMAL(19, 3),
            nullable=False,
            server_default="0.000",
        ),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column(
            "estado",
            sa.String(),
            nullable=False,
            server_default="activa",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["empresa_id"],
            ["empresa.id"],
        ),
        sa.ForeignKeyConstraint(
            ["proveedor_id"],
            ["proveedor.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Indexes for compra
    op.create_index(
        op.f("ix_compra_empresa_id"),
        "compra",
        ["empresa_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_compra_proveedor_id"),
        "compra",
        ["proveedor_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_compra_empresa_id_fecha"),
        "compra",
        ["empresa_id", "fecha"],
        unique=False,
    )
    op.create_index(
        op.f("ix_compra_empresa_id_proveedor_id"),
        "compra",
        ["empresa_id", "proveedor_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_compra_fecha"),
        "compra",
        ["fecha"],
        unique=False,
    )
    op.create_index(
        op.f("ix_compra_estado"),
        "compra",
        ["estado"],
        unique=False,
    )

    # Enable RLS on compra
    op.execute("ALTER TABLE compra ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY compra_empresa_isolation ON compra "
        "USING (empresa_id = current_setting('app.current_empresa', true)::uuid "
        "OR current_setting('app.current_empresa', true) = '');"
    )


def downgrade() -> None:
    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS compra_empresa_isolation ON compra;")
    op.execute("ALTER TABLE compra DISABLE ROW LEVEL SECURITY;")

    # Drop indexes
    op.drop_index(op.f("ix_compra_estado"), table_name="compra")
    op.drop_index(op.f("ix_compra_fecha"), table_name="compra")
    op.drop_index(op.f("ix_compra_empresa_id_proveedor_id"), table_name="compra")
    op.drop_index(op.f("ix_compra_empresa_id_fecha"), table_name="compra")
    op.drop_index(op.f("ix_compra_proveedor_id"), table_name="compra")
    op.drop_index(op.f("ix_compra_empresa_id"), table_name="compra")

    # Drop table
    op.drop_table("compra")
