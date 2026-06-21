import uuid
from decimal import Decimal
from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.modules.auth.models import Usuario, Rol, Empresa
from src.modules.producto.models import Producto
from src.modules.stock.models import MovimientoStock
from src.modules.caja.models import Caja, MovimientoCaja
from src.core.security import hash_password, create_access_token


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _crear_empresa(db: AsyncSession, nombre: str = "Carniceria Test") -> Empresa:
    empresa = Empresa(nombre_comercial=nombre, activa=True)
    db.add(empresa)
    await db.commit()
    await db.refresh(empresa)
    return empresa


async def _crear_rol(db: AsyncSession, nombre: str = "cajero", empresa_id=None) -> Rol:
    rol = Rol(nombre=nombre, empresa_id=empresa_id)
    db.add(rol)
    await db.commit()
    await db.refresh(rol)
    return rol


async def _crear_usuario(
    db: AsyncSession,
    email: str = "cajero@basile.app",
    empresa_id=None,
    rol_id=None,
) -> Usuario:
    usuario = Usuario(
        email=email,
        contrasena_hash=hash_password("Password123"),
        nombre="Test",
        apellido="User",
        rol_id=rol_id,
        activo=True,
        empresa_id=empresa_id,
    )
    db.add(usuario)
    await db.commit()
    await db.refresh(usuario)
    return usuario


def _auth_header(usuario: Usuario, rol_nombre: str = "cajero", empresa_id=None):
    token = create_access_token({
        "sub": str(usuario.id),
        "empresa_id": str(empresa_id or usuario.empresa_id),
        "rol": rol_nombre,
    })
    return {"Authorization": f"Bearer {token}"}


async def _crear_producto(db: AsyncSession, empresa_id: uuid.UUID, plu: str = "001") -> Producto:
    producto = Producto(
        empresa_id=empresa_id,
        plu=plu,
        nombre="Asado",
        precio_publico=Decimal("1000.0000"),
        precio_mayorista=Decimal("800.0000"),
        costo_por_kilo=Decimal("600.0000"),
        stock_actual=Decimal("100.0000"),
    )
    producto.recalcular_margen()
    db.add(producto)
    await db.commit()
    await db.refresh(producto)
    mov = MovimientoStock(
        empresa_id=empresa_id,
        producto_id=producto.id,
        tipo="entrada_compra",
        cantidad_kilos=Decimal("100.0000"),
        stock_resultante=Decimal("100.0000"),
        fecha=datetime.utcnow(),
    )
    db.add(mov)
    await db.commit()
    return producto


async def _setup_cajero(db: AsyncSession, nombre_empresa="Carniceria Test", email="cajero@basile.app"):
    empresa = await _crear_empresa(db, nombre_empresa)
    rol = await _crear_rol(db, "cajero", empresa_id=empresa.id)
    usuario = await _crear_usuario(db, email=email, empresa_id=empresa.id, rol_id=rol.id)
    return empresa, usuario


# ---------------------------------------------------------------------------
# Apertura
# ---------------------------------------------------------------------------
class TestApertura:
    async def test_apertura_exitosa(self, client: AsyncClient, db_session: AsyncSession):
        empresa, usuario = await _setup_cajero(db_session)
        response = await client.post(
            "/caja/apertura",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"efectivo_inicial": "100.00"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["estado"] == "abierta"
        assert Decimal(data["monto_inicial"]) == Decimal("100.00")
        assert data["usuario_apertura_id"] == str(usuario.id)

    async def test_segunda_apertura_rechazada(self, client: AsyncClient, db_session: AsyncSession):
        empresa, usuario = await _setup_cajero(db_session)
        await client.post(
            "/caja/apertura",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"efectivo_inicial": "100.00"},
        )
        response = await client.post(
            "/caja/apertura",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"efectivo_inicial": "50.00"},
        )
        assert response.status_code == 409
        assert "abierta" in response.json()["detail"].lower()

    async def test_apertura_aislada_por_empresa(self, client: AsyncClient, db_session: AsyncSession):
        empresa_a, usuario_a = await _setup_cajero(db_session, "Empresa A", "a@basile.app")
        empresa_b, usuario_b = await _setup_cajero(db_session, "Empresa B", "b@basile.app")
        await client.post(
            "/caja/apertura",
            headers=_auth_header(usuario_a, empresa_id=empresa_a.id),
            json={"efectivo_inicial": "100.00"},
        )
        # Empresa B can still open its own caja
        response = await client.post(
            "/caja/apertura",
            headers=_auth_header(usuario_b, empresa_id=empresa_b.id),
            json={"efectivo_inicial": "200.00"},
        )
        assert response.status_code == 201


