"""Dashboard router — read-only aggregation endpoints.

All endpoints require authentication (get_current_user injected via main.py's
auth dependency). No endpoint mutates state.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.modules.auth.dependencies import get_current_user
from src.modules.auth.models import Usuario
from src.modules.dashboard import service
from src.modules.dashboard.schemas import (
    GraficosResponse,
    IndicadoresResponse,
    RankingsResponse,
)

router = APIRouter()


@router.get("/indicadores", response_model=IndicadoresResponse)
async def get_indicadores(
    request: Request,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> IndicadoresResponse:
    """Return operational and financial KPIs for the authenticated user's empresa."""
    if current_user.empresa_id is None:
        raise HTTPException(
            status_code=403,
            detail="El dashboard requiere una empresa asociada. Use /admin/soporte para impersonar un tenant.",
        )
    empresa_id = current_user.empresa_id
    return await service.calcular_indicadores(
        db=db,
        empresa_id=empresa_id,
        usuario=current_user,
    )


@router.get("/rankings", response_model=RankingsResponse)
async def get_rankings(
    request: Request,
    top: int = Query(default=10, ge=1, le=100),
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RankingsResponse:
    """Return the top-N most-sold products by kilos for the current month."""
    if current_user.empresa_id is None:
        raise HTTPException(
            status_code=403,
            detail="El dashboard requiere una empresa asociada. Use /admin/soporte para impersonar un tenant.",
        )
    empresa_id = current_user.empresa_id
    return await service.calcular_rankings(
        db=db,
        empresa_id=empresa_id,
        top=top,
    )


@router.get("/graficos", response_model=GraficosResponse)
async def get_graficos(
    request: Request,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GraficosResponse:
    """Return chart series: daily/monthly sales, payment distribution, profit evolution."""
    if current_user.empresa_id is None:
        raise HTTPException(
            status_code=403,
            detail="El dashboard requiere una empresa asociada. Use /admin/soporte para impersonar un tenant.",
        )
    empresa_id = current_user.empresa_id
    return await service.calcular_graficos(
        db=db,
        empresa_id=empresa_id,
        usuario=current_user,
    )
