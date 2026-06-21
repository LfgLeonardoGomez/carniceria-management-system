import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


TIPOS_MOVIMIENTO_MANUAL = {"retiro", "ingreso_manual"}


# ---------------------------------------------------------------------------
# Apertura
# ---------------------------------------------------------------------------
class AperturaCajaRequest(BaseModel):
    efectivo_inicial: Decimal = Field(..., ge=0, decimal_places=2, max_digits=19)

    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Movimiento
# ---------------------------------------------------------------------------
class MovimientoCajaRequest(BaseModel):
    tipo: str
    importe: Decimal = Field(..., gt=0, decimal_places=2, max_digits=19)
    descripcion: Optional[str] = Field(default=None, max_length=500)

    model_config = ConfigDict(extra="forbid")

    @field_validator("tipo")
    @classmethod
    def _validar_tipo(cls, v: str) -> str:
        if v not in TIPOS_MOVIMIENTO_MANUAL:
            raise ValueError(
                f"tipo debe ser uno de: {', '.join(sorted(TIPOS_MOVIMIENTO_MANUAL))}"
            )
        return v


class MovimientoCajaRead(BaseModel):
    id: uuid.UUID
    caja_id: uuid.UUID
    tipo: str
    medio: Optional[str] = None
    importe: Decimal
    descripcion: Optional[str] = None
    fecha: datetime

    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Cierre
# ---------------------------------------------------------------------------
class CierreCajaRequest(BaseModel):
    efectivo_real: Decimal = Field(..., ge=0, decimal_places=2, max_digits=19)
    transferencias_real: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2, max_digits=19)
    tarjetas_real: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2, max_digits=19)

    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------
class CajaRead(BaseModel):
    id: uuid.UUID
    empresa_id: uuid.UUID
    estado: str
    monto_inicial: Decimal
    monto_final: Optional[Decimal] = None
    fecha_apertura: datetime
    fecha_cierre: Optional[datetime] = None
    usuario_apertura_id: Optional[uuid.UUID] = None
    usuario_cierre_id: Optional[uuid.UUID] = None

    model_config = ConfigDict(extra="forbid")


class EsperadoRead(BaseModel):
    efectivo: Decimal
    transferencias: Decimal
    tarjetas: Decimal

    model_config = ConfigDict(extra="forbid")


class CajaActualResponse(BaseModel):
    caja: CajaRead
    esperado: EsperadoRead

    model_config = ConfigDict(extra="forbid")


class DiferenciasRead(BaseModel):
    diferencia_efectivo: Decimal
    diferencia_transferencias: Decimal
    diferencia_tarjetas: Decimal
    diferencia_total: Decimal
    tiene_diferencia: bool
    diferencia_significativa: bool

    model_config = ConfigDict(extra="forbid")


class RealesRead(BaseModel):
    efectivo: Decimal
    transferencias: Decimal
    tarjetas: Decimal

    model_config = ConfigDict(extra="forbid")


class CierreCajaResponse(BaseModel):
    caja: CajaRead
    esperado: EsperadoRead
    reales: RealesRead
    diferencias: DiferenciasRead

    model_config = ConfigDict(extra="forbid")
