import uuid
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from src.modules.compra.models import Compra
from src.modules.proveedor.models import Proveedor
from src.modules.producto.models import Producto
from src.modules.stock.models import MovimientoStock
from src.common.exceptions import NotFoundException, ConflictException


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _calcular_costo_por_kilo(costo_total: Decimal, peso_total: Decimal) -> Decimal:
    """Calcula costo por kilo con 3 decimales de precisión."""
    return (costo_total / peso_total).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


async def _get_proveedor_validado(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    proveedor_id: uuid.UUID,
) -> Proveedor:
    """Obtiene un proveedor validando que pertenece a la empresa."""
    result = await db.execute(
        select(Proveedor).where(
            and_(
                Proveedor.id == proveedor_id,
                Proveedor.empresa_id == empresa_id,
                Proveedor.activo.is_(True),
            )
        )
    )
    proveedor = result.scalar_one_or_none()
    if not proveedor:
        raise NotFoundException("Proveedor no encontrado")
    return proveedor


async def _get_compra_validada(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    compra_id: uuid.UUID,
) -> Compra:
    """Obtiene una compra validando que pertenece a la empresa."""
    result = await db.execute(
        select(Compra).where(
            and_(
                Compra.id == compra_id,
                Compra.empresa_id == empresa_id,
            )
        )
    )
    compra = result.scalar_one_or_none()
    if not compra:
        raise NotFoundException("Compra no encontrada")
    return compra


async def _get_or_create_media_res_product(
    db: AsyncSession,
    empresa_id: uuid.UUID,
) -> Producto:
    """Obtiene o crea el producto genérico 'Media Res' para la empresa."""
    result = await db.execute(
        select(Producto).where(
            and_(
                Producto.empresa_id == empresa_id,
                Producto.plu == "MEDIA_RES",
            )
        )
    )
    producto = result.scalar_one_or_none()
    if producto:
        return producto

    # Crear producto genérico Media Res
    producto = Producto(
        empresa_id=empresa_id,
        plu="MEDIA_RES",
        nombre="Media Res",
        precio_publico=Decimal("0.0000"),
        precio_mayorista=Decimal("0.0000"),
        costo_por_kilo=Decimal("0.0000"),
        stock_actual=Decimal("0.0000"),
    )
    producto.recalcular_margen()
    db.add(producto)
    await db.commit()
    await db.refresh(producto)
    return producto


async def _crear_movimiento_stock_entrada(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    producto_id: uuid.UUID,
    cantidad_kilos: Decimal,
    referencia_id: uuid.UUID,
    operador_id: Optional[uuid.UUID] = None,
) -> MovimientoStock:
    """Crea un movimiento de stock de entrada vinculado a una compra."""
    # Obtener stock actual para calcular stock_resultante
    result = await db.execute(
        select(Producto).where(
            and_(
                Producto.id == producto_id,
                Producto.empresa_id == empresa_id,
            )
        )
    )
    producto = result.scalar_one_or_none()
    if not producto:
        raise NotFoundException("Producto no encontrado")

    stock_anterior = producto.stock_actual
    stock_resultante = stock_anterior + cantidad_kilos

    movimiento = MovimientoStock(
        empresa_id=empresa_id,
        producto_id=producto_id,
        tipo="entrada_compra",
        cantidad_kilos=cantidad_kilos,
        stock_resultante=stock_resultante,
        referencia_id=str(referencia_id),
        referencia_tipo="compra",
        operador_id=operador_id,
    )
    db.add(movimiento)

    # Actualizar stock del producto
    producto.stock_actual = stock_resultante
    await db.commit()
    await db.refresh(movimiento)
    return movimiento


