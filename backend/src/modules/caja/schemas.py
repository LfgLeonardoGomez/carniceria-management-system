import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

# Manual movement tipos accepted via the API (subset of TIPOS_MOVIMIENTO_LITERAL).
# System-generated tipos (entrada_venta, salida_anulacion) are written internally and
# never accepted via the public movimiento endpoint.
TipoMovimientoManual = Literal["retiro", "ingreso_manual"]


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
    # Literal type provides schema-layer validation without a custom validator.
    tipo: TipoMovimientoManual
    importe: Decimal = Field(..., gt=0, decimal_places=2, max_digits=19)
    descripcion: Optional[str] = Field(default=None, max_length=500)

    model_config = ConfigDict(extra="forbid")


class MovimientoCajaRead(BaseModel):
    id: uuid.UUID
    caja_id: uuid.UUID
    # str here so the read schema accepts all internal system tipos too.
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
    efectivo_inicial: Decimal
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
