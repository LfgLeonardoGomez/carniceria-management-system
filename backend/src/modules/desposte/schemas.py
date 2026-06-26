import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DesposteCreate(BaseModel):
    compra_id: uuid.UUID
    fecha: date
    operador_id: uuid.UUID

    model_config = ConfigDict(extra="forbid")


class DesposteListParams(BaseModel):
    fecha: Optional[date] = None
    estado: Optional[str] = None
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)

    model_config = ConfigDict(extra="forbid")


class CompraCompacto(BaseModel):
    id: uuid.UUID
    fecha: date
    peso_total: Decimal
    costo_total: Decimal
    proveedor: Optional["ProveedorCompacto"] = None

    model_config = ConfigDict(extra="forbid")


class ProveedorCompacto(BaseModel):
    id: uuid.UUID
    nombre: str

    model_config = ConfigDict(extra="forbid")


class UsuarioCompacto(BaseModel):
    id: uuid.UUID
    nombre: Optional[str] = None
    apellido: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class ProductoCompacto(BaseModel):
    id: uuid.UUID
    nombre: str
    plu: str

    model_config = ConfigDict(extra="forbid")


class CorteDesposteResponse(BaseModel):
    id: uuid.UUID
    tipo_corte: str
    kilos_obtenidos: Decimal
    porcentaje_rendimiento: Decimal
    costo_asignado: Decimal
    costo_final_por_kilo: Decimal
    producto_id: Optional[uuid.UUID] = None
    producto: Optional[ProductoCompacto] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(extra="forbid")


class CorteDesposteCreate(BaseModel):
    tipo_corte: str
    kilos_obtenidos: Decimal = Field(..., gt=0)
    producto_id: Optional[uuid.UUID] = None

    model_config = ConfigDict(extra="forbid")


class MovimientoStockCompacto(BaseModel):
    id: uuid.UUID
    tipo: str
    cantidad_kilos: Decimal
    stock_resultante: Decimal
    producto_id: uuid.UUID
    fecha: datetime

    model_config = ConfigDict(extra="forbid")


class DesposteResponse(BaseModel):
    id: uuid.UUID
    empresa_id: uuid.UUID
    compra_id: uuid.UUID
    compra: Optional[CompraCompacto] = None
    fecha: date
    operador_id: uuid.UUID
    operador: Optional[UsuarioCompacto] = None
    estado: str
    rendimiento_total: Decimal
    merma: Decimal
    cortes: list[CorteDesposteResponse] = []
    movimientos_stock: list[MovimientoStockCompacto] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(extra="forbid")


class DesposteFinalizarResponse(DesposteResponse):
    pass


class DesposteListResponse(BaseModel):
    items: list[DesposteResponse]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(extra="forbid")


class TipoCorteRead(BaseModel):
    id: uuid.UUID
    nombre: str

    model_config = ConfigDict(from_attributes=True)
