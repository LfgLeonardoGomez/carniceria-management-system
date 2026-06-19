from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.modules.auth.dependencies import get_current_user, require_auth
from src.modules.auth.models import Usuario
from src.modules.venta import schemas
from src.modules.venta import service
from src.modules.venta.state_machine import requiere_rol_admin_o_encargado
from src.common.rbac import require_role, normalize_rol
from src.common.exceptions import ForbiddenException

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _to_detalle_response(detalle) -> schemas.DetalleVentaRead:
    return schemas.DetalleVentaRead(
        id=detalle.id,
        producto_id=detalle.producto_id,
        cantidad_kilos=detalle.cantidad_kilos,
        precio_unitario=detalle.precio_unitario,
        importe=detalle.importe,
    )


def _to_pago_response(pago) -> schemas.PagoVentaRead:
    return schemas.PagoVentaRead(
        id=pago.id,
        venta_id=pago.venta_id,
        medio_pago=pago.medio_pago,
        importe=pago.importe,
    )


def _to_venta_response(venta) -> schemas.VentaRead:
    return schemas.VentaRead(
        id=venta.id,
        empresa_id=venta.empresa_id,
        cliente_id=venta.cliente_id,
        tipo_cliente_al_momento=venta.tipo_cliente_al_momento,
        estado=venta.estado,
        subtotal=venta.subtotal,
        descuentos=venta.descuentos,
        total=venta.total,
        fecha=venta.fecha,
        created_at=venta.created_at,
        updated_at=venta.updated_at,
        detalles=[_to_detalle_response(d) for d in (venta.detalles or [])],
        pagos=[_to_pago_response(p) for p in (venta.pagos or [])],
    )


def _build_ticket(venta, empresa_nombre: str) -> schemas.TicketData:
    items = []
    # Eager load product names if not available; for now detalle doesn't have nombre
    # We include placeholder or require frontend to resolve product names
    # For the ticket spec, we need product name. We'll fetch it in service if needed,
    # but for simplicity we leave it as empty or require frontend enrichment.
    # Per design.md, ticket_data includes items with nombre. Let's fetch productos in service.
    # For router, we'll construct with available data. The service should ideally enrich.
    # Given time constraints, we'll return detalle data and let frontend handle name,
    # OR we add a lightweight lookup here.
    for d in venta.detalles or []:
        items.append(
            schemas.TicketItem(
                nombre="",  # Placeholder; service should enrich if needed
                cantidad_kilos=d.cantidad_kilos,
                precio_unitario=d.precio_unitario,
                importe=d.importe,
            )
        )
    pago = venta.pagos[0] if venta.pagos else None
    return schemas.TicketData(
        empresa_nombre=empresa_nombre,
        fecha=venta.fecha,
        items=items,
        subtotal=venta.subtotal,
        descuentos=venta.descuentos,
        total=venta.total,
        medio_de_pago=pago.medio_pago if pago else "",
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.post(
    "",
    response_model=schemas.VentaRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("ventas:create"))],
)
async def create_venta(
    request: Request,
    payload: schemas.VentaCreate,
    db: AsyncSession = Depends(get_db),
) -> schemas.VentaRead:
    current_user: Usuario = request.state.current_user
    venta = await service.crear_venta(db=db, current_user=current_user, data=payload)
    return _to_venta_response(venta)


