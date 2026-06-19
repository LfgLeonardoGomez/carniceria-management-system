from typing import Optional

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.modules.auth.dependencies import get_current_user, require_auth
from src.modules.auth.models import Usuario
from src.modules.proveedor import schemas
from src.modules.proveedor import service
from src.common.rbac import require_role
from src.common.exceptions import NotFoundException

router = APIRouter()


# ---------------------------------------------------------------------------
# List & Search
# ---------------------------------------------------------------------------
@router.get(
    "",
    response_model=schemas.ProveedorListResponse,
    dependencies=[Depends(require_role("proveedores:read"))],
)
async def list_proveedores(
    request: Request,
    skip: int = 0,
    limit: int = 20,
    nombre: Optional[str] = None,
    incluir_inactivos: bool = False,
    db: AsyncSession = Depends(get_db),
) -> schemas.ProveedorListResponse:
    empresa_id = request.state.empresa_id
    proveedores, total = await service.list_by_empresa(
        db=db,
        empresa_id=empresa_id,
        skip=skip,
        limit=limit,
        nombre=nombre,
        incluir_inactivos=incluir_inactivos,
    )
    return schemas.ProveedorListResponse(
        items=[_to_response(p) for p in proveedores],
        total=total,
        skip=skip,
        limit=limit,
    )


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------
@router.post(
    "",
    response_model=schemas.ProveedorResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("proveedores:create"))],
)
async def create_proveedor(
    request: Request,
    payload: schemas.ProveedorCreate,
    db: AsyncSession = Depends(get_db),
) -> schemas.ProveedorResponse:
    empresa_id = request.state.empresa_id
    proveedor = await service.create(
        db=db,
        empresa_id=empresa_id,
        nombre=payload.nombre,
        cuit=payload.cuit,
        telefono=payload.telefono,
        email=payload.email,
        direccion=payload.direccion,
    )
    return _to_response(proveedor)


# ---------------------------------------------------------------------------
# Get by ID
# ---------------------------------------------------------------------------
@router.get(
    "/{proveedor_id}",
    response_model=schemas.ProveedorResponse,
    dependencies=[Depends(require_role("proveedores:read"))],
)
async def get_proveedor(
    request: Request,
    proveedor_id: str,
    db: AsyncSession = Depends(get_db),
) -> schemas.ProveedorResponse:
    empresa_id = request.state.empresa_id
    import uuid
    try:
        pid = uuid.UUID(proveedor_id)
    except ValueError:
        raise NotFoundException("Proveedor no encontrado")
    proveedor = await service.get_by_id(db, empresa_id, pid)
    return _to_response(proveedor)


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------
@router.put(
    "/{proveedor_id}",
    response_model=schemas.ProveedorResponse,
    dependencies=[Depends(require_role("proveedores:update"))],
)
async def update_proveedor(
    request: Request,
    proveedor_id: str,
    payload: schemas.ProveedorUpdate,
    db: AsyncSession = Depends(get_db),
) -> schemas.ProveedorResponse:
    empresa_id = request.state.empresa_id
    import uuid
    try:
        pid = uuid.UUID(proveedor_id)
    except ValueError:
        raise NotFoundException("Proveedor no encontrado")

    proveedor = await service.update(
        db=db,
        empresa_id=empresa_id,
        proveedor_id=pid,
        nombre=payload.nombre,
        cuit=payload.cuit,
        telefono=payload.telefono,
        email=payload.email,
        direccion=payload.direccion,
    )
    return _to_response(proveedor)


# ---------------------------------------------------------------------------
# Delete (soft)
# ---------------------------------------------------------------------------
@router.delete(
    "/{proveedor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("proveedores:delete"))],
)
async def delete_proveedor(
    request: Request,
    proveedor_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    empresa_id = request.state.empresa_id
    import uuid
    try:
        pid = uuid.UUID(proveedor_id)
    except ValueError:
        raise NotFoundException("Proveedor no encontrado")
    await service.delete_logic(db, empresa_id, pid)


# ---------------------------------------------------------------------------
# Historial de compras (populated in C-08)
# ---------------------------------------------------------------------------
from src.modules.compra import schemas as compra_schemas
from src.modules.compra import service as compra_service

@router.get(
    "/{proveedor_id}/historial",
    response_model=compra_schemas.CompraListResponse,
    dependencies=[Depends(require_role("proveedores:read"))],
)
async def get_historial(
    request: Request,
    proveedor_id: str,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> compra_schemas.CompraListResponse:
    empresa_id = request.state.empresa_id
    import uuid
    try:
        pid = uuid.UUID(proveedor_id)
    except ValueError:
        raise NotFoundException("Proveedor no encontrado")
    # Verify the proveedor exists and belongs to the tenant
    await service.get_by_id(db, empresa_id, pid)
    compras, total, costo_promedio = await compra_service.get_historial_por_proveedor(
        db=db,
        empresa_id=empresa_id,
        proveedor_id=pid,
        skip=skip,
        limit=limit,
    )
    return compra_schemas.CompraListResponse(
        items=[
            compra_schemas.CompraResponse(
                id=c.id,
                empresa_id=c.empresa_id,
                proveedor_id=c.proveedor_id,
                proveedor=compra_schemas.ProveedorCompacto(
                    id=c.proveedor.id,
                    nombre=c.proveedor.nombre,
                ) if c.proveedor else None,
                fecha=c.fecha,
                cantidad_medias_reses=c.cantidad_medias_reses,
                peso_total=c.peso_total,
                costo_total=c.costo_total,
                costo_por_kilo=c.costo_por_kilo,
                costo_promedio_historico=c.costo_promedio_historico,
                observaciones=c.observaciones,
                estado=c.estado,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in compras
        ],
        total=total,
        skip=skip,
        limit=limit,
        costo_promedio_historico=costo_promedio,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _to_response(proveedor) -> schemas.ProveedorResponse:
    return schemas.ProveedorResponse(
        id=proveedor.id,
        empresa_id=proveedor.empresa_id,
        nombre=proveedor.nombre,
        cuit=proveedor.cuit,
        telefono=proveedor.telefono,
        email=proveedor.email,
        direccion=proveedor.direccion,
        activo=proveedor.activo,
        created_at=proveedor.created_at,
        updated_at=proveedor.updated_at,
    )
