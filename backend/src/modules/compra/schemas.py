import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CompraCreate(BaseModel):
    fecha: date
    proveedor_id: uuid.UUID
    cantidad_medias_reses: int = Field(..., ge=1)
    peso_total: Decimal = Field(..., gt=0)
    costo_total: Decimal = Field(..., gt=0)
    observaciones: Optional[str] = Field(default=None, max_length=1000)

    model_config = ConfigDict(extra="forbid")

    @field_validator("fecha")
    @classmethod
    def fecha_no_futura(cls, v: date) -> date:
        if v > datetime.utcnow().date():
            raise ValueError("La fecha no puede ser futura")
        return v


class CompraUpdate(BaseModel):
    fecha: Optional[date] = None
    cantidad_medias_reses: Optional[int] = Field(default=None, ge=1)
    peso_total: Optional[Decimal] = Field(default=None, gt=0)
    costo_total: Optional[Decimal] = Field(default=None, gt=0)
    observaciones: Optional[str] = Field(default=None, max_length=1000)

    model_config = ConfigDict(extra="forbid")

    @field_validator("fecha")
    @classmethod
    def fecha_no_futura(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and v > datetime.utcnow().date():
            raise ValueError("La fecha no puede ser futura")
        return v


class ProveedorCompacto(BaseModel):
    id: uuid.UUID
    nombre: str

    model_config = ConfigDict(extra="forbid")


class CompraResponse(BaseModel):
    id: uuid.UUID
    empresa_id: uuid.UUID
    proveedor_id: uuid.UUID
    proveedor: Optional[ProveedorCompacto] = None
    fecha: date
    cantidad_medias_reses: int
    peso_total: Decimal
    costo_total: Decimal
    costo_por_kilo: Decimal
    costo_promedio_historico: Decimal
    observaciones: Optional[str] = None
    estado: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(extra="forbid")


class CompraListResponse(BaseModel):
    items: list[CompraResponse]
    total: int
    skip: int
    limit: int
    costo_promedio_historico: Optional[Decimal] = None

    model_config = ConfigDict(extra="forbid")


class CompraHistorialItem(BaseModel):
    id: uuid.UUID
    fecha: date
    cantidad_medias_reses: int
    peso_total: Decimal
    costo_total: Decimal
    costo_por_kilo: Decimal
    observaciones: Optional[str] = None
    estado: str

    model_config = ConfigDict(extra="forbid")
