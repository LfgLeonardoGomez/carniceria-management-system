import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from src.modules.notificacion.models import Notificacion
from src.modules.empresa.models import Empresa
from src.common.exceptions import NotFoundException


async def generar_stock_bajo(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    producto_id: uuid.UUID,
    producto_nombre: str,
    stock_actual: Decimal,
    stock_minimo: Decimal,
) -> Optional[Notificacion]:
    mensaje = (
        f"Stock bajo: {producto_nombre} tiene {stock_actual} kg "
        f"(mínimo {stock_minimo} kg)"
    )
    return await _crear_notificacion(
        db, empresa_id, "stock_bajo", mensaje, "producto", producto_id
    )


async def generar_stock_critico(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    producto_id: uuid.UUID,
    producto_nombre: str,
    stock_actual: Decimal,
) -> Optional[Notificacion]:
    mensaje = (
        f"Stock crítico: {producto_nombre} tiene {stock_actual} kg "
        f"(cero o negativo)"
    )
    return await _crear_notificacion(
        db, empresa_id, "stock_critico", mensaje, "producto", producto_id
    )


async def generar_diferencia_caja(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    caja_id: uuid.UUID,
    diferencia_total: Decimal,
) -> Optional[Notificacion]:
    mensaje = f"Diferencia de caja: {diferencia_total} en cierre de caja"
    return await _crear_notificacion(
        db, empresa_id, "diferencia_caja", mensaje, "caja", caja_id
    )


async def generar_deuda_vencida(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    cuenta_corriente_id: uuid.UUID,
    cliente_nombre: str,
    dias_vencimiento: int,
) -> Optional[Notificacion]:
    if not dias_vencimiento:
        return None
    mensaje = (
        f"Deuda vencida: {cliente_nombre} excede {dias_vencimiento} días"
    )
    return await _crear_notificacion(
        db, empresa_id, "deuda_vencida", mensaje, "cuenta_corriente", cuenta_corriente_id
    )


async def generar_gasto_elevado(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    gasto_id: uuid.UUID,
    importe: Decimal,
    umbral_gasto: Decimal,
) -> Optional[Notificacion]:
    if not umbral_gasto or importe <= umbral_gasto:
        return None
    mensaje = f"Gasto elevado: {importe} supera el umbral {umbral_gasto}"
    return await _crear_notificacion(
        db, empresa_id, "gasto_elevado", mensaje, "gasto", gasto_id
    )


async def _crear_notificacion(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    tipo: str,
    mensaje: str,
    entidad_tipo: str,
    entidad_id: uuid.UUID,
) -> Notificacion:
    notif = Notificacion(
        empresa_id=empresa_id,
        tipo=tipo,
        mensaje=mensaje,
        entidad_tipo=entidad_tipo,
        entidad_id=entidad_id,
    )
    db.add(notif)
    await db.commit()
    await db.refresh(notif)
    return notif


async def listar_notificaciones(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    skip: int = 0,
    limit: int = 20,
    leida: Optional[bool] = None,
) -> tuple[list[Notificacion], int]:
    where_clause = [Notificacion.empresa_id == empresa_id]
    if leida is not None:
        where_clause.append(Notificacion.leida == leida)

    count_result = await db.execute(
        select(func.count(Notificacion.id)).where(*where_clause)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(Notificacion)
        .where(*where_clause)
        .order_by(desc(Notificacion.created_at))
        .offset(skip)
        .limit(limit)
    )
    notifs = result.scalars().all()
    return list(notifs), total


async def marcar_leida(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    notificacion_id: uuid.UUID,
) -> Notificacion:
    result = await db.execute(
        select(Notificacion).where(
            Notificacion.id == notificacion_id,
            Notificacion.empresa_id == empresa_id,
        )
    )
    notif = result.scalar_one_or_none()
    if notif is None:
        raise NotFoundException("Notificación no encontrada")

    notif.leida = True
    notif.fecha_lectura = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(notif)
    return notif
