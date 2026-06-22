"""Pydantic schemas for the reporte module.

All monetary values are serialised as strings (Decimal-safe JSON representation).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Export format discriminator
# ---------------------------------------------------------------------------

ExportFormato = Literal["xlsx", "csv", "pdf"]


# ---------------------------------------------------------------------------
# Report row (one row per Venta — Decision 3)
# ---------------------------------------------------------------------------

class VentaReporteRow(BaseModel):
    """Single row in the sales report.

    Columns match RN-REP-03:
      fecha | cliente_nombre | productos | total_kilos |
      subtotal | total | medios_pago | ganancia_estimada
    """

    model_config = {"extra": "forbid"}

    venta_id: uuid.UUID
    fecha: datetime
    cliente_nombre: str
    productos: str
    total_kilos: Decimal = Field(decimal_places=3)
    subtotal: Decimal = Field(decimal_places=2)
    total: Decimal = Field(decimal_places=2)
    medios_pago: str
    ganancia_estimada: Optional[Decimal] = Field(default=None, decimal_places=2)


# ---------------------------------------------------------------------------
# Paginated response wrapper
# ---------------------------------------------------------------------------

class ReporteVentasResponse(BaseModel):
    """Paginated wrapper for the sales report list endpoint."""

    model_config = {"extra": "forbid"}

    rows: List[VentaReporteRow]
    total: int
    skip: int
    limit: int
