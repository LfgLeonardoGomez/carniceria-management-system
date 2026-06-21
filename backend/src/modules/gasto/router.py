import uuid
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.modules.gasto import schemas
from src.modules.gasto import service
from src.common.rbac import require_role

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _to_gasto_response(gasto) -> schemas.GastoRead:
    return schemas.GastoRead(
        id=gasto.id,
        empresa_id=gasto.empresa_id,
        fecha=gasto.fecha,
        categoria=gasto.categoria,
        descripcion=gasto.descripcion,
        importe=gasto.importe,
        medio_pago=gasto.medio_pago,
        created_at=gasto.created_at,
        updated_at=gasto.updated_at,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.post(
    "",
    response_model=schemas.GastoRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("gastos:create"))],
)
async def create_gasto(
    request: Request,
    payload: schemas.GastoCreate,
    db: AsyncSession = Depends(get_db),
) -> schemas.GastoRead:
    empresa_id: uuid.UUID = request.state.empresa_id
    gasto = await service.crear_gasto(db=db, empresa_id=empresa_id, data=payload)
    return _to_gasto_response(gasto)


@router.get(
    "",
    response_model=schemas.GastoListResponse,
    dependencies=[Depends(require_role("gastos:read"))],
)
async def list_gastos(
    request: Request,
    skip: int = 0,
    limit: int = 20,
    categoria: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
) -> schemas.GastoListResponse:
    empresa_id: uuid.UUID = request.state.empresa_id
    gastos, total = await service.listar_gastos(
        db=db,
        empresa_id=empresa_id,
        skip=skip,
        limit=limit,
        categoria=categoria,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
    return schemas.GastoListResponse(
        items=[_to_gasto_response(g) for g in gastos],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{gasto_id}",
    response_model=schemas.GastoRead,
    dependencies=[Depends(require_role("gastos:read"))],
)
async def get_gasto(
    request: Request,
    gasto_id: str,
    db: AsyncSession = Depends(get_db),
) -> schemas.GastoRead:
    empresa_id: uuid.UUID = request.state.empresa_id
    gasto = await service.obtener_gasto(db, empresa_id, uuid.UUID(gasto_id))
    return _to_gasto_response(gasto)


@router.put(
    "/{gasto_id}",
    response_model=schemas.GastoRead,
    dependencies=[Depends(require_role("gastos:create"))],
)
async def update_gasto(
    request: Request,
    gasto_id: str,
    payload: schemas.GastoUpdate,
    db: AsyncSession = Depends(get_db),
) -> schemas.GastoRead:
    empresa_id: uuid.UUID = request.state.empresa_id
    gasto = await service.actualizar_gasto(db, empresa_id, uuid.UUID(gasto_id), payload)
    return _to_gasto_response(gasto)


@router.delete(
    "/{gasto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("gastos:create"))],
)
async def delete_gasto(
    request: Request,
    gasto_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    empresa_id: uuid.UUID = request.state.empresa_id
    await service.eliminar_gasto(db, empresa_id, uuid.UUID(gasto_id))
