"""Pydantic schemas for the cuenta_corriente module (C-14).

All monetary values are Decimal with 2 decimal places.
extra='forbid' on every schema — no unexpected fields.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

ExportFormato = Literal["xlsx", "csv", "pdf"]


class PagoCreate(BaseModel):
    """Request body for POST /{cliente_id}/pagos.

    importe must be strictly positive (gt=0).
    extra='forbid' rejects unknown fields.
    """

    model_config = {"extra": "forbid"}

    importe: Decimal = Field(gt=0)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class MovimientoCCResponse(BaseModel):
    """One current-account movement (deuda or pago)."""

    model_config = {"extra": "forbid"}

    id: uuid.UUID
    tipo: str
    importe: Decimal = Field(decimal_places=2)
    saldo_resultante: Decimal = Field(decimal_places=2)
    venta_id: Optional[uuid.UUID] = None
    fecha: datetime


class PagoResponse(BaseModel):
    """Response for a successfully registered payment."""

    model_config = {"extra": "forbid"}

    movimiento: MovimientoCCResponse
    saldo_actual: Decimal = Field(decimal_places=2)


class HistorialCCResponse(BaseModel):
    """Paginated history response for GET /{cliente_id}."""

    model_config = {"extra": "forbid"}

    items: List[MovimientoCCResponse]
    total: int
    skip: int
    limit: int
    saldo_actual: Decimal = Field(decimal_places=2)


class EstadoCuentaResponse(BaseModel):
    """Full (unpaginated) account statement data for export."""

    model_config = {"extra": "forbid"}

    cliente_id: uuid.UUID
    cliente_nombre: str
    saldo_actual: Decimal = Field(decimal_places=2)
    movimientos: List[MovimientoCCResponse]
