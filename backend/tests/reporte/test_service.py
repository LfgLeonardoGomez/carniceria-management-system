"""Tests for reporte.service — listar_ventas_reporte.

TDD cycle: RED → GREEN → TRIANGULATE → REFACTOR
Uses testcontainers (real PostgreSQL). Every test is isolated via transaction rollback.

Tasks covered:
  2.1 — listar_ventas_reporte returns only 'cobrada' sales for the empresa,
         with correct cliente_nombre, productos, total_kilos, subtotal, total, medios_pago
  2.3 — filter by fecha_desde/fecha_hasta returns only matching rows
  2.3 — filter by cliente_id from another empresa returns 0 rows (not 403)
  2.4 — ganancia_estimada is Decimal when all costo_unitario set; None when any NULL
  2.5 — calcular_ganancia is wired inside the service
  2.6 — sales with cliente_id IS NULL return cliente_nombre = "Público general"
  2.7 — client-name resolution: razon_social → nombre+apellido → "Público general"
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.modules.empresa.models import Empresa
from src.modules.auth.models import Usuario, Rol
from src.modules.cliente.models import Cliente
from src.modules.producto.models import Producto
from src.modules.venta.models import Venta, DetalleVenta, PagoVenta
from src.core.security import hash_password

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _crear_empresa(db: AsyncSession, nombre: str = "Emp Reporte") -> Empresa:
    emp = Empresa(nombre_comercial=nombre, activa=True)
    db.add(emp)
    await db.commit()
    await db.refresh(emp)
    return emp


async def _crear_rol(db: AsyncSession, nombre: str = "administrador", empresa_id: uuid.UUID | None = None) -> Rol:
    rol = Rol(nombre=nombre, empresa_id=empresa_id)
    db.add(rol)
    await db.commit()
    await db.refresh(rol)
    return rol


async def _crear_usuario(
    db: AsyncSession,
    email: str,
    empresa_id: uuid.UUID,
    rol_id: uuid.UUID,
) -> Usuario:
    usuario = Usuario(
        email=email,
        contrasena_hash=hash_password("Pass123!"),
        nombre="Rep",
        apellido="Test",
        rol_id=rol_id,
        activo=True,
        empresa_id=empresa_id,
    )
    db.add(usuario)
    await db.commit()
    await db.refresh(usuario)
    return usuario


async def _crear_producto(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    nombre: str = "Asado",
    costo: str = "500.00",
) -> Producto:
    prod = Producto(
        empresa_id=empresa_id,
        plu=f"P-{nombre[:3].upper()}-{uuid.uuid4().hex[:4]}",
        nombre=nombre,
        precio_publico=Decimal("1000.00"),
        precio_mayorista=Decimal("900.00"),
        costo_por_kilo=Decimal(costo),
        margen=Decimal("0.5000"),
        stock_actual=Decimal("100.000"),
    )
    db.add(prod)
    await db.commit()
    await db.refresh(prod)
    return prod


async def _crear_venta_cobrada(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    producto: Producto,
    cliente: Cliente | None = None,
    cantidad_kilos: str = "2.000",
    precio_unitario: str = "1000.00",
    costo_unitario: str | None = "500.00",
    fecha: datetime | None = None,
    medio_pago: str = "efectivo",
) -> Venta:
    if fecha is None:
        fecha = datetime.now(timezone.utc)
    cantidad = Decimal(cantidad_kilos)
    precio = Decimal(precio_unitario)
    importe = (cantidad * precio).quantize(Decimal("0.01"))
    subtotal = importe
    total = importe

    costo_snap = Decimal(costo_unitario) if costo_unitario is not None else None

    detalle = DetalleVenta(
        producto_id=producto.id,
        cantidad_kilos=cantidad,
        precio_unitario=precio,
        importe=importe,
        costo_unitario=costo_snap,
    )

    venta = Venta(
        empresa_id=empresa_id,
        cliente_id=cliente.id if cliente else None,
        tipo_cliente_al_momento="publico_general" if cliente is None else "minorista",
        estado="cobrada",
        subtotal=subtotal,
        descuentos=Decimal("0.00"),
        total=total,
        fecha=fecha,
    )
    venta.detalles = [detalle]
    db.add(venta)
    await db.commit()
    await db.refresh(venta)

    pago = PagoVenta(
        venta_id=venta.id,
        medio_pago=medio_pago,
        importe=total,
    )
    db.add(pago)
    await db.commit()
    return venta


async def _crear_cliente(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    nombre: str = "Juan",
    apellido: str = "Perez",
    razon_social: str | None = None,
) -> Cliente:
    cliente = Cliente(
        empresa_id=empresa_id,
        nombre=nombre,
        apellido=apellido,
        razon_social=razon_social,
    )
    db.add(cliente)
    await db.commit()
    await db.refresh(cliente)
    return cliente


# ---------------------------------------------------------------------------
# Task 2.1 — RED: listar_ventas_reporte returns only cobrada sales for empresa
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_listar_ventas_reporte_returns_cobrada_only(db_session: AsyncSession):
    """Only 'cobrada' sales are returned; en_curso / anulada are excluded."""
    from src.modules.reporte.service import listar_ventas_reporte

    emp = await _crear_empresa(db_session, "Emp 2.1 cobrada")
    prod = await _crear_producto(db_session, emp.id, "Asado")

    # Create one cobrada venta
    await _crear_venta_cobrada(db_session, emp.id, prod)

    # Create one en_curso venta (not cobrada)
    venta_en_curso = Venta(
        empresa_id=emp.id,
        cliente_id=None,
        tipo_cliente_al_momento="publico_general",
        estado="en_curso",
        subtotal=Decimal("2000.00"),
        descuentos=Decimal("0.00"),
        total=Decimal("2000.00"),
        fecha=datetime.now(timezone.utc),
    )
    db_session.add(venta_en_curso)
    await db_session.commit()

    rows, total = await listar_ventas_reporte(db_session, emp.id)

    assert total == 1
    assert len(rows) == 1
    assert rows[0].cliente_nombre == "Público general"
    assert rows[0].total_kilos == Decimal("2.000")


@pytest.mark.asyncio
async def test_listar_ventas_reporte_correct_fields(db_session: AsyncSession):
    """Row fields: productos, total_kilos, subtotal, total, medios_pago are populated."""
    from src.modules.reporte.service import listar_ventas_reporte

    emp = await _crear_empresa(db_session, "Emp 2.1 fields")
    prod = await _crear_producto(db_session, emp.id, "Costilla")
    await _crear_venta_cobrada(
        db_session, emp.id, prod,
        cantidad_kilos="3.500",
        precio_unitario="1200.00",
        medio_pago="tarjeta",
    )

    rows, total = await listar_ventas_reporte(db_session, emp.id)

    assert total == 1
    row = rows[0]
    assert "Costilla" in row.productos
    assert row.total_kilos == Decimal("3.500")
    assert row.subtotal == Decimal("4200.00")
    assert row.total == Decimal("4200.00")
    assert "tarjeta" in row.medios_pago


# ---------------------------------------------------------------------------
# Task 2.3 — TRIANGULATE: date range filter + cross-tenant isolation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_listar_ventas_reporte_fecha_filter(db_session: AsyncSession):
    """Filter by fecha_desde/fecha_hasta returns only matching rows."""
    from src.modules.reporte.service import listar_ventas_reporte

    emp = await _crear_empresa(db_session, "Emp 2.3 fecha")
    prod = await _crear_producto(db_session, emp.id, "Asado")

    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)
    two_days_ago = now - timedelta(days=2)

    # Two cobradas: yesterday and two_days_ago
    await _crear_venta_cobrada(db_session, emp.id, prod, fecha=yesterday)
    await _crear_venta_cobrada(db_session, emp.id, prod, fecha=two_days_ago)

    # Filter from two days ago to yesterday
    rows, total = await listar_ventas_reporte(
        db_session, emp.id,
        fecha_desde=two_days_ago,
        fecha_hasta=yesterday,
    )
    assert total == 2

    # Filter only yesterday
    rows_y, total_y = await listar_ventas_reporte(
        db_session, emp.id,
        fecha_desde=yesterday,
        fecha_hasta=now,
    )
    assert total_y == 1


@pytest.mark.asyncio
async def test_listar_ventas_reporte_cross_tenant_cliente_filter(db_session: AsyncSession):
    """Filter by cliente_id from another empresa returns 0 rows (not 403)."""
    from src.modules.reporte.service import listar_ventas_reporte

    emp_a = await _crear_empresa(db_session, "Emp A cross-tenant")
    emp_b = await _crear_empresa(db_session, "Emp B cross-tenant")
    prod_b = await _crear_producto(db_session, emp_b.id, "Vacío")
    cliente_b = await _crear_cliente(db_session, emp_b.id, "Cliente", "B")

    await _crear_venta_cobrada(db_session, emp_b.id, prod_b, cliente=cliente_b)

    # Empresa A asks for results filtered by a cliente that belongs to empresa B
    rows, total = await listar_ventas_reporte(
        db_session, emp_a.id,
        cliente_id=cliente_b.id,
    )
    assert total == 0
    assert rows == []


# ---------------------------------------------------------------------------
# Tasks 2.4/2.5 — ganancia_estimada
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ganancia_estimada_decimal_when_all_costs_set(db_session: AsyncSession):
    """ganancia_estimada is a Decimal when all costo_unitario are set."""
    from src.modules.reporte.service import listar_ventas_reporte

    emp = await _crear_empresa(db_session, "Emp ganancia decimal")
    prod = await _crear_producto(db_session, emp.id, "Bife")

    # 2 kg at 1000.00, costo 500.00 → ganancia = (2*1000) - (2*500) = 1000.00
    await _crear_venta_cobrada(
        db_session, emp.id, prod,
        cantidad_kilos="2.000",
        precio_unitario="1000.00",
        costo_unitario="500.00",
    )

    rows, _ = await listar_ventas_reporte(db_session, emp.id)
    assert len(rows) == 1
    assert rows[0].ganancia_estimada == Decimal("1000.00")


@pytest.mark.asyncio
async def test_ganancia_estimada_none_when_any_cost_null(db_session: AsyncSession):
    """ganancia_estimada is None when any costo_unitario is NULL."""
    from src.modules.reporte.service import listar_ventas_reporte

    emp = await _crear_empresa(db_session, "Emp ganancia null")
    prod = await _crear_producto(db_session, emp.id, "Chorizo")

    await _crear_venta_cobrada(
        db_session, emp.id, prod,
        costo_unitario=None,  # NULL costo → ganancia None
    )

    rows, _ = await listar_ventas_reporte(db_session, emp.id)
    assert len(rows) == 1
    assert rows[0].ganancia_estimada is None


# ---------------------------------------------------------------------------
# Tasks 2.6/2.7 — client-name resolution
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cliente_nombre_publico_general_when_no_cliente(db_session: AsyncSession):
    """Sales with cliente_id IS NULL return cliente_nombre = 'Público general'."""
    from src.modules.reporte.service import listar_ventas_reporte

    emp = await _crear_empresa(db_session, "Emp publico general")
    prod = await _crear_producto(db_session, emp.id, "Paleta")

    await _crear_venta_cobrada(db_session, emp.id, prod, cliente=None)

    rows, _ = await listar_ventas_reporte(db_session, emp.id)
    assert rows[0].cliente_nombre == "Público general"


@pytest.mark.asyncio
async def test_cliente_nombre_uses_razon_social_when_set(db_session: AsyncSession):
    """B2B clients with razon_social use that as display name."""
    from src.modules.reporte.service import listar_ventas_reporte

    emp = await _crear_empresa(db_session, "Emp razon social")
    prod = await _crear_producto(db_session, emp.id, "Lomo")
    cliente = await _crear_cliente(
        db_session, emp.id,
        nombre="Juan", apellido="Garcia",
        razon_social="Supermercado SA",
    )

    await _crear_venta_cobrada(db_session, emp.id, prod, cliente=cliente)

    rows, _ = await listar_ventas_reporte(db_session, emp.id)
    assert rows[0].cliente_nombre == "Supermercado SA"


@pytest.mark.asyncio
async def test_cliente_nombre_uses_nombre_apellido_when_no_razon_social(db_session: AsyncSession):
    """Individual clients without razon_social use nombre + apellido."""
    from src.modules.reporte.service import listar_ventas_reporte

    emp = await _crear_empresa(db_session, "Emp nombre apellido")
    prod = await _crear_producto(db_session, emp.id, "Morcilla")
    cliente = await _crear_cliente(
        db_session, emp.id,
        nombre="Maria", apellido="Lopez",
        razon_social=None,
    )

    await _crear_venta_cobrada(db_session, emp.id, prod, cliente=cliente)

    rows, _ = await listar_ventas_reporte(db_session, emp.id)
    assert rows[0].cliente_nombre == "Maria Lopez"
