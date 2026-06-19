import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.modules.auth.models import Usuario, Rol, Empresa
from src.modules.producto.models import Producto
from src.modules.stock.models import MovimientoStock
from src.core.security import hash_password, create_access_token


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _crear_empresa(db_session: AsyncSession, nombre: str = "Carniceria Test") -> Empresa:
    empresa = Empresa(nombre_comercial=nombre, activa=True)
    db_session.add(empresa)
    await db_session.commit()
    await db_session.refresh(empresa)
    return empresa


async def _crear_rol(db_session: AsyncSession, nombre: str = "Administrador", empresa_id=None) -> Rol:
    rol = Rol(nombre=nombre, empresa_id=empresa_id)
    db_session.add(rol)
    await db_session.commit()
    await db_session.refresh(rol)
    return rol


async def _crear_usuario(
    db_session: AsyncSession,
    email: str = "test@basile.app",
    password: str = "Password123",
    activo: bool = True,
    empresa_id=None,
    rol_id=None,
) -> Usuario:
    if rol_id is None:
        rol = await _crear_rol(db_session, empresa_id=empresa_id)
        rol_id = rol.id
    usuario = Usuario(
        email=email,
        contrasena_hash=hash_password(password),
        nombre="Test",
        apellido="User",
        rol_id=rol_id,
        activo=activo,
        empresa_id=empresa_id,
    )
    db_session.add(usuario)
    await db_session.commit()
    await db_session.refresh(usuario)
    return usuario


def _auth_header(usuario: Usuario, rol_nombre: str = "Administrador", empresa_id=None):
    token = create_access_token({
        "sub": str(usuario.id),
        "empresa_id": str(empresa_id or usuario.empresa_id),
        "rol": rol_nombre,
    })
    return {"Authorization": f"Bearer {token}"}


async def _crear_producto(
    db_session: AsyncSession,
    empresa_id: uuid.UUID,
    plu: str = "001",
    nombre: str = "Producto Test",
    stock_minimo: Decimal = Decimal("5.0000"),
    stock_actual: Decimal = Decimal("10.0000"),
) -> Producto:
    producto = Producto(
        empresa_id=empresa_id,
        plu=plu,
        nombre=nombre,
        precio_publico=Decimal("1000.0000"),
        precio_mayorista=Decimal("800.0000"),
        costo_por_kilo=Decimal("600.0000"),
        stock_actual=stock_actual,
        stock_minimo=stock_minimo,
    )
    producto.recalcular_margen()
    db_session.add(producto)
    await db_session.commit()
    await db_session.refresh(producto)
    return producto


async def _crear_movimiento(
    db_session: AsyncSession,
    empresa_id: uuid.UUID,
    producto_id: uuid.UUID,
    tipo: str,
    cantidad: Decimal,
    stock_resultante: Decimal,
) -> MovimientoStock:
    mov = MovimientoStock(
        empresa_id=empresa_id,
        producto_id=producto_id,
        tipo=tipo,
        cantidad_kilos=cantidad,
        stock_resultante=stock_resultante,
        fecha=__import__("datetime").datetime.utcnow(),
    )
    db_session.add(mov)
    await db_session.commit()
    await db_session.refresh(mov)
    return mov