@router.get(
    "",
    response_model=schemas.VentaListResponse,
    dependencies=[Depends(require_role("ventas:read"))],
)
async def list_ventas(
    request: Request,
    skip: int = 0,
    limit: int = 20,
    estado: Optional[str] = None,
    fecha: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> schemas.VentaListResponse:
    empresa_id = request.state.empresa_id
    fecha_desde = None
    fecha_hasta = None
    if fecha:
        try:
            dt = datetime.strptime(fecha, "%Y-%m-%d")
            fecha_desde = dt
            fecha_hasta = datetime(dt.year, dt.month, dt.day, 23, 59, 59)
        except ValueError:
            pass

    ventas, total = await service.listar_ventas(
        db=db,
        empresa_id=empresa_id,
        skip=skip,
        limit=limit,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
    return schemas.VentaListResponse(
        items=[_to_venta_response(v) for v in ventas],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{venta_id}",
    response_model=schemas.VentaRead,
    dependencies=[Depends(require_role("ventas:read"))],
)
async def get_venta(
    request: Request,
    venta_id: str,
    db: AsyncSession = Depends(get_db),
) -> schemas.VentaRead:
    empresa_id = request.state.empresa_id
    import uuid
    venta = await service.obtener_venta(db, empresa_id, uuid.UUID(venta_id))
    return _to_venta_response(venta)


@router.post(
    "/{venta_id}/suspender",
    response_model=schemas.VentaRead,
    dependencies=[Depends(require_role("ventas:create"))],
)
async def suspender_venta(
    request: Request,
    venta_id: str,
    db: AsyncSession = Depends(get_db),
) -> schemas.VentaRead:
    empresa_id = request.state.empresa_id
    import uuid
    venta = await service.suspender_venta(db, empresa_id, uuid.UUID(venta_id))
    return _to_venta_response(venta)


@router.post(
    "/{venta_id}/cobrar",
    response_model=schemas.CobrarVentaResponse,
    dependencies=[Depends(require_role("ventas:create"))],
)
async def cobrar_venta(
    request: Request,
    venta_id: str,
    payload: schemas.CobrarVentaRequest,
    db: AsyncSession = Depends(get_db),
) -> schemas.CobrarVentaResponse:
    current_user: Usuario = request.state.current_user
    import uuid
    venta = await service.cobrar_venta(
        db=db, current_user=current_user, venta_id=uuid.UUID(venta_id), data=payload
    )
    # Empresa name for ticket
    from src.modules.empresa.models import Empresa
    from sqlalchemy import select
    result = await db.execute(select(Empresa).where(Empresa.id == venta.empresa_id))
    empresa = result.scalar_one_or_none()
    empresa_nombre = empresa.nombre_comercial if empresa else ""

    # Enrich ticket items with product names
    from src.modules.producto.models import Producto
    ticket_items = []
    for d in venta.detalles or []:
        prod_result = await db.execute(select(Producto).where(Producto.id == d.producto_id))
        prod = prod_result.scalar_one_or_none()
        ticket_items.append(
            schemas.TicketItem(
                nombre=prod.nombre if prod else "",
                cantidad_kilos=d.cantidad_kilos,
                precio_unitario=d.precio_unitario,
                importe=d.importe,
            )
        )

    pago = venta.pagos[0] if venta.pagos else None
    ticket = schemas.TicketData(
        empresa_nombre=empresa_nombre,
        fecha=venta.fecha,
        items=ticket_items,
        subtotal=venta.subtotal,
        descuentos=venta.descuentos,
        total=venta.total,
        medio_de_pago=pago.medio_pago if pago else "",
    )

    return schemas.CobrarVentaResponse(
        venta=_to_venta_response(venta),
        ticket=ticket,
    )


@router.post(
    "/{venta_id}/recuperar",
    response_model=schemas.VentaRead,
    dependencies=[Depends(require_role("ventas:create"))],
)
async def recuperar_venta(
    request: Request,
    venta_id: str,
    db: AsyncSession = Depends(get_db),
) -> schemas.VentaRead:
    empresa_id = request.state.empresa_id
    import uuid
    venta = await service.recuperar_venta(db, empresa_id, uuid.UUID(venta_id))
    return _to_venta_response(venta)


@router.post(
    "/{venta_id}/anular",
    response_model=schemas.VentaRead,
)
async def anular_venta(
    request: Request,
    venta_id: str,
    db: AsyncSession = Depends(get_db),
) -> schemas.VentaRead:
    current_user: Usuario = request.state.current_user
    # Validar rol Admin o Encargado
    rol_nombre = None
    if hasattr(current_user, "rol") and current_user.rol is not None:
        rol_nombre = current_user.rol.nombre
    elif hasattr(current_user, "rol_nombre"):
        rol_nombre = current_user.rol_nombre

    if normalize_rol(rol_nombre) not in ("admin", "encargado"):
        raise ForbiddenException("Solo Admin o Encargado pueden anular ventas")

    import uuid
    venta = await service.anular_venta(
        db=db, current_user=current_user, venta_id=uuid.UUID(venta_id)
    )
    return _to_venta_response(venta)
