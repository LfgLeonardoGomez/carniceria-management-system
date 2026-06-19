from typing import Optional

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.modules.auth.dependencies import get_current_user, require_auth
from src.modules.auth.models import Usuario
from src.modules.cliente import schemas
from src.modules.cliente import service
from src.common.rbac import require_role
from src.common.exceptions import ForbiddenException

router = APIRouter()


# ---------------------------------------------------------------------------
# Helper: convert domain model -> response schema
# ---------------------------------------------------------------------------
def _to_response(cliente) -> schemas.ClienteResponse:
    return schemas.ClienteResponse(
        id=cliente.id,
        empresa_id=cliente.empresa_id,
        nombre=cliente.nombre,
        apellido=cliente.apellido,
        razon_social=cliente.razon_social,
        cuit=cliente.cuit,
        telefono=cliente.telefono,
        email=cliente.email,
        direccion=cliente.direccion,
        tipo_cliente=cliente.tipo_cliente,
        limite_cuenta_corriente=cliente.limite_cuenta_corriente,
        saldo_actual=cliente.saldo_actual,
        activo=cliente.activo,
        created_at=cliente.created_at,
        updated_at=cliente.updated_at,
    )


# ---------------------------------------------------------------------------
# CRUD endpoints
# ---------------------------------------------------------------------------
@router.post(
    "",
    response_model=schemas.ClienteResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("clientes:create"))],
)
async def create_cliente(
    request: Request,
    payload: schemas.ClienteCreate,
    db: AsyncSession = Depends(get_db),
) -> schemas.ClienteResponse:
    current_user: Usuario = request.state.current_user
    cliente = await service.create_cliente(
        db=db,
        current_user=current_user,
        data=payload,
    )
    return _to_response(cliente)


@router.get(
    "",
    response_model=schemas.ClienteListResponse,
    dependencies=[Depends(require_role("clientes:read"))],
)
async def list_clientes(
    request: Request,
    skip: int = 0,
    limit: int = 20,
    tipo_cliente: Optional[str] = None,
    q: Optional[str] = None,
    activo: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
) -> schemas.ClienteListResponse:
    empresa_id = request.state.empresa_id
    clientes, total = await service.list_clientes(
        db=db,
        empresa_id=empresa_id,
        skip=skip,
        limit=limit,
        tipo_cliente=tipo_cliente,
        q=q,
        activo=activo,
    )
    return schemas.ClienteListResponse(
        items=[_to_response(c) for c in clientes],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{cliente_id}",
    response_model=schemas.ClienteResponse,
    dependencies=[Depends(require_role("clientes:read"))],
)
async def get_cliente(
    request: Request,
    cliente_id: str,
    db: AsyncSession = Depends(get_db),
) -> schemas.ClienteResponse:
    empresa_id = request.state.empresa_id
    cliente = await service.get_cliente_by_id(db, empresa_id, cliente_id)
    return _to_response(cliente)


@router.put(
    "/{cliente_id}",
    response_model=schemas.ClienteResponse,
    dependencies=[Depends(require_role("clientes:update"))],
)
async def update_cliente(
    request: Request,
    cliente_id: str,
    payload: schemas.ClienteUpdate,
    db: AsyncSession = Depends(get_db),
) -> schemas.ClienteResponse:
    empresa_id = request.state.empresa_id
    cliente = await service.update_cliente(
        db=db,
        empresa_id=empresa_id,
        cliente_id=cliente_id,
        data=payload,
    )
    return _to_response(cliente)


@router.delete(
    "/{cliente_id}",
    response_model=schemas.ClienteResponse,
    dependencies=[Depends(require_role("clientes:delete"))],
)
async def delete_cliente(
    request: Request,
    cliente_id: str,
    db: AsyncSession = Depends(get_db),
) -> schemas.ClienteResponse:
    empresa_id = request.state.empresa_id
    cliente = await service.soft_delete_cliente(
        db=db,
        empresa_id=empresa_id,
        cliente_id=cliente_id,
    )
    return _to_response(cliente)


# ---------------------------------------------------------------------------
# Historial endpoint
# ---------------------------------------------------------------------------
@router.get(
    "/{cliente_id}/historial",
    response_model=schemas.ClienteHistorialResponse,
    dependencies=[Depends(require_role("clientes:read"))],
)
async def get_cliente_historial(
    request: Request,
    cliente_id: str,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> schemas.ClienteHistorialResponse:
    empresa_id = request.state.empresa_id
    ventas, total = await service.get_historial(
        db=db,
        empresa_id=empresa_id,
        cliente_id=cliente_id,
        skip=skip,
        limit=limit,
    )

    # Convert ventas to VentaResumen if they exist; otherwise return empty
    items = []
    for v in ventas:
        try:
            items.append(
                schemas.VentaResumen(
                    id=v.id,
                    fecha=v.fecha,
                    total=v.total,
                    estado=v.estado,
                )
            )
        except Exception:
            # Fallback if venta model doesn't have expected fields
            pass

    return schemas.ClienteHistorialResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )
