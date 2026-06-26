import uuid
from datetime import datetime, timezone, date, time
from typing import Optional, Any

from sqlalchemy import JSON, Index
from sqlmodel import SQLModel, Field


class Auditoria(SQLModel, table=True):
    __tablename__ = "auditoria"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    empresa_id: uuid.UUID = Field(foreign_key="empresa.id", nullable=False, index=True)
    usuario_id: Optional[uuid.UUID] = Field(default=None, foreign_key="usuario.id", index=True)
    accion: str = Field(nullable=False, index=True)
    entidad_tipo: str = Field(nullable=False, index=True)
    entidad_id: Optional[uuid.UUID] = Field(default=None, index=True)
    payload: Optional[dict[str, Any]] = Field(default=None, sa_type=JSON)
    fecha: date = Field(default_factory=lambda: datetime.now(timezone.utc).date(), nullable=False, index=True)
    hora: time = Field(default_factory=lambda: datetime.now(timezone.utc).time(), nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_auditoria_empresa_id_fecha", "empresa_id", "fecha"),
        Index("ix_auditoria_empresa_id_accion", "empresa_id", "accion"),
        Index("ix_auditoria_empresa_id_entidad_tipo", "empresa_id", "entidad_tipo"),
    )
