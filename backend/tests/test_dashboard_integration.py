"""Integration tests for the dashboard endpoints.

TDD cycle: RED → GREEN → TRIANGULATE → REFACTOR
Uses testcontainers (real PostgreSQL). Every test is isolated via transaction rollback.

Covers tasks:
  2.1 — ventas_dia/ventas_mes only include 'cobrada' ventas
  2.2 — kilos_vendidos sums cantidad_kilos of cobradas
  2.3 — clientes_atendidos counts cobradas of the day (including NULL cliente_id)
  2.4 — stock_critico counts active products with stock_actual <= stock_minimo
  2.5 — gastos_mes sums gasto.importe of the month
  2.6 — isolation: empresa A doesn't see empresa B data
  3.1 — cajero/vendedor receives ganancia_bruta/neta = null
  3.2 — without costo_unitario snapshot: ganancia null + ganancia_disponible: false
  3.4 — with snapshot + reportes:read: ganancia computed correctly
  4.1 — rankings returns products ordered by SUM(cantidad_kilos) desc
  5.1 — ventas_diarias groups by day (last 7); ventas_mensuales by month (last 12)
  5.2 — distribucion_medio_pago groups SUM(importe) by medio_pago
"""
import uuid
from datetime import datetime, date, timezone, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.modules.auth.models import Usuario, Rol
from src.modules.empresa.models import Empresa
from src.modules.venta.models import Venta, DetalleVenta, PagoVenta
from src.modules.producto.models import Producto
from src.modules.gasto.models import Gasto
from src.modules.stock.models import MovimientoStock
from src.core.security import create_access_token


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

async def _crear_empresa(db: AsyncSession, nombre: str = "Emp Test") -> Empresa:
    emp = Empresa(nombre_comercial=nombre, activa=True)
    db.add(emp)
    await db.commit()
    await db.refresh(emp)
    return emp


async def _crear_rol(
    db: AsyncSession, nombre: str = "cajero", empresa_id: uuid.UUID | None = None
) -> Rol:
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
    from src.core.security import hash_password
    usuario = Usuario(
        email=email,
        contrasena_hash=hash_password("Pass123!"),
        nombre="Dash",
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
    plu: str,
    nombre: str = "Producto",
    precio_publico: Decimal = Decimal("1000.00"),
    costo_por_kilo: Decimal = Decimal("400.00"),
    stock_actual: Decimal = Decimal("50.000"),
    stock_minimo: Decimal | None = None,
) -> Producto:
    prod = Producto(
        empresa_id=empresa_id,
        plu=plu,
        nombre=nombre,
        precio_publico=precio_publico,
        precio_mayorista=Decimal("800.00"),
        costo_por_kilo=costo_por_kilo,
        stock_actual=stock_actual,
        stock_minimo=stock_minimo,
        activo=True,
    )
    prod.recalcular_margen()
    db.add(prod)
    await db.commit()
    await db.refresh(prod)
    return prod


async def _crear_venta_cobrada(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    total: Decimal,
    fecha: datetime,
    kilos: Decimal = Decimal("1.000"),
    producto_id: uuid.UUID | None = None,
    costo_unitario: Decimal | None = None,
    medio_pago: str = "efectivo",
    cliente_id: uuid.UUID | None = None,
) -> Venta:
    """Create a cobrada sale directly in DB (bypassing endpoint for speed)."""
    # Ensure a real producto FK reference exists
    if producto_id is None:
        prod = await _crear_producto(
            db, empresa_id, plu=f"VC{uuid.uuid4().hex[:6]}", nombre="Prod Test"
        )
        producto_id = prod.id

    venta = Venta(
        empresa_id=empresa_id,
        cliente_id=cliente_id,
        tipo_cliente_al_momento="publico_general" if cliente_id is None else "minorista",
        estado="cobrada",
        subtotal=total,
        descuentos=Decimal("0.00"),
        total=total,
        fecha=fecha,
    )
    db.add(venta)
    await db.flush()

    detalle = DetalleVenta(
        venta_id=venta.id,
        producto_id=producto_id,
        cantidad_kilos=kilos,
        precio_unitario=total / kilos,
        importe=total,
        costo_unitario=costo_unitario,
    )
    db.add(detalle)

    pago = PagoVenta(
        venta_id=venta.id,
        medio_pago=medio_pago,
        importe=total,
    )
    db.add(pago)

    await db.commit()
    await db.refresh(venta)
    return venta


