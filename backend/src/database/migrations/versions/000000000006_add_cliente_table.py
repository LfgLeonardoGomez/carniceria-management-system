"""add cliente table

Revision ID: 000000000006
Revises: 000000000005
Create Date: 2024-06-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "000000000006"
down_revision = "000000000005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cliente",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("empresa_id", sa.Uuid(), nullable=False),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column("apellido", sa.String(), nullable=True),
        sa.Column("razon_social", sa.String(), nullable=True),
        sa.Column("cuit", sa.String(), nullable=True),
        sa.Column("telefono", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("direccion", sa.String(), nullable=True),
        sa.Column("tipo_cliente", sa.String(), nullable=False, server_default="publico_general"),
        sa.Column("limite_cuenta_corriente", sa.Numeric(19, 4), nullable=False, server_default="0.0000"),
        sa.Column("saldo_actual", sa.Numeric(19, 4), nullable=False, server_default="0.0000"),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["empresa_id"],
            ["empresa.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Unique constraint on (empresa_id, cuit) where cuit IS NOT NULL
    op.create_index(
        op.f("ix_cliente_empresa_id_cuit"),
        "cliente",
        ["empresa_id", "cuit"],
        unique=True,
        postgresql_where=sa.text("cuit IS NOT NULL"),
    )

    # Indexes for filtering
    op.create_index(
        op.f("ix_cliente_empresa_id_tipo"),
        "cliente",
        ["empresa_id", "tipo_cliente"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cliente_empresa_id_nombre"),
        "cliente",
        ["empresa_id", sa.text("lower(nombre)")],
        unique=False,
    )
    op.create_index(
        op.f("ix_cliente_empresa_id"),
        "cliente",
        ["empresa_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cliente_nombre_lower"),
        "cliente",
        [sa.text("lower(nombre)")],
        unique=False,
    )

    # Enable RLS
    op.execute("ALTER TABLE cliente ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY cliente_empresa_isolation ON cliente "
        "USING (empresa_id = current_setting('app.current_empresa', true)::uuid "
        "OR current_setting('app.current_empresa', true) = '');"
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS cliente_empresa_isolation ON cliente;")
    op.execute("ALTER TABLE cliente DISABLE ROW LEVEL SECURITY;")
    op.drop_index(op.f("ix_cliente_nombre_lower"), table_name="cliente")
    op.drop_index(op.f("ix_cliente_empresa_id"), table_name="cliente")
    op.drop_index(op.f("ix_cliente_empresa_id_nombre"), table_name="cliente")
    op.drop_index(op.f("ix_cliente_empresa_id_tipo"), table_name="cliente")
    op.drop_index(op.f("ix_cliente_empresa_id_cuit"), table_name="cliente")
    op.drop_table("cliente")
