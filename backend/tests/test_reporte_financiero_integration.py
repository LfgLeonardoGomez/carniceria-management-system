"""Integration tests for C-18 financial report — real PostgreSQL via testcontainers.

Tasks:
  4.1 RED — multi-tenant isolation (empresa A vs B)
  4.3 TRIANGULATE — swap empresa, indicators flip
  5.1 RED — 200 for reportes:read, 403 for unauthorized
  5.2 RED — invalid group_by → 422; missing group_by defaults to mes
  5.4 TRIANGULATE — date range filter narrows results
  5.5 — route reachable via already-mounted router (no new include_router)
  6.1 — C-17 symbols unchanged (smoke test)
"""
from __future__ import annotations

import sys
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "src"))

from src.modules.auth.models import Empresa, Rol, Usuario
from src.modules.gasto.models import Gasto
from src.modules.producto.models import Producto
from src.modules.venta.models import DetalleVenta, Venta
from src.core.security import hash_password, create_access_token


# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

async def _crear_empresa(db: AsyncSession, nombre: str = "Carniceria Test") -> Empresa:
    empresa = Empresa(nombre_comercial=nombre, activa=True)
    db.add(empresa)
    await db.commit()
    await db.refresh(empresa)
    return empresa


async def _crear_rol(db: AsyncSession, nombre: str = "admin", empresa_id=None) -> Rol:
    rol = Rol(nombre=nombre, empresa_id=empresa_id)
    db.add(rol)
    await db.commit()
    await db.refresh(rol)
    return rol


async def _crear_usuario(
    db: AsyncSession,
    email: str,
    empresa_id=None,
    rol_nombre: str = "admin",
) -> Usuario:
    rol = await _crear_rol(db, rol_nombre, empresa_id=empresa_id)
    usuario = Usuario(
        email=email,
        contrasena_hash=hash_password("Password123"),
        nombre="Test",
        apellido="User",
        rol_id=rol.id,
        activo=True,
        empresa_id=empresa_id,
    )
    db.add(usuario)
    await db.commit()
    await db.refresh(usuario)
    return usuario


def _auth_header(usuario: Usuario, rol_nombre: str = "admin") -> dict:
    token = create_access_token({
        "sub": str(usuario.id),
        "empresa_id": str(usuario.empresa_id),
        "rol": rol_nombre,
    })
    return {"Authorization": f"Bearer {token}"}


async def _get_or_create_producto(
    db: AsyncSession,
    empresa_id: uuid.UUID,
) -> Producto:
    """Get an existing product for this empresa, or create a minimal one."""
    from sqlalchemy import select

    result = await db.execute(
        select(Producto).where(Producto.empresa_id == empresa_id).limit(1)
    )
    producto = result.scalar_one_or_none()
    if producto is None:
        producto = Producto(
            empresa_id=empresa_id,
            plu=f"T{uuid.uuid4().hex[:5]}",
            nombre="Test Producto",
            precio_publico=Decimal("100.0000"),
            precio_mayorista=Decimal("80.0000"),
            costo_por_kilo=Decimal("50.0000"),
            margen=Decimal("0.5000"),
            stock_actual=Decimal("100.0000"),
        )
        db.add(producto)
        await db.flush()
    return producto


async def _seed_venta(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    total: Decimal,
    fecha: datetime,
    costo_unitario: Decimal | None = Decimal("50.00"),
    estado: str = "cobrada",
    kilos: Decimal = Decimal("2.000"),
) -> None:
    """Seed a venta + detalle with given parameters."""
    producto = await _get_or_create_producto(db, empresa_id)

    venta = Venta(
        empresa_id=empresa_id,
        estado=estado,
        subtotal=total,
        total=total,
        fecha=fecha,
    )
    db.add(venta)
    await db.flush()

    precio_u = (total / kilos).quantize(Decimal("0.01"))
    det = DetalleVenta(
        venta_id=venta.id,
        producto_id=producto.id,
        cantidad_kilos=kilos,
        precio_unitario=precio_u,
        importe=total,
        costo_unitario=costo_unitario,
    )
    db.add(det)
    await db.commit()


async def _seed_gasto(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    importe: Decimal,
    fecha: date,
) -> None:
    gasto = Gasto(
        empresa_id=empresa_id,
        fecha=fecha,
        categoria="operativo",
        importe=importe,
        medio_pago="efectivo",
    )
    db.add(gasto)
    await db.commit()


