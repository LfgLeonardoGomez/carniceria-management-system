"""Cross-module integration test: C-12 (venta/cobrar) → C-14 (cuenta_corriente).

Task 5.7 RED→GREEN:
  A credit sale (medio=cuenta_corriente) processed by C-12 creates a `tipo="deuda"`
  movement.  That movement must be visible via C-14 obtener_historial.  A subsequent
  registrar_pago must compose correctly so that:
    - cliente.saldo_actual == (deuda_importe - pago_importe).quantize("0.01")
    - saldo_resultante on the pago movement == same value
    - The history now contains both the deuda and the pago entries

Requires Docker+testcontainers (real PostgreSQL).  Will ERROR when Docker is not running.

NOTE: C-12 production code (venta/service.py) is NOT modified.  This test only
      *consumes* the existing cobrar_venta behavior.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.modules.auth.models import Empresa, Rol, Usuario
from src.modules.cliente.models import Cliente
from src.modules.cuenta_corriente.models import CuentaCorriente
from src.modules.cuenta_corriente.schemas import PagoCreate
from src.modules.producto.models import Producto
from src.modules.stock.models import MovimientoStock
from src.modules.venta.models import Venta, DetalleVenta
from src.core.security import hash_password


# ---------------------------------------------------------------------------
# Helpers (mirror test_service_pago.py + test_venta_integration.py patterns)
# ---------------------------------------------------------------------------

async def _crear_empresa(db: AsyncSession, nombre: str = "CC-C12 Test") -> Empresa:
    e = Empresa(nombre_comercial=nombre, activa=True)
    db.add(e)
    await db.commit()
    await db.refresh(e)
    return e


async def _crear_rol(db: AsyncSession, nombre: str = "cajero", empresa_id=None) -> Rol:
    r = Rol(nombre=nombre, empresa_id=empresa_id)
    db.add(r)
    await db.commit()
    await db.refresh(r)
    return r


async def _crear_usuario(
    db: AsyncSession,
    email: str,
    empresa_id: uuid.UUID,
    rol_nombre: str = "cajero",
) -> Usuario:
    rol = await _crear_rol(db, rol_nombre, empresa_id=empresa_id)
    u = Usuario(
        email=email,
        contrasena_hash=hash_password("Password123"),
        nombre="Test",
        apellido="User",
        rol_id=rol.id,
        activo=True,
        empresa_id=empresa_id,
    )
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


async def _crear_cliente_cc(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    nombre: str = "CC Cliente",
    saldo: Decimal = Decimal("0.00"),
) -> Cliente:
    c = Cliente(
        empresa_id=empresa_id,
        nombre=nombre,
        tipo_cliente="cuenta_corriente",
        limite_cuenta_corriente=Decimal("0.0000"),
        saldo_actual=saldo,
    )
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return c


async def _crear_producto(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    nombre: str = "Asado CC",
    precio_publico: Decimal = Decimal("1000.0000"),
    costo_por_kilo: Decimal = Decimal("600.0000"),
    stock_inicial: Decimal = Decimal("10.000"),
) -> Producto:
    plu = f"CC{uuid.uuid4().hex[:6]}"
    p = Producto(
        empresa_id=empresa_id,
        plu=plu,
        nombre=nombre,
        precio_publico=precio_publico,
        precio_mayorista=precio_publico * Decimal("0.9"),
        costo_por_kilo=costo_por_kilo,
        margen=Decimal("0.40"),
        stock_actual=stock_inicial,
    )
    db.add(p)
    await db.flush()

    # Seed stock movement so calcular_stock_actual works
    mov = MovimientoStock(
        empresa_id=empresa_id,
        producto_id=p.id,
        tipo="entrada_compra",
        cantidad_kilos=stock_inicial,
        stock_resultante=stock_inicial,
        fecha=datetime.now(timezone.utc),
    )
    db.add(mov)
    await db.commit()
    await db.refresh(p)
    return p


async def _seed_venta_cobrada_cc(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    cliente_id: uuid.UUID,
    usuario: Usuario,
    producto: Producto,
    cantidad_kilos: Decimal,
    precio_unitario: Decimal,
) -> Venta:
    """Seed a completed credit sale through the C-12 cobrar_venta service.

    We call venta/service.cobrar_venta directly so this test exercises the
    *real* C-12 path, including the CuentaCorriente insertion.
    """
    from src.modules.venta import service as venta_service
    from src.modules.venta.schemas import VentaCreate, DetalleVentaCreate, CobrarVentaRequest

    # 1. Create the venta
    create_data = VentaCreate(
        cliente_id=cliente_id,
        items=[
            DetalleVentaCreate(
                producto_id=producto.id,
                cantidad_kilos=cantidad_kilos,
                precio_unitario=precio_unitario,
            )
        ],
    )
    venta = await venta_service.crear_venta(db, usuario, create_data)

    # 2. Cobrar with medio=cuenta_corriente (no caja needed for CC)
    cobrar_data = CobrarVentaRequest(medio_pago="cuenta_corriente")
    venta_cobrada = await venta_service.cobrar_venta(db, usuario, venta.id, cobrar_data)
    return venta_cobrada


# ---------------------------------------------------------------------------
# Task 5.7 RED → GREEN
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_credit_sale_creates_deuda_visible_in_historial_and_pago_composes(
    db_session: AsyncSession,
):
    """Full C-12 → C-14 composition:
    1. A credit sale creates a deuda movement with the correct importe.
    2. obtener_historial returns that deuda.
    3. registrar_pago reduces the balance correctly.
    4. saldo_actual and saldo_resultante are consistent (Decimal, no float).
    """
    from src.modules.cuenta_corriente import service as cc_service

    suffix = uuid.uuid4().hex[:6]
    empresa = await _crear_empresa(db_session, f"C12C14-{suffix}")
    usuario = await _crear_usuario(db_session, f"cajero_{suffix}@test.com", empresa.id, "cajero")
    cliente = await _crear_cliente_cc(db_session, empresa.id, f"Cliente-{suffix}", saldo=Decimal("0.00"))
    producto = await _crear_producto(
        db_session,
        empresa.id,
        nombre=f"Prod-{suffix}",
        precio_publico=Decimal("1000.0000"),
        costo_por_kilo=Decimal("600.0000"),
        stock_inicial=Decimal("10.000"),
    )

    # --- Step 1: C-12 credit sale (2 kilos @ 1000/kilo = total 2000.00) ---
    cantidad_kilos = Decimal("2.000")
    precio_unitario = Decimal("1000.00")
    importe_esperado = (cantidad_kilos * precio_unitario).quantize(Decimal("0.01"))  # 2000.00

    await _seed_venta_cobrada_cc(
        db_session,
        empresa.id,
        cliente.id,
        usuario,
        producto,
        cantidad_kilos,
        precio_unitario,
    )

    # --- Step 2: deuda movement must exist with correct importe ---
    deuda_stmt = select(CuentaCorriente).where(
        CuentaCorriente.empresa_id == empresa.id,
        CuentaCorriente.cliente_id == cliente.id,
        CuentaCorriente.tipo == "deuda",
    )
    deuda_result = await db_session.execute(deuda_stmt)
    deuda_rows = deuda_result.scalars().all()

    assert len(deuda_rows) == 1, "Exactly one deuda movement must be created by cobrar_venta"
    deuda_mov = deuda_rows[0]
    assert Decimal(str(deuda_mov.importe)).quantize(Decimal("0.01")) == importe_esperado
    assert Decimal(str(deuda_mov.saldo_resultante)).quantize(Decimal("0.01")) == importe_esperado

    # --- Step 3: obtener_historial returns the deuda ---
    historial = await cc_service.obtener_historial(db_session, empresa.id, cliente.id)

    assert historial.total >= 1
    deuda_items = [m for m in historial.items if m.tipo == "deuda"]
    assert len(deuda_items) == 1
    assert deuda_items[0].importe == importe_esperado
    assert historial.saldo_actual == importe_esperado

    # --- Step 4: registrar_pago composes correctly ---
    pago_importe = Decimal("500.00")
    saldo_esperado_post_pago = (importe_esperado - pago_importe).quantize(Decimal("0.01"))

    pago_result = await cc_service.registrar_pago(
        db_session,
        empresa.id,
        cliente.id,
        PagoCreate(importe=pago_importe),
    )

    assert pago_result.movimiento.tipo == "pago"
    assert pago_result.movimiento.importe == pago_importe
    assert pago_result.movimiento.saldo_resultante == saldo_esperado_post_pago
    assert pago_result.saldo_actual == saldo_esperado_post_pago

    # --- Step 5: historial now contains both deuda + pago ---
    historial_post = await cc_service.obtener_historial(db_session, empresa.id, cliente.id)
    assert historial_post.total == 2
    tipos = [m.tipo for m in historial_post.items]
    assert "deuda" in tipos
    assert "pago" in tipos
    assert historial_post.saldo_actual == saldo_esperado_post_pago


@pytest.mark.asyncio
async def test_credit_sale_full_payment_clears_balance(db_session: AsyncSession):
    """Triangulate: a full payment after a credit sale clears saldo_actual to 0.00."""
    from src.modules.cuenta_corriente import service as cc_service

    suffix = uuid.uuid4().hex[:6]
    empresa = await _crear_empresa(db_session, f"C12Full-{suffix}")
    usuario = await _crear_usuario(db_session, f"cajero_{suffix}@test.com", empresa.id, "cajero")
    cliente = await _crear_cliente_cc(db_session, empresa.id, f"Cliente-{suffix}", saldo=Decimal("0.00"))
    producto = await _crear_producto(
        db_session,
        empresa.id,
        nombre=f"Prod-{suffix}",
        precio_publico=Decimal("500.0000"),
        costo_por_kilo=Decimal("300.0000"),
        stock_inicial=Decimal("5.000"),
    )

    await _seed_venta_cobrada_cc(
        db_session, empresa.id, cliente.id, usuario, producto,
        Decimal("1.000"), Decimal("500.00"),
    )

    # Full repayment of the 500.00 debt
    pago_result = await cc_service.registrar_pago(
        db_session,
        empresa.id,
        cliente.id,
        PagoCreate(importe=Decimal("500.00")),
    )

    assert pago_result.saldo_actual == Decimal("0.00")
    assert pago_result.movimiento.saldo_resultante == Decimal("0.00")

    # Confirm cliente row is also zero
    await db_session.refresh(cliente)
    assert Decimal(str(cliente.saldo_actual)).quantize(Decimal("0.01")) == Decimal("0.00")