# ---------------------------------------------------------------------------
# TASK-4.1: Stock calculado desde movimientos
# ---------------------------------------------------------------------------
class TestStockCalculado:
    async def test_stock_resultante_con_entradas_y_salidas(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="Encargado", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="enc@basile.app", empresa_id=empresa.id, rol_id=rol.id)
        producto = await _crear_producto(db_session, empresa.id, stock_actual=Decimal("0.0000"), stock_minimo=Decimal("5.0000"))

        # Entrada de 20 kg
        await _crear_movimiento(db_session, empresa.id, producto.id, "entrada_compra", Decimal("20.000"), Decimal("20.000"))
        # Salida de 7 kg
        await _crear_movimiento(db_session, empresa.id, producto.id, "salida_venta", Decimal("-7.000"), Decimal("13.000"))
        # Entrada de 5 kg
        await _crear_movimiento(db_session, empresa.id, producto.id, "entrada_desposte", Decimal("5.000"), Decimal("18.000"))

        response = await client.get("/stock", headers=_auth_header(usuario, rol_nombre="Encargado", empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        item = data["items"][0]
        assert item["producto_id"] == str(producto.id)
        # 20 - 7 + 5 = 18
        assert Decimal(item["stock_actual"]) == Decimal("18.000")
        assert item["estado"] == "ok"

    async def test_stock_sin_movimientos_es_cero(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="Encargado", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="enc@basile.app", empresa_id=empresa.id, rol_id=rol.id)
        producto = await _crear_producto(db_session, empresa.id, stock_actual=Decimal("0.0000"), stock_minimo=Decimal("1.0000"))

        response = await client.get("/stock", headers=_auth_header(usuario, rol_nombre="Encargado", empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        item = data["items"][0]
        assert Decimal(item["stock_actual"]) == Decimal("0.000")


# ---------------------------------------------------------------------------
# TASK-4.2 y 4.3: Bloqueo de stock negativo
# ---------------------------------------------------------------------------
class TestBloqueoStockNegativo:
    async def test_bloqueo_stock_negativo_en_ajuste(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="Encargado", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="enc@basile.app", empresa_id=empresa.id, rol_id=rol.id)
        producto = await _crear_producto(db_session, empresa.id, stock_actual=Decimal("0.0000"), stock_minimo=Decimal("0.0000"))
        # Stock actual = 5
        await _crear_movimiento(db_session, empresa.id, producto.id, "entrada_compra", Decimal("5.000"), Decimal("5.000"))

        response = await client.post("/stock/ajustes", headers=_auth_header(usuario, rol_nombre="Encargado", empresa_id=empresa.id), json={
            "producto_id": str(producto.id),
            "cantidad_kilos": "-6.000",
            "motivo": "Ajuste que excede stock",
        })
        assert response.status_code == 409
        assert "negativo" in response.json()["detail"].lower()

    async def test_ajuste_negativo_permitido_si_hay_stock(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="Encargado", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="enc@basile.app", empresa_id=empresa.id, rol_id=rol.id)
        producto = await _crear_producto(db_session, empresa.id, stock_actual=Decimal("0.0000"), stock_minimo=Decimal("0.0000"))
        await _crear_movimiento(db_session, empresa.id, producto.id, "entrada_compra", Decimal("10.000"), Decimal("10.000"))

        response = await client.post("/stock/ajustes", headers=_auth_header(usuario, rol_nombre="Encargado", empresa_id=empresa.id), json={
            "producto_id": str(producto.id),
            "cantidad_kilos": "-3.500",
            "motivo": "Merma registrada",
        })
        assert response.status_code == 201
        data = response.json()
        assert Decimal(data["cantidad_kilos"]) == Decimal("-3.500")
        assert Decimal(data["stock_resultante"]) == Decimal("6.500")


# ---------------------------------------------------------------------------
# TASK-4.4: Alertas de stock minimo
# ---------------------------------------------------------------------------
class TestAlertasStockMinimo:
    async def test_alerta_cuando_stock_menor_igual_minimo(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="Encargado", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="enc@basile.app", empresa_id=empresa.id, rol_id=rol.id)
        producto = await _crear_producto(db_session, empresa.id, stock_minimo=Decimal("5.0000"), stock_actual=Decimal("0.0000"))
        await _crear_movimiento(db_session, empresa.id, producto.id, "entrada_compra", Decimal("4.000"), Decimal("4.000"))

        response = await client.get("/stock/alertas", headers=_auth_header(usuario, rol_nombre="Encargado", empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["producto_id"] == str(producto.id)
        assert data[0]["estado"] == "alerta"
        assert Decimal(data[0]["stock_actual"]) == Decimal("4.000")

    async def test_critico_cuando_stock_es_cero(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="Encargado", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="enc@basile.app", empresa_id=empresa.id, rol_id=rol.id)
        producto = await _crear_producto(db_session, empresa.id, stock_minimo=Decimal("2.0000"), stock_actual=Decimal("0.0000"))
        # Sin movimientos => stock 0

        response = await client.get("/stock/alertas", headers=_auth_header(usuario, rol_nombre="Encargado", empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["estado"] == "critico"

    async def test_sin_alertas(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="Encargado", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="enc@basile.app", empresa_id=empresa.id, rol_id=rol.id)
        producto = await _crear_producto(db_session, empresa.id, stock_minimo=Decimal("5.0000"), stock_actual=Decimal("0.0000"))
        await _crear_movimiento(db_session, empresa.id, producto.id, "entrada_compra", Decimal("10.000"), Decimal("10.000"))

        response = await client.get("/stock/alertas", headers=_auth_header(usuario, rol_nombre="Encargado", empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


# ---------------------------------------------------------------------------
# TASK-4.5: Kardex paginado
# ---------------------------------------------------------------------------
class TestKardexPaginado:
    async def test_kardex_orden_descendente(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="Encargado", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="enc@basile.app", empresa_id=empresa.id, rol_id=rol.id)
        producto = await _crear_producto(db_session, empresa.id, stock_actual=Decimal("0.0000"))

        for i in range(5):
            await _crear_movimiento(db_session, empresa.id, producto.id, "entrada_compra", Decimal("1.000"), Decimal(str(i + 1)))

        response = await client.get(f"/stock/movimientos/{producto.id}?skip=0&limit=3", headers=_auth_header(usuario, rol_nombre="Encargado", empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 3
        # El mas reciente primero
        fechas = [item["fecha"] for item in data["items"]]
        assert fechas == sorted(fechas, reverse=True)


# ---------------------------------------------------------------------------
# TASK-4.6: Aislamiento multi-tenant
# ---------------------------------------------------------------------------
class TestAislamientoMultiTenant:
    async def test_usuario_no_ve_stock_de_otra_empresa(self, client: AsyncClient, db_session: AsyncSession):
        empresa_a = await _crear_empresa(db_session, nombre="Empresa A")
        empresa_b = await _crear_empresa(db_session, nombre="Empresa B")
        rol = await _crear_rol(db_session, nombre="Encargado", empresa_id=empresa_a.id)
        usuario_a = await _crear_usuario(db_session, email="enc_a@basile.app", empresa_id=empresa_a.id, rol_id=rol.id)
        producto_b = await _crear_producto(db_session, empresa_b.id, plu="B01", nombre="Producto B")
        await _crear_movimiento(db_session, empresa_b.id, producto_b.id, "entrada_compra", Decimal("10.000"), Decimal("10.000"))

        response = await client.get("/stock", headers=_auth_header(usuario_a, rol_nombre="Encargado", empresa_id=empresa_a.id))
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    async def test_kardex_producto_de_otra_empresa_devuelve_404(self, client: AsyncClient, db_session: AsyncSession):
        empresa_a = await _crear_empresa(db_session, nombre="Empresa A")
        empresa_b = await _crear_empresa(db_session, nombre="Empresa B")
        rol = await _crear_rol(db_session, nombre="Encargado", empresa_id=empresa_a.id)
        usuario_a = await _crear_usuario(db_session, email="enc_a@basile.app", empresa_id=empresa_a.id, rol_id=rol.id)
        producto_b = await _crear_producto(db_session, empresa_b.id, plu="B01", nombre="Producto B")

        response = await client.get(f"/stock/movimientos/{producto_b.id}", headers=_auth_header(usuario_a, rol_nombre="Encargado", empresa_id=empresa_a.id))
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# TASK-4.7: Ajuste requiere rol Encargado/Admin
# ---------------------------------------------------------------------------
class TestPermisosAjuste:
    async def test_cajero_no_puede_ajustar_stock(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_cajero = await _crear_rol(db_session, nombre="Cajero", empresa_id=empresa.id)
        usuario_cajero = await _crear_usuario(db_session, email="cajero@basile.app", empresa_id=empresa.id, rol_id=rol_cajero.id)
        producto = await _crear_producto(db_session, empresa.id)

        response = await client.post("/stock/ajustes", headers=_auth_header(usuario_cajero, rol_nombre="Cajero", empresa_id=empresa.id), json={
            "producto_id": str(producto.id),
            "cantidad_kilos": "5.000",
            "motivo": "Intento de ajuste",
        })
        assert response.status_code == 403

    async def test_admin_puede_ajustar_stock(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_admin = await _crear_rol(db_session, nombre="Administrador", empresa_id=empresa.id)
        usuario_admin = await _crear_usuario(db_session, email="admin@basile.app", empresa_id=empresa.id, rol_id=rol_admin.id)
        producto = await _crear_producto(db_session, empresa.id, stock_actual=Decimal("0.0000"), stock_minimo=Decimal("0.0000"))

        response = await client.post("/stock/ajustes", headers=_auth_header(usuario_admin, rol_nombre="Administrador", empresa_id=empresa.id), json={
            "producto_id": str(producto.id),
            "cantidad_kilos": "5.000",
            "motivo": "Ajuste admin",
        })
        assert response.status_code == 201
