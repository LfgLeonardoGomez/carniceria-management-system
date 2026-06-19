from typing import Optional

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.modules.auth.dependencies import require_auth
from src.modules.stock import schemas
from src.modules.stock import service
from src.common.rbac import require_role
from src.common.exceptions import ConflictException, BasileException

router = APIRouter()


# ---------------------------------------------------------------------------
# Stock endpoints
# ---------------------------------------------------------------------------
@router.get(
    "",
    response_model=schemas.PaginatedStockResponse,
    dependencies=[Depends(require_role("stock:read"))],
)
async def list_stock(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> schemas.PaginatedStockResponse:
    empresa_id = request.state.empresa_id
    items, total = await service.get_stock_por_producto(db, empresa_id, skip=skip, limit=limit)
    return schemas.PaginatedStockResponse(
        items=[schemas.StockItem.model_validate(item) for item in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/movimientos/{producto_id}",
    response_model=schemas.PaginatedKardexResponse,
    dependencies=[Depends(require_role("stock:read"))],
)
async def get_kardex(
    request: Request,
    producto_id: str,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> schemas.PaginatedKardexResponse:
    empresa_id = request.state.empresa_id
    import uuid
    movimientos, total = await service.get_kardex(
        db, empresa_id, uuid.UUID(producto_id), skip=skip, limit=limit
    )
    return schemas.PaginatedKardexResponse(
        items=[schemas.MovimientoStockPublic.model_validate(m.model_dump()) for m in movimientos],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/ajustes",
    response_model=schemas.MovimientoStockPublic,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("stock:create"))],
)
async def crear_ajuste(
    request: Request,
    payload: schemas.AjusteStockCreate,
    db: AsyncSession = Depends(get_db),
) -> schemas.MovimientoStockPublic:
    empresa_id = request.state.empresa_id
    current_user = request.state.current_user
    import uuid
    movimiento = await service.ajustar_stock(
        db=db,
        empresa_id=empresa_id,
        producto_id=payload.producto_id,
        cantidad_kilos=payload.cantidad_kilos,
        motivo=payload.motivo,
        operador_id=current_user.id,
    )
    return schemas.MovimientoStockPublic.model_validate(movimiento.model_dump())


@router.get(
    "/alertas",
    response_model=list[schemas.AlertaStockItem],
    dependencies=[Depends(require_role("stock:read"))],
)
async def get_alertas(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> list[schemas.AlertaStockItem]:
    empresa_id = request.state.empresa_id
    alertas = await service.get_alertas(db, empresa_id)
    return [schemas.AlertaStockItem.model_validate(a) for a in alertas]
