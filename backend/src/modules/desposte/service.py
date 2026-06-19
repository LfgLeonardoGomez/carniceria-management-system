import uuid
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from src.modules.desposte.models import Desposte, CorteDesposte
from src.modules.compra.models import Compra
from src.modules.auth.models import Usuario
from src.modules.producto.models import Producto
from src.modules.stock.models import MovimientoStock
from src.common.exceptions import NotFoundException, ConflictException, BasileException

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TIPOS_CORTE_VALIDOS = frozenset([
    "asado", "vacio", "nalga", "cuadril", "peceto",
    "bola_de_lomo", "lomo", "matambre", "costilla",
    "osobuco", "molida", "otros",
])

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _calcular_costo_asignado(kilos_obtenidos: Decimal, costo_total: Decimal, peso_total: Decimal) -> Decimal:
    """Calcula costo asignado proporcional al peso del corte."""
    if peso_total == 0:
        return Decimal("0.00")
    return (costo_total / peso_total * kilos_obtenidos).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _calcular_costo_final_por_kilo(costo_asignado: Decimal, kilos_obtenidos: Decimal) -> Decimal:
    """Calcula costo final por kilo del corte."""
    if kilos_obtenidos == 0:
        return Decimal("0.00")
    return (costo_asignado / kilos_obtenidos).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _calcular_porcentaje_rendimiento(kilos_obtenidos: Decimal, peso_total: Decimal) -> Decimal:
    """Calcula porcentaje de rendimiento del corte sobre el peso total de la compra."""
    if peso_total == 0:
        return Decimal("0.000")
    return (kilos_obtenidos / peso_total * 100).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


async def _get_compra_validada(db: AsyncSession, empresa_id: uuid.UUID, compra_id: uuid.UUID) -> Compra:
    """Obtiene una compra validando que pertenece a la empresa."""
    result = await db.execute(
        select(Compra).where(
            and_(
                Compra.id == compra_id,
                Compra.empresa_id == empresa_id,
                Compra.estado == "activa",
            )
        )
    )
    compra = result.scalar_one_or_none()
    if not compra:
        raise NotFoundException("Compra no encontrada")
    return compra


async def _get_usuario_validado(db: AsyncSession, empresa_id: uuid.UUID, usuario_id: uuid.UUID) -> Usuario:
    """Obtiene un usuario validando que pertenece a la empresa."""
    result = await db.execute(
        select(Usuario).where(
            and_(
                Usuario.id == usuario_id,
                Usuario.empresa_id == empresa_id,
                Usuario.activo.is_(True),
            )
        )
    )
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise NotFoundException("Operador no encontrado")
    return usuario


async def _get_desposte_validado(db: AsyncSession, desposte_id: uuid.UUID, empresa_id: uuid.UUID) -> Desposte:
    """Obtiene un desposte validando que pertenece a la empresa."""
    result = await db.execute(
        select(Desposte).where(
            and_(
                Desposte.id == desposte_id,
                Desposte.empresa_id == empresa_id,
            )
        )
    )
    desposte = result.scalar_one_or_none()
    if not desposte:
        raise NotFoundException("Desposte no encontrado")
    return desposte


async def _get_desposte_con_cortes(db: AsyncSession, desposte_id: uuid.UUID, empresa_id: uuid.UUID) -> Desposte:
    """Obtiene un desposte con cortes cargados."""
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Desposte)
        .options(selectinload(Desposte.cortes))
        .where(
            and_(
                Desposte.id == desposte_id,
                Desposte.empresa_id == empresa_id,
            )
        )
    )
    desposte = result.scalar_one_or_none()
    if not desposte:
        raise NotFoundException("Desposte no encontrado")
    return desposte


# ---------------------------------------------------------------------------
# Desposte Service
# ---------------------------------------------------------------------------
async def crear_desposte(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    compra_id: uuid.UUID,
    fecha: date,
    operador_id: uuid.UUID,
) -> Desposte:
    """Crea un desposte en estado 'en_proceso' vinculado a una compra."""
    # Validar compra y operador
    await _get_compra_validada(db, empresa_id, compra_id)
    await _get_usuario_validado(db, empresa_id, operador_id)

    desposte = Desposte(
        empresa_id=empresa_id,
        compra_id=compra_id,
        fecha=fecha,
        operador_id=operador_id,
        estado="en_proceso",
        rendimiento_total=Decimal("0.000"),
        merma=Decimal("0.000"),
    )
    db.add(desposte)
    await db.commit()
    await db.refresh(desposte)
    return desposte


