import uuid
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AuditoriaPublic(BaseModel):
    id: uuid.UUID
    empresa_id: uuid.UUID
    usuario_id: Optional[uuid.UUID] = None
    accion: str
    entidad_tipo: str
    entidad_id: Optional[uuid.UUID] = None
    payload: Optional[dict] = None
    fecha: date
    hora: str
    created_at: str

    model_config = ConfigDict(extra="forbid")


class PaginatedAuditoriaResponse(BaseModel):
    items: list[AuditoriaPublic]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(extra="forbid")
