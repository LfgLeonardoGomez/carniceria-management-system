import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from src.modules.proveedor.models import Proveedor
from src.common.exceptions import NotFoundException, ConflictException


async def create(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    nombre: str,
    cuit: Optional[str] = None,
    telefono: Optional[str] = None,
    email: Optional[str] = None,
    direccion: Optional[str] = None,
) -> Proveedor:
    if cuit is not None:
        existing = await _get_by_cuit(db, empresa_id, cuit)
        if existing:
            raise ConflictException("CUIT ya registrado para esta empresa")

    proveedor = Proveedor(
        empresa_id=empresa_id,
        nombre=nombre,
        cuit=cuit,
        telefono=telefono,
        email=email,
        direccion=direccion,
    )
    db.add(proveedor)
    await db.commit()
    await db.refresh(proveedor)
    return proveedor


async def get_by_id(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    proveedor_id: uuid.UUID,
) -> Proveedor:
    result = await db.execute(
        select(Proveedor).where(
            and_(
                Proveedor.id == proveedor_id,
                Proveedor.empresa_id == empresa_id,
            )
        )
    )
    proveedor: Optional[Proveedor] = result.scalar_one_or_none()
    if not proveedor:
        raise NotFoundException("Proveedor no encontrado")
    return proveedor


async def list_by_empresa(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    skip: int = 0,
    limit: int = 20,
    nombre: Optional[str] = None,
    incluir_inactivos: bool = False,
) -> tuple[list[Proveedor], int]:
    base_query = select(Proveedor).where(Proveedor.empresa_id == empresa_id)

    if not incluir_inactivos:
        base_query = base_query.where(Proveedor.activo.is_(True))

    if nombre:
        base_query = base_query.where(Proveedor.nombre.ilike(f"%{nombre}%"))

    # Count total
    count_query = select(func.count()).select_from(base_query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Paginated results
    result = await db.execute(
        base_query.order_by(Proveedor.nombre).offset(skip).limit(limit)
    )
    proveedores = result.scalars().all()
    return list(proveedores), total


async def update(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    proveedor_id: uuid.UUID,
    nombre: Optional[str] = None,
    cuit: Optional[str] = None,
    telefono: Optional[str] = None,
    email: Optional[str] = None,
    direccion: Optional[str] = None,
) -> Proveedor:
    proveedor = await get_by_id(db, empresa_id, proveedor_id)

    if cuit is not None and cuit != proveedor.cuit:
        existing = await _get_by_cuit(db, empresa_id, cuit)
        if existing and existing.id != proveedor.id:
            raise ConflictException("CUIT ya registrado para esta empresa")
        proveedor.cuit = cuit

    if nombre is not None:
        proveedor.nombre = nombre
    if telefono is not None:
        proveedor.telefono = telefono
    if email is not None:
        proveedor.email = email
    if direccion is not None:
        proveedor.direccion = direccion

    await db.commit()
    await db.refresh(proveedor)
    return proveedor


async def delete_logic(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    proveedor_id: uuid.UUID,
) -> None:
    proveedor = await get_by_id(db, empresa_id, proveedor_id)
    proveedor.activo = False
    await db.commit()


async def _get_by_cuit(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    cuit: str,
) -> Optional[Proveedor]:
    result = await db.execute(
        select(Proveedor).where(
            and_(
                Proveedor.empresa_id == empresa_id,
                Proveedor.cuit == cuit,
                Proveedor.activo.is_(True),
            )
        )
    )
    return result.scalar_one_or_none()
