import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Stock Schemas
# ---------------------------------------------------------------------------
class StockItem(BaseModel):
    producto_id: uuid.UUID
    nombre: str
    plu: str
    stock_actual: Decimal
    stock_minimo: Optional[Decimal] = None
    estado: str  # ok, alerta, critico

    model_config = ConfigDict(extra="forbid")


class PaginatedStockResponse(BaseModel):
    items: list[StockItem]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(extra="forbid")


class MovimientoStockPublic(BaseModel):
    id: uuid.UUID
    empresa_id: uuid.UUID
    producto_id: uuid.UUID
    tipo: str
    cantidad_kilos: Decimal
    stock_resultante: Decimal
    referencia_id: Optional[str] = None
    referencia_tipo: Optional[str] = None
    motivo: Optional[str] = None
    operador_id: Optional[uuid.UUID] = None
    fecha: datetime
    created_at: datetime

    model_config = ConfigDict(extra="forbid")


class PaginatedKardexResponse(BaseModel):
    items: list[MovimientoStockPublic]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(extra="forbid")


class AjusteStockCreate(BaseModel):
    producto_id: uuid.UUID
    cantidad_kilos: Decimal = Field(..., description="Positivo para entrada, negativo para salida")
    motivo: str = Field(..., min_length=1, max_length=500)

    model_config = ConfigDict(extra="forbid")


class AlertaStockItem(BaseModel):
    producto_id: uuid.UUID
    nombre: str
    plu: str
    stock_actual: Decimal
    stock_minimo: Decimal
    estado: str  # alerta, critico

    model_config = ConfigDict(extra="forbid")
