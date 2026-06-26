import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Index
from sqlmodel import SQLModel, Field


TIPOS_NOTIFICACION_LITERAL = [
    "stock_bajo",
    "stock_critico",
    "deuda_vencida",
    "gasto_elevado",
    "diferencia_caja",
]


class Notificacion(SQLModel, table=True):
    __tablename__ = "notificacion"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    empresa_id: uuid.UUID = Field(foreign_key="empresa.id", nullable=False, index=True)
    tipo: str = Field(nullable=False, index=True)
    mensaje: str = Field(nullable=False)
    leida: bool = Field(default=False, nullable=False)
    fecha_lectura: Optional[datetime] = Field(default=None)
    entidad_tipo: str = Field(nullable=False)
    entidad_id: uuid.UUID = Field(nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_notificacion_empresa_id_tipo", "empresa_id", "tipo"),
        Index("ix_notificacion_empresa_id_leida", "empresa_id", "leida"),
        Index("ix_notificacion_empresa_id_created_at", "empresa_id", "created_at"),
    )
