"""Dashboard aggregation service.

All aggregation queries are pure reads over existing tables.
Every query carries empresa_id for strict multi-tenant isolation (RN-SEG-01).
Money uses Decimal; stock uses Decimal with 3 decimals.
"""
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from src.modules.venta.models import Venta, DetalleVenta, PagoVenta
from src.modules.producto.models import Producto
from src.modules.gasto.models import Gasto
from src.common.rbac import has_permission, normalize_rol
from src.modules.dashboard.schemas import (
    IndicadoresResponse,
    ProductoRankingItem,
    RankingsResponse,
    VentaDiariaItem,
    VentaMensualItem,
    MedioPagoItem,
    EvolucionGananciaItem,
    GraficosResponse,
)


# ---------------------------------------------------------------------------
# Date range helpers (Task 2.8)
# ---------------------------------------------------------------------------

def calcular_rango_dia(ref: datetime) -> tuple[datetime, datetime]:
    """Return (start_of_day, end_of_day) UTC for the date of `ref`.

    ``ref`` should be UTC-aware. The boundaries are inclusive start / exclusive
    end: start <= venta.fecha < end+1s is handled by comparing >= start and < end.
    We use midnight as the start and the last second of the day (23:59:59.999999)
    as the end so that SQL BETWEEN-style comparisons work with either ``<=`` or ``<``.
    """
    d = ref.date()
    inicio = datetime(d.year, d.month, d.day, 0, 0, 0, 0, tzinfo=timezone.utc)
    fin = datetime(d.year, d.month, d.day, 23, 59, 59, 999999, tzinfo=timezone.utc)
    return inicio, fin


def calcular_rango_mes(ref: datetime) -> tuple[datetime, datetime]:
    """Return (start_of_month, ref) UTC for the month of `ref`."""
    d = ref.date()
    inicio = datetime(d.year, d.month, 1, 0, 0, 0, 0, tzinfo=timezone.utc)
    return inicio, ref


# ---------------------------------------------------------------------------
# Permission helpers (Task 3.1)
# ---------------------------------------------------------------------------

def tiene_permiso_reportes(usuario: Any) -> bool:
    """Check whether the user has the ``reportes:read`` permission."""
    if usuario is None:
        return False
    rol = getattr(usuario, "rol", None)
    if rol is None:
        return False
    rol_nombre = getattr(rol, "nombre", None)
    return has_permission(rol_nombre or "", "reportes:read")


# ---------------------------------------------------------------------------
# Snapshot availability (Task 3.2)
# ---------------------------------------------------------------------------

def verificar_snapshot_disponible(lineas: list[Any]) -> bool:
    """Return True only when every line has a non-NULL costo_unitario.

    An empty list returns False — we cannot confirm the snapshot exists.
    """
    if not lineas:
        return False
    for linea in lineas:
        # Support both dict-like and object-like access
        if isinstance(linea, dict):
            costo = linea.get("costo_unitario")
        else:
            costo = getattr(linea, "costo_unitario", None)
        if costo is None:
            return False
    return True


# ---------------------------------------------------------------------------
# Indicadores service (Task 2.7 / 3.3 / 3.4)
# ---------------------------------------------------------------------------

