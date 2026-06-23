"""Integration tests for C-19 rentabilidad — real PostgreSQL via testcontainers.

Tasks:
  6.1 Products ranking happy path — correct ganancia/margen, orden ordering
  6.2 NULL costo_unitario → margin null (not zero), ordered last
  6.3 Multi-tenant isolation — empresa A never sees empresa B data
  6.4 Access control — reportes:read → 200; cajero → 403 (both endpoints)
  6.5 Cortes: matched cut returns margin; NULL producto_id excluded; no sales → null price
  6.6 Date-range filter narrows results; no range aggregates all cobrada
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

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "src"))

from src.modules.auth.models import Empresa, Rol, Usuario
from src.modules.compra.models import Compra
from src.modules.desposte.models import CorteDesposte, Desposte
from src.modules.producto.models import Producto
from src.modules.proveedor.models import Proveedor
from src.modules.venta.models import DetalleVenta, Venta
from src.core.security import hash_password, create_access_token


# ---------------------------------------------------------------------------
# Shared seed helpers (mirror test_reporte_financiero_integration.py pattern)
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
    nombre: str = "Test Producto",
    plu_suffix: str = "",
) -> Producto:
    """Create a new product with unique PLU for this empresa."""
    plu = f"R{uuid.uuid4().hex[:6]}{plu_suffix}"
    producto = Producto(
        empresa_id=empresa_id,
        plu=plu,
        nombre=nombre,
        precio_publico=Decimal("100.0000"),
        precio_mayorista=Decimal("80.0000"),
        costo_por_kilo=Decimal("50.0000"),
        margen=Decimal("0.5000"),
        stock_actual=Decimal("100.0000"),
    )
    db.add(producto)
    await db.flush()
    return producto


async def _seed_venta_con_detalle(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    producto_id: uuid.UUID,
    importe: Decimal,
    kilos: Decimal,
    costo_unitario: Decimal | None,
    fecha: datetime,
    estado: str = "cobrada",
) -> Venta:
    """Seed a venta + one detalle with explicit cost snapshot."""
    venta = Venta(
        empresa_id=empresa_id,
        estado=estado,
        subtotal=importe,
        total=importe,
        fecha=fecha,
    )
    db.add(venta)
    await db.flush()

    det = DetalleVenta(
        venta_id=venta.id,
        producto_id=producto_id,
        cantidad_kilos=kilos,
        precio_unitario=(importe / kilos).quantize(Decimal("0.01")),
        importe=importe,
        costo_unitario=costo_unitario,
    )
    db.add(det)
    await db.commit()
    return venta


async def _seed_proveedor(db: AsyncSession, empresa_id: uuid.UUID) -> Proveedor:
    """Seed a minimal proveedor for this empresa."""
    proveedor = Proveedor(
        empresa_id=empresa_id,
        nombre=f"Proveedor-{uuid.uuid4().hex[:6]}",
    )
    db.add(proveedor)
    await db.flush()
    return proveedor


async def _seed_compra(db: AsyncSession, empresa_id: uuid.UUID, proveedor_id: uuid.UUID | None = None) -> Compra:
    """Seed a minimal compra needed by Desposte FK."""
    if proveedor_id is None:
        proveedor = await _seed_proveedor(db, empresa_id)
        proveedor_id = proveedor.id
    compra = Compra(
        empresa_id=empresa_id,
        proveedor_id=proveedor_id,
        fecha=date(2026, 6, 1),
        cantidad_medias_reses=1,
        peso_total=Decimal("100.000"),
        costo_total=Decimal("10000.000"),
        costo_por_kilo=Decimal("100.000"),
    )
    db.add(compra)
    await db.flush()
    return compra


async def _seed_corte(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    tipo_corte: str,
    costo_final_por_kilo: Decimal,
    producto_id: uuid.UUID | None,
    operador_id: uuid.UUID,
) -> CorteDesposte:
    """Seed a Proveedor → Compra → Desposte → CorteDesposte chain."""
    compra = await _seed_compra(db, empresa_id)
    desposte = Desposte(
        empresa_id=empresa_id,
        compra_id=compra.id,
        fecha=date(2026, 6, 1),
        operador_id=operador_id,
        estado="finalizado",
        rendimiento_total=Decimal("10.000"),
        merma=Decimal("0.500"),
    )
    db.add(desposte)
    await db.flush()

    corte = CorteDesposte(
        desposte_id=desposte.id,
        tipo_corte=tipo_corte,
        kilos_obtenidos=Decimal("5.000"),
        porcentaje_rendimiento=Decimal("50.000"),
        costo_asignado=Decimal("500.00"),
        costo_final_por_kilo=costo_final_por_kilo,
        producto_id=producto_id,
    )
    db.add(corte)
    await db.commit()
    await db.refresh(corte)
    return corte


# ---------------------------------------------------------------------------
# Task 6.1 — Products ranking happy path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_productos_ranking_happy_path(client: AsyncClient, db_session: AsyncSession):
    """Returns rows with correct ganancia/margen in mayor order."""
    suffix = uuid.uuid4().hex[:6]
    empresa = await _crear_empresa(db_session, f"RentHappy-{suffix}")
    usuario = await _crear_usuario(db_session, f"admin_{suffix}@test.com", empresa.id, "admin")

    prod_a = await _get_or_create_producto(db_session, empresa.id, "Producto A")
    prod_b = await _get_or_create_producto(db_session, empresa.id, "Producto B")

    fecha = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)

    # Prod A: importe=1000, kilos=10, costo=60/kilo → ganancia=400, margen=40%
    await _seed_venta_con_detalle(db_session, empresa.id, prod_a.id,
                                  Decimal("1000.00"), Decimal("10.000"),
                                  Decimal("60.00"), fecha)
    # Prod B: importe=600, kilos=5, costo=80/kilo → ganancia=200, margen=33.33%
    await _seed_venta_con_detalle(db_session, empresa.id, prod_b.id,
                                  Decimal("600.00"), Decimal("5.000"),
                                  Decimal("80.00"), fecha)

    resp = await client.get(
        "/rentabilidad/productos?orden=mayor",
        headers=_auth_header(usuario, "admin"),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "rows" in data
    rows = data["rows"]
    assert len(rows) >= 2

    # Find our two products
    rows_by_nombre = {r["nombre"]: r for r in rows if r["nombre"] in ("Producto A", "Producto B")}
    assert "Producto A" in rows_by_nombre
    assert "Producto B" in rows_by_nombre

    row_a = rows_by_nombre["Producto A"]
    assert Decimal(row_a["ventas"]) == Decimal("1000.00")
    assert Decimal(row_a["ganancia"]) == Decimal("400.00")
    assert Decimal(row_a["margen_porcentaje"]) == Decimal("40.00")

    # mayor order: A (40%) should come before B (33.33%)
    idx_a = next(i for i, r in enumerate(rows) if r["nombre"] == "Producto A")
    idx_b = next(i for i, r in enumerate(rows) if r["nombre"] == "Producto B")
    assert idx_a < idx_b


# ---------------------------------------------------------------------------
# Task 6.2 — NULL costo_unitario → null margin, ordered last
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_null_costo_margin_null_not_zero_ordered_last(
    client: AsyncClient, db_session: AsyncSession
):
    """NULL costo_unitario → ganancia=None (not zero) and product ordered last."""
    suffix = uuid.uuid4().hex[:6]
    empresa = await _crear_empresa(db_session, f"RentNull-{suffix}")
    usuario = await _crear_usuario(db_session, f"admin_{suffix}@test.com", empresa.id, "admin")

    prod_known = await _get_or_create_producto(db_session, empresa.id, f"KnownCost-{suffix}")
    prod_null = await _get_or_create_producto(db_session, empresa.id, f"NullCost-{suffix}")

    fecha = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)

    # Known cost product
    await _seed_venta_con_detalle(db_session, empresa.id, prod_known.id,
                                  Decimal("500.00"), Decimal("5.000"),
                                  Decimal("60.00"), fecha)
    # Null cost product
    await _seed_venta_con_detalle(db_session, empresa.id, prod_null.id,
                                  Decimal("500.00"), Decimal("5.000"),
                                  None, fecha)

    resp = await client.get(
        "/rentabilidad/productos?orden=mayor",
        headers=_auth_header(usuario, "admin"),
    )
    assert resp.status_code == 200, resp.text
    rows = resp.json()["rows"]

    null_rows = [r for r in rows if r["nombre"] == f"NullCost-{suffix}"]
    known_rows = [r for r in rows if r["nombre"] == f"KnownCost-{suffix}"]
    assert len(null_rows) == 1
    assert len(known_rows) == 1

    # Null margin must be explicitly null, not 0
    assert null_rows[0]["ganancia"] is None
    assert null_rows[0]["margen_porcentaje"] is None

    # Null product must appear AFTER the known product
    idx_null = rows.index(null_rows[0])
    idx_known = rows.index(known_rows[0])
    assert idx_null > idx_known


# ---------------------------------------------------------------------------
# Task 6.3 — Multi-tenant isolation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_multi_tenant_isolation_productos(client: AsyncClient, db_session: AsyncSession):
    """Empresa A request never returns empresa B products."""
    suffix = uuid.uuid4().hex[:6]
    emp_a = await _crear_empresa(db_session, f"RentA-{suffix}")
    emp_b = await _crear_empresa(db_session, f"RentB-{suffix}")

    user_a = await _crear_usuario(db_session, f"a_{suffix}@test.com", emp_a.id)
    user_b = await _crear_usuario(db_session, f"b_{suffix}@test.com", emp_b.id)

    prod_a = await _get_or_create_producto(db_session, emp_a.id, f"ProdA-{suffix}")
    prod_b = await _get_or_create_producto(db_session, emp_b.id, f"ProdB-{suffix}")

    fecha = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)
    await _seed_venta_con_detalle(db_session, emp_a.id, prod_a.id,
                                  Decimal("1000.00"), Decimal("5.000"), Decimal("60.00"), fecha)
    await _seed_venta_con_detalle(db_session, emp_b.id, prod_b.id,
                                  Decimal("5000.00"), Decimal("10.000"), Decimal("200.00"), fecha)

    # Empresa A sees only its own data
    resp_a = await client.get("/rentabilidad/productos", headers=_auth_header(user_a, "admin"))
    assert resp_a.status_code == 200
    names_a = [r["nombre"] for r in resp_a.json()["rows"]]
    assert f"ProdA-{suffix}" in names_a
    assert f"ProdB-{suffix}" not in names_a

    # Empresa B sees only its own data
    resp_b = await client.get("/rentabilidad/productos", headers=_auth_header(user_b, "admin"))
    assert resp_b.status_code == 200
    names_b = [r["nombre"] for r in resp_b.json()["rows"]]
    assert f"ProdB-{suffix}" in names_b
    assert f"ProdA-{suffix}" not in names_b


# ---------------------------------------------------------------------------
# Task 6.4 — Access control (both endpoints)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_access_control_reportes_read_allows_both_endpoints(
    client: AsyncClient, db_session: AsyncSession
):
    """admin (reportes:read) → 200 on both endpoints."""
    suffix = uuid.uuid4().hex[:6]
    empresa = await _crear_empresa(db_session, f"RentACL-{suffix}")
    admin = await _crear_usuario(db_session, f"admin_{suffix}@test.com", empresa.id, "admin")

    resp_productos = await client.get(
        "/rentabilidad/productos", headers=_auth_header(admin, "admin")
    )
    resp_cortes = await client.get(
        "/rentabilidad/cortes", headers=_auth_header(admin, "admin")
    )

    assert resp_productos.status_code == 200, resp_productos.text
    assert resp_cortes.status_code == 200, resp_cortes.text


@pytest.mark.asyncio
async def test_access_control_cajero_blocked_both_endpoints(
    client: AsyncClient, db_session: AsyncSession
):
    """cajero (no reportes:read) → 403 on both endpoints."""
    suffix = uuid.uuid4().hex[:6]
    empresa = await _crear_empresa(db_session, f"RentACL403-{suffix}")
    cajero = await _crear_usuario(db_session, f"cajero_{suffix}@test.com", empresa.id, "cajero")

    resp_productos = await client.get(
        "/rentabilidad/productos", headers=_auth_header(cajero, "cajero")
    )
    resp_cortes = await client.get(
        "/rentabilidad/cortes", headers=_auth_header(cajero, "cajero")
    )

    assert resp_productos.status_code == 403
    assert resp_cortes.status_code == 403


# ---------------------------------------------------------------------------
# Task 6.5 — Cortes: matched cut, NULL producto_id excluded, no sales → null price
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cortes_matched_cut_returns_margin(client: AsyncClient, db_session: AsyncSession):
    """Matched cut (producto_id linked to a product with sales) returns margin."""
    suffix = uuid.uuid4().hex[:6]
    empresa = await _crear_empresa(db_session, f"RentCorte-{suffix}")
    usuario = await _crear_usuario(db_session, f"admin_{suffix}@test.com", empresa.id, "admin")

    producto = await _get_or_create_producto(db_session, empresa.id, f"Asado-{suffix}")
    await _seed_corte(
        db_session, empresa.id, "asado", Decimal("800.00"),
        producto.id, usuario.id,
    )

    fecha = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)
    # 1 kilo of this product sold at 1000
    await _seed_venta_con_detalle(db_session, empresa.id, producto.id,
                                  Decimal("1000.00"), Decimal("1.000"),
                                  Decimal("600.00"), fecha)

    resp = await client.get("/rentabilidad/cortes", headers=_auth_header(usuario, "admin"))
    assert resp.status_code == 200, resp.text
    rows = resp.json()["rows"]

    matching = [r for r in rows if r["tipo_corte"] == "asado" and r["costo_por_kilo"] == "800.00"]
    assert len(matching) >= 1
    row = matching[0]
    assert Decimal(row["precio_venta_promedio"]) == Decimal("1000.00")
    assert Decimal(row["margen_por_kilo"]) == Decimal("200.00")
    assert Decimal(row["margen_porcentaje"]) == Decimal("20.00")


@pytest.mark.asyncio
async def test_cortes_null_producto_id_excluded(client: AsyncClient, db_session: AsyncSession):
    """Cut with producto_id=NULL is excluded from the response (not returned as null margin row)."""
    suffix = uuid.uuid4().hex[:6]
    empresa = await _crear_empresa(db_session, f"RentCorteNull-{suffix}")
    usuario = await _crear_usuario(db_session, f"admin_{suffix}@test.com", empresa.id, "admin")

    # Seed a cut with NULL producto_id
    await _seed_corte(
        db_session, empresa.id, "molida", Decimal("500.00"),
        None, usuario.id,
    )

    resp = await client.get("/rentabilidad/cortes", headers=_auth_header(usuario, "admin"))
    assert resp.status_code == 200, resp.text
    rows = resp.json()["rows"]
    # The null-linked cut must NOT appear in the response
    molida_rows = [r for r in rows if r["tipo_corte"] == "molida"]
    assert len(molida_rows) == 0


@pytest.mark.asyncio
async def test_cortes_linked_product_no_sales_null_price(
    client: AsyncClient, db_session: AsyncSession
):
    """Cut linked to product with no sales → precio_venta_promedio=null."""
    suffix = uuid.uuid4().hex[:6]
    empresa = await _crear_empresa(db_session, f"RentCorteNoSales-{suffix}")
    usuario = await _crear_usuario(db_session, f"admin_{suffix}@test.com", empresa.id, "admin")

    produto2 = await _get_or_create_producto(db_session, empresa.id, f"Vacio-{suffix}")
    await _seed_corte(
        db_session, empresa.id, "vacio", Decimal("900.00"),
        produto2.id, usuario.id,
    )
    # No ventas seeded for this empresa/product

    resp = await client.get("/rentabilidad/cortes", headers=_auth_header(usuario, "admin"))
    assert resp.status_code == 200, resp.text
    rows = resp.json()["rows"]

    vacio_rows = [r for r in rows if r["tipo_corte"] == "vacio"]
    assert len(vacio_rows) == 1
    row = vacio_rows[0]
    assert row["precio_venta_promedio"] is None
    assert row["margen_por_kilo"] is None
    assert row["margen_porcentaje"] is None


# ---------------------------------------------------------------------------
# Task 6.6 — Date-range filter
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_date_range_filter_narrows_products(client: AsyncClient, db_session: AsyncSession):
    """Sales outside the range do not contribute to the margin calculation."""
    suffix = uuid.uuid4().hex[:6]
    empresa = await _crear_empresa(db_session, f"RentDateRange-{suffix}")
    usuario = await _crear_usuario(db_session, f"admin_{suffix}@test.com", empresa.id, "admin")

    prod_range = await _get_or_create_producto(db_session, empresa.id, f"ProdRange-{suffix}")

    fecha_inside = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)
    fecha_outside = datetime(2026, 12, 15, 12, 0, tzinfo=timezone.utc)

    await _seed_venta_con_detalle(db_session, empresa.id, prod_range.id,
                                  Decimal("1000.00"), Decimal("5.000"),
                                  Decimal("60.00"), fecha_inside)
    await _seed_venta_con_detalle(db_session, empresa.id, prod_range.id,
                                  Decimal("500.00"), Decimal("2.000"),
                                  Decimal("60.00"), fecha_outside)

    # Only include the June sale
    resp = await client.get(
        "/rentabilidad/productos"
        "?fecha_desde=2026-06-01T00:00:00Z"
        "&fecha_hasta=2026-06-30T23:59:59Z",
        headers=_auth_header(usuario, "admin"),
    )
    assert resp.status_code == 200, resp.text
    rows = resp.json()["rows"]
    our_rows = [r for r in rows if r["nombre"] == f"ProdRange-{suffix}"]
    assert len(our_rows) == 1
    # ventas should only reflect the June sale (1000), not December (500)
    assert Decimal(our_rows[0]["ventas"]) == Decimal("1000.00")


@pytest.mark.asyncio
async def test_no_date_range_returns_all_cobrada(client: AsyncClient, db_session: AsyncSession):
    """No filter: all cobrada sales for the empresa are aggregated."""
    suffix = uuid.uuid4().hex[:6]
    empresa = await _crear_empresa(db_session, f"RentNoDate-{suffix}")
    usuario = await _crear_usuario(db_session, f"admin_{suffix}@test.com", empresa.id, "admin")

    prod_all = await _get_or_create_producto(db_session, empresa.id, f"ProdAllDates-{suffix}")

    fecha_a = datetime(2026, 2, 10, tzinfo=timezone.utc)
    fecha_b = datetime(2026, 9, 10, tzinfo=timezone.utc)

    await _seed_venta_con_detalle(db_session, empresa.id, prod_all.id,
                                  Decimal("300.00"), Decimal("3.000"),
                                  Decimal("40.00"), fecha_a)
    await _seed_venta_con_detalle(db_session, empresa.id, prod_all.id,
                                  Decimal("600.00"), Decimal("5.000"),
                                  Decimal("40.00"), fecha_b)

    resp = await client.get("/rentabilidad/productos", headers=_auth_header(usuario, "admin"))
    assert resp.status_code == 200, resp.text
    rows = resp.json()["rows"]
    our_rows = [r for r in rows if r["nombre"] == f"ProdAllDates-{suffix}"]
    assert len(our_rows) == 1
    # Both sales aggregated: 300 + 600 = 900
    assert Decimal(our_rows[0]["ventas"]) == Decimal("900.00")


# ---------------------------------------------------------------------------
# Task 9.3 — No /rentabilidad/general route
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_no_rentabilidad_general_route(client: AsyncClient, db_session: AsyncSession):
    """CA-4 is served by /reportes/financieros — /rentabilidad/general must 404."""
    suffix = uuid.uuid4().hex[:6]
    empresa = await _crear_empresa(db_session, f"RentNoGeneral-{suffix}")
    usuario = await _crear_usuario(db_session, f"admin_{suffix}@test.com", empresa.id, "admin")

    resp = await client.get(
        "/rentabilidad/general",
        headers=_auth_header(usuario, "admin"),
    )
    assert resp.status_code == 404
