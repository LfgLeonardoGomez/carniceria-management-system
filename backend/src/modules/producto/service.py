import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from src.modules.producto.models import Producto, CategoriaProducto
from src.common.exceptions import ConflictException, NotFoundException


# ---------------------------------------------------------------------------
# Producto Service
# ---------------------------------------------------------------------------
async def _get_producto_de_empresa(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    producto_id: uuid.UUID,
) -> Producto:
    """Obtiene un producto asegurando que pertenece a la empresa."""
    result = await db.execute(
        select(Producto)
        .options(selectinload(Producto.categoria))
        .where(
            Producto.id == producto_id,
            Producto.empresa_id == empresa_id,
        )
    )
    producto = result.scalar_one_or_none()
    if not producto:
        raise NotFoundException("Producto no encontrado")
    return producto


async def crear_producto(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    plu: str,
    nombre: str,
    categoria_id: Optional[uuid.UUID],
    precio_publico: Decimal,
    precio_mayorista: Decimal,
    costo_por_kilo: Decimal,
    stock_actual: Decimal,
    stock_minimo: Optional[Decimal] = None,
) -> Producto:
    """Crea un nuevo producto, validando PLU único por empresa y calculando margen."""
    # Validar PLU único por empresa (capa de aplicación adicional a la DB constraint)
    existing = await db.execute(
        select(Producto).where(
            Producto.empresa_id == empresa_id,
            Producto.plu == plu,
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictException("PLU ya existe en esta empresa")

    producto = Producto(
        empresa_id=empresa_id,
        plu=plu,
        nombre=nombre,
        categoria_id=categoria_id,
        precio_publico=precio_publico,
        precio_mayorista=precio_mayorista,
        costo_por_kilo=costo_por_kilo,
        stock_actual=stock_actual,
        stock_minimo=stock_minimo,
    )
    producto.recalcular_margen()

    db.add(producto)
    await db.commit()
    await db.refresh(producto)
    return producto


async def listar_productos(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    categoria_id: Optional[uuid.UUID] = None,
    activo: Optional[bool] = True,
) -> tuple[list[Producto], int]:
    """Lista productos de una empresa con filtros, búsqueda y paginación."""
    where_clause = [Producto.empresa_id == empresa_id]
    if activo is not None:
        where_clause.append(Producto.activo == activo)
    if categoria_id is not None:
        where_clause.append(Producto.categoria_id == categoria_id)

    if search:
        # Búsqueda por PLU exacto o nombre parcial (case-insensitive)
        where_clause.append(
            (Producto.plu.ilike(f"%{search}%")) |
            (func.lower(Producto.nombre).contains(func.lower(search)))
        )

    count_result = await db.execute(
        select(func.count(Producto.id)).where(*where_clause)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(Producto)
        .options(selectinload(Producto.categoria))
        .where(*where_clause)
        .order_by(Producto.nombre)
        .offset(skip)
        .limit(limit)
    )
    productos = result.scalars().all()
    return list(productos), total


async def obtener_producto(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    producto_id: uuid.UUID,
) -> Producto:
    """Obtiene un producto por ID verificando empresa."""
    return await _get_producto_de_empresa(db, empresa_id, producto_id)


async def actualizar_producto(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    producto_id: uuid.UUID,
    nombre: Optional[str] = None,
    categoria_id: Optional[uuid.UUID] = None,
    precio_publico: Optional[Decimal] = None,
    precio_mayorista: Optional[Decimal] = None,
    costo_por_kilo: Optional[Decimal] = None,
    stock_actual: Optional[Decimal] = None,
    stock_minimo: Optional[Decimal] = None,
    plu: Optional[str] = None,
) -> Producto:
    """Actualiza un producto y recalcula margen si cambian precio o costo."""
    producto = await _get_producto_de_empresa(db, empresa_id, producto_id)

    if plu is not None and plu != producto.plu:
        existing = await db.execute(
            select(Producto).where(
                Producto.empresa_id == empresa_id,
                Producto.plu == plu,
                Producto.id != producto_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictException("PLU ya existe en esta empresa")
        producto.plu = plu

    if nombre is not None:
        producto.nombre = nombre
    if categoria_id is not None:
        producto.categoria_id = categoria_id
    if precio_publico is not None:
        producto.precio_publico = precio_publico
    if precio_mayorista is not None:
        producto.precio_mayorista = precio_mayorista
    if costo_por_kilo is not None:
        producto.costo_por_kilo = costo_por_kilo
    if stock_actual is not None:
        producto.stock_actual = stock_actual
    if stock_minimo is not None:
        producto.stock_minimo = stock_minimo

    # Recalcular margen si cambió precio o costo
    if precio_publico is not None or costo_por_kilo is not None:
        producto.recalcular_margen()

    await db.commit()
    await db.refresh(producto)
    return producto


async def desactivar_producto(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    producto_id: uuid.UUID,
) -> Producto:
    """Soft-delete: marca producto como inactivo."""
    producto = await _get_producto_de_empresa(db, empresa_id, producto_id)
    producto.activo = False
    await db.commit()
    await db.refresh(producto)
    return producto


async def reactivar_producto(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    producto_id: uuid.UUID,
) -> Producto:
    """Reactiva un producto inactivo."""
    producto = await _get_producto_de_empresa(db, empresa_id, producto_id)
    producto.activo = True
    await db.commit()
    await db.refresh(producto)
    return producto


# ---------------------------------------------------------------------------
# CategoriaProducto Service
# ---------------------------------------------------------------------------
async def _get_categoria_de_empresa(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    categoria_id: uuid.UUID,
) -> CategoriaProducto:
    """Obtiene una categoría asegurando que pertenece a la empresa."""
    result = await db.execute(
        select(CategoriaProducto).where(
            CategoriaProducto.id == categoria_id,
            CategoriaProducto.empresa_id == empresa_id,
        )
    )
    categoria = result.scalar_one_or_none()
    if not categoria:
        raise NotFoundException("Categoría no encontrada")
    return categoria


async def crear_categoria(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    nombre: str,
) -> CategoriaProducto:
    """Crea una categoría validando nombre único por empresa."""
    existing = await db.execute(
        select(CategoriaProducto).where(
            CategoriaProducto.empresa_id == empresa_id,
            func.lower(CategoriaProducto.nombre) == func.lower(nombre),
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictException("Ya existe una categoría con ese nombre en esta empresa")

    categoria = CategoriaProducto(nombre=nombre, empresa_id=empresa_id)
    db.add(categoria)
    await db.commit()
    await db.refresh(categoria)
    return categoria


async def listar_categorias(
    db: AsyncSession,
    empresa_id: uuid.UUID,
) -> list[CategoriaProducto]:
    """Lista categorías de la empresa."""
    result = await db.execute(
        select(CategoriaProducto)
        .where(CategoriaProducto.empresa_id == empresa_id)
        .order_by(CategoriaProducto.nombre)
    )
    return list(result.scalars().all())


async def actualizar_categoria(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    categoria_id: uuid.UUID,
    nombre: str,
) -> CategoriaProducto:
    """Actualiza el nombre de una categoría."""
    categoria = await _get_categoria_de_empresa(db, empresa_id, categoria_id)

    if nombre.lower() != categoria.nombre.lower():
        existing = await db.execute(
            select(CategoriaProducto).where(
                CategoriaProducto.empresa_id == empresa_id,
                func.lower(CategoriaProducto.nombre) == func.lower(nombre),
                CategoriaProducto.id != categoria_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictException("Ya existe una categoría con ese nombre en esta empresa")

    categoria.nombre = nombre
    await db.commit()
    await db.refresh(categoria)
    return categoria


async def eliminar_categoria(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    categoria_id: uuid.UUID,
) -> None:
    """Elimina una categoría solo si no tiene productos asociados."""
    categoria = await _get_categoria_de_empresa(db, empresa_id, categoria_id)

    # Verificar si tiene productos asociados
    productos_result = await db.execute(
        select(func.count(Producto.id)).where(
            Producto.categoria_id == categoria_id,
            Producto.empresa_id == empresa_id,
        )
    )
    count = productos_result.scalar_one()
    if count > 0:
        raise ConflictException("La categoría tiene productos asociados")

    await db.delete(categoria)
    await db.commit()