async def calcular_indicadores(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    usuario: Any,
    ahora: Optional[datetime] = None,
) -> IndicadoresResponse:
    """Compute all dashboard KPIs for `empresa_id` at the given moment."""
    if ahora is None:
        ahora = datetime.now(timezone.utc)

    inicio_dia, fin_dia = calcular_rango_dia(ahora)
    inicio_mes, _ = calcular_rango_mes(ahora)

    # --- ventas_dia ---
    result = await db.execute(
        select(func.coalesce(func.sum(Venta.total), Decimal("0.00")))
        .where(
            Venta.empresa_id == empresa_id,
            Venta.estado == "cobrada",
            Venta.fecha >= inicio_dia,
            Venta.fecha <= fin_dia,
        )
    )
    ventas_dia: Decimal = Decimal(str(result.scalar_one() or "0.00"))

    # --- ventas_mes ---
    result = await db.execute(
        select(func.coalesce(func.sum(Venta.total), Decimal("0.00")))
        .where(
            Venta.empresa_id == empresa_id,
            Venta.estado == "cobrada",
            Venta.fecha >= inicio_mes,
            Venta.fecha <= ahora,
        )
    )
    ventas_mes: Decimal = Decimal(str(result.scalar_one() or "0.00"))

    # --- kilos_vendidos (mes) ---
    result = await db.execute(
        select(func.coalesce(func.sum(DetalleVenta.cantidad_kilos), Decimal("0.000")))
        .join(Venta, DetalleVenta.venta_id == Venta.id)
        .where(
            Venta.empresa_id == empresa_id,
            Venta.estado == "cobrada",
            Venta.fecha >= inicio_mes,
            Venta.fecha <= ahora,
        )
    )
    kilos_vendidos: Decimal = Decimal(str(result.scalar_one() or "0.000"))

    # --- clientes_atendidos (día) ---
    result = await db.execute(
        select(func.count(Venta.id))
        .where(
            Venta.empresa_id == empresa_id,
            Venta.estado == "cobrada",
            Venta.fecha >= inicio_dia,
            Venta.fecha <= fin_dia,
        )
    )
    clientes_atendidos: int = result.scalar_one() or 0

    # --- stock_critico ---
    result = await db.execute(
        select(func.count(Producto.id))
        .where(
            Producto.empresa_id == empresa_id,
            Producto.activo == True,  # noqa: E712
            Producto.stock_minimo.isnot(None),
            Producto.stock_actual <= Producto.stock_minimo,
        )
    )
    stock_critico: int = result.scalar_one() or 0

    # --- gastos_mes ---
    result = await db.execute(
        select(func.coalesce(func.sum(Gasto.importe), Decimal("0.00")))
        .where(
            Gasto.empresa_id == empresa_id,
            Gasto.fecha >= inicio_mes.date(),
            Gasto.fecha <= ahora.date(),
        )
    )
    gastos_mes: Decimal = Decimal(str(result.scalar_one() or "0.00"))

    # --- ganancia (gated by permission + snapshot) ---
    ganancia_bruta: Optional[Decimal] = None
    ganancia_neta: Optional[Decimal] = None
    ganancia_disponible = False

    if tiene_permiso_reportes(usuario):
        # Check if snapshot data is available: fetch a sample of detalle lines
        sample_result = await db.execute(
            select(DetalleVenta.costo_unitario)
            .join(Venta, DetalleVenta.venta_id == Venta.id)
            .where(
                Venta.empresa_id == empresa_id,
                Venta.estado == "cobrada",
                Venta.fecha >= inicio_mes,
                Venta.fecha <= ahora,
            )
            .limit(100)
        )
        sample_costos = sample_result.scalars().all()

        # Build dict-like list for verificar_snapshot_disponible
        sample_lineas = [{"costo_unitario": c} for c in sample_costos]
        ganancia_disponible = verificar_snapshot_disponible(sample_lineas)

        if ganancia_disponible:
            # Compute aggregate profit in SQL for performance
            result = await db.execute(
                select(
                    func.sum(DetalleVenta.importe),
                    func.sum(
                        DetalleVenta.cantidad_kilos * DetalleVenta.costo_unitario
                    ),
                )
                .join(Venta, DetalleVenta.venta_id == Venta.id)
                .where(
                    Venta.empresa_id == empresa_id,
                    Venta.estado == "cobrada",
                    Venta.fecha >= inicio_mes,
                    Venta.fecha <= ahora,
                    DetalleVenta.costo_unitario.isnot(None),
                )
            )
            row = result.one()
            total_importe = row[0]
            total_costo = row[1]

            if total_importe is not None and total_costo is not None:
                ganancia_bruta = (
                    Decimal(str(total_importe)) - Decimal(str(total_costo))
                ).quantize(Decimal("0.01"))
                ganancia_neta = (ganancia_bruta - gastos_mes).quantize(
                    Decimal("0.01")
                )

    return IndicadoresResponse(
        ventas_dia=ventas_dia.quantize(Decimal("0.01")),
        ventas_mes=ventas_mes.quantize(Decimal("0.01")),
        kilos_vendidos=kilos_vendidos.quantize(Decimal("0.001")),
        clientes_atendidos=clientes_atendidos,
        stock_critico=stock_critico,
        gastos_mes=gastos_mes.quantize(Decimal("0.01")),
        ganancia_bruta=ganancia_bruta,
        ganancia_neta=ganancia_neta,
        ganancia_disponible=ganancia_disponible,
    )


# ---------------------------------------------------------------------------
# Rankings service (Task 4.2)
# ---------------------------------------------------------------------------

async def calcular_rankings(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    top: int = 10,
) -> RankingsResponse:
    """Return the top N products by kilos sold in the current month."""
    ahora = datetime.now(timezone.utc)
    inicio_mes, _ = calcular_rango_mes(ahora)

    result = await db.execute(
        select(
            DetalleVenta.producto_id,
            Producto.nombre,
            func.sum(DetalleVenta.cantidad_kilos).label("total_kilos"),
        )
        .join(Venta, DetalleVenta.venta_id == Venta.id)
        .join(Producto, DetalleVenta.producto_id == Producto.id)
        .where(
            Venta.empresa_id == empresa_id,
            Venta.estado == "cobrada",
            Venta.fecha >= inicio_mes,
            Venta.fecha <= ahora,
        )
        .group_by(DetalleVenta.producto_id, Producto.nombre)
        .order_by(func.sum(DetalleVenta.cantidad_kilos).desc())
        .limit(top)
    )
    rows = result.all()
    items = [
        ProductoRankingItem(
            producto_id=row.producto_id,
            nombre=row.nombre,
            kilos=Decimal(str(row.total_kilos)).quantize(Decimal("0.001")),
        )
        for row in rows
    ]
    return RankingsResponse(productos_mas_vendidos=items)


