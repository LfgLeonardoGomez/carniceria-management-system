import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from src.modules.stock.models import MovimientoStock
from src.modules.producto.models import Producto
from src.modules.notificacion import service as notificacion_service
from src.common.exceptions import NotFoundException, ConflictException


# ---------------------------------------------------------------------------
# Stock Service
# ---------------------------------------------------------------------------
async def _get_producto_de_empresa(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    producto_id: uuid.UUID,
) -> Producto:
    """Obtiene un producto asegurando que pertenece a la empresa."""
    result = await db.execute(
        select(Producto).where(
            Producto.id == producto_id,
            Producto.empresa_id == empresa_id,
        )
    )
    producto = result.scalar_one_or_none()
    if not producto:
        raise NotFoundException("Producto no encontrado")
    return producto


async def calcular_stock_actual(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    producto_id: uuid.UUID,
) -> Decimal:
    """Calcula el stock actual de un producto sumando todos sus movimientos."""
    result = await db.execute(
        select(func.coalesce(func.sum(MovimientoStock.cantidad_kilos), Decimal("0.000"))).where(
            MovimientoStock.empresa_id == empresa_id,
            MovimientoStock.producto_id == producto_id,
        )
    )
    stock = result.scalar_one()
    return Decimal(str(stock)).quantize(Decimal("0.001"))


async def validar_stock_no_negativo(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    producto_id: uuid.UUID,
    cantidad_a_descontar: Decimal,
) -> Decimal:
    """Valida que descontar cantidad_a_descontar no deje stock negativo.
    
    Returns:
        Decimal: stock actual calculado.
    Raises:
        ConflictException: si el resultado seria negativo.
    """
    stock_actual = await calcular_stock_actual(db, empresa_id, producto_id)
    if stock_actual + cantidad_a_descontar < Decimal("0.000"):
        raise ConflictException("Stock insuficiente: el movimiento dejaria stock negativo")
    return stock_actual


async def get_stock_por_producto(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[dict], int]:
    """Devuelve stock actual, stock_minimo y estado para cada producto de la empresa."""
    where_clause = [Producto.empresa_id == empresa_id]

    count_result = await db.execute(
        select(func.count(Producto.id)).where(*where_clause)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(Producto)
        .where(*where_clause)
        .order_by(Producto.nombre)
        .offset(skip)
        .limit(limit)
    )
    productos = result.scalars().all()

    items = []
    for p in productos:
        stock_actual = await calcular_stock_actual(db, empresa_id, p.id)
        stock_minimo = p.stock_minimo or Decimal("0.000")
        if stock_actual <= Decimal("0.000") and stock_minimo > Decimal("0.000"):
            estado = "critico"
        elif stock_actual <= stock_minimo:
            estado = "alerta"
        else:
            estado = "ok"
        items.append({
            "producto_id": p.id,
            "nombre": p.nombre,
            "plu": p.plu,
            "stock_actual": stock_actual,
            "stock_minimo": p.stock_minimo,
            "estado": estado,
        })

    return items, total


async def get_kardex(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    producto_id: uuid.UUID,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[MovimientoStock], int]:
    """Devuelve el kardex paginado de un producto, ordenado por fecha descendente."""
    await _get_producto_de_empresa(db, empresa_id, producto_id)

    count_result = await db.execute(
        select(func.count(MovimientoStock.id)).where(
            MovimientoStock.empresa_id == empresa_id,
            MovimientoStock.producto_id == producto_id,
        )
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(MovimientoStock)
        .where(
            MovimientoStock.empresa_id == empresa_id,
            MovimientoStock.producto_id == producto_id,
        )
        .order_by(desc(MovimientoStock.fecha))
        .offset(skip)
        .limit(limit)
    )
    movimientos = result.scalars().all()
    return list(movimientos), total


async def ajustar_stock(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    producto_id: uuid.UUID,
    cantidad_kilos: Decimal,
    motivo: str,
    operador_id: uuid.UUID,
) -> MovimientoStock:
    """Crea un movimiento de ajuste manual de stock.
    
    Valida que no deje stock negativo si es una salida.
    """
    await _get_producto_de_empresa(db, empresa_id, producto_id)

    stock_actual = await validar_stock_no_negativo(
        db, empresa_id, producto_id, cantidad_kilos
    )
    stock_resultante = stock_actual + cantidad_kilos

    movimiento = MovimientoStock(
        empresa_id=empresa_id,
        producto_id=producto_id,
        tipo="ajuste",
        cantidad_kilos=cantidad_kilos,
        stock_resultante=stock_resultante,
        referencia_tipo="ajuste",
        referencia_id=str(operador_id),
        motivo=motivo,
        operador_id=operador_id,
        fecha=datetime.utcnow(),
    )
    db.add(movimiento)
    await db.commit()
    await db.refresh(movimiento)

    # Trigger notificaciones de stock bajo/crítico
    producto = await _get_producto_de_empresa(db, empresa_id, producto_id)
    stock_minimo = producto.stock_minimo or Decimal("0.000")
    if stock_resultante <= Decimal("0.000"):
        await notificacion_service.generar_stock_critico(
            db, empresa_id, producto_id, producto.nombre, stock_resultante
        )
    elif stock_resultante <= stock_minimo:
        await notificacion_service.generar_stock_bajo(
            db, empresa_id, producto_id, producto.nombre, stock_resultante, stock_minimo
        )

    return movimiento


async def get_alertas(
    db: AsyncSession,
    empresa_id: uuid.UUID,
) -> list[dict]:
    """Lista productos cuyo stock actual es menor o igual al stock minimo."""
    result = await db.execute(
        select(Producto).where(
            Producto.empresa_id == empresa_id,
            Producto.activo == True,
            Producto.stock_minimo != None,
        )
        .order_by(Producto.nombre)
    )
    productos = result.scalars().all()

    alertas = []
    for p in productos:
        stock_actual = await calcular_stock_actual(db, empresa_id, p.id)
        stock_minimo = p.stock_minimo or Decimal("0.000")
        if stock_actual <= stock_minimo:
            if stock_actual <= Decimal("0.000"):
                estado = "critico"
            else:
                estado = "alerta"
            alertas.append({
                "producto_id": p.id,
                "nombre": p.nombre,
                "plu": p.plu,
                "stock_actual": stock_actual,
                "stock_minimo": p.stock_minimo,
                "estado": estado,
            })

    return alertas