# ---------------------------------------------------------------------------
# Movimientos
# ---------------------------------------------------------------------------
class TestMovimientos:
    async def test_registrar_retiro(self, client: AsyncClient, db_session: AsyncSession):
        empresa, usuario = await _setup_cajero(db_session)
        await client.post("/caja/apertura", headers=_auth_header(usuario, empresa_id=empresa.id), json={"efectivo_inicial": "100.00"})
        response = await client.post(
            "/caja/movimientos",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"tipo": "retiro", "importe": "30.00", "descripcion": "Pago proveedor"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["tipo"] == "retiro"
        assert Decimal(data["importe"]) == Decimal("30.00")
        assert data["descripcion"] == "Pago proveedor"

    async def test_registrar_ingreso_manual(self, client: AsyncClient, db_session: AsyncSession):
        empresa, usuario = await _setup_cajero(db_session)
        await client.post("/caja/apertura", headers=_auth_header(usuario, empresa_id=empresa.id), json={"efectivo_inicial": "100.00"})
        response = await client.post(
            "/caja/movimientos",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"tipo": "ingreso_manual", "importe": "20.00", "descripcion": "Reposición fondo"},
        )
        assert response.status_code == 201
        assert response.json()["tipo"] == "ingreso_manual"

    async def test_movimiento_sin_caja_abierta(self, client: AsyncClient, db_session: AsyncSession):
        empresa, usuario = await _setup_cajero(db_session)
        response = await client.post(
            "/caja/movimientos",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"tipo": "retiro", "importe": "10.00"},
        )
        assert response.status_code == 409


# ---------------------------------------------------------------------------
# Cierre con diferencias (esperado vs real)
# ---------------------------------------------------------------------------
class TestCierre:
    async def test_cierre_sin_diferencia(self, client: AsyncClient, db_session: AsyncSession):
        empresa, usuario = await _setup_cajero(db_session)
        producto = await _crear_producto(db_session, empresa.id)
        await client.post("/caja/apertura", headers=_auth_header(usuario, empresa_id=empresa.id), json={"efectivo_inicial": "100.00"})

        # Una venta cobrada en efectivo => MovimientoCaja entrada_venta efectivo
        resp = await client.post("/venta", headers=_auth_header(usuario, empresa_id=empresa.id), json={
            "items": [{"producto_id": str(producto.id), "cantidad_kilos": "1.000"}],
        })
        venta_id = resp.json()["id"]
        await client.post(f"/venta/{venta_id}/cobrar", headers=_auth_header(usuario, empresa_id=empresa.id), json={"medio_pago": "efectivo"})

        # esperado efectivo = 100 + 1000 = 1100
        response = await client.post(
            "/caja/cierre",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"efectivo_real": "1100.00", "transferencias_real": "0.00", "tarjetas_real": "0.00"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["caja"]["estado"] == "cerrada"
        assert Decimal(data["esperado"]["efectivo"]) == Decimal("1100.00")
        assert Decimal(data["diferencias"]["diferencia_total"]) == Decimal("0.00")
        assert data["diferencias"]["tiene_diferencia"] is False
        assert data["diferencias"]["diferencia_significativa"] is False

    async def test_cierre_con_faltante_significativo(self, client: AsyncClient, db_session: AsyncSession):
        empresa, usuario = await _setup_cajero(db_session)
        await client.post("/caja/apertura", headers=_auth_header(usuario, empresa_id=empresa.id), json={"efectivo_inicial": "140.00"})
        response = await client.post(
            "/caja/cierre",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"efectivo_real": "130.00", "transferencias_real": "0.00", "tarjetas_real": "0.00"},
        )
        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["diferencias"]["diferencia_efectivo"]) == Decimal("-10.00")
        assert Decimal(data["diferencias"]["diferencia_total"]) == Decimal("-10.00")
        assert data["diferencias"]["tiene_diferencia"] is True
        assert data["diferencias"]["diferencia_significativa"] is True

    async def test_cierre_tarjetas_y_transferencias(self, client: AsyncClient, db_session: AsyncSession):
        empresa, usuario = await _setup_cajero(db_session)
        producto = await _crear_producto(db_session, empresa.id)
        await client.post("/caja/apertura", headers=_auth_header(usuario, empresa_id=empresa.id), json={"efectivo_inicial": "0.00"})

        # venta débito 1000
        resp = await client.post("/venta", headers=_auth_header(usuario, empresa_id=empresa.id), json={
            "items": [{"producto_id": str(producto.id), "cantidad_kilos": "1.000"}],
        })
        vid = resp.json()["id"]
        await client.post(f"/venta/{vid}/cobrar", headers=_auth_header(usuario, empresa_id=empresa.id), json={"medio_pago": "debito"})
        # venta transferencia 1000
        resp = await client.post("/venta", headers=_auth_header(usuario, empresa_id=empresa.id), json={
            "items": [{"producto_id": str(producto.id), "cantidad_kilos": "1.000"}],
        })
        vid2 = resp.json()["id"]
        await client.post(f"/venta/{vid2}/cobrar", headers=_auth_header(usuario, empresa_id=empresa.id), json={"medio_pago": "transferencia"})

        response = await client.post(
            "/caja/cierre",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"efectivo_real": "0.00", "transferencias_real": "1000.00", "tarjetas_real": "1000.00"},
        )
        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["esperado"]["tarjetas"]) == Decimal("1000.00")
        assert Decimal(data["esperado"]["transferencias"]) == Decimal("1000.00")
        assert Decimal(data["diferencias"]["diferencia_total"]) == Decimal("0.00")

    async def test_cierre_sin_caja_abierta(self, client: AsyncClient, db_session: AsyncSession):
        empresa, usuario = await _setup_cajero(db_session)
        response = await client.post(
            "/caja/cierre",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            json={"efectivo_real": "0.00"},
        )
        assert response.status_code == 409


