import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.caja.models import Caja, MovimientoCaja
from src.common.exceptions import ConflictException, NotFoundException

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
# Below this absolute magnitude, a cierre difference is treated as not significant.
# Centralized so C-20 (notificacion) / per-empresa config can tune the threshold.
UMBRAL_DIFERENCIA_SIGNIFICATIVA = Decimal("0.01")

_CENT = Decimal("0.01")

# Movement types that contribute as cash inflow from sales / reversals.
_TIPOS_VENTA = {"entrada_venta", "salida_anulacion"}


def _q(value: Decimal) -> Decimal:
    return Decimal(str(value)).quantize(_CENT)


# ---------------------------------------------------------------------------
# Pure calculation value objects
# ---------------------------------------------------------------------------
@dataclass
class EsperadoCaja:
    efectivo: Decimal
    transferencias: Decimal
    tarjetas: Decimal


@dataclass
class DiferenciasCaja:
    diferencia_efectivo: Decimal
    diferencia_transferencias: Decimal
    diferencia_tarjetas: Decimal
    diferencia_total: Decimal
    tiene_diferencia: bool
    diferencia_significativa: bool


def _calcular_esperado(monto_inicial: Decimal, movimientos: list) -> EsperadoCaja:
    """Compute esperado per medio from an open caja's movements (RN-CAJA-03).

    efectivo       = monto_inicial + ventas_efectivo + ingresos_manuales - retiros
    transferencias = ventas_transferencia
    tarjetas       = ventas_debito + ventas_credito

    `salida_anulacion` rows carry a negative importe (written by the venta service),
    so summing venta-type rows naturally nets out reversed sales. `retiro` rows carry
    a positive magnitude and are subtracted explicitly; `ingreso_manual` positive, added.
    """
    ventas_efectivo = Decimal("0.00")
    ventas_transferencia = Decimal("0.00")
    ventas_debito = Decimal("0.00")
    ventas_credito = Decimal("0.00")
    ingresos_manuales = Decimal("0.00")
    retiros = Decimal("0.00")

    for mov in movimientos:
        importe = Decimal(str(mov.importe))
        if mov.tipo in _TIPOS_VENTA:
            if mov.medio == "efectivo":
                ventas_efectivo += importe
            elif mov.medio == "transferencia":
                ventas_transferencia += importe
            elif mov.medio == "debito":
                ventas_debito += importe
            elif mov.medio == "credito":
                ventas_credito += importe
        elif mov.tipo == "ingreso_manual":
            ingresos_manuales += importe
        elif mov.tipo == "retiro":
            retiros += importe

    efectivo = _q(monto_inicial + ventas_efectivo + ingresos_manuales - retiros)
    transferencias = _q(ventas_transferencia)
    tarjetas = _q(ventas_debito + ventas_credito)
    return EsperadoCaja(efectivo=efectivo, transferencias=transferencias, tarjetas=tarjetas)


def _calcular_diferencias(
    esperado: EsperadoCaja,
    efectivo_real: Decimal,
    transferencias_real: Decimal,
    tarjetas_real: Decimal,
) -> DiferenciasCaja:
    """Compute real - esperado per medio and the total (RN-CAJA-02).

    Positive = sobrante, negative = faltante.
    """
    dif_efectivo = _q(Decimal(str(efectivo_real)) - esperado.efectivo)
    dif_transferencias = _q(Decimal(str(transferencias_real)) - esperado.transferencias)
    dif_tarjetas = _q(Decimal(str(tarjetas_real)) - esperado.tarjetas)
    dif_total = _q(dif_efectivo + dif_transferencias + dif_tarjetas)

    tiene_diferencia = dif_total != Decimal("0.00")
    diferencia_significativa = abs(dif_total) >= UMBRAL_DIFERENCIA_SIGNIFICATIVA
    return DiferenciasCaja(
        diferencia_efectivo=dif_efectivo,
        diferencia_transferencias=dif_transferencias,
        diferencia_tarjetas=dif_tarjetas,
        diferencia_total=dif_total,
        tiene_diferencia=tiene_diferencia,
        diferencia_significativa=diferencia_significativa,
    )


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------
async def _obtener_caja_abierta(db: AsyncSession, empresa_id: uuid.UUID) -> Optional[Caja]:
    result = await db.execute(
        select(Caja).where(Caja.empresa_id == empresa_id, Caja.estado == "abierta")
    )
    return result.scalar_one_or_none()


