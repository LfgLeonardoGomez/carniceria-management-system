"""Rentabilidad service — read-only profitability aggregation (C-19).

Architecture (Decision 3): pure helpers separated from DB queries so they
can be unit-tested without a database. The async service functions do the
tenant-scoped queries and call the pure helpers.

Cost contract (Decision 2, mirrors calcular_ganancia):
  - If ANY line for a product has costo_unitario IS NULL → ganancia=None (never 0).
  - margen_porcentaje = ganancia / ventas × 100; None when ganancia=None or ventas=0.

Cut margin (Decision 4): average sale price Σ(importe)/Σ(kilos) for the
linked product over the range. precio_venta_promedio=None when no sales in
range (never zero price).
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.rentabilidad.schemas import (
    CorteRentabilidadRow,
    Orden,
    ProductoRentabilidadRow,
    RentabilidadCortesResponse,
    RentabilidadProductosResponse,
)


# ---------------------------------------------------------------------------
# Pure helper: product profitability ranking (Tasks 3.1–3.3)
# ---------------------------------------------------------------------------

def _ranking_productos(
    detalles: list,
    product_names: dict[uuid.UUID, str],
) -> list[ProductoRentabilidadRow]:
    """Aggregate per-product margin from a flat list of DetalleVenta objects.

    Each detalle is expected to have:
      .producto_id   — uuid
      .importe       — Decimal (sale line revenue)
      .cantidad_kilos — Decimal (kilos sold)
      .costo_unitario — Optional[Decimal] (snapshot; None = unavailable)

    NULL contract: if ANY line for a product has costo_unitario IS NULL,
    that product's ganancia and margen_porcentaje are None (never zero).
    """
    ventas_by_id: dict[uuid.UUID, Decimal] = {}
    costos_by_id: dict[uuid.UUID, Optional[Decimal]] = {}

    for det in detalles:
        pid = det.producto_id
        importe = Decimal(str(det.importe))
        ventas_by_id[pid] = ventas_by_id.get(pid, Decimal("0.00")) + importe

        # Once null for a product, stay null — stop accumulating cost
        if pid in costos_by_id and costos_by_id[pid] is None:
            continue

        if det.costo_unitario is None:
            costos_by_id[pid] = None
        else:
            kilo_costo = Decimal(str(det.cantidad_kilos)) * Decimal(str(det.costo_unitario))
            if pid not in costos_by_id:
                costos_by_id[pid] = kilo_costo
            else:
                costos_by_id[pid] = costos_by_id[pid] + kilo_costo  # type: ignore[operator]

    rows: list[ProductoRentabilidadRow] = []
    for pid, ventas in ventas_by_id.items():
        costos = costos_by_id.get(pid)  # None if null snapshot exists

        if costos is None:
            ganancia: Optional[Decimal] = None
            margen_porcentaje: Optional[Decimal] = None
        else:
            ganancia = (ventas - costos).quantize(Decimal("0.01"))
            if ventas == Decimal("0.00"):
                margen_porcentaje = None
            else:
                margen_porcentaje = (ganancia / ventas * Decimal("100")).quantize(Decimal("0.01"))

        rows.append(
            ProductoRentabilidadRow(
                producto_id=pid,
                nombre=product_names.get(pid, ""),
                ventas=ventas.quantize(Decimal("0.01")),
                ganancia=ganancia,
                margen_porcentaje=margen_porcentaje,
            )
        )

    return rows


def _apply_ordering(
    rows: list[ProductoRentabilidadRow],
    orden: Orden,
    top: Optional[int],
) -> list[ProductoRentabilidadRow]:
    """Sort product rows by margin direction; null-margin rows always LAST.

    Decision 5: null-last regardless of direction so missing data never
    appears as most/least profitable. top=N limits the head after sorting.
    """
    known = [r for r in rows if r.margen_porcentaje is not None]
    null_margin = [r for r in rows if r.margen_porcentaje is None]

    reverse = orden == "mayor"
    sorted_known = sorted(known, key=lambda r: r.margen_porcentaje, reverse=reverse)  # type: ignore[arg-type]
    ordered = sorted_known + null_margin

    if top is not None:
        ordered = ordered[:top]
    return ordered


# ---------------------------------------------------------------------------
# Pure helper: cut margin (Tasks 3.5–3.7)
# ---------------------------------------------------------------------------

def _margen_cortes(
    cortes: list,
    detalles: list,
    product_names: dict[uuid.UUID, str],
) -> list[CorteRentabilidadRow]:
    """Compute per-cut margin from CorteDesposte and DetalleVenta lists.

    Bridge: corte.producto_id → detalle.producto_id.
    Average sale price per linked product: Σ(importe)/Σ(kilos).

    Exclusions:
      - Cuts with producto_id IS NULL → excluded entirely
      - Linked product with no sales in range → precio_venta_promedio=None (never 0)
    """
    ventas_importe: dict[uuid.UUID, Decimal] = {}
    ventas_kilos: dict[uuid.UUID, Decimal] = {}

    for det in detalles:
        pid = det.producto_id
        ventas_importe[pid] = ventas_importe.get(pid, Decimal("0.00")) + Decimal(str(det.importe))
        ventas_kilos[pid] = ventas_kilos.get(pid, Decimal("0.000")) + Decimal(str(det.cantidad_kilos))

    rows: list[CorteRentabilidadRow] = []
    for corte in cortes:
        if corte.producto_id is None:
            continue  # excluded — no meaningful margin without sale price

        pid: uuid.UUID = corte.producto_id
        costo = Decimal(str(corte.costo_final_por_kilo))
        nombre = product_names.get(pid, "")

        if pid not in ventas_kilos or ventas_kilos[pid] == Decimal("0.000"):
            # No sales for this product in range
            precio_venta_promedio: Optional[Decimal] = None
            margen_por_kilo: Optional[Decimal] = None
            margen_porcentaje: Optional[Decimal] = None
        else:
            total_importe = ventas_importe[pid]
            total_kilos = ventas_kilos[pid]
            precio_venta_promedio = (total_importe / total_kilos).quantize(Decimal("0.01"))
            margen_por_kilo = (precio_venta_promedio - costo).quantize(Decimal("0.01"))
            if precio_venta_promedio == Decimal("0.00"):
                margen_porcentaje = None
            else:
                margen_porcentaje = (
                    margen_por_kilo / precio_venta_promedio * Decimal("100")
                ).quantize(Decimal("0.01"))

        rows.append(
            CorteRentabilidadRow(
                tipo_corte=corte.tipo_corte,
                producto_id=pid,
                nombre_producto=nombre,
                costo_por_kilo=costo.quantize(Decimal("0.01")),
                precio_venta_promedio=precio_venta_promedio,
                margen_por_kilo=margen_por_kilo,
                margen_porcentaje=margen_porcentaje,
            )
        )

    return rows


# ---------------------------------------------------------------------------
# UTC date range helpers (mirrors C-18 reporte_financiero pattern)
# ---------------------------------------------------------------------------

def _to_utc_date(dt: datetime) -> date:
    """Normalise a datetime to a UTC calendar date (mirrors C-18 _to_utc_date)."""
    if dt.tzinfo is None:
        return dt.date()
    return dt.astimezone(timezone.utc).date()


# ---------------------------------------------------------------------------
# Async service: product ranking query (Task 4.1)
# ---------------------------------------------------------------------------

async def ranking_productos(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    fecha_desde: Optional[datetime],
    fecha_hasta: Optional[datetime],
    orden: Orden,
    top: Optional[int],
) -> RentabilidadProductosResponse:
    """Tenant-scoped query of cobrada ventas + detalles, then rank by margin.

    Multi-tenant isolation: empresa_id is first in every WHERE clause.
    Date range: same calendar-day UTC bounds as C-18 reporte_financiero (Decision 7).
    """
    from src.modules.producto.models import Producto
    from src.modules.venta.models import Venta

    where_v = [
        Venta.empresa_id == empresa_id,
        Venta.estado == "cobrada",
    ]
    if fecha_desde is not None:
        cal_desde = _to_utc_date(fecha_desde)
        where_v.append(
            Venta.fecha >= datetime(cal_desde.year, cal_desde.month, cal_desde.day, 0, 0, 0)
        )
    if fecha_hasta is not None:
        cal_hasta = _to_utc_date(fecha_hasta)
        next_day = datetime(cal_hasta.year, cal_hasta.month, cal_hasta.day, 0, 0, 0) + timedelta(days=1)
        where_v.append(Venta.fecha < next_day)

    ventas_q = (
        select(Venta)
        .options(selectinload(Venta.detalles))
        .where(*where_v)
    )
    result_v = await db.execute(ventas_q)
    ventas = list(result_v.scalars().all())

    all_detalles = [det for v in ventas for det in v.detalles]

    # Batch-load product names
    producto_ids = {det.producto_id for det in all_detalles}
    product_names: dict[uuid.UUID, str] = {}
    if producto_ids:
        productos_q = select(Producto).where(Producto.id.in_(producto_ids))
        productos_result = await db.execute(productos_q)
        for p in productos_result.scalars().all():
            product_names[p.id] = p.nombre

    rows = _ranking_productos(all_detalles, product_names=product_names)
    ordered = _apply_ordering(rows, orden=orden, top=top)

    return RentabilidadProductosResponse(rows=ordered)


# ---------------------------------------------------------------------------
# Async service: cut margin query (Task 4.2)
# ---------------------------------------------------------------------------

async def margen_cortes(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    fecha_desde: Optional[datetime],
    fecha_hasta: Optional[datetime],
) -> RentabilidadCortesResponse:
    """Tenant-scoped query of CorteDesposte (with producto_id) and cobrada
    sale lines for linked products over the range.

    Multi-tenant isolation: empresa_id scopes both Desposte and Venta queries.
    Cuts with producto_id IS NULL are excluded in the pure helper.
    """
    from src.modules.desposte.models import CorteDesposte, Desposte
    from src.modules.producto.models import Producto
    from src.modules.venta.models import Venta

    # Query 1: all CorteDesposte for this empresa (via Desposte.empresa_id)
    cortes_q = (
        select(CorteDesposte)
        .join(Desposte, CorteDesposte.desposte_id == Desposte.id)
        .where(Desposte.empresa_id == empresa_id)
    )
    result_c = await db.execute(cortes_q)
    cortes = list(result_c.scalars().all())

    linked_producto_ids = {c.producto_id for c in cortes if c.producto_id is not None}

    if not linked_producto_ids:
        return RentabilidadCortesResponse(rows=[])

    # Query 2: cobrada sale lines for linked products over date range
    where_v = [
        Venta.empresa_id == empresa_id,
        Venta.estado == "cobrada",
    ]
    if fecha_desde is not None:
        cal_desde = _to_utc_date(fecha_desde)
        where_v.append(
            Venta.fecha >= datetime(cal_desde.year, cal_desde.month, cal_desde.day, 0, 0, 0)
        )
    if fecha_hasta is not None:
        cal_hasta = _to_utc_date(fecha_hasta)
        next_day = datetime(cal_hasta.year, cal_hasta.month, cal_hasta.day, 0, 0, 0) + timedelta(days=1)
        where_v.append(Venta.fecha < next_day)

    ventas_q = (
        select(Venta)
        .options(selectinload(Venta.detalles))
        .where(*where_v)
    )
    result_v = await db.execute(ventas_q)
    ventas = list(result_v.scalars().all())

    detalles = [
        det
        for v in ventas
        for det in v.detalles
        if det.producto_id in linked_producto_ids
    ]

    # Batch-load product names
    productos_q = select(Producto).where(Producto.id.in_(linked_producto_ids))
    productos_result = await db.execute(productos_q)
    product_names: dict[uuid.UUID, str] = {
        p.id: p.nombre for p in productos_result.scalars().all()
    }

    rows = _margen_cortes(cortes, detalles, product_names=product_names)

    return RentabilidadCortesResponse(rows=rows)