# ---------------------------------------------------------------------------
# Graficos service (Task 5.3)
# ---------------------------------------------------------------------------

async def calcular_graficos(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    usuario: Any,
) -> GraficosResponse:
    """Return chart series for the dashboard."""
    ahora = datetime.now(timezone.utc)

    # --- ventas_diarias (last 7 days) ---
    result = await db.execute(
        select(
            func.date(Venta.fecha).label("dia"),
            func.sum(Venta.total).label("total"),
        )
        .where(
            Venta.empresa_id == empresa_id,
            Venta.estado == "cobrada",
            Venta.fecha >= text("NOW() - INTERVAL '7 days'"),
            Venta.fecha <= ahora,
        )
        .group_by(func.date(Venta.fecha))
        .order_by(func.date(Venta.fecha))
    )
    ventas_diarias = [
        VentaDiariaItem(
            fecha=str(row.dia),
            total=Decimal(str(row.total)).quantize(Decimal("0.01")),
        )
        for row in result.all()
    ]

    # --- ventas_mensuales (last 12 months) ---
    periodo_col = func.to_char(Venta.fecha, "YYYY-MM").label("periodo")
    result = await db.execute(
        select(
            periodo_col,
            func.sum(Venta.total).label("total"),
        )
        .where(
            Venta.empresa_id == empresa_id,
            Venta.estado == "cobrada",
            Venta.fecha >= text("NOW() - INTERVAL '12 months'"),
            Venta.fecha <= ahora,
        )
        .group_by(text("periodo"))
        .order_by(text("periodo"))
    )
    ventas_mensuales = [
        VentaMensualItem(
            periodo=row.periodo,
            total=Decimal(str(row.total)).quantize(Decimal("0.01")),
        )
        for row in result.all()
    ]

    # --- distribucion_medio_pago (current month) ---
    inicio_mes, _ = calcular_rango_mes(ahora)
    result = await db.execute(
        select(
            PagoVenta.medio_pago,
            func.sum(PagoVenta.importe).label("total"),
        )
        .join(Venta, PagoVenta.venta_id == Venta.id)
        .where(
            Venta.empresa_id == empresa_id,
            Venta.estado == "cobrada",
            Venta.fecha >= inicio_mes,
            Venta.fecha <= ahora,
        )
        .group_by(PagoVenta.medio_pago)
        .order_by(PagoVenta.medio_pago)
    )
    distribucion_medio_pago = [
        MedioPagoItem(
            medio_pago=row.medio_pago,
            total=Decimal(str(row.total)).quantize(Decimal("0.01")),
        )
        for row in result.all()
    ]

    # --- evolucion_ganancias (monthly, last 12 months) ---
    # Depends on snapshot prereq — empty list + flag=False when unavailable
    evolucion_ganancias: list[EvolucionGananciaItem] = []
    ganancia_disponible = False

    if tiene_permiso_reportes(usuario):
        # Check snapshot availability (sample from last 12 months)
        sample_result = await db.execute(
            select(DetalleVenta.costo_unitario)
            .join(Venta, DetalleVenta.venta_id == Venta.id)
            .where(
                Venta.empresa_id == empresa_id,
                Venta.estado == "cobrada",
                Venta.fecha >= text("NOW() - INTERVAL '12 months'"),
            )
            .limit(50)
        )
        sample_costos = sample_result.scalars().all()
        sample_lineas = [{"costo_unitario": c} for c in sample_costos]
        ganancia_disponible = verificar_snapshot_disponible(sample_lineas)

        if ganancia_disponible:
            evo_periodo_col = func.to_char(Venta.fecha, "YYYY-MM").label("periodo")
            result = await db.execute(
                select(
                    evo_periodo_col,
                    (
                        func.sum(DetalleVenta.importe)
                        - func.sum(
                            DetalleVenta.cantidad_kilos * DetalleVenta.costo_unitario
                        )
                    ).label("ganancia"),
                )
                .join(Venta, DetalleVenta.venta_id == Venta.id)
                .where(
                    Venta.empresa_id == empresa_id,
                    Venta.estado == "cobrada",
                    Venta.fecha >= text("NOW() - INTERVAL '12 months'"),
                    Venta.fecha <= ahora,
                    DetalleVenta.costo_unitario.isnot(None),
                )
                .group_by(text("periodo"))
                .order_by(text("periodo"))
            )
            evolucion_ganancias = [
                EvolucionGananciaItem(
                    periodo=row.periodo,
                    ganancia_bruta=(
                        Decimal(str(row.ganancia)).quantize(Decimal("0.01"))
                        if row.ganancia is not None
                        else None
                    ),
                )
                for row in result.all()
            ]

    return GraficosResponse(
        ventas_diarias=ventas_diarias,
        ventas_mensuales=ventas_mensuales,
        distribucion_medio_pago=distribucion_medio_pago,
        evolucion_ganancias=evolucion_ganancias,
        ganancia_disponible=ganancia_disponible,
    )
