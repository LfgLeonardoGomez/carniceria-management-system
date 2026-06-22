"""unify caja apertura amount: efectivo_inicial (NOT NULL), drop monto_inicial

Revision ID: 000000000016
Revises: 000000000015
Create Date: 2026-06-21 00:00:00.000000

Polish-1 (C-13 debt cleanup). The original caja table (migration 012) had
`monto_inicial` as the NOT NULL apertura amount. Migration 013 added a redundant
nullable `efectivo_inicial`. Both were written by the apertura service path. The
cierre service path read `monto_inicial` — a latent consistency risk.

This migration resolves the duplication:
  1. Backfill `efectivo_inicial` from `monto_inicial` where NULL (safety net for
     any row created before migration 013 ran or via direct insert).
  2. Set `efectivo_inicial` NOT NULL.
  3. Drop `monto_inicial`.

Net result: single `efectivo_inicial` column, NOT NULL, for both apertura and cierre.
"""
from alembic import op
import sqlalchemy as sa

revision = "000000000016"
down_revision = "000000000015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Backfill any rows where efectivo_inicial was not set (defensive; in
    # practice the service always wrote both since migration 013 was applied).
    op.execute(
        "UPDATE caja SET efectivo_inicial = monto_inicial WHERE efectivo_inicial IS NULL"
    )

    # Step 2: Set NOT NULL constraint on efectivo_inicial now that all rows have a value.
    op.alter_column(
        "caja",
        "efectivo_inicial",
        nullable=False,
        existing_type=sa.Numeric(precision=19, scale=2),
    )

    # Step 3: Drop the now-redundant monto_inicial column.
    op.drop_column("caja", "monto_inicial")


def downgrade() -> None:
    # Restore monto_inicial as NOT NULL, copying efectivo_inicial back.
    op.add_column(
        "caja",
        sa.Column(
            "monto_inicial",
            sa.Numeric(precision=19, scale=2),
            nullable=True,
        ),
    )
    op.execute("UPDATE caja SET monto_inicial = efectivo_inicial")
    op.alter_column(
        "caja",
        "monto_inicial",
        nullable=False,
        existing_type=sa.Numeric(precision=19, scale=2),
    )
    # Restore efectivo_inicial as nullable.
    op.alter_column(
        "caja",
        "efectivo_inicial",
        nullable=True,
        existing_type=sa.Numeric(precision=19, scale=2),
    )
