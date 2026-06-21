"""
Gasto service — CRUD operativo de gastos por empresa.

Alertas de gastos elevados: PLACEHOLDER / seam para implementación futura (IN-04).
Cuando se implemente: cargar threshold desde empresa.config['gasto_alerta_threshold']
y comparar con el importe. Por ahora el seam queda como función stub.
"""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from src.modules.gasto.models import Gasto
from src.modules.gasto.schemas import GastoCreate, GastoUpdate
from src.common.exceptions import NotFoundException


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
async def _get_gasto_de_empresa(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    gasto_id: uuid.UUID,
) -> Gasto:
    result = await db.execute(
        select(Gasto).where(Gasto.id == gasto_id, Gasto.empresa_id == empresa_id)
    )
    gasto = result.scalar_one_or_none()
    if not gasto:
        raise NotFoundException("Gasto no encontrado")
    return gasto


# ---------------------------------------------------------------------------
# PLACEHOLDER: alert seam for gastos elevados (IN-04)
# ---------------------------------------------------------------------------
async def _check_alerta_gasto_elevado(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    importe: Decimal,
) -> None:
    """
    TODO (IN-04): Alertas de gastos elevados.
    Implementación pendiente:
      - Cargar threshold desde empresa.config['gasto_alerta_threshold']
      - Si importe > threshold, crear notificación en tabla notificacion
        o enviar evento al sistema de notificaciones.
    Por ahora no hace nada — el seam está acá para facilitar la implementación futura.
    """
    pass


# ---------------------------------------------------------------------------
# Crear gasto
# ---------------------------------------------------------------------------
async def crear_gasto(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    data: GastoCreate,
) -> Gasto:
    now = datetime.utcnow()
    gasto = Gasto(
        empresa_id=empresa_id,
        fecha=data.fecha,
        categoria=data.categoria,
        descripcion=data.descripcion,
        importe=Decimal(str(data.importe)).quantize(Decimal("0.01")),
        medio_pago=data.medio_pago,
        created_at=now,
        updated_at=now,
    )
    db.add(gasto)
    await db.commit()
    await db.refresh(gasto)

    # Seam: check for elevated-gasto alert (IN-04)
    await _check_alerta_gasto_elevado(db, empresa_id, gasto.importe)

    return gasto


# ---------------------------------------------------------------------------
# Listar gastos con filtros
# ---------------------------------------------------------------------------
async def listar_gastos(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    skip: int = 0,
    limit: int = 20,
    categoria: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
) -> tuple[list[Gasto], int]:
    where_clause = [Gasto.empresa_id == empresa_id]

    if categoria:
        where_clause.append(Gasto.categoria == categoria)
    if fecha_desde:
        where_clause.append(Gasto.fecha >= fecha_desde)
    if fecha_hasta:
        where_clause.append(Gasto.fecha <= fecha_hasta)

    count_result = await db.execute(
        select(func.count(Gasto.id)).where(*where_clause)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(Gasto)
        .where(*where_clause)
        .order_by(desc(Gasto.fecha))
        .offset(skip)
        .limit(limit)
    )
    gastos = result.scalars().all()
    return list(gastos), total


# ---------------------------------------------------------------------------
# Obtener gasto por id
# ---------------------------------------------------------------------------
async def obtener_gasto(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    gasto_id: uuid.UUID,
) -> Gasto:
    return await _get_gasto_de_empresa(db, empresa_id, gasto_id)


# ---------------------------------------------------------------------------
# Actualizar gasto
# ---------------------------------------------------------------------------
async def actualizar_gasto(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    gasto_id: uuid.UUID,
    data: GastoUpdate,
) -> Gasto:
    gasto = await _get_gasto_de_empresa(db, empresa_id, gasto_id)

    if data.fecha is not None:
        gasto.fecha = data.fecha
    if data.categoria is not None:
        gasto.categoria = data.categoria
    if data.descripcion is not None:
        gasto.descripcion = data.descripcion
    if data.importe is not None:
        gasto.importe = Decimal(str(data.importe)).quantize(Decimal("0.01"))
    if data.medio_pago is not None:
        gasto.medio_pago = data.medio_pago

    gasto.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(gasto)
    return gasto


# ---------------------------------------------------------------------------
# Eliminar gasto (hard delete — gastos no tienen impacto en stock ni caja)
# ---------------------------------------------------------------------------
async def eliminar_gasto(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    gasto_id: uuid.UUID,
) -> None:
    gasto = await _get_gasto_de_empresa(db, empresa_id, gasto_id)
    await db.delete(gasto)
    await db.commit()