async def agregar_corte(
    db: AsyncSession,
    desposte_id: uuid.UUID,
    empresa_id: uuid.UUID,
    tipo_corte: str,
    kilos_obtenidos: Decimal,
    producto_id: Optional[uuid.UUID] = None,
) -> CorteDesposte:
    """Agrega o actualiza un corte al desposte en estado 'en_proceso'."""
    # Validar tipo de corte
    if tipo_corte not in TIPOS_CORTE_VALIDOS:
        raise BasileException(f"Tipo de corte no válido: {tipo_corte}", status_code=422)

    if kilos_obtenidos <= 0:
        raise BasileException("Los kilos obtenidos deben ser mayores a cero", status_code=422)

    # Obtener desposte con cortes
    desposte = await _get_desposte_con_cortes(db, desposte_id, empresa_id)

    if desposte.estado != "en_proceso":
        raise ConflictException("No se pueden agregar cortes a un desposte finalizado")

    # Validar producto si se proporciona
    if producto_id is not None:
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

    # Buscar corte existente del mismo tipo
    corte_existente = None
    for c in desposte.cortes:
        if c.tipo_corte == tipo_corte:
            corte_existente = c
            break

    # Obtener compra para cálculos
    compra = await _get_compra_validada(db, empresa_id, desposte.compra_id)

    # Calcular costos
    costo_asignado = _calcular_costo_asignado(kilos_obtenidos, compra.costo_total, compra.peso_total)
    costo_final_por_kilo = _calcular_costo_final_por_kilo(costo_asignado, kilos_obtenidos)
    porcentaje_rendimiento = _calcular_porcentaje_rendimiento(kilos_obtenidos, compra.peso_total)

    if corte_existente:
        # Actualizar corte existente (upsert)
        corte_existente.kilos_obtenidos = kilos_obtenidos
        corte_existente.costo_asignado = costo_asignado
        corte_existente.costo_final_por_kilo = costo_final_por_kilo
        corte_existente.porcentaje_rendimiento = porcentaje_rendimiento
        corte_existente.producto_id = producto_id
        corte = corte_existente
    else:
        # Crear nuevo corte
        corte = CorteDesposte(
            desposte_id=desposte_id,
            tipo_corte=tipo_corte,
            kilos_obtenidos=kilos_obtenidos,
            porcentaje_rendimiento=porcentaje_rendimiento,
            costo_asignado=costo_asignado,
            costo_final_por_kilo=costo_final_por_kilo,
            producto_id=producto_id,
        )
        db.add(corte)

    # Recalcular rendimiento_total del desposte
    await db.flush()
    await db.refresh(desposte)
    # Recargar cortes
    result = await db.execute(
        select(CorteDesposte).where(CorteDesposte.desposte_id == desposte_id)
    )
    cortes = result.scalars().all()
    rendimiento_total = sum(c.kilos_obtenidos for c in cortes)
    desposte.rendimiento_total = rendimiento_total.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)

    await db.commit()
    await db.refresh(corte)
    return corte


async def finalizar_desposte(
    db: AsyncSession,
    desposte_id: uuid.UUID,
    empresa_id: uuid.UUID,
    operador_id: uuid.UUID,
) -> Desposte:
    """Finaliza un desposte: valida, calcula merma, asigna costos, genera stock, registra auditoría."""
    desposte = await _get_desposte_con_cortes(db, desposte_id, empresa_id)

    if desposte.estado == "finalizado":
        raise ConflictException("El desposte ya está finalizado")

    if not desposte.cortes:
        raise BasileException("El desposte debe tener al menos un corte", status_code=422)

    # Obtener compra
    compra = await _get_compra_validada(db, empresa_id, desposte.compra_id)

    # Recalcular rendimiento_total y validar
    rendimiento_total = sum(c.kilos_obtenidos for c in desposte.cortes)
    rendimiento_total = rendimiento_total.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
    desposte.rendimiento_total = rendimiento_total

    if rendimiento_total > compra.peso_total:
        raise BasileException(
            "El rendimiento total no puede superar el peso de la compra",
            status_code=422,
        )

    # Calcular merma
    merma = (compra.peso_total - rendimiento_total).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
    desposte.merma = merma

    # Recalcular costos de todos los cortes (por si cambió algo)
    for corte in desposte.cortes:
        corte.costo_asignado = _calcular_costo_asignado(corte.kilos_obtenidos, compra.costo_total, compra.peso_total)
        corte.costo_final_por_kilo = _calcular_costo_final_por_kilo(corte.costo_asignado, corte.kilos_obtenidos)
        corte.porcentaje_rendimiento = _calcular_porcentaje_rendimiento(corte.kilos_obtenidos, compra.peso_total)

    # Generar stock
    movimientos = await _generar_stock_desposte(db, empresa_id, desposte, operador_id)

    # Cambiar estado
    desposte.estado = "finalizado"

    # Registrar auditoría
    await _registrar_auditoria_desposte(db, desposte, operador_id)

    await db.commit()
    await db.refresh(desposte)
    return desposte


