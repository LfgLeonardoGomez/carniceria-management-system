import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Producto Schemas
# ---------------------------------------------------------------------------
class ProductoCreate(BaseModel):
    plu: str = Field(..., min_length=1, max_length=50)
    nombre: str = Field(..., min_length=1, max_length=255)
    categoria_id: Optional[uuid.UUID] = None
    precio_publico: Decimal = Field(..., ge=0)
    precio_mayorista: Decimal = Field(..., ge=0)
    costo_por_kilo: Decimal = Field(..., ge=0)
    stock_actual: Decimal = Field(..., ge=0)
    stock_minimo: Optional[Decimal] = Field(default=None, ge=0)

    model_config = ConfigDict(extra="forbid")


class ProductoUpdate(BaseModel):
    plu: Optional[str] = Field(default=None, min_length=1, max_length=50)
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=255)
    categoria_id: Optional[uuid.UUID] = None
    precio_publico: Optional[Decimal] = Field(default=None, ge=0)
    precio_mayorista: Optional[Decimal] = Field(default=None, ge=0)
    costo_por_kilo: Optional[Decimal] = Field(default=None, ge=0)
    stock_actual: Optional[Decimal] = Field(default=None, ge=0)
    stock_minimo: Optional[Decimal] = Field(default=None, ge=0)

    model_config = ConfigDict(extra="forbid")


class ProductoPublic(BaseModel):
    id: uuid.UUID
    empresa_id: uuid.UUID
    plu: str
    nombre: str
    categoria_id: Optional[uuid.UUID] = None
    precio_publico: Decimal
    precio_mayorista: Decimal
    costo_por_kilo: Decimal
    margen: Decimal
    stock_actual: Decimal
    stock_minimo: Optional[Decimal] = None
    activo: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(extra="forbid")


class ProductoToggleActivo(BaseModel):
    activo: bool

    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# CategoriaProducto Schemas
# ---------------------------------------------------------------------------
class CategoriaProductoCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=255)

    model_config = ConfigDict(extra="forbid")


class CategoriaProductoUpdate(BaseModel):
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=255)

    model_config = ConfigDict(extra="forbid")


class CategoriaProductoPublic(BaseModel):
    id: uuid.UUID
    empresa_id: Optional[uuid.UUID] = None
    nombre: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Paginated Response Schemas
# ---------------------------------------------------------------------------
class PaginatedProductoResponse(BaseModel):
    items: list[ProductoPublic]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(extra="forbid")


class PaginatedCategoriaResponse(BaseModel):
    items: list[CategoriaProductoPublic]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(extra="forbid")
