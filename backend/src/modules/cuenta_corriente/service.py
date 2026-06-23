"""Service for the cuenta_corriente module (C-14).

Implements:
  - registrar_pago: ACID payment registration (SELECT FOR UPDATE, insert, update)
  - obtener_historial: paginated movement history + balance
  - obtener_estado_cuenta: full history for export
  - generar_xlsx, generar_csv, generar_pdf: export generators (reuse C-17/C-18 approach)

Governance: HIGH (money). Atomicity, tenant isolation, and Decimal precision are
first-class requirements. Every query is tenant-scoped by empresa_id.

Quantization convention (matches venta/service.py):
  .quantize(Decimal("0.01"))
"""
from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.exceptions import ConflictException, NotFoundException
from src.modules.cliente.models import Cliente
from src.modules.cuenta_corriente.models import CuentaCorriente
from src.modules.cuenta_corriente.schemas import (
    EstadoCuentaResponse,
    HistorialCCResponse,
    MovimientoCCResponse,
    PagoCreate,
    PagoResponse,
)


# ---------------------------------------------------------------------------
# Register payment (ACID, tenant-scoped)
# ---------------------------------------------------------------------------

async def registrar_pago(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    cliente_id: uuid.UUID,
    data: PagoCreate,
) -> PagoResponse:
    """Register a partial or total payment against a customer's current account.

    Guarantees:
    - SELECT cliente FOR UPDATE: serialises concurrent payments for same customer.
    - Overpayment (importe > saldo_actual) → ConflictException (HTTP 409).
    - Foreign-tenant cliente_id → NotFoundException (HTTP 404).
    - Inserts CuentaCorriente movement (tipo="pago") + updates cliente.saldo_actual
      in a single ACID transaction.

    Quantization: .quantize(Decimal("0.01")) — matches venta/service.py convention.
    """
    # Lock the customer row to prevent concurrent payment races
    stmt = (
        select(Cliente)
        .where(
            Cliente.id == cliente_id,
            Cliente.empresa_id == empresa_id,
        )
        .with_for_update()
    )
    result = await db.execute(stmt)
    cliente = result.scalar_one_or_none()

    if cliente is None:
        raise NotFoundException("Cliente no encontrado en este tenant")

    saldo_actual = Decimal(str(cliente.saldo_actual)).quantize(Decimal("0.01"))
    importe = data.importe.quantize(Decimal("0.01"))

    # PO Decision: overpayment rejected with HTTP 409
    if importe > saldo_actual:
        raise ConflictException(
            f"El importe ({importe}) supera el saldo actual ({saldo_actual}). "
            "No se permiten pagos en exceso."
        )

    nuevo_saldo = (saldo_actual - importe).quantize(Decimal("0.01"))

    # Insert movement
    movimiento = CuentaCorriente(
        empresa_id=empresa_id,
        cliente_id=cliente_id,
        tipo="pago",
        importe=importe,
        saldo_resultante=nuevo_saldo,
        venta_id=None,
        fecha=datetime.now(timezone.utc),
    )
    db.add(movimiento)

    # Update running balance
    cliente.saldo_actual = nuevo_saldo

    await db.commit()
    await db.refresh(movimiento)
    await db.refresh(cliente)

    return PagoResponse(
        movimiento=MovimientoCCResponse(
            id=movimiento.id,
            tipo=movimiento.tipo,
            importe=Decimal(str(movimiento.importe)).quantize(Decimal("0.01")),
            saldo_resultante=Decimal(str(movimiento.saldo_resultante)).quantize(Decimal("0.01")),
            venta_id=movimiento.venta_id,
            fecha=movimiento.fecha,
        ),
        saldo_actual=Decimal(str(cliente.saldo_actual)).quantize(Decimal("0.01")),
    )


# ---------------------------------------------------------------------------
# History + balance (paginated)
# ---------------------------------------------------------------------------

async def obtener_historial(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    cliente_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
) -> HistorialCCResponse:
    """Return paginated current-account movements for a customer.

    Ordered by fecha ASC, then created_at ASC (deterministic tiebreaker).
    Returns the standard items/total/skip/limit envelope plus current saldo_actual.
    Foreign-tenant cliente_id → NotFoundException (HTTP 404).
    """
    # Verify customer belongs to tenant
    cliente_stmt = select(Cliente).where(
        Cliente.id == cliente_id,
        Cliente.empresa_id == empresa_id,
    )
    cliente_result = await db.execute(cliente_stmt)
    cliente = cliente_result.scalar_one_or_none()
    if cliente is None:
        raise NotFoundException("Cliente no encontrado en este tenant")

    # Count total movements
    count_stmt = select(func.count(CuentaCorriente.id)).where(
        CuentaCorriente.empresa_id == empresa_id,
        CuentaCorriente.cliente_id == cliente_id,
    )
    total = (await db.execute(count_stmt)).scalar_one()

    # Fetch paginated movements
    items_stmt = (
        select(CuentaCorriente)
        .where(
            CuentaCorriente.empresa_id == empresa_id,
            CuentaCorriente.cliente_id == cliente_id,
        )
        .order_by(CuentaCorriente.fecha.asc(), CuentaCorriente.created_at.asc())
        .offset(skip)
        .limit(limit)
    )
    items_result = await db.execute(items_stmt)
    movimientos = list(items_result.scalars().all())

    items = [
        MovimientoCCResponse(
            id=m.id,
            tipo=m.tipo,
            importe=Decimal(str(m.importe)).quantize(Decimal("0.01")),
            saldo_resultante=Decimal(str(m.saldo_resultante)).quantize(Decimal("0.01")),
            venta_id=m.venta_id,
            fecha=m.fecha,
        )
        for m in movimientos
    ]

    return HistorialCCResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
        saldo_actual=Decimal(str(cliente.saldo_actual)).quantize(Decimal("0.01")),
    )