async def _generar_stock_desposte(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    desposte: Desposte,
    operador_id: uuid.UUID,
) -> list[MovimientoStock]:
    """Genera MovimientoStock tipo entrada_desposte por cada corte con producto."""
    movimientos = []
    for corte in desposte.cortes:
        if corte.producto_id is None:
            continue

        # Obtener producto
        result = await db.execute(
            select(Producto).where(
                and_(
                    Producto.id == corte.producto_id,
                    Producto.empresa_id == empresa_id,
                )
            )
        )
        producto = result.scalar_one_or_none()
        if not producto:
            continue

        stock_anterior = producto.stock_actual
        stock_resultante = stock_anterior + corte.kilos_obtenidos

        movimiento = MovimientoStock(
            empresa_id=empresa_id,
            producto_id=corte.producto_id,
            tipo="entrada_desposte",
            cantidad_kilos=corte.kilos_obtenidos,
            stock_resultante=stock_resultante,
            referencia_id=str(desposte.id),
            referencia_tipo="desposte",
            operador_id=operador_id,
        )
        db.add(movimiento)
        producto.stock_actual = stock_resultante
        movimientos.append(movimiento)

    return movimientos


async def _registrar_auditoria_desposte(
    db: AsyncSession,
    desposte: Desposte,
    operador_id: uuid.UUID,
) -> None:
    """Registra auditoría de finalización de desposte."""
    # Nota: en v1.0, usamos el módulo de auditoría si existe, o log estructurado
    # El snapshot se guarda como JSON
    import json
    from datetime import datetime

    snapshot = {
        "desposte_id": str(desposte.id),
        "compra_id": str(desposte.compra_id),
        "fecha": desposte.fecha.isoformat(),
        "operador_id": str(desposte.operador_id),
        "rendimiento_total": str(desposte.rendimiento_total),
        "merma": str(desposte.merma),
        "estado": desposte.estado,
        "cortes": [
            {
                "tipo_corte": c.tipo_corte,
                "kilos_obtenidos": str(c.kilos_obtenidos),
                "porcentaje_rendimiento": str(c.porcentaje_rendimiento),
                "costo_asignado": str(c.costo_asignado),
                "costo_final_por_kilo": str(c.costo_final_por_kilo),
                "producto_id": str(c.producto_id) if c.producto_id else None,
            }
            for c in desposte.cortes
        ],
    }

    # Si existe tabla de auditoría, crear registro
    # Por ahora, log estructurado como placeholder hasta C-20
    import logging
    logger = logging.getLogger("basile.auditoria")
    logger.info(
        "FINALIZAR_DESPOSTE",
        extra={
            "accion": "FINALIZAR_DESPOSTE",
            "usuario_id": str(operador_id),
            "desposte_id": str(desposte.id),
            "empresa_id": str(desposte.empresa_id),
            "snapshot": json.dumps(snapshot),
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


async def listar_despostes(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    fecha: Optional[date] = None,
    estado: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[Desposte], int]:
    """Lista despostes filtrados por empresa con paginación."""
    where_clause = [
        Desposte.empresa_id == empresa_id,
    ]
    if fecha is not None:
        where_clause.append(Desposte.fecha == fecha)
    if estado is not None:
        where_clause.append(Desposte.estado == estado)

    # Count total
    count_query = select(func.count(Desposte.id)).where(*where_clause)
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    # Paginated results
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Desposte)
        .options(
            selectinload(Desposte.compra),
            selectinload(Desposte.operador),
        )
        .where(*where_clause)
        .order_by(Desposte.fecha.desc())
        .offset(skip)
        .limit(limit)
    )
    despostes = result.scalars().all()
    return list(despostes), total


async def obtener_desposte(
    db: AsyncSession,
    desposte_id: uuid.UUID,
    empresa_id: uuid.UUID,
) -> Desposte:
    """Obtiene un desposte con todas sus relaciones cargadas."""
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Desposte)
        .options(
            selectinload(Desposte.compra).selectinload(Compra.proveedor),
            selectinload(Desposte.operador),
            selectinload(Desposte.cortes).selectinload(CorteDesposte.producto),
        )
        .where(
            and_(
                Desposte.id == desposte_id,
                Desposte.empresa_id == empresa_id,
            )
        )
    )
    desposte = result.scalar_one_or_none()
    if not desposte:
        raise NotFoundException("Desposte no encontrado")

    # Cargar movimientos de stock manualmente
    result = await db.execute(
        select(MovimientoStock).where(
            and_(
                MovimientoStock.referencia_id == str(desposte_id),
                MovimientoStock.referencia_tipo == "desposte",
                MovimientoStock.empresa_id == empresa_id,
            )
        )
    )
    movimientos = list(result.scalars().all())
    # Attach as a dynamic attribute for response building (not a SQLModel field)
    object.__setattr__(desposte, "_movimientos_stock", movimientos)
    return desposte
