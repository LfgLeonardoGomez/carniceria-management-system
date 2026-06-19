"""add admin_id to empresa and auditoria table

Revision ID: 000000000010
Revises: 000000000009
Create Date: 2024-06-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "000000000010"
down_revision = "000000000009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "empresa",
        sa.Column("admin_id", sa.Uuid(), nullable=True),
    )
    op.create_index(
        op.f("ix_empresa_admin_id"),
        "empresa",
        ["admin_id"],
        unique=False,
    )
    op.create_foreign_key(
        op.f("fk_empresa_admin_id_usuario"),
        "empresa",
        "usuario",
        ["admin_id"],
        ["id"],
    )

    op.create_table(
        "auditoria",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("target_empresa_id", sa.Uuid(), nullable=True),
        sa.Column("target_usuario_id", sa.Uuid(), nullable=True),
        sa.Column("details", sa.String(), nullable=True),
        sa.Column("ip_address", sa.String(), nullable=True),
        sa.Column("user_agent", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["usuario.id"],
        ),
        sa.ForeignKeyConstraint(
            ["target_empresa_id"],
            ["empresa.id"],
        ),
        sa.ForeignKeyConstraint(
            ["target_usuario_id"],
            ["usuario.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_auditoria_action"),
        "auditoria",
        ["action"],
        unique=False,
    )
    op.create_index(
        op.f("ix_auditoria_actor_id"),
        "auditoria",
        ["actor_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_auditoria_target_empresa_id"),
        "auditoria",
        ["target_empresa_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_auditoria_target_usuario_id"),
        "auditoria",
        ["target_usuario_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_auditoria_target_usuario_id"), table_name="auditoria")
    op.drop_index(op.f("ix_auditoria_target_empresa_id"), table_name="auditoria")
    op.drop_index(op.f("ix_auditoria_actor_id"), table_name="auditoria")
    op.drop_index(op.f("ix_auditoria_action"), table_name="auditoria")
    op.drop_table("auditoria")

    op.drop_constraint(op.f("fk_empresa_admin_id_usuario"), "empresa", type_="foreignkey")
    op.drop_index(op.f("ix_empresa_admin_id"), table_name="empresa")
    op.drop_column("empresa", "admin_id")
