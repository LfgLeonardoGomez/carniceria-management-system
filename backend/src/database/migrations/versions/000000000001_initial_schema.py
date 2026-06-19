"""initial schema

Revision ID: 000000000001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "000000000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated please adjust! ###
    op.create_table(
        "empresa",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("nombre_comercial", sa.String(), nullable=False),
        sa.Column("razon_social", sa.String(), nullable=True),
        sa.Column("cuit", sa.String(), nullable=True),
        sa.Column("domicilio", sa.String(), nullable=True),
        sa.Column("telefono", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("logo_url", sa.String(), nullable=True),
        sa.Column("datos_fiscales", sa.JSON(), nullable=True),
        sa.Column("configuracion_general", sa.JSON(), nullable=True),
        sa.Column("parametros_operativos", sa.JSON(), nullable=True),
        sa.Column("activa", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_empresa_cuit"), "empresa", ["cuit"], unique=False)

    op.create_table(
        "rol",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column("permisos", sa.JSON(), nullable=True),
        sa.Column("empresa_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["empresa_id"],
            ["empresa.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_rol_empresa_id"), "rol", ["empresa_id"], unique=False)

    op.create_table(
        "usuario",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("empresa_id", sa.Uuid(), nullable=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("contrasena_hash", sa.String(), nullable=False),
        sa.Column("nombre", sa.String(), nullable=True),
        sa.Column("apellido", sa.String(), nullable=True),
        sa.Column("rol_id", sa.Uuid(), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.Column("ultimo_acceso", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["empresa_id"],
            ["empresa.id"],
        ),
        sa.ForeignKeyConstraint(
            ["rol_id"],
            ["rol.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_usuario_email"), "usuario", ["email"], unique=True)
    op.create_index(op.f("ix_usuario_empresa_id"), "usuario", ["empresa_id"], unique=False)

    op.create_table(
        "categoria_producto",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("empresa_id", sa.Uuid(), nullable=True),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["empresa_id"],
            ["empresa.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "tipo_corte",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nombre"),
    )

    op.create_table(
        "categoria_gasto",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nombre"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated please adjust! ###
    op.drop_table("categoria_gasto")
    op.drop_table("tipo_corte")
    op.drop_table("categoria_producto")
    op.drop_index(op.f("ix_usuario_empresa_id"), table_name="usuario")
    op.drop_index(op.f("ix_usuario_email"), table_name="usuario")
    op.drop_table("usuario")
    op.drop_index(op.f("ix_rol_empresa_id"), table_name="rol")
    op.drop_table("rol")
    op.drop_index(op.f("ix_empresa_cuit"), table_name="empresa")
    op.drop_table("empresa")
    # ### end Alembic commands ###
