import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from src.modules.empresa.validators import validate_cuit


class ProveedorCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=255)
    cuit: Optional[str] = None
    telefono: Optional[str] = Field(default=None, max_length=50)
    email: Optional[EmailStr] = None
    direccion: Optional[str] = Field(default=None, max_length=255)

    model_config = ConfigDict(extra="forbid")

    @field_validator("cuit")
    @classmethod
    def check_cuit(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_cuit(v)
        return v


class ProveedorUpdate(BaseModel):
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=255)
    cuit: Optional[str] = None
    telefono: Optional[str] = Field(default=None, max_length=50)
    email: Optional[EmailStr] = None
    direccion: Optional[str] = Field(default=None, max_length=255)

    model_config = ConfigDict(extra="forbid")

    @field_validator("cuit")
    @classmethod
    def check_cuit(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_cuit(v)
        return v


class ProveedorResponse(BaseModel):
    id: uuid.UUID
    empresa_id: uuid.UUID
    nombre: str
    cuit: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None
    activo: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(extra="forbid")


class ProveedorListResponse(BaseModel):
    items: list[ProveedorResponse]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(extra="forbid")
