"""add auth tables

Revision ID: 000000000002
Revises: 000000000001
Create Date: 2024-01-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "000000000002"
down_revision = "000000000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated please adjust! ###
    op.create_table(
        "refresh_token",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("jti", sa.String(), nullable=False),
        sa.Column("exp", sa.DateTime(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuario.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("jti"),
    )
    op.create_index(op.f("ix_refresh_token_jti"), "refresh_token", ["jti"], unique=True)
    op.create_index(op.f("ix_refresh_token_usuario_id"), "refresh_token", ["usuario_id"], unique=False)

    op.create_table(
        "token_recuperacion",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("expiracion", sa.DateTime(), nullable=False),
        sa.Column("usado", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuario.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_token_recuperacion_usuario_id"), "token_recuperacion", ["usuario_id"], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated please adjust! ###
    op.drop_index(op.f("ix_token_recuperacion_usuario_id"), table_name="token_recuperacion")
    op.drop_table("token_recuperacion")
    op.drop_index(op.f("ix_refresh_token_usuario_id"), table_name="refresh_token")
    op.drop_index(op.f("ix_refresh_token_jti"), table_name="refresh_token")
    op.drop_table("refresh_token")
    # ### end Alembic commands ###
