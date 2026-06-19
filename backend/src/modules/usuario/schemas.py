import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class UsuarioCreate(BaseModel):
    nombre: str
    apellido: str
    email: EmailStr
    rol_id: uuid.UUID
    empresa_id: Optional[uuid.UUID] = None  # Solo superadmin puede especificarlo

    model_config = ConfigDict(extra="forbid")


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    email: Optional[EmailStr] = None
    rol_id: Optional[uuid.UUID] = None
    activo: Optional[bool] = None

    model_config = ConfigDict(extra="forbid")


class UsuarioPublic(BaseModel):
    id: uuid.UUID
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    email: str
    rol: Optional[str] = None
    activo: bool
    empresa_id: Optional[uuid.UUID] = None
    ultimo_acceso: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(extra="forbid")


class UsuarioListResponse(BaseModel):
    items: list[UsuarioPublic]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(extra="forbid")


class ContrasenaTemporalResponse(BaseModel):
    usuario: UsuarioPublic
    contrasena_temporal: str

    model_config = ConfigDict(extra="forbid")


class PerfilUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    email: Optional[EmailStr] = None
    rol_id: Optional[uuid.UUID] = None  # Ignorado intencionalmente por el servicio

    model_config = ConfigDict(extra="forbid")


class PerfilPublic(BaseModel):
    id: uuid.UUID
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    email: str
    rol: Optional[str] = None
    empresa: Optional[str] = None
    ultimo_acceso: Optional[datetime] = None

    model_config = ConfigDict(extra="forbid")
