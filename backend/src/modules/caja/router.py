from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.modules.auth.models import Usuario
from src.modules.caja import schemas, service
from src.common.rbac import require_role

router = APIRouter()


def _to_caja_read(caja) -> schemas.CajaRead:
    return schemas.CajaRead(
        id=caja.id,
        empresa_id=caja.empresa_id,
        estado=caja.estado,
        efectivo_inicial=caja.efectivo_inicial,
        monto_final=caja.monto_final,
        fecha_apertura=caja.fecha_apertura,
        fecha_cierre=caja.fecha_cierre,
        usuario_apertura_id=caja.usuario_apertura_id,
        usuario_cierre_id=caja.usuario_cierre_id,
    )


def _to_esperado_read(esperado) -> schemas.EsperadoRead:
    return schemas.EsperadoRead(
        efectivo=esperado.efectivo,
        transferencias=esperado.transferencias,
        tarjetas=esperado.tarjetas,
    )


@router.post(
    "/apertura",
    response_model=schemas.CajaRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("caja:operate"))],
)
async def apertura_caja(
    request: Request,
    payload: schemas.AperturaCajaRequest,
    db: AsyncSession = Depends(get_db),
) -> schemas.CajaRead:
    current_user: Usuario = request.state.current_user
    caja = await service.abrir_caja(
        db=db,
        empresa_id=current_user.empresa_id,
        usuario_id=current_user.id,
        efectivo_inicial=payload.efectivo_inicial,
    )
    return _to_caja_read(caja)


@router.post(
    "/movimientos",
    response_model=schemas.MovimientoCajaRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("caja:operate"))],
)
async def crear_movimiento(
    request: Request,
    payload: schemas.MovimientoCajaRequest,
    db: AsyncSession = Depends(get_db),
) -> schemas.MovimientoCajaRead:
    current_user: Usuario = request.state.current_user
    movimiento = await service.registrar_movimiento(
        db=db,
        empresa_id=current_user.empresa_id,
        usuario_id=current_user.id,
        tipo=payload.tipo,
        importe=payload.importe,
        descripcion=payload.descripcion,
    )
    return schemas.MovimientoCajaRead(
        id=movimiento.id,
        caja_id=movimiento.caja_id,
        tipo=movimiento.tipo,
        medio=movimiento.medio,
        importe=movimiento.importe,
        descripcion=movimiento.descripcion,
        fecha=movimiento.fecha,
    )


@router.get(
    "/actual",
    response_model=schemas.CajaActualResponse,
    dependencies=[Depends(require_role("caja:operate"))],
)
async def caja_actual(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> schemas.CajaActualResponse:
    current_user: Usuario = request.state.current_user
    caja, esperado = await service.obtener_caja_abierta_con_esperado(
        db=db, empresa_id=current_user.empresa_id, usuario_id=current_user.id
    )
    return schemas.CajaActualResponse(
        caja=_to_caja_read(caja),
        esperado=_to_esperado_read(esperado),
    )


@router.post(
    "/cierre",
    response_model=schemas.CierreCajaResponse,
    dependencies=[Depends(require_role("caja:operate"))],
)
async def cierre_caja(
    request: Request,
    payload: schemas.CierreCajaRequest,
    db: AsyncSession = Depends(get_db),
) -> schemas.CierreCajaResponse:
    current_user: Usuario = request.state.current_user
    caja, esperado, diferencias = await service.cerrar_caja(
        db=db,
        empresa_id=current_user.empresa_id,
        usuario_id=current_user.id,
        efectivo_real=payload.efectivo_real,
        transferencias_real=payload.transferencias_real,
        tarjetas_real=payload.tarjetas_real,
    )
    return schemas.CierreCajaResponse(
        caja=_to_caja_read(caja),
        esperado=_to_esperado_read(esperado),
        reales=schemas.RealesRead(
            efectivo=caja.efectivo_real,
            transferencias=caja.transferencias_reales,
            tarjetas=caja.tarjetas_reales,
        ),
        diferencias=schemas.DiferenciasRead(
            diferencia_efectivo=diferencias.diferencia_efectivo,
            diferencia_transferencias=diferencias.diferencia_transferencias,
            diferencia_tarjetas=diferencias.diferencia_tarjetas,
            diferencia_total=diferencias.diferencia_total,
            tiene_diferencia=diferencias.tiene_diferencia,
            diferencia_significativa=diferencias.diferencia_significativa,
        ),
    )
