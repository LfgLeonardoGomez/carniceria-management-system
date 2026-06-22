"""Reporte service — read-only aggregation over ventas data.

No new DB tables. No state mutations. Multi-tenant isolation via empresa_id.
All money is Decimal. Stock is Decimal with 3 decimal places.
"""
from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.cliente.models import Cliente
from src.modules.producto.models import Producto
from src.modules.reporte.schemas import VentaReporteRow
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
