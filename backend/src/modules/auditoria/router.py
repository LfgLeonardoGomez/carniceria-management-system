from typing import Optional
from datetime import date

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.modules.auth.dependencies import require_auth, require_admin
from src.modules.auditoria import service
from src.modules.auditoria import schemas

router = APIRouter()


@router.get(
    "",
    response_model=schemas.PaginatedAuditoriaResponse,
    dependencies=[Depends(require_admin)],
)
async def list_auditoria(
    request: Request,
    skip: int = 0,
    limit: int = 20,
    usuario_id: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    accion: Optional[str] = None,
    entidad_tipo: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> schemas.PaginatedAuditoriaResponse:
    empresa_id = request.state.empresa_id
    uid = None
    if usuario_id:
        import uuid
        uid = uuid.UUID(usuario_id)

    registros, total = await service.listar_auditoria(
        db=db,
        empresa_id=empresa_id,
        skip=skip,
        limit=limit,
        usuario_id=uid,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        accion=accion,
        entidad_tipo=entidad_tipo,
    )

    items = []
    for r in registros:
        items.append(schemas.AuditoriaPublic(
            id=r.id,
            empresa_id=r.empresa_id,
            usuario_id=r.usuario_id,
            accion=r.accion,
            entidad_tipo=r.entidad_tipo,
            entidad_id=r.entidad_id,
            payload=r.payload,
            fecha=r.fecha,
            hora=r.hora.isoformat() if r.hora else None,
            created_at=r.created_at.isoformat() if r.created_at else None,
        ))

    return schemas.PaginatedAuditoriaResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )
