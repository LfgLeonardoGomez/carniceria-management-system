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


# ---------------------------------------------------------------------------
# C-18 — Financial report schemas (Decision 6)
# NOTE: APPEND-ONLY. Do not modify C-17 symbols above.
# ---------------------------------------------------------------------------

GroupBy = Literal["dia", "semana", "mes", "anio"]


class FinancieroPeriodoRow(BaseModel):
    """One period bucket in the financial report.

    Five indicators per bucket:
      ventas         — total revenue from cobrada sales (always present)
      gastos         — operating expenses (always present)
      costos         — COGS from cost snapshot; null if any line lacks costo_unitario
      utilidad_bruta — ventas - costos; null when costos is null
      utilidad_neta  — utilidad_bruta - gastos; null when utilidad_bruta is null

    NULL is NEVER zero (spec mandate, mirrors calcular_ganancia contract).
    Monetary values are Decimal for precision; they serialize as strings in JSON.
    """

    model_config = {"extra": "forbid"}

    periodo: str                              # e.g. "2026-06", "2026-W25", "2026"
    ventas: Decimal = Field(decimal_places=2)
    gastos: Decimal = Field(decimal_places=2)
    costos: Optional[Decimal] = Field(default=None, decimal_places=2)
    utilidad_bruta: Optional[Decimal] = Field(default=None, decimal_places=2)
    utilidad_neta: Optional[Decimal] = Field(default=None, decimal_places=2)


class ReporteFinancieroResponse(BaseModel):
    """Response wrapper for the financial report endpoint."""

    model_config = {"extra": "forbid"}

    group_by: GroupBy
    rows: List[FinancieroPeriodoRow]
