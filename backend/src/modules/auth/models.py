import uuid
from datetime import datetime
from typing import Optional, Any

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import JSON, Index

from src.modules.empresa.models import Empresa


class Rol(SQLModel, table=True):
    __tablename__ = "rol"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    nombre: str = Field(nullable=False)
    permisos: Optional[dict[str, Any]] = Field(default=None, sa_type=JSON)
    empresa_id: Optional[uuid.UUID] = Field(
        default=None, foreign_key="empresa.id", index=True
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    empresa: Optional[Empresa] = Relationship()
    usuarios: list["Usuario"] = Relationship(back_populates="rol")


class Usuario(SQLModel, table=True):
    __tablename__ = "usuario"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    empresa_id: Optional[uuid.UUID] = Field(
        default=None, foreign_key="empresa.id", index=True
    )
    email: str = Field(nullable=False, unique=True, index=True)
    contrasena_hash: str = Field(nullable=False)
    nombre: Optional[str] = Field(default=None)
    apellido: Optional[str] = Field(default=None)
    rol_id: uuid.UUID = Field(foreign_key="rol.id", nullable=False, index=True)
    activo: bool = Field(default=True)
    ultimo_acceso: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    empresa: Optional[Empresa] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "Usuario.empresa_id"}
    )
    rol: Optional[Rol] = Relationship(back_populates="usuarios")

    refresh_tokens: list["RefreshToken"] = Relationship(back_populates="usuario")
    tokens_recuperacion: list["TokenRecuperacion"] = Relationship(back_populates="usuario")

    __table_args__ = (
        Index("ix_usuario_empresa_id_activo", "empresa_id", "activo"),
    )


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_token"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    usuario_id: uuid.UUID = Field(foreign_key="usuario.id", nullable=False, index=True)
    jti: str = Field(nullable=False, unique=True, index=True)
    exp: datetime = Field(nullable=False)
    revoked: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    usuario: Optional[Usuario] = Relationship(back_populates="refresh_tokens")


class TokenRecuperacion(SQLModel, table=True):
    __tablename__ = "token_recuperacion"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    usuario_id: uuid.UUID = Field(foreign_key="usuario.id", nullable=False, index=True)
    token_hash: str = Field(nullable=False)
    expiracion: datetime = Field(nullable=False)
    usado: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    usuario: Optional[Usuario] = Relationship(back_populates="tokens_recuperacion")
