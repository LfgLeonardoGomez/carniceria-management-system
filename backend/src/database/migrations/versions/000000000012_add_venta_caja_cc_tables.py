"""add venta, detalle_venta, pago_venta, caja, movimiento_caja, cuenta_corriente tables

Revision ID: 000000000012
Revises: 000000000011
Create Date: 2024-06-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "000000000012"
down_revision = "000000000011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # venta
    op.create_table(
        "venta",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("empresa_id", sa.Uuid(), nullable=False),
        sa.Column("cliente_id", sa.Uuid(), nullable=True),
        sa.Column("tipo_cliente_al_momento", sa.String(), nullable=False, server_default="publico_general"),
        sa.Column("estado", sa.String(), nullable=False, server_default="en_curso"),
        sa.Column("subtotal", sa.Numeric(precision=19, scale=2), nullable=False),
        sa.Column("descuentos", sa.Numeric(precision=19, scale=2), nullable=False, server_default="0.00"),
        sa.Column("total", sa.Numeric(precision=19, scale=2), nullable=False),
        sa.Column("fecha", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresa.id"]),
        sa.ForeignKeyConstraint(["cliente_id"], ["cliente.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_venta_empresa_id"), "venta", ["empresa_id"], unique=False)
    op.create_index(op.f("ix_venta_cliente_id"), "venta", ["cliente_id"], unique=False)
    op.create_index(op.f("ix_venta_empresa_id_fecha"), "venta", ["empresa_id", "fecha"], unique=False)
    op.create_index(op.f("ix_venta_empresa_id_cliente_id"), "venta", ["empresa_id", "cliente_id"], unique=False)
    op.create_index(op.f("ix_venta_empresa_id_estado"), "venta", ["empresa_id", "estado"], unique=False)

    # detalle_venta
    op.create_table(
        "detalle_venta",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("venta_id", sa.Uuid(), nullable=False),
        sa.Column("producto_id", sa.Uuid(), nullable=False),
        sa.Column("cantidad_kilos", sa.Numeric(precision=19, scale=3), nullable=False),
        sa.Column("precio_unitario", sa.Numeric(precision=19, scale=2), nullable=False),
        sa.Column("importe", sa.Numeric(precision=19, scale=2), nullable=False),
        sa.ForeignKeyConstraint(["venta_id"], ["venta.id"]),
        sa.ForeignKeyConstraint(["producto_id"], ["producto.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_detalle_venta_venta_id"), "detalle_venta", ["venta_id"], unique=False)
    op.create_index(op.f("ix_detalle_venta_producto_id"), "detalle_venta", ["producto_id"], unique=False)

    # pago_venta
    op.create_table(
        "pago_venta",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("venta_id", sa.Uuid(), nullable=False),
        sa.Column("medio_pago", sa.String(), nullable=False),
        sa.Column("importe", sa.Numeric(precision=19, scale=2), nullable=False),
        sa.ForeignKeyConstraint(["venta_id"], ["venta.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_pago_venta_venta_id"), "pago_venta", ["venta_id"], unique=False)

    # caja
    op.create_table(
        "caja",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("empresa_id", sa.Uuid(), nullable=False),
        sa.Column("operador_id", sa.Uuid(), nullable=False),
        sa.Column("fecha_apertura", sa.DateTime(), nullable=False),
        sa.Column("fecha_cierre", sa.DateTime(), nullable=True),
        sa.Column("monto_inicial", sa.Numeric(precision=19, scale=2), nullable=False),
        sa.Column("monto_final", sa.Numeric(precision=19, scale=2), nullable=True),
        sa.Column("estado", sa.String(), nullable=False, server_default="abierta"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresa.id"]),
        sa.ForeignKeyConstraint(["operador_id"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_caja_empresa_id"), "caja", ["empresa_id"], unique=False)
    op.create_index(op.f("ix_caja_operador_id"), "caja", ["operador_id"], unique=False)
    op.create_index(op.f("ix_caja_empresa_id_estado"), "caja", ["empresa_id", "estado"], unique=False)

    # movimiento_caja
    op.create_table(
        "movimiento_caja",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("caja_id", sa.Uuid(), nullable=False),
        sa.Column("empresa_id", sa.Uuid(), nullable=False),
        sa.Column("tipo", sa.String(), nullable=False),
        sa.Column("medio", sa.String(), nullable=True),
        sa.Column("importe", sa.Numeric(precision=19, scale=2), nullable=False),
        sa.Column("venta_id", sa.Uuid(), nullable=True),
        sa.Column("fecha", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["caja_id"], ["caja.id"]),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresa.id"]),
        sa.ForeignKeyConstraint(["venta_id"], ["venta.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_movimiento_caja_caja_id"), "movimiento_caja", ["caja_id"], unique=False)
    op.create_index(op.f("ix_movimiento_caja_empresa_id"), "movimiento_caja", ["empresa_id"], unique=False)
    op.create_index(op.f("ix_movimiento_caja_venta_id"), "movimiento_caja", ["venta_id"], unique=False)

    # cuenta_corriente
    op.create_table(
        "cuenta_corriente",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("empresa_id", sa.Uuid(), nullable=False),
        sa.Column("cliente_id", sa.Uuid(), nullable=False),
        sa.Column("tipo", sa.String(), nullable=False),
        sa.Column("importe", sa.Numeric(precision=19, scale=2), nullable=False),
        sa.Column("saldo_resultante", sa.Numeric(precision=19, scale=2), nullable=False),
        sa.Column("venta_id", sa.Uuid(), nullable=True),
        sa.Column("fecha", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresa.id"]),
        sa.ForeignKeyConstraint(["cliente_id"], ["cliente.id"]),
        sa.ForeignKeyConstraint(["venta_id"], ["venta.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_cuenta_corriente_empresa_id"), "cuenta_corriente", ["empresa_id"], unique=False)
    op.create_index(op.f("ix_cuenta_corriente_cliente_id"), "cuenta_corriente", ["cliente_id"], unique=False)
    op.create_index(op.f("ix_cuenta_corriente_venta_id"), "cuenta_corriente", ["venta_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_cuenta_corriente_venta_id"), table_name="cuenta_corriente")
    op.drop_index(op.f("ix_cuenta_corriente_cliente_id"), table_name="cuenta_corriente")
    op.drop_index(op.f("ix_cuenta_corriente_empresa_id"), table_name="cuenta_corriente")
    op.drop_table("cuenta_corriente")

    op.drop_index(op.f("ix_movimiento_caja_venta_id"), table_name="movimiento_caja")
    op.drop_index(op.f("ix_movimiento_caja_empresa_id"), table_name="movimiento_caja")
    op.drop_index(op.f("ix_movimiento_caja_caja_id"), table_name="movimiento_caja")
    op.drop_table("movimiento_caja")

    op.drop_index(op.f("ix_caja_empresa_id_estado"), table_name="caja")
    op.drop_index(op.f("ix_caja_operador_id"), table_name="caja")
    op.drop_index(op.f("ix_caja_empresa_id"), table_name="caja")
    op.drop_table("caja")

    op.drop_index(op.f("ix_pago_venta_venta_id"), table_name="pago_venta")
    op.drop_table("pago_venta")

    op.drop_index(op.f("ix_detalle_venta_producto_id"), table_name="detalle_venta")
    op.drop_index(op.f("ix_detalle_venta_venta_id"), table_name="detalle_venta")
    op.drop_table("detalle_venta")

    op.drop_index(op.f("ix_venta_empresa_id_estado"), table_name="venta")
    op.drop_index(op.f("ix_venta_empresa_id_cliente_id"), table_name="venta")
    op.drop_index(op.f("ix_venta_empresa_id_fecha"), table_name="venta")
    op.drop_index(op.f("ix_venta_cliente_id"), table_name="venta")
    op.drop_index(op.f("ix_venta_empresa_id"), table_name="venta")
    op.drop_table("venta")