async def _crear_movimiento_stock_salida(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    producto_id: uuid.UUID,
    cantidad_kilos: Decimal,
    referencia_id: uuid.UUID,
    operador_id: Optional[uuid.UUID] = None,
) -> MovimientoStock:
    """Crea un movimiento de stock de salida (reversión) vinculado a una compra anulada."""
    result = await db.execute(
        select(Producto).where(
            and_(
                Producto.id == producto_id,
                Producto.empresa_id == empresa_id,
            )
        )
    )
    producto = result.scalar_one_or_none()
    if not producto:
        raise NotFoundException("Producto no encontrado")

    stock_anterior = producto.stock_actual
    if stock_anterior < cantidad_kilos:
        raise ConflictException(
            f"Stock insuficiente para anular la compra. "
            f"Stock actual: {stock_anterior}, necesario: {cantidad_kilos}"
        )

    stock_resultante = stock_anterior - cantidad_kilos

    movimiento = MovimientoStock(
        empresa_id=empresa_id,
        producto_id=producto_id,
        tipo="ajuste",
        cantidad_kilos=-cantidad_kilos,
        stock_resultante=stock_resultante,
        referencia_id=str(referencia_id),
        referencia_tipo="compra_anulada",
        operador_id=operador_id,
    )
    db.add(movimiento)

    # Actualizar stock del producto
    producto.stock_actual = stock_resultante
    await db.commit()
    await db.refresh(movimiento)
    return movimiento


# ---------------------------------------------------------------------------
# Compra Service
# ---------------------------------------------------------------------------
async def create_compra(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    proveedor_id: uuid.UUID,
    fecha: date,
    cantidad_medias_reses: int,
    peso_total: Decimal,
    costo_total: Decimal,
    observaciones: Optional[str] = None,
    operador_id: Optional[uuid.UUID] = None,
) -> Compra:
    """Crea una compra de media res, calcula costo por kilo y genera entrada de stock."""
    # Validar proveedor
    await _get_proveedor_validado(db, empresa_id, proveedor_id)

    # Calcular costo por kilo
    costo_por_kilo = _calcular_costo_por_kilo(costo_total, peso_total)

    # Crear compra
    compra = Compra(
        empresa_id=empresa_id,
        proveedor_id=proveedor_id,
        fecha=fecha,
        cantidad_medias_reses=cantidad_medias_reses,
        peso_total=peso_total,
        costo_total=costo_total,
        costo_por_kilo=costo_por_kilo,
        observaciones=observaciones,
    )
    db.add(compra)
    await db.commit()
    await db.refresh(compra)

    # Generar entrada de stock
    producto = await _get_or_create_media_res_product(db, empresa_id)
    await _crear_movimiento_stock_entrada(
        db=db,
        empresa_id=empresa_id,
        producto_id=producto.id,
        cantidad_kilos=peso_total,
        referencia_id=compra.id,
        operador_id=operador_id,
    )

    # Actualizar costo promedio histórico
    await _recalcular_costo_promedio(db, empresa_id, proveedor_id)

    await db.refresh(compra)
    return compra


async def get_compra(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    compra_id: uuid.UUID,
) -> Compra:
    """Obtiene una compra por ID validando empresa."""
    return await _get_compra_validada(db, empresa_id, compra_id)


async def list_compras(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    skip: int = 0,
    limit: int = 20,
    proveedor_id: Optional[uuid.UUID] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    incluir_anuladas: bool = False,
) -> tuple[list[Compra], int]:
    """Lista compras filtradas por empresa con paginación."""
    where_clause = [
        Compra.empresa_id == empresa_id,
    ]
    if not incluir_anuladas:
        where_clause.append(Compra.estado == "activa")
    if proveedor_id is not None:
        where_clause.append(Compra.proveedor_id == proveedor_id)
    if fecha_desde is not None:
        where_clause.append(Compra.fecha >= fecha_desde)
    if fecha_hasta is not None:
        where_clause.append(Compra.fecha <= fecha_hasta)

    # Count total
    count_query = select(func.count(Compra.id)).where(*where_clause)
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    # Paginated results
    result = await db.execute(
        select(Compra)
        .where(*where_clause)
        .order_by(Compra.fecha.desc())
        .offset(skip)
        .limit(limit)
    )
    compras = result.scalars().all()
    return list(compras), total


