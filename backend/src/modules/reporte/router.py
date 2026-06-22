"""Reporte router — sales report endpoints.

Two routes:
  GET /reportes/ventas                    — paginated JSON report
  GET /reportes/ventas/exportar?formato=  — binary file download (xlsx / csv / pdf)

Both routes are read-only and require role administrador or encargado (reportes:read).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.rbac import require_role
from src.config.database import get_db
from src.modules.auth.dependencies import get_current_user
from src.modules.auth.models import Usuario
from src.modules.empresa.models import Empresa
from src.modules.reporte import service
from src.modules.reporte.schemas import ExportFormato, ReporteVentasResponse

router = APIRouter()


# ---------------------------------------------------------------------------
# Helper: resolve empresa name for PDF header
# ---------------------------------------------------------------------------

async def _get_empresa_nombre(db: AsyncSession, empresa_id: uuid.UUID) -> str:
    from sqlalchemy import select
    result = await db.execute(select(Empresa).where(Empresa.id == empresa_id))
    empresa = result.scalar_one_or_none()
    return empresa.nombre_comercial if empresa else "Empresa"


# ---------------------------------------------------------------------------
# GET /reportes/ventas — paginated JSON list
# ---------------------------------------------------------------------------

@router.get(
    "/ventas",
    response_model=ReporteVentasResponse,
    dependencies=[Depends(require_role("reportes:read"))],
)
async def listar_reporte_ventas(
    request: Request,
    fecha_desde: Optional[datetime] = Query(default=None),
    fecha_hasta: Optional[datetime] = Query(default=None),
    cliente_id: Optional[uuid.UUID] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReporteVentasResponse:
    """Paginated sales report for the authenticated user's empresa.

    Filters: date range (fecha_desde/fecha_hasta), cliente_id.
    Only cobrada sales are returned. Multi-tenant isolation is enforced.
    """
    empresa_id = current_user.empresa_id
    rows, total = await service.listar_ventas_reporte(
        db=db,
        empresa_id=empresa_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        cliente_id=cliente_id,
        skip=skip,
        limit=limit,
    )
    return ReporteVentasResponse(rows=rows, total=total, skip=skip, limit=limit)


# ---------------------------------------------------------------------------
# GET /reportes/ventas/exportar — binary file download
# ---------------------------------------------------------------------------

_CONTENT_TYPE_MAP: dict[str, str] = {
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "csv": "text/csv; charset=utf-8",
    "pdf": "application/pdf",
}

# ---------------------------------------------------------------------------
# Helper: build download filename with date range
#
# Rules (agreed with spec — see C-17 spec.md):
#   both dates present  → ventas-<desde_date>-<hasta_date>.<fmt>
#   both dates absent   → ventas.<fmt>
#   only desde present  → ventas-<desde_date>-all.<fmt>
#   only hasta present  → ventas-all-<hasta_date>.<fmt>
# Dates are formatted as YYYY-MM-DD (date portion of the ISO-8601 datetime).
# ---------------------------------------------------------------------------

def _build_filename(
    formato: str,
    fecha_desde: Optional[datetime],
    fecha_hasta: Optional[datetime],
) -> str:
    """Return the download filename embedding the applied date range."""
    if fecha_desde is None and fecha_hasta is None:
        return f"ventas.{formato}"

    desde_str = fecha_desde.strftime("%Y-%m-%d") if fecha_desde is not None else "all"
    hasta_str = fecha_hasta.strftime("%Y-%m-%d") if fecha_hasta is not None else "all"
    return f"ventas-{desde_str}-{hasta_str}.{formato}"


@router.get(
    "/ventas/exportar",
    dependencies=[Depends(require_role("reportes:read"))],
)
async def exportar_reporte_ventas(
    request: Request,
    formato: ExportFormato = Query(...),
    fecha_desde: Optional[datetime] = Query(default=None),
    fecha_hasta: Optional[datetime] = Query(default=None),
    cliente_id: Optional[uuid.UUID] = Query(default=None),
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Download the sales report as xlsx, csv, or pdf.

    The same filter params as the list endpoint apply. No pagination limit.
    """
    empresa_id = current_user.empresa_id

    # Fetch all matching rows (no pagination for exports)
    rows, _ = await service.listar_ventas_reporte(
        db=db,
        empresa_id=empresa_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        cliente_id=cliente_id,
        skip=0,
        limit=100_000,  # effectively no cap — bounded by filters
    )

    filename = _build_filename(str(formato), fecha_desde, fecha_hasta)

    if formato == "xlsx":
        file_bytes = service.generar_xlsx(rows)
    elif formato == "csv":
        file_bytes = service.generar_csv(rows)
    else:  # pdf
        empresa_nombre = await _get_empresa_nombre(db, empresa_id)
        file_bytes = service.generar_pdf(rows, empresa_nombre, fecha_desde, fecha_hasta)

    import io

    return StreamingResponse(
        content=io.BytesIO(file_bytes),
        media_type=_CONTENT_TYPE_MAP[formato],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