async def _crear_venta_no_cobrada(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    total: Decimal,
    fecha: datetime,
    estado: str = "anulada",
) -> Venta:
    venta = Venta(
        empresa_id=empresa_id,
        estado=estado,
        subtotal=total,
        descuentos=Decimal("0.00"),
        total=total,
        fecha=fecha,
        tipo_cliente_al_momento="publico_general",
    )
    db.add(venta)
    await db.commit()
    await db.refresh(venta)
    return venta


async def _crear_gasto(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    importe: Decimal,
    fecha: date | None = None,
) -> Gasto:
    gasto = Gasto(
        empresa_id=empresa_id,
        fecha=fecha or datetime.now(timezone.utc).date(),
        categoria="insumos",
        descripcion="Test gasto",
        importe=importe,
        medio_pago="efectivo",
    )
    db.add(gasto)
    await db.commit()
    await db.refresh(gasto)
    return gasto


def _token(usuario: Usuario, rol_nombre: str) -> dict:
    token = create_access_token({
        "sub": str(usuario.id),
        "empresa_id": str(usuario.empresa_id),
        "rol": rol_nombre,
    })
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Tests — Task 2.1: ventas_dia/ventas_mes only count 'cobrada'
# ---------------------------------------------------------------------------
class TestIndicadoresVentas:
    async def test_ventas_dia_solo_cobradas(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """ventas_dia sums only cobradas. Anuladas/en_curso are excluded."""
        emp = await _crear_empresa(db_session, "VD-Cobrada")
        rol = await _crear_rol(db_session, "cajero", emp.id)
        user = await _crear_usuario(db_session, "vd1@d.com", emp.id, rol.id)

        ahora = datetime.now(timezone.utc)
        # One cobrada — should be counted
        await _crear_venta_cobrada(db_session, emp.id, Decimal("500.00"), ahora)
        # One anulada — must NOT be counted
        await _crear_venta_no_cobrada(db_session, emp.id, Decimal("999.00"), ahora, estado="anulada")

        resp = await client.get("/dashboard/indicadores", headers=_token(user, "cajero"))
        assert resp.status_code == 200
        data = resp.json()
        assert Decimal(data["ventas_dia"]) == Decimal("500.00")

    async def test_ventas_dia_excluye_en_curso_y_suspendida(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Triangulation: en_curso and suspendida ventas do not count."""
        emp = await _crear_empresa(db_session, "VD-ExcludeStates")
        rol = await _crear_rol(db_session, "cajero", emp.id)
        user = await _crear_usuario(db_session, "vd2@d.com", emp.id, rol.id)

        ahora = datetime.now(timezone.utc)
        await _crear_venta_no_cobrada(db_session, emp.id, Decimal("200.00"), ahora, "en_curso")
        await _crear_venta_no_cobrada(db_session, emp.id, Decimal("300.00"), ahora, "suspendida")

        resp = await client.get("/dashboard/indicadores", headers=_token(user, "cajero"))
        assert resp.status_code == 200
        assert Decimal(resp.json()["ventas_dia"]) == Decimal("0.00")

    async def test_ventas_mes_suma_todo_el_mes(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """ventas_mes sums all cobradas from month start to now."""
        emp = await _crear_empresa(db_session, "VM-Mes")
        rol = await _crear_rol(db_session, "cajero", emp.id)
        user = await _crear_usuario(db_session, "vm1@d.com", emp.id, rol.id)

        ahora = datetime.now(timezone.utc)
        # Two sales this month
        await _crear_venta_cobrada(db_session, emp.id, Decimal("1000.00"), ahora)
        await _crear_venta_cobrada(db_session, emp.id, Decimal("2000.00"), ahora)

        resp = await client.get("/dashboard/indicadores", headers=_token(user, "cajero"))
        assert resp.status_code == 200
        assert Decimal(resp.json()["ventas_mes"]) == Decimal("3000.00")


# ---------------------------------------------------------------------------
# Tests — Task 2.2: kilos_vendidos
# ---------------------------------------------------------------------------
class TestKilosVendidos:
    async def test_kilos_vendidos_mes(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """kilos_vendidos sums cantidad_kilos from cobradas of the month."""
        emp = await _crear_empresa(db_session, "KV-Mes")
        rol = await _crear_rol(db_session, "cajero", emp.id)
        user = await _crear_usuario(db_session, "kv1@d.com", emp.id, rol.id)

        ahora = datetime.now(timezone.utc)
        await _crear_venta_cobrada(
            db_session, emp.id, Decimal("800.00"), ahora, kilos=Decimal("2.500")
        )
        await _crear_venta_cobrada(
            db_session, emp.id, Decimal("400.00"), ahora, kilos=Decimal("1.000")
        )

        resp = await client.get("/dashboard/indicadores", headers=_token(user, "cajero"))
        assert resp.status_code == 200
        assert Decimal(resp.json()["kilos_vendidos"]) == Decimal("3.500")

    async def test_kilos_vendidos_excluye_anuladas(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Triangulation: anuladas do not contribute to kilos."""
        emp = await _crear_empresa(db_session, "KV-Anuladas")
        rol = await _crear_rol(db_session, "cajero", emp.id)
        user = await _crear_usuario(db_session, "kv2@d.com", emp.id, rol.id)

        ahora = datetime.now(timezone.utc)
        await _crear_venta_no_cobrada(db_session, emp.id, Decimal("500.00"), ahora)

        resp = await client.get("/dashboard/indicadores", headers=_token(user, "cajero"))
        assert resp.status_code == 200
        assert Decimal(resp.json()["kilos_vendidos"]) == Decimal("0.000")


# ---------------------------------------------------------------------------
# Tests — Task 2.3: clientes_atendidos
# ---------------------------------------------------------------------------
class TestClientesAtendidos:
    async def test_clientes_atendidos_cuenta_ventas_del_dia(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """clientes_atendidos = count of cobradas today, including NULL cliente_id."""
        emp = await _crear_empresa(db_session, "CA-Dia")
        rol = await _crear_rol(db_session, "cajero", emp.id)
        user = await _crear_usuario(db_session, "ca1@d.com", emp.id, rol.id)

        ahora = datetime.now(timezone.utc)
        # Two ventas without cliente_id (mostrador)
        await _crear_venta_cobrada(db_session, emp.id, Decimal("100.00"), ahora)
        await _crear_venta_cobrada(db_session, emp.id, Decimal("200.00"), ahora)

        resp = await client.get("/dashboard/indicadores", headers=_token(user, "cajero"))
        assert resp.status_code == 200
        assert resp.json()["clientes_atendidos"] == 2

    async def test_clientes_atendidos_no_cuenta_anuladas(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Triangulation: anuladas are not counted in clientes_atendidos."""
        emp = await _crear_empresa(db_session, "CA-Anuladas")
        rol = await _crear_rol(db_session, "cajero", emp.id)
        user = await _crear_usuario(db_session, "ca2@d.com", emp.id, rol.id)

        ahora = datetime.now(timezone.utc)
        await _crear_venta_no_cobrada(db_session, emp.id, Decimal("100.00"), ahora)

        resp = await client.get("/dashboard/indicadores", headers=_token(user, "cajero"))
        assert resp.status_code == 200
        assert resp.json()["clientes_atendidos"] == 0


# ---------------------------------------------------------------------------
# Tests — Task 2.4: stock_critico
# ---------------------------------------------------------------------------
class TestStockCritico:
    async def test_stock_critico_cuenta_por_debajo_minimo(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """stock_critico counts active products with stock_actual <= stock_minimo."""
        emp = await _crear_empresa(db_session, "SC-Critico")
        rol = await _crear_rol(db_session, "cajero", emp.id)
        user = await _crear_usuario(db_session, "sc1@d.com", emp.id, rol.id)

        # Product at critical level
        await _crear_producto(
            db_session, emp.id, "SC01", stock_actual=Decimal("2.000"), stock_minimo=Decimal("5.000")
        )
        # Product above minimum — should NOT count
        await _crear_producto(
            db_session, emp.id, "SC02", stock_actual=Decimal("10.000"), stock_minimo=Decimal("5.000")
        )
        # Product without stock_minimo — should NOT count
        await _crear_producto(
            db_session, emp.id, "SC03", stock_actual=Decimal("1.000"), stock_minimo=None
        )

        resp = await client.get("/dashboard/indicadores", headers=_token(user, "cajero"))
        assert resp.status_code == 200
        assert resp.json()["stock_critico"] == 1

    async def test_stock_critico_exactamente_en_minimo(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Triangulation: product exactly at stock_minimo also counts (<=)."""
        emp = await _crear_empresa(db_session, "SC-Exact")
        rol = await _crear_rol(db_session, "cajero", emp.id)
        user = await _crear_usuario(db_session, "sc2@d.com", emp.id, rol.id)

        await _crear_producto(
            db_session, emp.id, "SCE1", stock_actual=Decimal("5.000"), stock_minimo=Decimal("5.000")
        )

        resp = await client.get("/dashboard/indicadores", headers=_token(user, "cajero"))
        assert resp.status_code == 200
        assert resp.json()["stock_critico"] == 1


# ---------------------------------------------------------------------------
# Tests — Task 2.5: gastos_mes
# ---------------------------------------------------------------------------
class TestGastosMes:
    async def test_gastos_mes_suma_del_mes(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """gastos_mes sums Gasto.importe for the current month."""
        emp = await _crear_empresa(db_session, "GM-Mes")
        rol = await _crear_rol(db_session, "cajero", emp.id)
        user = await _crear_usuario(db_session, "gm1@d.com", emp.id, rol.id)

        await _crear_gasto(db_session, emp.id, Decimal("300.00"))
        await _crear_gasto(db_session, emp.id, Decimal("150.00"))

        resp = await client.get("/dashboard/indicadores", headers=_token(user, "cajero"))
        assert resp.status_code == 200
        assert Decimal(resp.json()["gastos_mes"]) == Decimal("450.00")

    async def test_gastos_mes_sin_gastos_devuelve_cero(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Triangulation: empresa with no gastos returns 0.00."""
        emp = await _crear_empresa(db_session, "GM-Zero")
        rol = await _crear_rol(db_session, "cajero", emp.id)
        user = await _crear_usuario(db_session, "gm2@d.com", emp.id, rol.id)

        resp = await client.get("/dashboard/indicadores", headers=_token(user, "cajero"))
        assert resp.status_code == 200
        assert Decimal(resp.json()["gastos_mes"]) == Decimal("0.00")


# ---------------------------------------------------------------------------
# Tests — Task 2.6: empresa isolation
# ---------------------------------------------------------------------------
class TestAislamiento:
    async def test_empresa_a_no_ve_datos_empresa_b(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Empresa A's indicators must not include empresa B's data."""
        emp_a = await _crear_empresa(db_session, "EmpA")
        emp_b = await _crear_empresa(db_session, "EmpB")

        rol_a = await _crear_rol(db_session, "cajero", emp_a.id)
        user_a = await _crear_usuario(db_session, "iso_a@d.com", emp_a.id, rol_a.id)

        ahora = datetime.now(timezone.utc)
        # Empresa B has a sale — empresa A must NOT see it
        await _crear_venta_cobrada(db_session, emp_b.id, Decimal("9999.00"), ahora)

        resp = await client.get("/dashboard/indicadores", headers=_token(user_a, "cajero"))
        assert resp.status_code == 200
        data = resp.json()
        assert Decimal(data["ventas_dia"]) == Decimal("0.00")
        assert Decimal(data["ventas_mes"]) == Decimal("0.00")

    async def test_empresa_b_no_ve_datos_empresa_a(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Triangulation: the isolation is bidirectional."""
        emp_a = await _crear_empresa(db_session, "EmpA2")
        emp_b = await _crear_empresa(db_session, "EmpB2")

        rol_b = await _crear_rol(db_session, "cajero", emp_b.id)
        user_b = await _crear_usuario(db_session, "iso_b@d.com", emp_b.id, rol_b.id)

        ahora = datetime.now(timezone.utc)
        await _crear_venta_cobrada(db_session, emp_a.id, Decimal("5000.00"), ahora)

        resp = await client.get("/dashboard/indicadores", headers=_token(user_b, "cajero"))
        assert resp.status_code == 200
        assert Decimal(resp.json()["ventas_mes"]) == Decimal("0.00")


# ---------------------------------------------------------------------------
# Tests — Task 3.1: permission gate for ganancia
# ---------------------------------------------------------------------------
class TestGananciaPorPermiso:
    async def test_cajero_recibe_ganancia_null(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Cajero does NOT have reportes:read → ganancia_bruta/neta must be null."""
        emp = await _crear_empresa(db_session, "G-Cajero")
        rol = await _crear_rol(db_session, "cajero", emp.id)
        user = await _crear_usuario(db_session, "gcj1@d.com", emp.id, rol.id)

        resp = await client.get("/dashboard/indicadores", headers=_token(user, "cajero"))
        assert resp.status_code == 200
        data = resp.json()
        assert data["ganancia_bruta"] is None
        assert data["ganancia_neta"] is None

    async def test_vendedor_recibe_ganancia_null(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Triangulation: vendedor also lacks reportes:read → null ganancia."""
        emp = await _crear_empresa(db_session, "G-Vendedor")
        rol = await _crear_rol(db_session, "vendedor", emp.id)
        user = await _crear_usuario(db_session, "gvd1@d.com", emp.id, rol.id)

        resp = await client.get("/dashboard/indicadores", headers=_token(user, "vendedor"))
        assert resp.status_code == 200
        data = resp.json()
        assert data["ganancia_bruta"] is None
        assert data["ganancia_neta"] is None


# ---------------------------------------------------------------------------
# Tests — Task 3.2: no snapshot → ganancia_disponible false
# ---------------------------------------------------------------------------
class TestGananciaDisponible:
    async def test_sin_snapshot_ganancia_no_disponible(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """When costo_unitario is NULL on detail lines → ganancia_disponible: false."""
        emp = await _crear_empresa(db_session, "GD-NoSnap")
        rol = await _crear_rol(db_session, "admin", emp.id)
        user = await _crear_usuario(db_session, "gds1@d.com", emp.id, rol.id)

        ahora = datetime.now(timezone.utc)
        # Sale with NULL costo_unitario (pre-snapshot historical)
        await _crear_venta_cobrada(
            db_session, emp.id, Decimal("1000.00"), ahora, costo_unitario=None
        )

        resp = await client.get("/dashboard/indicadores", headers=_token(user, "admin"))
        assert resp.status_code == 200
        data = resp.json()
        assert data["ganancia_disponible"] is False
        assert data["ganancia_bruta"] is None
        assert data["ganancia_neta"] is None

    async def test_con_snapshot_ganancia_disponible(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Triangulation: with costo_unitario populated → ganancia_disponible: true."""
        emp = await _crear_empresa(db_session, "GD-WithSnap")
        rol = await _crear_rol(db_session, "admin", emp.id)
        user = await _crear_usuario(db_session, "gds2@d.com", emp.id, rol.id)

        ahora = datetime.now(timezone.utc)
        # Sale with snapshot — importe=1000, costo=2kg × 400 = 800 → ganancia=200
        await _crear_venta_cobrada(
            db_session, emp.id, Decimal("1000.00"), ahora,
            kilos=Decimal("2.000"), costo_unitario=Decimal("400.00")
        )
        await _crear_gasto(db_session, emp.id, Decimal("100.00"))

        resp = await client.get("/dashboard/indicadores", headers=_token(user, "admin"))
        assert resp.status_code == 200
        data = resp.json()
        assert data["ganancia_disponible"] is True
        assert Decimal(data["ganancia_bruta"]) == Decimal("200.00")
        # ganancia_neta = ganancia_bruta - gastos_mes = 200 - 100 = 100
        assert Decimal(data["ganancia_neta"]) == Decimal("100.00")


# ---------------------------------------------------------------------------
# Tests — Task 4.1: rankings
# ---------------------------------------------------------------------------
class TestRankings:
    async def test_productos_ordenados_por_kilos(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Rankings returns products ordered by SUM(cantidad_kilos) desc."""
        emp = await _crear_empresa(db_session, "RK-Top")
        rol = await _crear_rol(db_session, "cajero", emp.id)
        user = await _crear_usuario(db_session, "rk1@d.com", emp.id, rol.id)

        prod_a = await _crear_producto(db_session, emp.id, "RKA", nombre="Asado")
        prod_b = await _crear_producto(db_session, emp.id, "RKB", nombre="Vacío")

        ahora = datetime.now(timezone.utc)
        # prod_b sells more kilos
        await _crear_venta_cobrada(
            db_session, emp.id, Decimal("2000.00"), ahora,
            kilos=Decimal("5.000"), producto_id=prod_b.id
        )
        await _crear_venta_cobrada(
            db_session, emp.id, Decimal("1000.00"), ahora,
            kilos=Decimal("2.000"), producto_id=prod_a.id
        )

        resp = await client.get("/dashboard/rankings", headers=_token(user, "cajero"))
        assert resp.status_code == 200
        items = resp.json()["productos_mas_vendidos"]
        assert len(items) == 2
        assert items[0]["nombre"] == "Vacío"
        assert Decimal(items[0]["kilos"]) == Decimal("5.000")
        assert items[1]["nombre"] == "Asado"

    async def test_rankings_empresa_sin_ventas_lista_vacia(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Triangulation: empresa with no cobradas returns empty ranking."""
        emp = await _crear_empresa(db_session, "RK-Empty")
        rol = await _crear_rol(db_session, "cajero", emp.id)
        user = await _crear_usuario(db_session, "rk2@d.com", emp.id, rol.id)

        resp = await client.get("/dashboard/rankings", headers=_token(user, "cajero"))
        assert resp.status_code == 200
        assert resp.json()["productos_mas_vendidos"] == []


# ---------------------------------------------------------------------------
# Tests — Task 5.1 & 5.2: graficos endpoint
# ---------------------------------------------------------------------------
class TestGraficos:
    async def test_distribucion_medio_pago(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """distribucion_medio_pago groups SUM(importe) by medio_pago."""
        emp = await _crear_empresa(db_session, "GF-MedioPago")
        rol = await _crear_rol(db_session, "cajero", emp.id)
        user = await _crear_usuario(db_session, "gf1@d.com", emp.id, rol.id)

        ahora = datetime.now(timezone.utc)
        await _crear_venta_cobrada(
            db_session, emp.id, Decimal("500.00"), ahora, medio_pago="efectivo"
        )
        await _crear_venta_cobrada(
            db_session, emp.id, Decimal("300.00"), ahora, medio_pago="tarjeta"
        )
        await _crear_venta_cobrada(
            db_session, emp.id, Decimal("200.00"), ahora, medio_pago="efectivo"
        )

        resp = await client.get("/dashboard/graficos", headers=_token(user, "cajero"))
        assert resp.status_code == 200
        dist = {item["medio_pago"]: Decimal(item["total"]) for item in resp.json()["distribucion_medio_pago"]}
        assert dist["efectivo"] == Decimal("700.00")
        assert dist["tarjeta"] == Decimal("300.00")

    async def test_ventas_diarias_agrupa_por_dia(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """ventas_diarias groups by day (last 7 days)."""
        emp = await _crear_empresa(db_session, "GF-Diarias")
        rol = await _crear_rol(db_session, "cajero", emp.id)
        user = await _crear_usuario(db_session, "gf2@d.com", emp.id, rol.id)

        ahora = datetime.now(timezone.utc)
        await _crear_venta_cobrada(db_session, emp.id, Decimal("1000.00"), ahora)

        resp = await client.get("/dashboard/graficos", headers=_token(user, "cajero"))
        assert resp.status_code == 200
        diarias = resp.json()["ventas_diarias"]
        today_str = ahora.strftime("%Y-%m-%d")
        today_total = next(
            (Decimal(item["total"]) for item in diarias if item["fecha"] == today_str),
            None,
        )
        assert today_total is not None
        assert today_total == Decimal("1000.00")

    async def test_distribucion_medio_pago_excluye_anuladas(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Triangulation: anuladas are NOT included in medio_pago distribution."""
        emp = await _crear_empresa(db_session, "GF-Anuladas")
        rol = await _crear_rol(db_session, "cajero", emp.id)
        user = await _crear_usuario(db_session, "gf3@d.com", emp.id, rol.id)

        ahora = datetime.now(timezone.utc)
        await _crear_venta_no_cobrada(db_session, emp.id, Decimal("1000.00"), ahora)

        resp = await client.get("/dashboard/graficos", headers=_token(user, "cajero"))
        assert resp.status_code == 200
        assert resp.json()["distribucion_medio_pago"] == []
