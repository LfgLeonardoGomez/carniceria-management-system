"""Pydantic schemas for the rentabilidad module (C-19).

All monetary and margin values are Decimal (serialized as strings).
Optional fields are genuinely nullable — null is NEVER coerced to zero.

Decision 6: extra='forbid' mirrors reporte/schemas.py.
"""
from __future__ import annotations

import uuid
from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Orden discriminator — controls ranking sort direction
# ---------------------------------------------------------------------------

Orden = Literal["mayor", "menor"]


# ---------------------------------------------------------------------------
# Product ranking row
# ---------------------------------------------------------------------------

class ProductoRentabilidadRow(BaseModel):
    """One row in the product profitability ranking.

    Fields:
      producto_id  — UUID of the product
      nombre       — product display name
      ventas       — Σ(importe) across cobrada sale lines for this product
      ganancia     — ventas − Σ(kilos × costo_unitario); None if ANY line has
                     costo_unitario IS NULL (never zero)
      margen_porcentaje — ganancia / ventas × 100; None when ganancia is None
                          or ventas is 0

    NULL is NEVER zero — matches the calcular_ganancia contract.
    """

    model_config = {"extra": "forbid"}

    producto_id: uuid.UUID
    nombre: str
    ventas: Decimal = Field(decimal_places=2)
    ganancia: Optional[Decimal] = Field(default=None, decimal_places=2)
    margen_porcentaje: Optional[Decimal] = Field(default=None, decimal_places=2)


class RentabilidadProductosResponse(BaseModel):
    """Response wrapper for GET /rentabilidad/productos."""

    model_config = {"extra": "forbid"}

    rows: List[ProductoRentabilidadRow]


# ---------------------------------------------------------------------------
# Cut margin row
# ---------------------------------------------------------------------------

class CorteRentabilidadRow(BaseModel):
    """One row in the cut profitability view.

    Bridge: CorteDesposte.producto_id → DetalleVenta.producto_id.

    Fields:
      tipo_corte          — cut type string (e.g. "asado", "vacio")
      producto_id         — linked product UUID
      nombre_producto     — linked product display name
      costo_por_kilo      — CorteDesposte.costo_final_por_kilo (Decimal)
      precio_venta_promedio — Σ(importe)/Σ(kilos) for the linked product;
                              None when no sales in range (never zero price)
      margen_por_kilo     — precio_venta_promedio − costo_por_kilo; None when
                              precio_venta_promedio is None
      margen_porcentaje   — margen_por_kilo / precio_venta_promedio × 100;
                              None when price is None (never zero)

    Cuts with producto_id IS NULL are excluded from the result entirely.
    """

    model_config = {"extra": "forbid"}

    tipo_corte: str
    producto_id: uuid.UUID
    nombre_producto: str
    costo_por_kilo: Decimal = Field(decimal_places=2)
    precio_venta_promedio: Optional[Decimal] = Field(default=None, decimal_places=2)
    margen_por_kilo: Optional[Decimal] = Field(default=None, decimal_places=2)
    margen_porcentaje: Optional[Decimal] = Field(default=None, decimal_places=2)


class RentabilidadCortesResponse(BaseModel):
    """Response wrapper for GET /rentabilidad/cortes."""

    model_config = {"extra": "forbid"}

    rows: List[CorteRentabilidadRow]
