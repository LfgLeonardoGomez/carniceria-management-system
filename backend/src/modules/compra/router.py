from typing import Optional

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.modules.auth.dependencies import get_current_user
from src.modules.auth.models import Usuario
from src.modules.compra import schemas as compra_schemas
from src.modules.compra import service as compra_service
from src.common.rbac import require_role
from src.common.exceptions import NotFoundException

router = APIRouter()


# ---------------------------------------------------------------------------
# List & Search
# ---------------------------------------------------------------------------
@router.get(
    "",
    response_model=compra_schemas.CompraListResponse,
    dependencies=[Depends(require_role("compras:read"))],
)
async def list_compras(
    request: Request,
    skip: int = 0,
    limit: int = 20,
    proveedor_id: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    incluir_anuladas: bool = False,
    db: AsyncSession = Depends(get_db),
) -> compra_schemas.CompraListResponse:
    empresa_id = request.state.empresa_id
    from datetime import date
    import uuid

    pid = None
    if proveedor_id:
        try:
            pid = uuid.UUID(proveedor_id)
        except ValueError:
            raise NotFoundException("Proveedor no encontrado")

    fd = date.fromisoformat(fecha_desde) if fecha_desde else None
    fh = date.fromisoformat(fecha_hasta) if fecha_hasta else None

    compras, total = await compra_service.list_compras(
        db=db,
        empresa_id=empresa_id,
        skip=skip,
        limit=limit,
        proveedor_id=pid,
        fecha_desde=fd,
        fecha_hasta=fh,
        incluir_anuladas=incluir_anuladas,
    )
    return compra_schemas.CompraListResponse(
        items=[_to_response(c, include_proveedor=True) for c in compras],
        total=total,
        skip=skip,
        limit=limit,
    )


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------
@router.post(
    "",
    response_model=compra_schemas.CompraResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("compras:create"))],
)
async def create_compra(
    request: Request,
    payload: compra_schemas.CompraCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> compra_schemas.CompraResponse:
    empresa_id = request.state.empresa_id
    compra = await compra_service.create_compra(
        db=db,
        empresa_id=empresa_id,
        proveedor_id=payload.proveedor_id,
        fecha=payload.fecha,
        cantidad_medias_reses=payload.cantidad_medias_reses,
        peso_total=payload.peso_total,
        costo_total=payload.costo_total,
        observaciones=payload.observaciones,
        operador_id=current_user.id,
    )
    return _to_response(compra, include_proveedor=True)


# ---------------------------------------------------------------------------
# Get by ID
# ---------------------------------------------------------------------------
@router.get(
    "/{compra_id}",
    response_model=compra_schemas.CompraResponse,
    dependencies=[Depends(require_role("compras:read"))],
)
async def get_compra(
    request: Request,
    compra_id: str,
    db: AsyncSession = Depends(get_db),
) -> compra_schemas.CompraResponse:
    empresa_id = request.state.empresa_id
    import uuid
    try:
        cid = uuid.UUID(compra_id)
    except ValueError:
        raise NotFoundException("Compra no encontrada")
    compra = await compra_service.get_compra(db, empresa_id, cid)
    return _to_response(compra, include_proveedor=True)


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------
@router.put(
    "/{compra_id}",
    response_model=compra_schemas.CompraResponse,
    dependencies=[Depends(require_role("compras:update"))],
)
async def update_compra(
    request: Request,
    compra_id: str,
    payload: compra_schemas.CompraUpdate,
    db: AsyncSession = Depends(get_db),
) -> compra_schemas.CompraResponse:
    empresa_id = request.state.empresa_id
    import uuid
    try:
        cid = uuid.UUID(compra_id)
    except ValueError:
        raise NotFoundException("Compra no encontrada")

    compra = await compra_service.update_compra(
        db=db,
        empresa_id=empresa_id,
        compra_id=cid,
        fecha=payload.fecha,
        cantidad_medias_reses=payload.cantidad_medias_reses,
        peso_total=payload.peso_total,
        costo_total=payload.costo_total,
        observaciones=payload.observaciones,
    )
    return _to_response(compra, include_proveedor=True)


# ---------------------------------------------------------------------------
# Delete (soft)
# ---------------------------------------------------------------------------
@router.delete(
    "/{compra_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("compras:delete"))],
)
async def delete_compra(
    request: Request,
    compra_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> None:
    empresa_id = request.state.empresa_id
    import uuid
    try:
        cid = uuid.UUID(compra_id)
    except ValueError:
        raise NotFoundException("Compra no encontrada")
    await compra_service.delete_compra(
        db=db,
        empresa_id=empresa_id,
        compra_id=cid,
        operador_id=current_user.id,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _to_response(compra, include_proveedor: bool = False) -> compra_schemas.CompraResponse:
    proveedor = None
    if include_proveedor and compra.proveedor:
        proveedor = compra_schemas.ProveedorCompacto(
            id=compra.proveedor.id,
            nombre=compra.proveedor.nombre,
        )
    return compra_schemas.CompraResponse(
        id=compra.id,
        empresa_id=compra.empresa_id,
        proveedor_id=compra.proveedor_id,
        proveedor=proveedor,
        fecha=compra.fecha,
        cantidad_medias_reses=compra.cantidad_medias_reses,
        peso_total=compra.peso_total,
        costo_total=compra.costo_total,
        costo_por_kilo=compra.costo_por_kilo,
        costo_promedio_historico=compra.costo_promedio_historico,
        observaciones=compra.observaciones,
        estado=compra.estado,
        created_at=compra.created_at,
        updated_at=compra.updated_at,
    )