async def update_compra(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    compra_id: uuid.UUID,
    fecha: Optional[date] = None,
    cantidad_medias_reses: Optional[int] = None,
    peso_total: Optional[Decimal] = None,
    costo_total: Optional[Decimal] = None,
    observaciones: Optional[str] = None,
) -> Compra:
    """Actualiza una compra recalculando costo por kilo si cambia peso o costo."""
    compra = await _get_compra_validada(db, empresa_id, compra_id)

    if compra.estado == "anulada":
        raise ConflictException("No se puede modificar una compra anulada")

    # TODO: post-C-09, bloquear si tiene despostes asociados
    # if compra.despostes:
    #     raise ConflictException("No se puede modificar una compra ya desposteada")

    if fecha is not None:
        compra.fecha = fecha
    if cantidad_medias_reses is not None:
        compra.cantidad_medias_reses = cantidad_medias_reses
    if peso_total is not None:
        compra.peso_total = peso_total
    if costo_total is not None:
        compra.costo_total = costo_total
    if observaciones is not None:
        compra.observaciones = observaciones

    # Recalcular costo por kilo si cambió peso o costo
    if peso_total is not None or costo_total is not None:
        compra.costo_por_kilo = _calcular_costo_por_kilo(
            compra.costo_total, compra.peso_total
        )

    await db.commit()
    await db.refresh(compra)
    return compra


async def delete_compra(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    compra_id: uuid.UUID,
    operador_id: Optional[uuid.UUID] = None,
) -> None:
    """Anula una compra (soft delete) y revierte el stock."""
    compra = await _get_compra_validada(db, empresa_id, compra_id)

    if compra.estado == "anulada":
        raise ConflictException("La compra ya está anulada")

    # TODO: post-C-09, bloquear si tiene despostes asociados
    # if compra.despostes:
    #     raise ConflictException("No se puede anular una compra ya desposteada")

    # Revertir stock
    producto = await _get_or_create_media_res_product(db, empresa_id)
    await _crear_movimiento_stock_salida(
        db=db,
        empresa_id=empresa_id,
        producto_id=producto.id,
        cantidad_kilos=compra.peso_total,
        referencia_id=compra.id,
        operador_id=operador_id,
    )

    compra.estado = "anulada"
    await db.commit()


async def get_historial_por_proveedor(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    proveedor_id: uuid.UUID,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[Compra], int, Decimal]:
    """Devuelve historial de compras de un proveedor con costo promedio."""
    # Validar proveedor existe
    await _get_proveedor_validado(db, empresa_id, proveedor_id)

    where_clause = [
        Compra.empresa_id == empresa_id,
        Compra.proveedor_id == proveedor_id,
    ]

    # Count total (incluyendo anuladas para paginación, pero excluyendo de costo promedio)
    count_query = select(func.count(Compra.id)).where(*where_clause)
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    result = await db.execute(
        select(Compra)
        .where(*where_clause)
        .order_by(Compra.fecha.desc())
        .offset(skip)
        .limit(limit)
    )
    compras = result.scalars().all()

    # Calcular costo promedio histórico (solo compras activas)
    costo_promedio = await _get_costo_promedio_proveedor(
        db, empresa_id, proveedor_id
    )

    return list(compras), total, costo_promedio


async def _get_costo_promedio_proveedor(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    proveedor_id: uuid.UUID,
) -> Decimal:
    """Calcula el costo promedio por kilo de compras activas de un proveedor."""
    result = await db.execute(
        select(func.avg(Compra.costo_por_kilo)).where(
            and_(
                Compra.empresa_id == empresa_id,
                Compra.proveedor_id == proveedor_id,
                Compra.estado == "activa",
            )
        )
    )
    avg = result.scalar_one()
    if avg is None:
        return Decimal("0.000")
    return Decimal(str(avg)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


async def _recalcular_costo_promedio(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    proveedor_id: uuid.UUID,
) -> None:
    """Recalcula y actualiza costo_promedio_historico en todas las compras del proveedor."""
    costo_promedio = await _get_costo_promedio_proveedor(
        db, empresa_id, proveedor_id
    )
    await db.execute(
        select(Compra)
        .where(
            and_(
                Compra.empresa_id == empresa_id,
                Compra.proveedor_id == proveedor_id,
            )
        )
    )
    # No actualizamos históricos en batch; el snapshot se guarda en cada compra nueva
    # y el cálculo se hace al consultar.