# ---------------------------------------------------------------------------
# Task 5.1 RED — 200 for reportes:read, 403 for unauthorized
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_reportes_financieros_authorized_returns_200(
    client: AsyncClient, db_session: AsyncSession
):
    empresa = await _crear_empresa(db_session, f"Test200-{uuid.uuid4().hex[:6]}")
    usuario = await _crear_usuario(db_session, f"admin_{uuid.uuid4().hex[:6]}@test.com", empresa.id, "admin")

    resp = await client.get(
        "/reportes/financieros?group_by=mes",
        headers=_auth_header(usuario, "admin"),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "group_by" in data
    assert data["group_by"] == "mes"
    assert "rows" in data


@pytest.mark.asyncio
async def test_reportes_financieros_unauthorized_returns_403(
    client: AsyncClient, db_session: AsyncSession
):
    empresa = await _crear_empresa(db_session, f"Test403-{uuid.uuid4().hex[:6]}")
    # cajero role does NOT have reportes:read
    usuario = await _crear_usuario(
        db_session, f"cajero_{uuid.uuid4().hex[:6]}@test.com", empresa.id, "cajero"
    )

    resp = await client.get(
        "/reportes/financieros?group_by=mes",
        headers=_auth_header(usuario, "cajero"),
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Task 5.2 RED — invalid group_by → 422; default → mes
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invalid_group_by_returns_422(
    client: AsyncClient, db_session: AsyncSession
):
    empresa = await _crear_empresa(db_session, f"Test422-{uuid.uuid4().hex[:6]}")
    usuario = await _crear_usuario(db_session, f"admin_{uuid.uuid4().hex[:6]}@test.com", empresa.id, "admin")

    resp = await client.get(
        "/reportes/financieros?group_by=trimestre",
        headers=_auth_header(usuario, "admin"),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_missing_group_by_defaults_to_mes(
    client: AsyncClient, db_session: AsyncSession
):
    empresa = await _crear_empresa(db_session, f"TestDef-{uuid.uuid4().hex[:6]}")
    usuario = await _crear_usuario(db_session, f"admin_{uuid.uuid4().hex[:6]}@test.com", empresa.id, "admin")

    resp = await client.get(
        "/reportes/financieros",  # no group_by param
        headers=_auth_header(usuario, "admin"),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["group_by"] == "mes"


# ---------------------------------------------------------------------------
# Task 5.5 — route reachable via already-mounted router
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_route_reachable_via_mounted_router(
    client: AsyncClient, db_session: AsyncSession
):
    """Route /reportes/financieros exists (mounted via existing reporte_router)."""
    empresa = await _crear_empresa(db_session, f"TestMount-{uuid.uuid4().hex[:6]}")
    usuario = await _crear_usuario(db_session, f"admin_{uuid.uuid4().hex[:6]}@test.com", empresa.id, "admin")

    resp = await client.get(
        "/reportes/financieros?group_by=anio",
        headers=_auth_header(usuario, "admin"),
    )
    assert resp.status_code == 200  # 200 proves route is not 404


# ---------------------------------------------------------------------------
# Task 6.1 — C-17 symbols unchanged
# ---------------------------------------------------------------------------

def test_c17_symbols_unchanged():
    """Coexistence guard: C-17 exported symbols still exist and are not altered."""
    from src.modules.reporte.schemas import (
        VentaReporteRow,
        ReporteVentasResponse,
        ExportFormato,
    )
    from src.modules.reporte.service import (
        listar_ventas_reporte,
    )
    from src.modules.reporte.router import (
        listar_reporte_ventas,
        exportar_reporte_ventas,
    )

    # Confirm they exist and are callable (import failure = broken coexistence)
    assert callable(listar_ventas_reporte)
    assert callable(listar_reporte_ventas)
    assert callable(exportar_reporte_ventas)

    # VentaReporteRow still has its original fields
    fields = VentaReporteRow.model_fields
    for field in ("venta_id", "fecha", "cliente_nombre", "productos",
                  "total_kilos", "subtotal", "total", "medios_pago",
                  "ganancia_estimada"):
        assert field in fields, f"C-17 field {field!r} was removed or renamed"


# ---------------------------------------------------------------------------
# Task 4.1 RED — multi-tenant isolation
# Task 4.3 TRIANGULATE — swap empresa
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_multi_tenant_isolation_empresa_a_vs_b(
    client: AsyncClient, db_session: AsyncSession
):
    """empresa A's report must not include empresa B's or C's data."""
    suffix = uuid.uuid4().hex[:6]
    emp_a = await _crear_empresa(db_session, f"EmpresaA-{suffix}")
    emp_b = await _crear_empresa(db_session, f"EmpresaB-{suffix}")
    emp_c = await _crear_empresa(db_session, f"EmpresaC-{suffix}")  # third tenant

    user_a = await _crear_usuario(db_session, f"a_{suffix}@test.com", emp_a.id)
    user_b = await _crear_usuario(db_session, f"b_{suffix}@test.com", emp_b.id)

    fecha = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)

    # empresa A: 1000 in ventas
    await _seed_venta(db_session, emp_a.id, Decimal("1000.00"), fecha, Decimal("50.00"))
    # empresa B: 5000 in ventas
    await _seed_venta(db_session, emp_b.id, Decimal("5000.00"), fecha, Decimal("200.00"))
    # empresa C: 2000 in ventas
    await _seed_venta(db_session, emp_c.id, Decimal("2000.00"), fecha, Decimal("80.00"))

    # empresa A's report
    resp_a = await client.get(
        "/reportes/financieros?group_by=mes",
        headers=_auth_header(user_a, "admin"),
    )
    assert resp_a.status_code == 200
    data_a = resp_a.json()
    ventas_a = sum(Decimal(row["ventas"]) for row in data_a["rows"])
    # Only A's 1000 — not B's 5000 or C's 2000
    assert ventas_a == Decimal("1000.00"), f"Isolation breach: expected 1000, got {ventas_a}"

    # empresa B's report (task 4.3 — swap)
    resp_b = await client.get(
        "/reportes/financieros?group_by=mes",
        headers=_auth_header(user_b, "admin"),
    )
    assert resp_b.status_code == 200
    data_b = resp_b.json()
    ventas_b = sum(Decimal(row["ventas"]) for row in data_b["rows"])
    assert ventas_b == Decimal("5000.00"), f"Expected 5000, got {ventas_b}"


# ---------------------------------------------------------------------------
# Task 5.4 TRIANGULATE — date range filter
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_date_range_filter_narrows_results(
    client: AsyncClient, db_session: AsyncSession
):
    suffix = uuid.uuid4().hex[:6]
    empresa = await _crear_empresa(db_session, f"DateRange-{suffix}")
    usuario = await _crear_usuario(db_session, f"admin_{suffix}@test.com", empresa.id)

    fecha_jun = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)
    fecha_dec = datetime(2026, 12, 15, 12, 0, tzinfo=timezone.utc)

    await _seed_venta(db_session, empresa.id, Decimal("1000.00"), fecha_jun)
    await _seed_venta(db_session, empresa.id, Decimal("500.00"), fecha_dec)

    # Filter to June only
    resp = await client.get(
        "/reportes/financieros?group_by=mes"
        "&fecha_desde=2026-06-01T00:00:00Z"
        "&fecha_hasta=2026-06-30T23:59:59Z",
        headers=_auth_header(usuario, "admin"),
    )
    assert resp.status_code == 200
    data = resp.json()

    periodos = [row["periodo"] for row in data["rows"]]
    # June must be in result
    assert "2026-06" in periodos
    # December must NOT be in result (filtered out)
    assert "2026-12" not in periodos


@pytest.mark.asyncio
async def test_no_filter_returns_all_periods(
    client: AsyncClient, db_session: AsyncSession
):
    suffix = uuid.uuid4().hex[:6]
    empresa = await _crear_empresa(db_session, f"NoDates-{suffix}")
    usuario = await _crear_usuario(db_session, f"admin_{suffix}@test.com", empresa.id)

    fecha_a = datetime(2026, 2, 10, tzinfo=timezone.utc)
    fecha_b = datetime(2026, 9, 10, tzinfo=timezone.utc)

    await _seed_venta(db_session, empresa.id, Decimal("300.00"), fecha_a)
    await _seed_venta(db_session, empresa.id, Decimal("600.00"), fecha_b)

    resp = await client.get(
        "/reportes/financieros?group_by=mes",
        headers=_auth_header(usuario, "admin"),
    )
    assert resp.status_code == 200
    data = resp.json()
    periods = [row["periodo"] for row in data["rows"]]
    assert "2026-02" in periods
    assert "2026-09" in periods


# ---------------------------------------------------------------------------
# Fix 2 — Symmetric UTC calendar-day boundary (ventas vs gastos)
# A venta (datetime) and a gasto (date) on the same UTC calendar day must land
# in the same period and both be included/excluded by the same fecha_hasta.
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_venta_and_gasto_same_utc_day_same_period(
    client: AsyncClient, db_session: AsyncSession
):
    """A venta with a mid-day datetime and a gasto on the same UTC calendar day
    must both appear in the same period bucket when grouped by 'dia'."""
    suffix = uuid.uuid4().hex[:6]
    empresa = await _crear_empresa(db_session, f"SameDayBoundary-{suffix}")
    usuario = await _crear_usuario(db_session, f"admin_{suffix}@test.com", empresa.id)

    # Venta at 14:30 UTC on 2026-06-15
    fecha_venta = datetime(2026, 6, 15, 14, 30, 0, tzinfo=timezone.utc)
    await _seed_venta(db_session, empresa.id, Decimal("500.00"), fecha_venta, Decimal("50.00"))

    # Gasto on the same calendar day
    await _seed_gasto(db_session, empresa.id, Decimal("100.00"), date(2026, 6, 15))

    resp = await client.get(
        "/reportes/financieros?group_by=dia",
        headers=_auth_header(usuario, "admin"),
    )
    assert resp.status_code == 200
    data = resp.json()
    rows_by_period = {row["periodo"]: row for row in data["rows"]}

    # Both venta and gasto must land in the same "2026-06-15" bucket
    assert "2026-06-15" in rows_by_period, f"Period 2026-06-15 missing; periods: {list(rows_by_period)}"
    row = rows_by_period["2026-06-15"]
    assert Decimal(row["ventas"]) == Decimal("500.00"), f"ventas mismatch: {row['ventas']}"
    assert Decimal(row["gastos"]) == Decimal("100.00"), f"gastos mismatch: {row['gastos']}"


@pytest.mark.asyncio
async def test_mid_day_fecha_hasta_includes_full_calendar_day(
    client: AsyncClient, db_session: AsyncSession
):
    """A mid-day fecha_hasta (e.g. 2026-06-15T14:00:00Z) must include a venta at
    23:59 on the same UTC calendar day, because both streams use the same
    calendar-day boundary (end of 2026-06-15)."""
    suffix = uuid.uuid4().hex[:6]
    empresa = await _crear_empresa(db_session, f"MidDayBoundary-{suffix}")
    usuario = await _crear_usuario(db_session, f"admin_{suffix}@test.com", empresa.id)

    # Venta late in the day on 2026-06-15
    fecha_late = datetime(2026, 6, 15, 23, 59, 0, tzinfo=timezone.utc)
    await _seed_venta(db_session, empresa.id, Decimal("800.00"), fecha_late, Decimal("40.00"))

    # Gasto on the same day
    await _seed_gasto(db_session, empresa.id, Decimal("50.00"), date(2026, 6, 15))

    # Venta in the next month — must be excluded
    fecha_future = datetime(2026, 7, 1, 10, 0, 0, tzinfo=timezone.utc)
    await _seed_venta(db_session, empresa.id, Decimal("999.00"), fecha_future, Decimal("40.00"))

    # fecha_hasta is mid-day on 2026-06-15 — symmetric boundary treats this as end of that day
    resp = await client.get(
        "/reportes/financieros?group_by=mes"
        "&fecha_desde=2026-06-01T00:00:00Z"
        "&fecha_hasta=2026-06-15T14:00:00Z",
        headers=_auth_header(usuario, "admin"),
    )
    assert resp.status_code == 200
    data = resp.json()
    rows_by_period = {row["periodo"]: row for row in data["rows"]}

    # 2026-06 must be present with BOTH the venta (23:59) and the gasto
    assert "2026-06" in rows_by_period, f"2026-06 missing; periods: {list(rows_by_period)}"
    row = rows_by_period["2026-06"]
    assert Decimal(row["ventas"]) == Decimal("800.00"), f"ventas mismatch: {row['ventas']}"
    assert Decimal(row["gastos"]) == Decimal("50.00"), f"gastos mismatch: {row['gastos']}"

    # 2026-07 must NOT be present (future venta filtered out)
    assert "2026-07" not in rows_by_period, f"2026-07 should be excluded; rows: {list(rows_by_period)}"
