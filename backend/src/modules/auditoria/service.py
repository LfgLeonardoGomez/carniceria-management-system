import uuid
from datetime import datetime, timezone, date, time
from typing import Optional, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from src.modules.auditoria.models import Auditoria
from src.common.exceptions import ForbiddenException


async def registrar(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    usuario_id: Optional[uuid.UUID],
    accion: str,
    entidad_tipo: str,
    entidad_id: Optional[uuid.UUID],
    payload: Optional[dict[str, Any]],
) -> Auditoria:
    """Registra una operación en auditoría de forma inmutable."""
    now = datetime.now(timezone.utc)
    registro = Auditoria(
        empresa_id=empresa_id,
        usuario_id=usuario_id,
        accion=accion,
        entidad_tipo=entidad_tipo,
        entidad_id=entidad_id,
        payload=payload,
        fecha=now.date(),
        hora=now.time(),
        created_at=now,
    )
    db.add(registro)
    await db.commit()
    await db.refresh(registro)
    return registro


async def listar_auditoria(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    skip: int = 0,
    limit: int = 20,
    usuario_id: Optional[uuid.UUID] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    accion: Optional[str] = None,
    entidad_tipo: Optional[str] = None,
) -> tuple[list[Auditoria], int]:
    """Lista registros de auditoría paginados y filtrados para una empresa."""
    where_clause = [Auditoria.empresa_id == empresa_id]

    if usuario_id:
        where_clause.append(Auditoria.usuario_id == usuario_id)
    if fecha_desde:
        where_clause.append(Auditoria.fecha >= fecha_desde)
    if fecha_hasta:
        where_clause.append(Auditoria.fecha <= fecha_hasta)
    if accion:
        where_clause.append(Auditoria.accion == accion)
    if entidad_tipo:
        where_clause.append(Auditoria.entidad_tipo == entidad_tipo)

    count_result = await db.execute(
        select(func.count(Auditoria.id)).where(*where_clause)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(Auditoria)
        .where(*where_clause)
        .order_by(desc(Auditoria.created_at))
        .offset(skip)
        .limit(limit)
    )
    registros = result.scalars().all()
    return list(registros), total
