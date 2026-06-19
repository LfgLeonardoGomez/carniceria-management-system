from typing import Optional

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.modules.auth.dependencies import get_current_user
from src.modules.auth.models import Usuario
from src.modules.desposte import schemas as desposte_schemas
from src.modules.desposte import service as desposte_service
from src.common.rbac import require_role
from src.common.exceptions import NotFoundException

router = APIRouter()


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------
@router.get(
    "",
    response_model=desposte_schemas.DesposteListResponse,
    dependencies=[Depends(require_role("despostes:read"))],
)
async def list_despostes(
    request: Request,
    fecha: Optional[str] = None,
    estado: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> desposte_schemas.DesposteListResponse:
    empresa_id = request.state.empresa_id
    from datetime import date

    fd = date.fromisoformat(fecha) if fecha else None

    despostes, total = await desposte_service.listar_despostes(
        db=db,
        empresa_id=empresa_id,
        fecha=fd,
        estado=estado,
        skip=skip,
        limit=limit,
    )
    return desposte_schemas.DesposteListResponse(
        items=[_to_response(d) for d in despostes],
        total=total,
        skip=skip,
        limit=limit,
    )


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------
@router.post(
    "",
    response_model=desposte_schemas.DesposteResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("despostes:create"))],
)
async def create_desposte(
    request: Request,
    payload: desposte_schemas.DesposteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> desposte_schemas.DesposteResponse:
    empresa_id = request.state.empresa_id
    desposte = await desposte_service.crear_desposte(
        db=db,
        empresa_id=empresa_id,
        compra_id=payload.compra_id,
        fecha=payload.fecha,
        operador_id=payload.operador_id,
    )
    return _to_response(desposte)


# ---------------------------------------------------------------------------
# Get by ID
# ---------------------------------------------------------------------------
@router.get(
    "/{desposte_id}",
    response_model=desposte_schemas.DesposteResponse,
    dependencies=[Depends(require_role("despostes:read"))],
)
async def get_desposte(
    request: Request,
    desposte_id: str,
    db: AsyncSession = Depends(get_db),
) -> desposte_schemas.DesposteResponse:
    empresa_id = request.state.empresa_id
    import uuid
    try:
        did = uuid.UUID(desposte_id)
    except ValueError:
        raise NotFoundException("Desposte no encontrado")
    desposte = await desposte_service.obtener_desposte(db, did, empresa_id)
    return _to_response(desposte)


# ---------------------------------------------------------------------------
# Add Corte
# ---------------------------------------------------------------------------
@router.post(
    "/{desposte_id}/cortes",
    response_model=desposte_schemas.CorteDesposteResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("despostes:update"))],
)
async def add_corte(
    request: Request,
    desposte_id: str,
    payload: desposte_schemas.CorteDesposteCreate,
    db: AsyncSession = Depends(get_db),
) -> desposte_schemas.CorteDesposteResponse:
    empresa_id = request.state.empresa_id
    import uuid
    try:
        did = uuid.UUID(desposte_id)
    except ValueError:
        raise NotFoundException("Desposte no encontrado")

    corte = await desposte_service.agregar_corte(
        db=db,
        desposte_id=did,
        empresa_id=empresa_id,
        tipo_corte=payload.tipo_corte,
        kilos_obtenidos=payload.kilos_obtenidos,
        producto_id=payload.producto_id,
    )
    return _to_corte_response(corte)


# ---------------------------------------------------------------------------
# Finalizar
# ---------------------------------------------------------------------------
@router.post(
    "/{desposte_id}/finalizar",
    response_model=desposte_schemas.DesposteFinalizarResponse,
    dependencies=[Depends(require_role("despostes:update"))],
)
async def finalizar_desposte(
    request: Request,
    desposte_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> desposte_schemas.DesposteFinalizarResponse:
    empresa_id = request.state.empresa_id
    import uuid
    try:
        did = uuid.UUID(desposte_id)
    except ValueError:
        raise NotFoundException("Desposte no encontrado")

    desposte = await desposte_service.finalizar_desposte(
        db=db,
        desposte_id=did,
        empresa_id=empresa_id,
        operador_id=current_user.id,
    )
    return _to_response(desposte)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _to_response(desposte) -> desposte_schemas.DesposteResponse:
    compra = None
    if desposte.compra:
        proveedor = None
        if desposte.compra.proveedor:
            proveedor = desposte_schemas.ProveedorCompacto(
                id=desposte.compra.proveedor.id,
                nombre=desposte.compra.proveedor.nombre,
            )
        compra = desposte_schemas.CompraCompacto(
            id=desposte.compra.id,
            fecha=desposte.compra.fecha,
            peso_total=desposte.compra.peso_total,
            costo_total=desposte.compra.costo_total,
            proveedor=proveedor,
        )

    operador = None
    if desposte.operador:
        operador = desposte_schemas.UsuarioCompacto(
            id=desposte.operador.id,
            nombre=desposte.operador.nombre,
            apellido=desposte.operador.apellido,
        )

    cortes = []
    if desposte.cortes:
        cortes = [_to_corte_response(c) for c in desposte.cortes]

    movimientos = []
    raw_movimientos = getattr(desposte, "_movimientos_stock", None)
    if raw_movimientos:
        movimientos = [
            desposte_schemas.MovimientoStockCompacto(
                id=m.id,
                tipo=m.tipo,
                cantidad_kilos=m.cantidad_kilos,
                stock_resultante=m.stock_resultante,
                producto_id=m.producto_id,
                fecha=m.fecha,
            )
            for m in raw_movimientos
        ]

    return desposte_schemas.DesposteResponse(
        id=desposte.id,
        empresa_id=desposte.empresa_id,
        compra_id=desposte.compra_id,
        compra=compra,
        fecha=desposte.fecha,
        operador_id=desposte.operador_id,
        operador=operador,
        estado=desposte.estado,
        rendimiento_total=desposte.rendimiento_total,
        merma=desposte.merma,
        cortes=cortes,
        movimientos_stock=movimientos,
        created_at=desposte.created_at,
        updated_at=desposte.updated_at,
    )


def _to_corte_response(corte) -> desposte_schemas.CorteDesposteResponse:
    producto = None
    if corte.producto:
        producto = desposte_schemas.ProductoCompacto(
            id=corte.producto.id,
            nombre=corte.producto.nombre,
            plu=corte.producto.plu,
        )
    return desposte_schemas.CorteDesposteResponse(
        id=corte.id,
        tipo_corte=corte.tipo_corte,
        kilos_obtenidos=corte.kilos_obtenidos,
        porcentaje_rendimiento=corte.porcentaje_rendimiento,
        costo_asignado=corte.costo_asignado,
        costo_final_por_kilo=corte.costo_final_por_kilo,
        producto_id=corte.producto_id,
        producto=producto,
        created_at=corte.created_at,
        updated_at=corte.updated_at,
    )