async def _cargar_movimientos(db: AsyncSession, caja_id: uuid.UUID) -> list:
    result = await db.execute(
        select(MovimientoCaja).where(MovimientoCaja.caja_id == caja_id)
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Apertura
# ---------------------------------------------------------------------------
async def abrir_caja(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    usuario_id: uuid.UUID,
    efectivo_inicial: Decimal,
) -> Caja:
    """Open a caja for an empresa. Only one caja may be `abierta` per empresa (v1.0)."""
    existente = await _obtener_caja_abierta(db, empresa_id)
    if existente is not None:
        raise ConflictException("Ya existe una caja abierta para esta empresa")

    caja = Caja(
        empresa_id=empresa_id,
        operador_id=usuario_id,
        usuario_apertura_id=usuario_id,
        monto_inicial=_q(efectivo_inicial),
        efectivo_inicial=_q(efectivo_inicial),
        estado="abierta",
        fecha_apertura=datetime.utcnow(),
    )
    db.add(caja)
    await db.commit()
    await db.refresh(caja)
    return caja


# ---------------------------------------------------------------------------
# Movimiento manual
# ---------------------------------------------------------------------------
async def registrar_movimiento(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    tipo: str,
    importe: Decimal,
    descripcion: Optional[str] = None,
) -> MovimientoCaja:
    """Register a manual `retiro` or `ingreso_manual` against the open caja."""
    caja = await _obtener_caja_abierta(db, empresa_id)
    if caja is None:
        raise ConflictException("No hay caja abierta para esta empresa")

    movimiento = MovimientoCaja(
        caja_id=caja.id,
        empresa_id=empresa_id,
        tipo=tipo,
        medio="efectivo",
        importe=_q(importe),
        descripcion=descripcion,
        fecha=datetime.utcnow(),
    )
    db.add(movimiento)
    await db.commit()
    await db.refresh(movimiento)
    return movimiento


# ---------------------------------------------------------------------------
# Obtener caja abierta con esperado (GET /caja/actual)
# ---------------------------------------------------------------------------
async def obtener_caja_abierta_con_esperado(
    db: AsyncSession,
    empresa_id: uuid.UUID,
) -> tuple[Caja, EsperadoCaja]:
    caja = await _obtener_caja_abierta(db, empresa_id)
    if caja is None:
        raise NotFoundException("No hay caja abierta para esta empresa")
    movimientos = await _cargar_movimientos(db, caja.id)
    esperado = _calcular_esperado(Decimal(str(caja.monto_inicial)), movimientos)
    return caja, esperado


# ---------------------------------------------------------------------------
# Cierre
# ---------------------------------------------------------------------------
async def cerrar_caja(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    usuario_id: uuid.UUID,
    efectivo_real: Decimal,
    transferencias_real: Decimal,
    tarjetas_real: Decimal,
) -> tuple[Caja, EsperadoCaja, DiferenciasCaja]:
    """Close the open caja: compute esperado, diferencias, flag, mark cerrada (ACID)."""
    caja = await _obtener_caja_abierta(db, empresa_id)
    if caja is None:
        raise ConflictException("No hay caja abierta para esta empresa")

    movimientos = await _cargar_movimientos(db, caja.id)
    esperado = _calcular_esperado(Decimal(str(caja.monto_inicial)), movimientos)
    diferencias = _calcular_diferencias(
        esperado,
        efectivo_real=efectivo_real,
        transferencias_real=transferencias_real,
        tarjetas_real=tarjetas_real,
    )

    caja.efectivo_esperado = esperado.efectivo
    caja.transferencias_esperadas = esperado.transferencias
    caja.tarjetas_esperadas = esperado.tarjetas
    caja.efectivo_real = _q(efectivo_real)
    caja.transferencias_reales = _q(transferencias_real)
    caja.tarjetas_reales = _q(tarjetas_real)
    caja.diferencia_efectivo = diferencias.diferencia_efectivo
    caja.diferencia_transferencias = diferencias.diferencia_transferencias
    caja.diferencia_tarjetas = diferencias.diferencia_tarjetas
    caja.diferencia_total = diferencias.diferencia_total
    caja.monto_final = _q(efectivo_real + transferencias_real + tarjetas_real)
    caja.usuario_cierre_id = usuario_id
    caja.estado = "cerrada"
    caja.fecha_cierre = datetime.utcnow()
    caja.updated_at = datetime.utcnow()

    # TODO(C-20): if diferencias.diferencia_significativa, fire a notificacion
    # (tipo="diferencia_caja"). The notificacion module is a C-20 stub today, so this
    # change only computes/returns the flag and leaves this seam for the future trigger.

    await db.commit()
    await db.refresh(caja)
    return caja, esperado, diferencias
