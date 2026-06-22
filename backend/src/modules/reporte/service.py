"""Reporte service — read-only aggregation over ventas data.

No new DB tables. No state mutations. Multi-tenant isolation via empresa_id.
All money is Decimal. Stock is Decimal with 3 decimal places.
"""
from __future__ import annotations

import csv
import io
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional, Tuple, Union

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.cliente.models import Cliente
from src.modules.producto.models import Producto
from src.modules.reporte.schemas import (
    FinancieroPeriodoRow,
    GroupBy,
    ReporteFinancieroResponse,
    VentaReporteRow,
)
from src.modules.venta.models import DetalleVenta, PagoVenta, Venta
from src.modules.venta.service import calcular_ganancia


# ---------------------------------------------------------------------------
# Client name resolution (Decision 5)
# ---------------------------------------------------------------------------

def _resolver_nombre_cliente(cliente: Optional[Cliente]) -> str:
    """Derive the display name for a sale's client.

    Priority:
      1. razon_social (B2B)
      2. nombre + apellido
      3. "Público general" (no client linked)
    """
    if cliente is None:
        return "Público general"
    if cliente.razon_social:
        return cliente.razon_social
    apellido = f" {cliente.apellido}" if cliente.apellido else ""
    return f"{cliente.nombre}{apellido}"


# ---------------------------------------------------------------------------
# Main report query
# ---------------------------------------------------------------------------

