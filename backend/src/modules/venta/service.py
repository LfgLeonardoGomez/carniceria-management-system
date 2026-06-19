import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from src.modules.venta.models import Venta, DetalleVenta, PagoVenta
from src.modules.venta.schemas import VentaCreate, CobrarVentaRequest
from src.modules.venta import state_machine
from src.modules.producto.models import Producto
from src.modules.cliente.models import Cliente
from src.modules.stock.models import MovimientoStock
from src.modules.stock.service import calcular_stock_actual
from src.modules.caja.models import Caja, MovimientoCaja
from src.modules.cuenta_corriente.models import CuentaCorriente
from src.modules.auditoria.models import Auditoria
from src.modules.auth.models import Usuario
from src.common.exceptions import NotFoundException, ConflictException, ForbiddenException


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _get_venta_de_empresa(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    venta_id: uuid.UUID,
) -> Venta:
    result = await db.execute(
        select(Venta)
        .options(selectinload(Venta.detalles))
        .options(selectinload(Venta.pagos))
        .where(Venta.id == venta_id, Venta.empresa_id == empresa_id)
    )
    venta = result.scalar_one_or_none()
    if not venta:
        raise NotFoundException("Venta no encontrada")
    return venta


async def _load_venta_relaciones(db: AsyncSession, venta: Venta) -> Venta:
    """Carga explícitamente las relaciones de Venta para evitar lazy load en async."""
    result = await db.execute(
        select(Venta)
        .options(selectinload(Venta.detalles))
        .options(selectinload(Venta.pagos))
        .where(Venta.id == venta.id)
    )
    return result.scalar_one()


async def _get_producto_de_empresa(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    producto_id: uuid.UUID,
) -> Producto:
    result = await db.execute(
        select(Producto).where(
            Producto.id == producto_id,
            Producto.empresa_id == empresa_id,
        )
    )
    producto = result.scalar_one_or_none()
    if not producto:
        raise NotFoundException(f"Producto no encontrado: {producto_id}")
    return producto


def _calcular_precio_unitario(producto: Producto, tipo_cliente: str) -> Decimal:
    if tipo_cliente == "mayorista":
        precio = producto.precio_mayorista
    else:
        precio = producto.precio_publico
    return Decimal(str(precio)).quantize(Decimal("0.01"))


def _calcular_totales(items: list[DetalleVenta], descuentos: Decimal) -> tuple[Decimal, Decimal]:
    subtotal = sum(item.importe for item in items)
    subtotal = Decimal(str(subtotal)).quantize(Decimal("0.01"))
    descuentos = Decimal(str(descuentos)).quantize(Decimal("0.01"))
    total = (subtotal - descuentos).quantize(Decimal("0.01"))
    if total < Decimal("0.00"):
        total = Decimal("0.00")
    return subtotal, total


async def _validar_stock_suficiente(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    items: list[DetalleVenta],
) -> None:
    for item in items:
        stock_actual = await calcular_stock_actual(db, empresa_id, item.producto_id)
        if stock_actual < item.cantidad_kilos:
            raise ConflictException(
                f"Stock insuficiente para producto {item.producto_id}: "
                f"disponible {stock_actual}, requerido {item.cantidad_kilos}"
            )


async def _obtener_caja_abierta(
    db: AsyncSession,
    empresa_id: uuid.UUID,
) -> Optional[Caja]:
    result = await db.execute(
        select(Caja).where(
            Caja.empresa_id == empresa_id,
            Caja.estado == "abierta",
        )
    )
    return result.scalar_one_or_none()


async def _registrar_auditoria(
    db: AsyncSession,
    action: str,
    actor_id: uuid.UUID,
    target_empresa_id: uuid.UUID,
    details: str,
) -> None:
    auditoria = Auditoria(
        action=action,
        actor_id=actor_id,
        target_empresa_id=target_empresa_id,
        details=details,
    )
    db.add(auditoria)


# ---------------------------------------------------------------------------
# Crear venta
# ---------------------------------------------------------------------------
async def crear_venta(
    db: AsyncSession,
    current_user: Usuario,
    data: VentaCreate,
) -> Venta:
    empresa_id = current_user.empresa_id

    # Resolver tipo_cliente y validar cliente si existe
    tipo_cliente = "publico_general"
    if data.cliente_id:
        result = await db.execute(
            select(Cliente).where(
                Cliente.id == data.cliente_id,
                Cliente.empresa_id == empresa_id,
            )
        )
        cliente = result.scalar_one_or_none()
        if not cliente:
            raise NotFoundException("Cliente no encontrado")
        tipo_cliente = cliente.tipo_cliente

    # Construir detalles y calcular precios
    detalles: list[DetalleVenta] = []
    for item in data.items:
        producto = await _get_producto_de_empresa(db, empresa_id, item.producto_id)
        precio_unitario = item.precio_unitario
        if precio_unitario is None:
            precio_unitario = _calcular_precio_unitario(producto, tipo_cliente)
        cantidad = Decimal(str(item.cantidad_kilos)).quantize(Decimal("0.001"))
        precio_unitario = Decimal(str(precio_unitario)).quantize(Decimal("0.01"))
        importe = (cantidad * precio_unitario).quantize(Decimal("0.01"))

        detalle = DetalleVenta(
            producto_id=item.producto_id,
            cantidad_kilos=cantidad,
            precio_unitario=precio_unitario,
            importe=importe,
        )
        detalles.append(detalle)

    descuentos = Decimal(str(data.descuentos)).quantize(Decimal("0.01"))
    subtotal, total = _calcular_totales(detalles, descuentos)

    venta = Venta(
        empresa_id=empresa_id,
        cliente_id=data.cliente_id,
        tipo_cliente_al_momento=tipo_cliente,
        estado="en_curso",
        subtotal=subtotal,
        descuentos=descuentos,
        total=total,
        fecha=datetime.utcnow(),
    )
    venta.detalles = detalles

    db.add(venta)
    await db.commit()
    await db.refresh(venta)
    return await _load_venta_relaciones(db, venta)


