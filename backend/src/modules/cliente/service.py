import uuid
from typing import Optional
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, desc
from sqlalchemy.orm import selectinload

from src.modules.cliente.models import Cliente
from src.modules.cliente.schemas import ClienteCreate, ClienteUpdate
from src.common.exceptions import NotFoundException, ConflictException
from src.modules.auth.models import Usuario


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
async def _get_cliente_de_empresa(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    cliente_id: uuid.UUID,
) -> Cliente:
    """Obtiene un cliente asegurando que pertenece a la empresa."""
    result = await db.execute(
        select(Cliente).where(
            Cliente.id == cliente_id,
            Cliente.empresa_id == empresa_id,
        )
    )
    cliente = result.scalar_one_or_none()
    if not cliente:
        raise NotFoundException("Cliente no encontrado")
    return cliente


async def _check_cuit_unico(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    cuit: Optional[str],
    exclude_id: Optional[uuid.UUID] = None,
) -> None:
    """Verifica que el CUIT no exista para la misma empresa."""
    if not cuit:
        return
    stmt = select(Cliente).where(
        Cliente.empresa_id == empresa_id,
        Cliente.cuit == cuit,
    )
    if exclude_id:
        stmt = stmt.where(Cliente.id != exclude_id)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise ConflictException("El CUIT ya está registrado para esta empresa")


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------
async def create_cliente(
    db: AsyncSession,
    current_user: Usuario,
    data: ClienteCreate,
) -> Cliente:
    """Crea un nuevo cliente en la empresa del usuario autenticado."""
    await _check_cuit_unico(db, current_user.empresa_id, data.cuit)

    cliente = Cliente(
        empresa_id=current_user.empresa_id,
        nombre=data.nombre,
        apellido=data.apellido,
        razon_social=data.razon_social,
        cuit=data.cuit,
        telefono=data.telefono,
        email=data.email,
        direccion=data.direccion,
        tipo_cliente=data.tipo_cliente,
        limite_cuenta_corriente=data.limite_cuenta_corriente or Decimal("0.0000"),
        saldo_actual=Decimal("0.0000"),
        activo=True,
    )
    db.add(cliente)
    await db.commit()
    await db.refresh(cliente)
    return cliente


async def update_cliente(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    cliente_id: uuid.UUID,
    data: ClienteUpdate,
) -> Cliente:
    """Actualiza los datos de un cliente."""
    cliente = await _get_cliente_de_empresa(db, empresa_id, cliente_id)

    if data.cuit is not None and data.cuit != cliente.cuit:
        await _check_cuit_unico(db, empresa_id, data.cuit, exclude_id=cliente_id)
        cliente.cuit = data.cuit

    if data.nombre is not None:
        cliente.nombre = data.nombre
    if data.apellido is not None:
        cliente.apellido = data.apellido
    if data.razon_social is not None:
        cliente.razon_social = data.razon_social
    if data.telefono is not None:
        cliente.telefono = data.telefono
    if data.email is not None:
        cliente.email = data.email
    if data.direccion is not None:
        cliente.direccion = data.direccion
    if data.tipo_cliente is not None:
        cliente.tipo_cliente = data.tipo_cliente
    if data.limite_cuenta_corriente is not None:
        cliente.limite_cuenta_corriente = data.limite_cuenta_corriente

    await db.commit()
    await db.refresh(cliente)
    return cliente


async def soft_delete_cliente(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    cliente_id: uuid.UUID,
) -> Cliente:
    """Desactiva un cliente (soft delete)."""
    cliente = await _get_cliente_de_empresa(db, empresa_id, cliente_id)
    cliente.activo = False
    await db.commit()
    await db.refresh(cliente)
    return cliente


async def get_cliente_by_id(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    cliente_id: uuid.UUID,
) -> Cliente:
    """Obtiene un cliente por ID dentro de la empresa."""
    return await _get_cliente_de_empresa(db, empresa_id, cliente_id)


async def list_clientes(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    skip: int = 0,
    limit: int = 20,
    tipo_cliente: Optional[str] = None,
    q: Optional[str] = None,
    activo: Optional[bool] = None,
) -> tuple[list[Cliente], int]:
    """Lista clientes de una empresa con filtros y paginación."""
    where_clause = [Cliente.empresa_id == empresa_id]
    if tipo_cliente is not None:
        where_clause.append(Cliente.tipo_cliente == tipo_cliente)
    if activo is not None:
        where_clause.append(Cliente.activo == activo)
    if q:
        search = f"%{q}%"
        where_clause.append(
            or_(
                Cliente.nombre.ilike(search),
                Cliente.apellido.ilike(search),
                Cliente.razon_social.ilike(search),
                Cliente.cuit.ilike(search),
            )
        )

    count_result = await db.execute(
        select(func.count(Cliente.id)).where(*where_clause)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(Cliente)
        .where(*where_clause)
        .offset(skip)
        .limit(limit)
        .order_by(desc(Cliente.created_at))
    )
    clientes = result.scalars().all()
    return list(clientes), total


async def search_clientes(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    q: str,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[Cliente], int]:
    """Busca clientes por nombre, apellido, razón social o CUIT."""
    return await list_clientes(db, empresa_id, skip=skip, limit=limit, q=q)


async def get_historial(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    cliente_id: uuid.UUID,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list, int]:
    """Obtiene el historial de compras de un cliente.

    Si la tabla venta no existe, retorna lista vacía y marca como deferred.
    """
    # Verificar que el cliente existe y pertenece a la empresa
    await _get_cliente_de_empresa(db, empresa_id, cliente_id)

    # Import inline to avoid circular dependency if venta module is not ready
    try:
        from src.modules.venta.models import Venta
    except ImportError:
        return [], 0

    try:
        from sqlalchemy import inspect as sa_inspect
        inspector = await db.run_sync(lambda sync_conn: sa_inspect(sync_conn).has_table("venta"))
        if not inspector:
            return [], 0
    except Exception:
        return [], 0

    where_clause = [
        Venta.cliente_id == cliente_id,
        Venta.empresa_id == empresa_id,
    ]

    count_result = await db.execute(
        select(func.count(Venta.id)).where(*where_clause)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(Venta)
        .where(*where_clause)
        .offset(skip)
        .limit(limit)
        .order_by(desc(Venta.fecha))
    )
    ventas = result.scalars().all()
    return list(ventas), total