async def listar_ventas_reporte(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
    cliente_id: Optional[uuid.UUID] = None,
    skip: int = 0,
    limit: int = 50,
) -> Tuple[List[VentaReporteRow], int]:
    """Return paginated sales report rows for a given empresa.

    Filters:
    - Only estado='cobrada' sales (spec requirement)
    - empresa_id from JWT (multi-tenant isolation — RN-SEG-01/02)
    - Optional date range and cliente_id

    Cross-tenant cliente_id filter: the query always scopes by empresa_id first,
    so a cliente_id from another empresa yields 0 results (not 403) per spec.

    Returns (rows, total_count).
    """
    # Base filters — empresa_id + estado=cobrada are ALWAYS applied
    where = [
        Venta.empresa_id == empresa_id,
        Venta.estado == "cobrada",
    ]
    if fecha_desde is not None:
        where.append(Venta.fecha >= fecha_desde)
    if fecha_hasta is not None:
        where.append(Venta.fecha <= fecha_hasta)
    if cliente_id is not None:
        where.append(Venta.cliente_id == cliente_id)

    # Count total (unpaged)
    count_q = select(func.count(Venta.id)).where(*where)
    total = (await db.execute(count_q)).scalar_one()

    if total == 0:
        return [], 0

    # Fetch ventas with their relations in one query (avoids N+1)
    ventas_q = (
        select(Venta)
        .options(
            selectinload(Venta.detalles).selectinload(DetalleVenta.venta),
            selectinload(Venta.pagos),
        )
        .where(*where)
        .order_by(Venta.fecha.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(ventas_q)
    ventas: list[Venta] = list(result.scalars().all())

    if not ventas:
        return [], total

    # Collect unique cliente_ids (excluding None) to batch-load clients
    cliente_ids = {v.cliente_id for v in ventas if v.cliente_id is not None}
    clientes_by_id: dict[uuid.UUID, Cliente] = {}
    if cliente_ids:
        clientes_q = select(Cliente).where(Cliente.id.in_(cliente_ids))
        clientes_result = await db.execute(clientes_q)
        for c in clientes_result.scalars().all():
            clientes_by_id[c.id] = c

    # Collect unique producto_ids to batch-load product names
    all_producto_ids: set[uuid.UUID] = set()
    for v in ventas:
        for d in v.detalles:
            all_producto_ids.add(d.producto_id)

    productos_by_id: dict[uuid.UUID, Producto] = {}
    if all_producto_ids:
        productos_q = select(Producto).where(Producto.id.in_(all_producto_ids))
        productos_result = await db.execute(productos_q)
        for p in productos_result.scalars().all():
            productos_by_id[p.id] = p

    # Build rows
    rows: list[VentaReporteRow] = []
    for v in ventas:
        cliente = clientes_by_id.get(v.cliente_id) if v.cliente_id else None
        cliente_nombre = _resolver_nombre_cliente(cliente)

        # Products column: comma-separated, sorted for determinism
        product_names = sorted(
            {
                productos_by_id[d.producto_id].nombre
                for d in v.detalles
                if d.producto_id in productos_by_id
            }
        )
        productos_str = ", ".join(product_names)

        # Kilos: sum of detalle.cantidad_kilos
        total_kilos = sum(
            (Decimal(str(d.cantidad_kilos)) for d in v.detalles),
            Decimal("0.000"),
        ).quantize(Decimal("0.001"))

        # Payment methods column
        medios = sorted({p.medio_pago for p in v.pagos})
        medios_pago_str = ", ".join(medios)

        # Profit (Decision 4 — computed in Python via existing helper)
        ganancia = calcular_ganancia(list(v.detalles))

        rows.append(
            VentaReporteRow(
                venta_id=v.id,
                fecha=v.fecha,
                cliente_nombre=cliente_nombre,
                productos=productos_str,
                total_kilos=total_kilos,
                subtotal=Decimal(str(v.subtotal)).quantize(Decimal("0.01")),
                total=Decimal(str(v.total)).quantize(Decimal("0.01")),
                medios_pago=medios_pago_str,
                ganancia_estimada=ganancia,
            )
        )

    return rows, total


# ---------------------------------------------------------------------------
# Excel export
# ---------------------------------------------------------------------------

def generar_xlsx(rows: List[VentaReporteRow]) -> bytes:
    """Generate an xlsx workbook from report rows.

    Sheet name: "Ventas"
    Header: fecha, cliente, productos, kilos_vendidos, subtotal, total,
            medio_pago, ganancia_estimada
    Monetary columns: float, 2 d.p.
    Kilos: float, 3 d.p.
    Null ganancia: blank cell (not "None")
    """
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Ventas"

    headers = [
        "fecha",
        "cliente",
        "productos",
        "kilos_vendidos",
        "subtotal",
        "total",
        "medio_pago",
        "ganancia_estimada",
    ]
    ws.append(headers)

    for row in rows:
        ganancia_val: float | None = (
            float(row.ganancia_estimada) if row.ganancia_estimada is not None else None
        )
        ws.append(
            [
                row.fecha.isoformat(),
                row.cliente_nombre,
                row.productos,
                float(row.total_kilos),
                float(row.subtotal),
                float(row.total),
                row.medios_pago,
                ganancia_val,
            ]
        )

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------

def generar_csv(rows: List[VentaReporteRow]) -> bytes:
    """Generate a UTF-8 BOM CSV from report rows.

    BOM included for Excel compatibility.
    Column order: fecha, cliente, productos, kilos_vendidos, subtotal, total,
                  medio_pago, ganancia_estimada
    Null ganancia → empty string (two consecutive delimiters).
    Strings with commas are quoted by the csv module automatically.
    """
    buffer = io.StringIO()
    writer = csv.writer(buffer, quoting=csv.QUOTE_MINIMAL)

    writer.writerow(
        [
            "fecha",
            "cliente",
            "productos",
            "kilos_vendidos",
            "subtotal",
            "total",
            "medio_pago",
            "ganancia_estimada",
        ]
    )

    for row in rows:
        ganancia_str = (
            str(row.ganancia_estimada) if row.ganancia_estimada is not None else ""
        )
        writer.writerow(
            [
                row.fecha.isoformat(),
                row.cliente_nombre,
                row.productos,
                str(row.total_kilos),
                str(row.subtotal),
                str(row.total),
                row.medios_pago,
                ganancia_str,
            ]
        )

    # Encode with UTF-8 BOM (utf-8-sig) for Excel compatibility
    return buffer.getvalue().encode("utf-8-sig")


# ---------------------------------------------------------------------------
# PDF export
# ---------------------------------------------------------------------------

def generar_pdf(
    rows: List[VentaReporteRow],
    empresa_nombre: str,
    fecha_desde: Optional[datetime],
    fecha_hasta: Optional[datetime],
) -> bytes:
    """Generate a PDF report using reportlab.

    Includes:
    - Header: empresa name + applied date range
    - Data table with RN-REP-03 columns
    - Footer totals row: sum of total, sum of total_kilos
    Null ganancia → em-dash "—"
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=1 * cm,
        rightMargin=1 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    story = []

    # --- Header ---
    date_range_str = ""
    if fecha_desde and fecha_hasta:
        date_range_str = (
            f" | {fecha_desde.date().isoformat()} – {fecha_hasta.date().isoformat()}"
        )
    elif fecha_desde:
        date_range_str = f" | desde {fecha_desde.date().isoformat()}"
    elif fecha_hasta:
        date_range_str = f" | hasta {fecha_hasta.date().isoformat()}"

    story.append(Paragraph(f"Reporte de Ventas — {empresa_nombre}{date_range_str}", styles["Title"]))
    story.append(Spacer(1, 0.4 * cm))

    # --- Table data ---
    col_headers = [
        "Fecha",
        "Cliente",
        "Productos",
        "Kilos",
        "Subtotal",
        "Total",
        "Medio pago",
        "Ganancia est.",
    ]
    table_data: list[list[str]] = [col_headers]

    sum_total = Decimal("0.00")
    sum_kilos = Decimal("0.000")

    for row in rows:
        ganancia_str = (
            str(row.ganancia_estimada) if row.ganancia_estimada is not None else "—"
        )
        table_data.append(
            [
                row.fecha.strftime("%Y-%m-%d %H:%M"),
                row.cliente_nombre,
                row.productos,
                str(row.total_kilos),
                str(row.subtotal),
                str(row.total),
                row.medios_pago,
                ganancia_str,
            ]
        )
        sum_total += Decimal(str(row.total))
        sum_kilos += Decimal(str(row.total_kilos))

    # Footer totals row
    table_data.append(
        [
            "TOTAL",
            "",
            "",
            str(sum_kilos.quantize(Decimal("0.001"))),
            "",
            str(sum_total.quantize(Decimal("0.01"))),
            "",
            "",
        ]
    )

    col_widths = [3.5 * cm, 4 * cm, 6 * cm, 2 * cm, 2.5 * cm, 2.5 * cm, 3 * cm, 3 * cm]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("FONTSIZE", (0, 1), (-1, -1), 7),
                ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#F2F3F4")]),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#2C3E50")),
                ("TEXTCOLOR", (0, -1), (-1, -1), colors.white),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#BDC3C7")),
                ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("WORDWRAP", (0, 0), (-1, -1), True),
            ]
        )
    )
    story.append(table)
    doc.build(story)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# C-18 — Financial report helpers (Decision 2, 3, 4)
# NOTE: APPEND-ONLY. Do not modify C-17 symbols above.
# ---------------------------------------------------------------------------

def periodo_key(fecha: Union[datetime, date], group_by: GroupBy) -> str:
    """Compute a deterministic period bucket key for a date or datetime.

    Normalises both `datetime` (UTC) and `date` inputs to the same UTC calendar
    so that a venta (datetime) and a gasto (date) in the same period share the
    same key.

    group_by values:
      'dia'    → "YYYY-MM-DD"
      'semana' → ISO year-week "YYYY-Www"  (ISO 8601: week starts Monday)
      'mes'    → "YYYY-MM"
      'anio'   → "YYYY"
    """
    # Normalise to a date in UTC
    if isinstance(fecha, datetime):
        # If naive, treat as UTC (project rule: DB is UTC)
        if fecha.tzinfo is None:
            d = fecha.date()
        else:
            d = fecha.astimezone(timezone.utc).date()
    else:
        d = fecha  # already a date

    if group_by == "dia":
        return d.isoformat()  # "YYYY-MM-DD"

    if group_by == "semana":
        iso_year, iso_week, _ = d.isocalendar()
        return f"{iso_year}-W{iso_week:02d}"

    if group_by == "mes":
        return f"{d.year}-{d.month:02d}"

    # anio
    return str(d.year)


def _build_buckets_financieros(
    ventas: list,
    gastos: list,
    group_by: GroupBy,
) -> list[FinancieroPeriodoRow]:
    """Compute per-period financial indicators from in-memory lists.

    This pure function is separated from the DB query so it can be unit-tested
    without a database.

    Cost contract (mirrors calcular_ganancia):
      - costos for a bucket = Σ(cantidad_kilos × costo_unitario) across all
        DetalleVenta of cobrada ventas in that bucket.
      - If ANY line has costo_unitario IS NULL → costos, utilidad_bruta,
        utilidad_neta are all None for that bucket.
      - NULL is NEVER zero.

    Ordering: buckets are returned sorted chronologically by period key string
    (ISO format is lexicographically monotone for dia/mes/anio; Www with
    zero-padded week also sorts correctly).
    """
    # ---- Phase 1: aggregate ventas by period key ----
    # bucket_ventas: period_key → total ventas (Decimal)
    # bucket_costos: period_key → Optional[Decimal] (None = any null snapshot)
    bucket_ventas: dict[str, Decimal] = {}
    # None means "cost unavailable for this bucket"
    bucket_costos: dict[str, Optional[Decimal]] = {}

    for v in ventas:
        key = periodo_key(v.fecha, group_by)

        # Add venta total — net revenue basis: Venta.total already includes descuentos (intentional)
        bucket_ventas[key] = bucket_ventas.get(key, Decimal("0.00")) + Decimal(str(v.total))

        # Compute costos for this venta's detalles
        # If the bucket is already null, stay null
        if bucket_costos.get(key) is None and key in bucket_costos:
            # Already null — no point computing
            continue

        venta_costo: Optional[Decimal] = Decimal("0.00")
        for det in v.detalles:
            if det.costo_unitario is None:
                venta_costo = None
                break
            venta_costo = venta_costo + Decimal(str(det.cantidad_kilos)) * Decimal(str(det.costo_unitario))  # type: ignore[operator]

        if key not in bucket_costos:
            bucket_costos[key] = venta_costo
        elif bucket_costos[key] is not None and venta_costo is None:
            bucket_costos[key] = None
        elif bucket_costos[key] is not None and venta_costo is not None:
            bucket_costos[key] = bucket_costos[key] + venta_costo  # type: ignore[operator]
        # else: already None, leave as None

    # ---- Phase 2: aggregate gastos by period key ----
    bucket_gastos: dict[str, Decimal] = {}
    for g in gastos:
        key = periodo_key(g.fecha, group_by)
        bucket_gastos[key] = bucket_gastos.get(key, Decimal("0.00")) + Decimal(str(g.importe))

    # ---- Phase 3: merge all period keys ----
    all_periods: set[str] = set(bucket_ventas.keys()) | set(bucket_gastos.keys())

    rows: list[FinancieroPeriodoRow] = []
    for period in sorted(all_periods):
        v_total = bucket_ventas.get(period, Decimal("0.00"))
        g_total = bucket_gastos.get(period, Decimal("0.00"))
        costos = bucket_costos.get(period)

        # If no ventas in this period (only gastos), costos=0 and formulas work
        if period not in bucket_ventas:
            costos = Decimal("0.00")

        if costos is None:
            utilidad_bruta = None
            utilidad_neta = None
        else:
            utilidad_bruta = (v_total - costos).quantize(Decimal("0.01"))
            utilidad_neta = (utilidad_bruta - g_total).quantize(Decimal("0.01"))

        rows.append(
            FinancieroPeriodoRow(
                periodo=period,
                ventas=v_total.quantize(Decimal("0.01")),
                gastos=g_total.quantize(Decimal("0.01")),
                costos=costos.quantize(Decimal("0.01")) if costos is not None else None,
                utilidad_bruta=utilidad_bruta,
                utilidad_neta=utilidad_neta,
            )
        )

    return rows


def _to_utc_date(dt: Union[datetime, date]) -> date:
    """Normalise a datetime or date to a UTC calendar date.

    Mirrors the same normalisation used by periodo_key:
    - naive datetime → treat as UTC, extract date
    - aware datetime → convert to UTC, extract date
    - date → returned as-is
    """
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            return dt.date()
        return dt.astimezone(timezone.utc).date()
    return dt


async def reporte_financiero(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    group_by: GroupBy,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
) -> ReporteFinancieroResponse:
    """Aggregate financial indicators per period for a given empresa.

    Three tenant-scoped queries (Decision 4):
    1. Load cobrada Venta rows + their DetalleVenta (for ventas + costos).
    2. Load Gasto rows (for gastos).
    3. Bucket in Python via periodo_key; compute five indicators; merge.

    Multi-tenant isolation: empresa_id is applied first in every query.

    Date-range boundaries: both ventas (datetime column) and gastos (date column)
    are filtered by the same UTC calendar-day boundaries so that a venta and a
    gasto on the same UTC calendar day are always included or excluded together.
    A mid-day fecha_hasta is treated as the END of that calendar day for ventas.
    """
    from src.modules.gasto.models import Gasto

    # Derive UTC calendar-day bounds once; use for both streams.
    # This ensures symmetric inclusivity: a venta datetime and a gasto date on the
    # same UTC calendar day are treated identically regardless of the time component.
    cal_desde: Optional[date] = _to_utc_date(fecha_desde) if fecha_desde is not None else None
    cal_hasta: Optional[date] = _to_utc_date(fecha_hasta) if fecha_hasta is not None else None

    # ---- Query 1: cobrada ventas + detalles ----
    # Uses calendar-day lower bound (start of day) and inclusive upper bound (end of day)
    # so that any venta with a datetime on the boundary calendar day is included.
    where_v = [
        Venta.empresa_id == empresa_id,
        Venta.estado == "cobrada",
    ]
    if cal_desde is not None:
        # Lower bound: start of UTC calendar day (inclusive)
        where_v.append(Venta.fecha >= datetime(cal_desde.year, cal_desde.month, cal_desde.day, 0, 0, 0))
    if cal_hasta is not None:
        # Upper bound: end of UTC calendar day (inclusive) — captures all datetimes on that day.
        # Use timedelta to safely advance by one day (avoids month-boundary arithmetic errors).
        next_day = datetime(cal_hasta.year, cal_hasta.month, cal_hasta.day, 0, 0, 0) + timedelta(days=1)
        where_v.append(Venta.fecha < next_day)

    ventas_q = (
        select(Venta)
        .options(selectinload(Venta.detalles))
        .where(*where_v)
    )
    result_v = await db.execute(ventas_q)
    ventas: list[Venta] = list(result_v.scalars().all())

    # ---- Query 2: gastos ----
    # Uses the same UTC calendar-day bounds (gastos.fecha is a date column).
    where_g = [Gasto.empresa_id == empresa_id]
    if cal_desde is not None:
        where_g.append(Gasto.fecha >= cal_desde)
    if cal_hasta is not None:
        where_g.append(Gasto.fecha <= cal_hasta)

    gastos_q = select(Gasto).where(*where_g)
    result_g = await db.execute(gastos_q)
    gastos: list[Gasto] = list(result_g.scalars().all())

    # ---- Query 3: bucket + compute indicators ----
    rows = _build_buckets_financieros(ventas, gastos, group_by)

    return ReporteFinancieroResponse(group_by=group_by, rows=rows)
