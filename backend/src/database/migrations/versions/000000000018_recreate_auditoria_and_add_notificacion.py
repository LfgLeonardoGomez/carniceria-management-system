"""recreate auditoria table and add notificacion table with rls

Revision ID: 000000000018
Revises: 000000000017
Create Date: 2026-06-24 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "000000000018"
down_revision = "000000000017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop old auditoria table
    op.drop_index(op.f("ix_auditoria_target_usuario_id"), table_name="auditoria")
    op.drop_index(op.f("ix_auditoria_target_empresa_id"), table_name="auditoria")
    op.drop_index(op.f("ix_auditoria_actor_id"), table_name="auditoria")
    op.drop_index(op.f("ix_auditoria_action"), table_name="auditoria")
    op.drop_table("auditoria")

    # Create new auditoria table
    op.create_table(
        "auditoria",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("empresa_id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=True),
        sa.Column("accion", sa.String(), nullable=False),
        sa.Column("entidad_tipo", sa.String(), nullable=False),
        sa.Column("entidad_id", sa.Uuid(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("hora", sa.Time(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresa.id"]),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_auditoria_empresa_id"), "auditoria", ["empresa_id"], unique=False)
    op.create_index(op.f("ix_auditoria_usuario_id"), "auditoria", ["usuario_id"], unique=False)
    op.create_index(op.f("ix_auditoria_accion"), "auditoria", ["accion"], unique=False)
    op.create_index(op.f("ix_auditoria_entidad_tipo"), "auditoria", ["entidad_tipo"], unique=False)
    op.create_index(op.f("ix_auditoria_fecha"), "auditoria", ["fecha"], unique=False)
    op.create_index(
        op.f("ix_auditoria_empresa_id_fecha"),
        "auditoria",
        ["empresa_id", "fecha"],
        unique=False,
    )
    op.create_index(
        op.f("ix_auditoria_empresa_id_accion"),
        "auditoria",
        ["empresa_id", "accion"],
        unique=False,
    )
    op.create_index(
        op.f("ix_auditoria_empresa_id_entidad_tipo"),
        "auditoria",
        ["empresa_id", "entidad_tipo"],
        unique=False,
    )

    # Enable RLS on auditoria
    op.execute("ALTER TABLE auditoria ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY auditoria_empresa_isolation ON auditoria "
        "USING (empresa_id = current_setting('app.current_empresa', true)::uuid "
        "OR current_setting('app.current_empresa', true) = '');"
    )

    # Create notificacion table
    op.create_table(
        "notificacion",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("empresa_id", sa.Uuid(), nullable=False),
        sa.Column("tipo", sa.String(), nullable=False),
        sa.Column("mensaje", sa.String(), nullable=False),
        sa.Column("leida", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("fecha_lectura", sa.DateTime(), nullable=True),
        sa.Column("entidad_tipo", sa.String(), nullable=False),
        sa.Column("entidad_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresa.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_notificacion_empresa_id"), "notificacion", ["empresa_id"], unique=False)
    op.create_index(op.f("ix_notificacion_tipo"), "notificacion", ["tipo"], unique=False)
    op.create_index(op.f("ix_notificacion_leida"), "notificacion", ["leida"], unique=False)
    op.create_index(op.f("ix_notificacion_created_at"), "notificacion", ["created_at"], unique=False)
    op.create_index(
        op.f("ix_notificacion_empresa_id_tipo"),
        "notificacion",
        ["empresa_id", "tipo"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notificacion_empresa_id_leida"),
        "notificacion",
        ["empresa_id", "leida"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notificacion_empresa_id_created_at"),
        "notificacion",
        ["empresa_id", "created_at"],
        unique=False,
    )

    # Enable RLS on notificacion
    op.execute("ALTER TABLE notificacion ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY notificacion_empresa_isolation ON notificacion "
        "USING (empresa_id = current_setting('app.current_empresa', true)::uuid "
        "OR current_setting('app.current_empresa', true) = '');"
    )


def downgrade() -> None:
    # Drop notificacion
    op.execute("DROP POLICY IF EXISTS notificacion_empresa_isolation ON notificacion;")
    op.execute("ALTER TABLE notificacion DISABLE ROW LEVEL SECURITY;")
    op.drop_index(op.f("ix_notificacion_empresa_id_created_at"), table_name="notificacion")
    op.drop_index(op.f("ix_notificacion_empresa_id_leida"), table_name="notificacion")
    op.drop_index(op.f("ix_notificacion_empresa_id_tipo"), table_name="notificacion")
    op.drop_index(op.f("ix_notificacion_created_at"), table_name="notificacion")
    op.drop_index(op.f("ix_notificacion_leida"), table_name="notificacion")
    op.drop_index(op.f("ix_notificacion_tipo"), table_name="notificacion")
    op.drop_index(op.f("ix_notificacion_empresa_id"), table_name="notificacion")
    op.drop_table("notificacion")

    # Drop auditoria
    op.execute("DROP POLICY IF EXISTS auditoria_empresa_isolation ON auditoria;")
    op.execute("ALTER TABLE auditoria DISABLE ROW LEVEL SECURITY;")
    op.drop_index(op.f("ix_auditoria_empresa_id_entidad_tipo"), table_name="auditoria")
    op.drop_index(op.f("ix_auditoria_empresa_id_accion"), table_name="auditoria")
    op.drop_index(op.f("ix_auditoria_empresa_id_fecha"), table_name="auditoria")
    op.drop_index(op.f("ix_auditoria_fecha"), table_name="auditoria")
    op.drop_index(op.f("ix_auditoria_entidad_tipo"), table_name="auditoria")
    op.drop_index(op.f("ix_auditoria_accion"), table_name="auditoria")
    op.drop_index(op.f("ix_auditoria_usuario_id"), table_name="auditoria")
    op.drop_index(op.f("ix_auditoria_empresa_id"), table_name="auditoria")
    op.drop_table("auditoria")

    # Recreate old auditoria table (from migration 010)
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
        sa.ForeignKeyConstraint(["actor_id"], ["usuario.id"]),
        sa.ForeignKeyConstraint(["target_empresa_id"], ["empresa.id"]),
        sa.ForeignKeyConstraint(["target_usuario_id"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_auditoria_action"), "auditoria", ["action"], unique=False)
    op.create_index(op.f("ix_auditoria_actor_id"), "auditoria", ["actor_id"], unique=False)
    op.create_index(
        op.f("ix_auditoria_target_empresa_id"), "auditoria", ["target_empresa_id"], unique=False
    )
    op.create_index(
        op.f("ix_auditoria_target_usuario_id"), "auditoria", ["target_usuario_id"], unique=False
    )
