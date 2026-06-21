import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Fixed category enum (stored as plain string, validated via Pydantic)
# ---------------------------------------------------------------------------
CATEGORIAS_GASTO = {
    "alquiler",
    "empleados",
    "luz",
    "agua",
    "gas",
    "internet",
    "combustible",
    "impuestos",
    "mantenimiento",
    "insumos",
    "otros",
}

MEDIOS_PAGO_GASTO = {
    "efectivo",
    "transferencia",
    "debito",
    "credito",
    "cheque",
}


# ---------------------------------------------------------------------------
# GastoCreate
# ---------------------------------------------------------------------------
class GastoCreate(BaseModel):
    fecha: date
    categoria: str
    descripcion: Optional[str] = None
    importe: Decimal = Field(..., gt=0, decimal_places=2, max_digits=19)
    medio_pago: str

    model_config = ConfigDict(extra="forbid")

    @field_validator("categoria")
    @classmethod
    def _validar_categoria(cls, v: str) -> str:
        if v not in CATEGORIAS_GASTO:
            raise ValueError(
                f"categoria debe ser una de: {', '.join(sorted(CATEGORIAS_GASTO))}"
            )
        return v

    @field_validator("medio_pago")
    @classmethod
    def _validar_medio_pago(cls, v: str) -> str:
        if v not in MEDIOS_PAGO_GASTO:
            raise ValueError(
                f"medio_pago debe ser uno de: {', '.join(sorted(MEDIOS_PAGO_GASTO))}"
            )
        return v


# ---------------------------------------------------------------------------
# GastoUpdate — all fields optional, same validation rules
# ---------------------------------------------------------------------------
class GastoUpdate(BaseModel):
    fecha: Optional[date] = None
    categoria: Optional[str] = None
    descripcion: Optional[str] = None
    importe: Optional[Decimal] = Field(default=None, gt=0, decimal_places=2, max_digits=19)
    medio_pago: Optional[str] = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("categoria")
    @classmethod
    def _validar_categoria(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in CATEGORIAS_GASTO:
            raise ValueError(
                f"categoria debe ser una de: {', '.join(sorted(CATEGORIAS_GASTO))}"
            )
        return v

    @field_validator("medio_pago")
    @classmethod
    def _validar_medio_pago(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in MEDIOS_PAGO_GASTO:
            raise ValueError(
                f"medio_pago debe ser uno de: {', '.join(sorted(MEDIOS_PAGO_GASTO))}"
            )
        return v


# ---------------------------------------------------------------------------
# GastoRead
# ---------------------------------------------------------------------------
class GastoRead(BaseModel):
    id: uuid.UUID
    empresa_id: uuid.UUID
    fecha: date
    categoria: str
    descripcion: Optional[str] = None
    importe: Decimal
    medio_pago: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# GastoListResponse
# ---------------------------------------------------------------------------
class GastoListResponse(BaseModel):
    items: List[GastoRead]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(extra="forbid")
