"""add motivo to movimiento_stock

Revision ID: 000000000009
Revises: 000000000008
Create Date: 2024-06-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "000000000009"
down_revision = "000000000008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "movimiento_stock",
        sa.Column("motivo", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("movimiento_stock", "motivo")
