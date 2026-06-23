"""Rentabilidad router — read-only profitability endpoints (C-19).

Routes:
  GET /rentabilidad/productos — product margin ranking (CA-1/CA-2, US-019)
  GET /rentabilidad/cortes   — cut margin per desposte cut (CA-3, US-019)

All routes are read-only and require reportes:read permission.
CA-4 (general profitability) is served by GET /reportes/financieros (C-18).
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query

from src.common.rbac import require_role
from src.config.database import get_db
from src.modules.auth.dependencies import get_current_user
from src.modules.auth.models import Usuario
from src.modules.rentabilidad import service
from src.modules.rentabilidad.schemas import (
    Orden,
    RentabilidadCortesResponse,
    RentabilidadProductosResponse,
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


# ---------------------------------------------------------------------------
# GET /rentabilidad/productos — product margin ranking (Tasks 4.1, 5.1)
# ---------------------------------------------------------------------------

@router.get(
    "/productos",
    response_model=RentabilidadProductosResponse,
    dependencies=[Depends(require_role("reportes:read"))],
)
async def listar_rentabilidad_productos(
    fecha_desde: Optional[datetime] = Query(default=None),
    fecha_hasta: Optional[datetime] = Query(default=None),
    orden: Orden = Query(default="mayor"),
    top: Optional[int] = Query(default=None, ge=1),
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RentabilidadProductosResponse:
    """Product profitability ranking ordered by real transactional margin.

    CA-1: most profitable (orden=mayor, default).
    CA-2: least profitable (orden=menor).
    top=N limits the number of results (applied after ordering).
    Products with null margin (missing cost snapshot) are always ordered last.
    Empresa_id is sourced from the JWT — no cross-tenant data is returned.
    """
    return await service.ranking_productos(
        db=db,
        empresa_id=current_user.empresa_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        orden=orden,
        top=top,
    )


# ---------------------------------------------------------------------------
# GET /rentabilidad/cortes — cut margin view (Tasks 4.2, 5.2)
# ---------------------------------------------------------------------------

@router.get(
    "/cortes",
    response_model=RentabilidadCortesResponse,
    dependencies=[Depends(require_role("reportes:read"))],
)
async def listar_rentabilidad_cortes(
    fecha_desde: Optional[datetime] = Query(default=None),
    fecha_hasta: Optional[datetime] = Query(default=None),
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RentabilidadCortesResponse:
    """Cut profitability view crossing CorteDesposte cost vs sale price.

    CA-3: per-cut margin for desposte cuts linked to a product.
    Cuts with producto_id IS NULL are excluded (no sale price to cross).
    Empresa_id is sourced from the JWT — no cross-tenant data is returned.
    """
    return await service.margen_cortes(
        db=db,
        empresa_id=current_user.empresa_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
