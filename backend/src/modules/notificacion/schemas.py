import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class NotificacionPublic(BaseModel):
    id: uuid.UUID
    empresa_id: uuid.UUID
    tipo: str
    mensaje: str
    leida: bool
    fecha_lectura: Optional[datetime] = None
    entidad_tipo: str
    entidad_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(extra="forbid")


class PaginatedNotificacionResponse(BaseModel):
    items: list[NotificacionPublic]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(extra="forbid")


class MarcarLeidaResponse(BaseModel):
    id: uuid.UUID
    leida: bool
    fecha_lectura: Optional[datetime] = None

    model_config = ConfigDict(extra="forbid")