# ---------------------------------------------------------------------------
# Estado cuenta (full history for export)
# ---------------------------------------------------------------------------

async def obtener_estado_cuenta(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    cliente_id: uuid.UUID,
) -> EstadoCuentaResponse:
    """Return full (unpaginated) account statement with customer info.

    Used by the export endpoint. Foreign-tenant → NotFoundException.
    """
    # Verify customer belongs to tenant
    cliente_stmt = select(Cliente).where(
        Cliente.id == cliente_id,
        Cliente.empresa_id == empresa_id,
    )
    cliente_result = await db.execute(cliente_stmt)
    cliente = cliente_result.scalar_one_or_none()
    if cliente is None:
        raise NotFoundException("Cliente no encontrado en este tenant")

    # Fetch all movements ordered by date
    movs_stmt = (
        select(CuentaCorriente)
        .where(
            CuentaCorriente.empresa_id == empresa_id,
            CuentaCorriente.cliente_id == cliente_id,
        )
        .order_by(CuentaCorriente.fecha.asc(), CuentaCorriente.created_at.asc())
    )
    movs_result = await db.execute(movs_stmt)
    movimientos = list(movs_result.scalars().all())

    # Build display name
    apellido = f" {cliente.apellido}" if cliente.apellido else ""
    if cliente.razon_social:
        nombre_display = cliente.razon_social
    else:
        nombre_display = f"{cliente.nombre}{apellido}"

    items = [
        MovimientoCCResponse(
            id=m.id,
            tipo=m.tipo,
            importe=Decimal(str(m.importe)).quantize(Decimal("0.01")),
            saldo_resultante=Decimal(str(m.saldo_resultante)).quantize(Decimal("0.01")),
            venta_id=m.venta_id,
            fecha=m.fecha,
        )
        for m in movimientos
    ]

    return EstadoCuentaResponse(
        cliente_id=cliente_id,
        cliente_nombre=nombre_display,
        saldo_actual=Decimal(str(cliente.saldo_actual)).quantize(Decimal("0.01")),
        movimientos=items,
    )


# ---------------------------------------------------------------------------
# Export generators (mirroring reporte/service.py — C-17/C-18 approach)
# ---------------------------------------------------------------------------

def generar_xlsx(estado: EstadoCuentaResponse) -> bytes:
    """Generate an xlsx workbook for the account statement.

    Sheet: "Estado de Cuenta"
    Header: fecha, tipo, importe, saldo_resultante, venta_id
    Footer: saldo actual row
    """
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Estado de Cuenta"

    # Customer header rows
    ws.append(["Cliente:", estado.cliente_nombre])
    ws.append(["Saldo actual:", estado.saldo_actual])
    ws.append([])  # blank row

    # Movement headers
    ws.append(["fecha", "tipo", "importe", "saldo_resultante", "venta_id"])

    for mov in estado.movimientos:
        ws.append([
            mov.fecha.isoformat(),
            mov.tipo,
            mov.importe,
            mov.saldo_resultante,
            str(mov.venta_id) if mov.venta_id else "",
        ])

    # Footer totals row
    ws.append(["SALDO FINAL", "", "", estado.saldo_actual, ""])

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def generar_csv(estado: EstadoCuentaResponse) -> bytes:
    """Generate a UTF-8 BOM CSV for the account statement."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, quoting=csv.QUOTE_MINIMAL)

    # Header comment rows
    writer.writerow(["cliente", estado.cliente_nombre])
    writer.writerow(["saldo_actual", str(estado.saldo_actual)])
    writer.writerow([])  # blank

    # Column headers
    writer.writerow(["fecha", "tipo", "importe", "saldo_resultante", "venta_id"])

    for mov in estado.movimientos:
        writer.writerow([
            mov.fecha.isoformat(),
            mov.tipo,
            str(mov.importe),
            str(mov.saldo_resultante),
            str(mov.venta_id) if mov.venta_id else "",
        ])

    return buffer.getvalue().encode("utf-8-sig")


def generar_pdf(estado: EstadoCuentaResponse) -> bytes:
    """Generate a PDF account statement using reportlab.

    Includes:
    - Customer name and current balance in the header
    - Table: fecha | tipo | importe | saldo_resultante
    - Footer saldo actual
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
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
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    story = []

    # --- Header ---
    story.append(Paragraph(f"Estado de Cuenta — {estado.cliente_nombre}", styles["Title"]))
    story.append(Paragraph(f"Saldo actual: {estado.saldo_actual}", styles["Normal"]))
    story.append(Spacer(1, 0.4 * cm))

    # --- Table ---
    col_headers = ["Fecha", "Tipo", "Importe", "Saldo resultante"]
    table_data: list[list[str]] = [col_headers]

    for mov in estado.movimientos:
        table_data.append([
            mov.fecha.strftime("%Y-%m-%d %H:%M"),
            mov.tipo,
            str(mov.importe),
            str(mov.saldo_resultante),
        ])

    # Footer saldo row
    table_data.append(["SALDO FINAL", "", "", str(estado.saldo_actual)])

    col_widths = [5 * cm, 3 * cm, 4 * cm, 4 * cm]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#F2F3F4")]),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#2C3E50")),
                ("TEXTCOLOR", (0, -1), (-1, -1), colors.white),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#BDC3C7")),
                ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(table)
    doc.build(story)
    return buffer.getvalue()
