"""add costo_unitario to detalle_venta (cost snapshot at sale time)

Revision ID: 000000000017
Revises: 000000000016
Create Date: 2026-06-21 00:00:00.000000

Adds a nullable Numeric(19,2) column `costo_unitario` to `detalle_venta`.

Design decision (locked by PO, 2026-06-21):
  The product's current `costo_por_kilo` is snapshotted into each DetalleVenta
  line at the moment the sale is created. This makes profit (ganancia) historically
  stable: updating a product's cost later does NOT retroactively change old sales.

  Pre-existing rows (created before this migration) keep costo_unitario = NULL.
  Their ganancia is "not available" — calcular_ganancia() returns None for any
  venta that has at least one NULL line.

No backfill by design: old rows stay NULL.
"""
from alembic import op
import sqlalchemy as sa

revision = "000000000017"
down_revision = "000000000016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "detalle_venta",
        sa.Column(
            "costo_unitario",
            sa.Numeric(precision=19, scale=2),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("detalle_venta", "costo_unitario")
