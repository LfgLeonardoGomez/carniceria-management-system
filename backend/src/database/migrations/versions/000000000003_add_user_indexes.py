"""add user indexes

Revision ID: 000000000003
Revises: 000000000002
Create Date: 2024-01-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "000000000003"
down_revision = "000000000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated please adjust! ###
    op.create_index(op.f("ix_usuario_rol_id"), "usuario", ["rol_id"], unique=False)
    op.create_index(
        "ix_usuario_empresa_id_activo",
        "usuario",
        ["empresa_id", "activo"],
        unique=False,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated please adjust! ###
    op.drop_index("ix_usuario_empresa_id_activo", table_name="usuario")
    op.drop_index(op.f("ix_usuario_rol_id"), table_name="usuario")
    # ### end Alembic commands ###