# ---------------------------------------------------------------------------
# GET /caja/actual
# ---------------------------------------------------------------------------
class TestCajaActual:
    async def test_actual_con_esperado_vivo(self, client: AsyncClient, db_session: AsyncSession):
        empresa, usuario = await _setup_cajero(db_session)
        await client.post("/caja/apertura", headers=_auth_header(usuario, empresa_id=empresa.id), json={"efectivo_inicial": "100.00"})
        await client.post("/caja/movimientos", headers=_auth_header(usuario, empresa_id=empresa.id), json={"tipo": "ingreso_manual", "importe": "50.00"})
        await client.post("/caja/movimientos", headers=_auth_header(usuario, empresa_id=empresa.id), json={"tipo": "retiro", "importe": "20.00"})

        response = await client.get("/caja/actual", headers=_auth_header(usuario, empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        # 100 + 50 - 20 = 130
        assert Decimal(data["esperado"]["efectivo"]) == Decimal("130.00")


# ---------------------------------------------------------------------------
# Multi-tenant + RBAC
# ---------------------------------------------------------------------------
class TestSeguridad:
    async def test_apertura_no_cruza_empresas(self, client: AsyncClient, db_session: AsyncSession):
        empresa_a, usuario_a = await _setup_cajero(db_session, "Empresa A", "a@basile.app")
        empresa_b, usuario_b = await _setup_cajero(db_session, "Empresa B", "b@basile.app")
        # A abre caja
        await client.post("/caja/apertura", headers=_auth_header(usuario_a, empresa_id=empresa_a.id), json={"efectivo_inicial": "100.00"})
        # B no ve caja de A: su /caja/actual da 404
        response = await client.get("/caja/actual", headers=_auth_header(usuario_b, empresa_id=empresa_b.id))
        assert response.status_code == 404

    async def test_vendedor_sin_permiso_caja(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "vendedor", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="vend@basile.app", empresa_id=empresa.id, rol_id=rol.id)
        response = await client.post(
            "/caja/apertura",
            headers=_auth_header(usuario, rol_nombre="vendedor", empresa_id=empresa.id),
            json={"efectivo_inicial": "100.00"},
        )
        assert response.status_code == 403
