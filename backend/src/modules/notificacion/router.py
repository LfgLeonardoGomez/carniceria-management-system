from typing import Optional

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from src.config.database import get_db
from src.modules.auth.dependencies import require_auth
from src.modules.notificacion import service
from src.modules.notificacion import schemas

router = APIRouter()


@router.get(
    "",
    response_model=schemas.PaginatedNotificacionResponse,
)
async def list_notificaciones(
    request: Request,
    skip: int = 0,
    limit: int = 20,
    leida: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
) -> schemas.PaginatedNotificacionResponse:
    empresa_id = request.state.empresa_id
    notifs, total = await service.listar_notificaciones(
        db=db,
        empresa_id=empresa_id,
        skip=skip,
        limit=limit,
        leida=leida,
    )
    return schemas.PaginatedNotificacionResponse(
        items=[schemas.NotificacionPublic.model_validate(n.model_dump()) for n in notifs],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.patch(
    "/{notificacion_id}/leida",
    response_model=schemas.MarcarLeidaResponse,
)
async def marcar_notificacion_leida(
    request: Request,
    notificacion_id: str,
    db: AsyncSession = Depends(get_db),
) -> schemas.MarcarLeidaResponse:
    empresa_id = request.state.empresa_id
    notif = await service.marcar_leida(
        db=db,
        empresa_id=empresa_id,
        notificacion_id=uuid.UUID(notificacion_id),
    )
    return schemas.MarcarLeidaResponse(
        id=notif.id,
        leida=notif.leida,
        fecha_lectura=notif.fecha_lectura,
    )
