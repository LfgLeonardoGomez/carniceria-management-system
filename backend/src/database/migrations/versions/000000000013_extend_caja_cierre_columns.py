"""extend caja with cierre calculation columns and add descripcion to movimiento_caja

Revision ID: 000000000013
Revises: 000000000012
Create Date: 2026-06-20 00:00:00.000000

C-13 caja-operaciones. Additive only: every new caja column is nullable, so existing
rows (and C-12 behavior) keep working. movimiento_caja.descripcion is nullable too.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "000000000013"
down_revision = "000000000012"
branch_labels = None
depends_on = None


_CAJA_NUMERIC_COLS = [
    "efectivo_inicial",
    "efectivo_esperado",
    "efectivo_real",
    "transferencias_esperadas",
    "transferencias_reales",
    "tarjetas_esperadas",
    "tarjetas_reales",
    "diferencia_efectivo",
    "diferencia_transferencias",
    "diferencia_tarjetas",
    "diferencia_total",
]


def upgrade() -> None:
    # caja: nullable cierre columns
    for col in _CAJA_NUMERIC_COLS:
        op.add_column("caja", sa.Column(col, sa.Numeric(precision=19, scale=2), nullable=True))
    op.add_column("caja", sa.Column("usuario_apertura_id", sa.Uuid(), nullable=True))
    op.add_column("caja", sa.Column("usuario_cierre_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_caja_usuario_apertura_id", "caja", "usuario", ["usuario_apertura_id"], ["id"]
    )
    op.create_foreign_key(
        "fk_caja_usuario_cierre_id", "caja", "usuario", ["usuario_cierre_id"], ["id"]
    )
    op.create_index(op.f("ix_caja_usuario_apertura_id"), "caja", ["usuario_apertura_id"], unique=False)
    op.create_index(op.f("ix_caja_usuario_cierre_id"), "caja", ["usuario_cierre_id"], unique=False)

    # movimiento_caja: descripcion for manual movements
    op.add_column("movimiento_caja", sa.Column("descripcion", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("movimiento_caja", "descripcion")

    op.drop_index(op.f("ix_caja_usuario_cierre_id"), table_name="caja")
    op.drop_index(op.f("ix_caja_usuario_apertura_id"), table_name="caja")
    op.drop_constraint("fk_caja_usuario_cierre_id", "caja", type_="foreignkey")
    op.drop_constraint("fk_caja_usuario_apertura_id", "caja", type_="foreignkey")
    op.drop_column("caja", "usuario_cierre_id")
    op.drop_column("caja", "usuario_apertura_id")
    for col in reversed(_CAJA_NUMERIC_COLS):
        op.drop_column("caja", col)
