"""Cuenta corriente router (C-14).

Routes:
  POST /{cliente_id}/pagos              — register a payment (cuenta-corriente:update)
  GET  /{cliente_id}                    — movement history + balance (cuenta-corriente:read)
  GET  /{cliente_id}/estado-cuenta      — downloadable account statement (cuenta-corriente:read)

RBAC:
  cuenta-corriente:update → admin, encargado, cajero (PO Decision C-14)
  cuenta-corriente:read   → admin, encargado, cajero

Tenant isolation: empresa_id always sourced from JWT (current_user.empresa_id).
A foreign-tenant cliente_id returns 404 — existence is never leaked.
"""
from __future__ import annotations

import io
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.rbac import require_role
from src.config.database import get_db
from src.modules.auth.dependencies import get_current_user
from src.modules.auth.models import Usuario
from src.modules.cuenta_corriente import service
from src.modules.cuenta_corriente.schemas import (
    HistorialCCResponse,
    PagoCreate,
    PagoResponse,
)

router = APIRouter()

# Content-type map mirrors reporte/router.py (_CONTENT_TYPE_MAP)
_CONTENT_TYPE_MAP: dict[str, str] = {
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "csv": "text/csv; charset=utf-8",
    "pdf": "application/pdf",
}


# ---------------------------------------------------------------------------
# POST /{cliente_id}/pagos — register payment
# ---------------------------------------------------------------------------

@router.post(
    "/{cliente_id}/pagos",
    response_model=PagoResponse,
    dependencies=[Depends(require_role("cuenta-corriente:update"))],
)
async def registrar_pago(
    cliente_id: uuid.UUID,
    data: PagoCreate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PagoResponse:
    """Register a partial or total payment against a customer's current account.

    Returns the created movement and the new saldo_actual.
    Overpayment (importe > saldo_actual) → HTTP 409.
    Zero or negative importe → HTTP 422 (Pydantic validation).
    Foreign-tenant cliente_id → HTTP 404.
    """
    return await service.registrar_pago(
        db=db,
        empresa_id=current_user.empresa_id,
        cliente_id=cliente_id,
        data=data,
    )


# ---------------------------------------------------------------------------
# GET /{cliente_id} — movement history + balance
# ---------------------------------------------------------------------------

@router.get(
    "/{cliente_id}",
    response_model=HistorialCCResponse,
    dependencies=[Depends(require_role("cuenta-corriente:read"))],
)
async def obtener_historial(
    cliente_id: uuid.UUID,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HistorialCCResponse:
    """Return paginated current-account movements for a customer.

    Movements are ordered by fecha ASC. The response includes the standard
    items/total/skip/limit envelope plus the current saldo_actual.
    Foreign-tenant cliente_id → HTTP 404.
    """
    return await service.obtener_historial(
        db=db,
        empresa_id=current_user.empresa_id,
        cliente_id=cliente_id,
        skip=skip,
        limit=limit,
    )


# ---------------------------------------------------------------------------
# GET /{cliente_id}/estado-cuenta — downloadable account statement
# ---------------------------------------------------------------------------

@router.get(
    "/{cliente_id}/estado-cuenta",
    dependencies=[Depends(require_role("cuenta-corriente:read"))],
)
async def exportar_estado_cuenta(
    cliente_id: uuid.UUID,
    formato: Literal["xlsx", "csv", "pdf"] = Query(default="pdf"),
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Download the account statement as xlsx, csv, or pdf (default pdf).

    Reuses the C-17/C-18 export approach: same content-type map, StreamingResponse.
    Foreign-tenant cliente_id → HTTP 404.
    Unsupported formato → HTTP 422 (Literal validation).
    """
    estado = await service.obtener_estado_cuenta(
        db=db,
        empresa_id=current_user.empresa_id,
        cliente_id=cliente_id,
    )

    if formato == "xlsx":
        file_bytes = service.generar_xlsx(estado)
        filename = f"estado-cuenta-{cliente_id}.xlsx"
    elif formato == "csv":
        file_bytes = service.generar_csv(estado)
        filename = f"estado-cuenta-{cliente_id}.csv"
    else:  # pdf (default)
        file_bytes = service.generar_pdf(estado)
        filename = f"estado-cuenta-{cliente_id}.pdf"

    return StreamingResponse(
        content=io.BytesIO(file_bytes),
        media_type=_CONTENT_TYPE_MAP[formato],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