# ---------------------------------------------------------------------------
# Suspender venta
# ---------------------------------------------------------------------------
async def suspender_venta(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    venta_id: uuid.UUID,
) -> Venta:
    venta = await _get_venta_de_empresa(db, empresa_id, venta_id)
    venta.estado = state_machine.transicionar(venta.estado, "suspendida")
    await db.commit()
    await db.refresh(venta)
    return await _load_venta_relaciones(db, venta)


# ---------------------------------------------------------------------------
# Recuperar venta
# ---------------------------------------------------------------------------
async def recuperar_venta(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    venta_id: uuid.UUID,
) -> Venta:
    venta = await _get_venta_de_empresa(db, empresa_id, venta_id)
    venta.estado = state_machine.transicionar(venta.estado, "en_curso")
    await db.commit()
    await db.refresh(venta)
    return await _load_venta_relaciones(db, venta)


# ---------------------------------------------------------------------------
# Cobrar venta
# ---------------------------------------------------------------------------
async def cobrar_venta(
    db: AsyncSession,
    current_user: Usuario,
    venta_id: uuid.UUID,
    data: CobrarVentaRequest,
) -> Venta:
    empresa_id = current_user.empresa_id
    venta = await _get_venta_de_empresa(db, empresa_id, venta_id)

    # Validar estado
    state_machine.transicionar(venta.estado, "cobrada")

    # Validar medio de pago
    medio_pago = data.medio_pago

    # Validar cuenta corriente requiere cliente
    if medio_pago == "cuenta_corriente" and venta.cliente_id is None:
        raise ConflictException(
            "No se puede cobrar con cuenta corriente sin un cliente asociado"
        )

    # Validar caja abierta (excepto CC según spec)
    if medio_pago != "cuenta_corriente":
        caja_abierta = await _obtener_caja_abierta(db, empresa_id)
        if not caja_abierta:
            raise ConflictException("No hay caja abierta para esta empresa")
        caja = caja_abierta
    else:
        caja = None

    # Validar stock suficiente
    await _validar_stock_suficiente(db, empresa_id, venta.detalles)

    # Procesar stock: crear movimientos y actualizar producto.stock_actual
    for detalle in venta.detalles:
        stock_actual = await calcular_stock_actual(db, empresa_id, detalle.producto_id)
        stock_resultante = (stock_actual - detalle.cantidad_kilos).quantize(Decimal("0.001"))

        movimiento = MovimientoStock(
            empresa_id=empresa_id,
            producto_id=detalle.producto_id,
            tipo="salida_venta",
            cantidad_kilos=-detalle.cantidad_kilos,
            stock_resultante=stock_resultante,
            referencia_tipo="venta",
            referencia_id=str(venta.id),
            operador_id=current_user.id,
            fecha=datetime.utcnow(),
        )
        db.add(movimiento)

        # Actualizar stock_actual del producto
        producto = await _get_producto_de_empresa(db, empresa_id, detalle.producto_id)
        producto.stock_actual = stock_resultante

    # Crear pago
    pago = PagoVenta(
        venta_id=venta.id,
        medio_pago=medio_pago,
        importe=venta.total,
    )
    db.add(pago)

    # Movimiento de caja (excepto CC)
    if caja and medio_pago != "cuenta_corriente":
        mov_caja = MovimientoCaja(
            caja_id=caja.id,
            empresa_id=empresa_id,
            tipo="entrada_venta",
            medio=medio_pago,
            importe=venta.total,
            venta_id=venta.id,
            fecha=datetime.utcnow(),
        )
        db.add(mov_caja)

    # Cuenta corriente
    if medio_pago == "cuenta_corriente":
        result = await db.execute(
            select(Cliente).where(
                Cliente.id == venta.cliente_id,
                Cliente.empresa_id == empresa_id,
            )
        )
        cliente = result.scalar_one()
        nuevo_saldo = (cliente.saldo_actual + venta.total).quantize(Decimal("0.01"))

        cc = CuentaCorriente(
            empresa_id=empresa_id,
            cliente_id=venta.cliente_id,
            tipo="deuda",
            importe=venta.total,
            saldo_resultante=nuevo_saldo,
            venta_id=venta.id,
            fecha=datetime.utcnow(),
        )
        db.add(cc)
        cliente.saldo_actual = nuevo_saldo

    # Cambiar estado
    venta.estado = "cobrada"
    await db.commit()
    await db.refresh(venta)
    return await _load_venta_relaciones(db, venta)


