"""add caja_origen_id to movimiento_caja and enforce closed-caja immutability

Revision ID: 000000000015
Revises: 000000000014
Create Date: 2026-06-21 00:00:00.000000

Rel-C1 cross-day anulación. Additive: caja_origen_id is nullable (only set on a
cross-day salida_anulacion). The trigger is the DB-layer guard that makes a `cerrada`
caja immutable — no movimiento may ever be inserted against it, independent of any
app-level check.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "000000000015"
down_revision = "000000000014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "movimiento_caja", sa.Column("caja_origen_id", sa.Uuid(), nullable=True)
    )
    op.create_foreign_key(
        "fk_movimiento_caja_caja_origen_id",
        "movimiento_caja",
        "caja",
        ["caja_origen_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_movimiento_caja_caja_origen_id"),
        "movimiento_caja",
        ["caja_origen_id"],
        unique=False,
    )

    # Defense in depth: reject any movimiento insert against a `cerrada` caja, so a
    # closed caja can never be mutated even by a future bug or stray query.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION reject_movimiento_on_closed_caja()
        RETURNS TRIGGER AS $$
        DECLARE
            caja_estado TEXT;
        BEGIN
            SELECT estado INTO caja_estado FROM caja WHERE id = NEW.caja_id;
            IF caja_estado = 'cerrada' THEN
                RAISE EXCEPTION
                    'No se puede registrar un movimiento en una caja cerrada (caja_id=%)',
                    NEW.caja_id;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_movimiento_caja_no_cerrada
        BEFORE INSERT ON movimiento_caja
        FOR EACH ROW EXECUTE FUNCTION reject_movimiento_on_closed_caja();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_movimiento_caja_no_cerrada ON movimiento_caja")
    op.execute("DROP FUNCTION IF EXISTS reject_movimiento_on_closed_caja()")

    op.drop_index(op.f("ix_movimiento_caja_caja_origen_id"), table_name="movimiento_caja")
    op.drop_constraint(
        "fk_movimiento_caja_caja_origen_id", "movimiento_caja", type_="foreignkey"
    )
    op.drop_column("movimiento_caja", "caja_origen_id")
