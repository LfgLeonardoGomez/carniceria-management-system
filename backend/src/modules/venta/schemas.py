import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
MEDIOS_PAGO = {"efectivo", "transferencia", "debito", "credito", "cuenta_corriente"}
ESTADOS_VENTA = {"en_curso", "suspendida", "cobrada", "anulada"}
TIPOS_CLIENTE = {"publico_general", "mayorista", "especial"}


# ---------------------------------------------------------------------------
# DetalleVenta schemas
# ---------------------------------------------------------------------------
class DetalleVentaCreate(BaseModel):
    producto_id: uuid.UUID
    cantidad_kilos: Decimal = Field(..., gt=0, decimal_places=3, max_digits=19)
    precio_unitario: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2, max_digits=19)

    model_config = ConfigDict(extra="forbid")

    @field_validator("cantidad_kilos")
    @classmethod
    def _validar_cantidad_precision(cls, v: Decimal) -> Decimal:
        # Ensure 3 decimal places
        quantized = Decimal(str(v)).quantize(Decimal("0.001"))
        if quantized <= Decimal("0.000"):
            raise ValueError("cantidad_kilos debe ser mayor a 0")
        return quantized


class DetalleVentaRead(BaseModel):
    id: uuid.UUID
    producto_id: uuid.UUID
    cantidad_kilos: Decimal
    precio_unitario: Decimal
    importe: Decimal
    costo_unitario: Optional[Decimal] = None

    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# PagoVenta schemas
# ---------------------------------------------------------------------------
class PagoVentaCreate(BaseModel):
    medio_pago: str
    importe: Decimal = Field(..., ge=0, decimal_places=2, max_digits=19)

    model_config = ConfigDict(extra="forbid")

    @field_validator("medio_pago")
    @classmethod
    def _validar_medio_pago(cls, v: str) -> str:
        if v not in MEDIOS_PAGO:
            raise ValueError(f"medio_pago debe ser uno de: {', '.join(MEDIOS_PAGO)}")
        return v


class PagoVentaRead(BaseModel):
    id: uuid.UUID
    venta_id: uuid.UUID
    medio_pago: str
    importe: Decimal

    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Ticket schema
# ---------------------------------------------------------------------------
class TicketItem(BaseModel):
    nombre: str
    cantidad_kilos: Decimal
    precio_unitario: Decimal
    importe: Decimal

    model_config = ConfigDict(extra="forbid")


class TicketData(BaseModel):
    empresa_nombre: str
    fecha: datetime
    items: List[TicketItem]
    subtotal: Decimal
    descuentos: Decimal
    total: Decimal
    medio_de_pago: str

    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Venta schemas
# ---------------------------------------------------------------------------
class VentaCreate(BaseModel):
    cliente_id: Optional[uuid.UUID] = None
    items: List[DetalleVentaCreate] = Field(..., min_length=1)
    descuentos: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2, max_digits=19)
    medio_pago: Optional[str] = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("medio_pago")
    @classmethod
    def _validar_medio_pago(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in MEDIOS_PAGO:
            raise ValueError(f"medio_pago debe ser uno de: {', '.join(MEDIOS_PAGO)}")
        return v


class VentaUpdate(BaseModel):
    cliente_id: Optional[uuid.UUID] = None
    items: Optional[List[DetalleVentaCreate]] = None
    descuentos: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2, max_digits=19)
    medio_pago: Optional[str] = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("medio_pago")
    @classmethod
    def _validar_medio_pago(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in MEDIOS_PAGO:
            raise ValueError(f"medio_pago debe ser uno de: {', '.join(MEDIOS_PAGO)}")
        return v


class VentaRead(BaseModel):
    id: uuid.UUID
    empresa_id: uuid.UUID
    cliente_id: Optional[uuid.UUID] = None
    tipo_cliente_al_momento: str
    estado: str
    subtotal: Decimal
    descuentos: Decimal
    total: Decimal
    fecha: datetime
    created_at: datetime
    updated_at: datetime
    detalles: List[DetalleVentaRead] = []
    pagos: List[PagoVentaRead] = []

    model_config = ConfigDict(extra="forbid")


class VentaListResponse(BaseModel):
    items: List[VentaRead]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(extra="forbid")


class CobrarVentaRequest(BaseModel):
    medio_pago: str

    model_config = ConfigDict(extra="forbid")

    @field_validator("medio_pago")
    @classmethod
    def _validar_medio_pago(cls, v: str) -> str:
        if v not in MEDIOS_PAGO:
            raise ValueError(f"medio_pago debe ser uno de: {', '.join(MEDIOS_PAGO)}")
        return v


class CobrarVentaResponse(BaseModel):
    venta: VentaRead
    ticket: TicketData

    model_config = ConfigDict(extra="forbid")