# ---------------------------------------------------------------------------
# Anular venta
# ---------------------------------------------------------------------------
async def anular_venta(
    db: AsyncSession,
    current_user: Usuario,
    venta_id: uuid.UUID,
) -> Venta:
    empresa_id = current_user.empresa_id
    venta = await _get_venta_de_empresa(db, empresa_id, venta_id)

    # Validar estado
    state_machine.transicionar(venta.estado, "anulada")

    # Reversión de stock: crear movimientos de entrada por anulación
    for detalle in venta.detalles:
        stock_actual = await calcular_stock_actual(db, empresa_id, detalle.producto_id)
        stock_resultante = (stock_actual + detalle.cantidad_kilos).quantize(Decimal("0.001"))

        movimiento = MovimientoStock(
            empresa_id=empresa_id,
            producto_id=detalle.producto_id,
            tipo="entrada_anulacion",
            cantidad_kilos=detalle.cantidad_kilos,
            stock_resultante=stock_resultante,
            referencia_tipo="anulacion_venta",
            referencia_id=str(venta.id),
            operador_id=current_user.id,
            fecha=datetime.utcnow(),
        )
        db.add(movimiento)

        producto = await _get_producto_de_empresa(db, empresa_id, detalle.producto_id)
        producto.stock_actual = stock_resultante

    # Reversión de caja: si había movimiento de entrada, crear salida
    result = await db.execute(
        select(MovimientoCaja).where(
            MovimientoCaja.venta_id == venta.id,
            MovimientoCaja.tipo == "entrada_venta",
        )
    )
    mov_caja_original = result.scalar_one_or_none()
    if mov_caja_original:
        mov_caja_reversion = MovimientoCaja(
            caja_id=mov_caja_original.caja_id,
            empresa_id=empresa_id,
            tipo="salida_anulacion",
            medio=mov_caja_original.medio,
            importe=-venta.total,
            venta_id=venta.id,
            fecha=datetime.utcnow(),
        )
        db.add(mov_caja_reversion)

    # Reversión de cuenta corriente
    result = await db.execute(
        select(CuentaCorriente).where(
            CuentaCorriente.venta_id == venta.id,
            CuentaCorriente.tipo == "deuda",
        )
    )
    cc_original = result.scalar_one_or_none()
    if cc_original:
        result = await db.execute(
            select(Cliente).where(
                Cliente.id == cc_original.cliente_id,
                Cliente.empresa_id == empresa_id,
            )
        )
        cliente = result.scalar_one()
        nuevo_saldo = (cliente.saldo_actual - venta.total).quantize(Decimal("0.01"))

        cc_reversion = CuentaCorriente(
            empresa_id=empresa_id,
            cliente_id=cc_original.cliente_id,
            tipo="pago",
            importe=venta.total,
            saldo_resultante=nuevo_saldo,
            venta_id=venta.id,
            fecha=datetime.utcnow(),
        )
        db.add(cc_reversion)
        cliente.saldo_actual = nuevo_saldo

    # Auditoría
    await _registrar_auditoria(
        db,
        action="venta_anulada",
        actor_id=current_user.id,
        target_empresa_id=empresa_id,
        details=f"Venta {venta.id} anulada por usuario {current_user.id}",
    )

    venta.estado = "anulada"
    await db.commit()
    await db.refresh(venta)
    return await _load_venta_relaciones(db, venta)


# ---------------------------------------------------------------------------
# Listar ventas
# ---------------------------------------------------------------------------
async def listar_ventas(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    skip: int = 0,
    limit: int = 20,
    estado: Optional[str] = None,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
) -> tuple[list[Venta], int]:
    where_clause = [Venta.empresa_id == empresa_id]
    if estado:
        where_clause.append(Venta.estado == estado)
    if fecha_desde:
        where_clause.append(Venta.fecha >= fecha_desde)
    if fecha_hasta:
        where_clause.append(Venta.fecha <= fecha_hasta)

    count_result = await db.execute(
        select(func.count(Venta.id)).where(*where_clause)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(Venta)
        .options(selectinload(Venta.detalles))
        .options(selectinload(Venta.pagos))
        .where(*where_clause)
        .order_by(desc(Venta.fecha))
        .offset(skip)
        .limit(limit)
    )
    ventas = result.scalars().all()
    return list(ventas), total


# ---------------------------------------------------------------------------
# Obtener venta
# ---------------------------------------------------------------------------
async def obtener_venta(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    venta_id: uuid.UUID,
) -> Venta:
    return await _get_venta_de_empresa(db, empresa_id, venta_id)
