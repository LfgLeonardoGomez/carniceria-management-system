"""add desposte and corte_desposte tables

Revision ID: 000000000011
Revises: 000000000010
Create Date: 2024-06-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "000000000011"
down_revision = "000000000010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "desposte",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("empresa_id", sa.Uuid(), nullable=False),
        sa.Column("compra_id", sa.Uuid(), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("operador_id", sa.Uuid(), nullable=False),
        sa.Column("estado", sa.String(), nullable=False, server_default="en_proceso"),
        sa.Column("rendimiento_total", sa.Numeric(precision=19, scale=3), nullable=False),
        sa.Column("merma", sa.Numeric(precision=19, scale=3), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["empresa_id"],
            ["empresa.id"],
        ),
        sa.ForeignKeyConstraint(
            ["compra_id"],
            ["compra.id"],
        ),
        sa.ForeignKeyConstraint(
            ["operador_id"],
            ["usuario.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_desposte_empresa_id"),
        "desposte",
        ["empresa_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_desposte_compra_id"),
        "desposte",
        ["compra_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_desposte_operador_id"),
        "desposte",
        ["operador_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_desposte_empresa_id_fecha"),
        "desposte",
        ["empresa_id", "fecha"],
        unique=False,
    )
    op.create_index(
        op.f("ix_desposte_empresa_id_compra_id"),
        "desposte",
        ["empresa_id", "compra_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_desposte_empresa_id_estado"),
        "desposte",
        ["empresa_id", "estado"],
        unique=False,
    )

    op.create_table(
        "corte_desposte",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("desposte_id", sa.Uuid(), nullable=False),
        sa.Column("tipo_corte", sa.String(), nullable=False),
        sa.Column("kilos_obtenidos", sa.Numeric(precision=19, scale=3), nullable=False),
        sa.Column("porcentaje_rendimiento", sa.Numeric(precision=19, scale=3), nullable=False),
        sa.Column("costo_asignado", sa.Numeric(precision=19, scale=2), nullable=False),
        sa.Column("costo_final_por_kilo", sa.Numeric(precision=19, scale=2), nullable=False),
        sa.Column("producto_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["desposte_id"],
            ["desposte.id"],
        ),
        sa.ForeignKeyConstraint(
            ["producto_id"],
            ["producto.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("desposte_id", "tipo_corte", name="uq_corte_desposte_tipo"),
    )
    op.create_index(
        op.f("ix_corte_desposte_desposte_id"),
        "corte_desposte",
        ["desposte_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_corte_desposte_producto_id"),
        "corte_desposte",
        ["producto_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_corte_desposte_producto_id"), table_name="corte_desposte")
    op.drop_index(op.f("ix_corte_desposte_desposte_id"), table_name="corte_desposte")
    op.drop_table("corte_desposte")

    op.drop_index(op.f("ix_desposte_empresa_id_estado"), table_name="desposte")
    op.drop_index(op.f("ix_desposte_empresa_id_compra_id"), table_name="desposte")
    op.drop_index(op.f("ix_desposte_empresa_id_fecha"), table_name="desposte")
    op.drop_index(op.f("ix_desposte_operador_id"), table_name="desposte")
    op.drop_index(op.f("ix_desposte_compra_id"), table_name="desposte")
    op.drop_index(op.f("ix_desposte_empresa_id"), table_name="desposte")
    op.drop_table("desposte")
