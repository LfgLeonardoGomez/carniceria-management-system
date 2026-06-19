import uuid
from decimal import Decimal
from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.modules.auth.models import Usuario, Rol, Empresa
from src.modules.producto.models import Producto
from src.modules.cliente.models import Cliente
from src.modules.stock.models import MovimientoStock
from src.modules.caja.models import Caja, MovimientoCaja
from src.modules.cuenta_corriente.models import CuentaCorriente
from src.modules.auditoria.models import Auditoria
from src.modules.venta.models import Venta, DetalleVenta, PagoVenta
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


async def _crear_rol(db: AsyncSession, nombre: str = "admin", empresa_id=None) -> Rol:
    rol = Rol(nombre=nombre, empresa_id=empresa_id)
    db.add(rol)
    await db.commit()
    await db.refresh(rol)
    return rol


async def _crear_usuario(
    db: AsyncSession,
    email: str = "test@basile.app",
    password: str = "Password123",
    activo: bool = True,
    empresa_id=None,
    rol_id=None,
) -> Usuario:
    if rol_id is None:
        rol = await _crear_rol(db, empresa_id=empresa_id)
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
    db.add(usuario)
    await db.commit()
    await db.refresh(usuario)
    return usuario


def _auth_header(usuario: Usuario, rol_nombre: str = "admin", empresa_id=None):
    token = create_access_token({
        "sub": str(usuario.id),
        "empresa_id": str(empresa_id or usuario.empresa_id),
        "rol": rol_nombre,
    })
    return {"Authorization": f"Bearer {token}"}


async def _crear_producto(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    plu: str = "001",
    nombre: str = "Producto Test",
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
    )
    producto.recalcular_margen()
    db.add(producto)
    await db.commit()
    await db.refresh(producto)

    # Crear movimiento de stock inicial para que calcular_stock_actual funcione
    if stock_actual > Decimal("0.0000"):
        mov = MovimientoStock(
            empresa_id=empresa_id,
            producto_id=producto.id,
            tipo="entrada_compra",
            cantidad_kilos=stock_actual,
            stock_resultante=stock_actual,
            fecha=datetime.utcnow(),
        )
        db.add(mov)
        await db.commit()

    return producto


async def _crear_cliente(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    nombre: str = "Juan",
    tipo_cliente: str = "publico_general",
) -> Cliente:
    cliente = Cliente(
        empresa_id=empresa_id,
        nombre=nombre,
        tipo_cliente=tipo_cliente,
        saldo_actual=Decimal("0.0000"),
    )
    db.add(cliente)
    await db.commit()
    await db.refresh(cliente)
    return cliente


async def _crear_caja_abierta(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    operador_id: uuid.UUID,
) -> Caja:
    caja = Caja(
        empresa_id=empresa_id,
        operador_id=operador_id,
        monto_inicial=Decimal("100.00"),
        estado="abierta",
    )
    db.add(caja)
    await db.commit()
    await db.refresh(caja)
    return caja


async def _crear_venta_en_curso(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    cliente_id: uuid.UUID = None,
) -> Venta:
    venta = Venta(
        empresa_id=empresa_id,
        cliente_id=cliente_id,
        tipo_cliente_al_momento="publico_general",
        estado="en_curso",
        subtotal=Decimal("100.00"),
        descuentos=Decimal("0.00"),
        total=Decimal("100.00"),
        fecha=datetime.utcnow(),
    )
    db.add(venta)
    await db.commit()
    await db.refresh(venta)
    return venta


# ---------------------------------------------------------------------------
# 6.3 Test integración: crear venta con carrito y cliente
# ---------------------------------------------------------------------------
class TestCrearVenta:
    async def test_crear_venta_con_cliente(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="cajero", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="cajero@basile.app", empresa_id=empresa.id, rol_id=rol.id)
        producto = await _crear_producto(db_session, empresa.id)
        cliente = await _crear_cliente(db_session, empresa.id, tipo_cliente="mayorista")

        response = await client.post("/venta", headers=_auth_header(usuario, rol_nombre="cajero", empresa_id=empresa.id), json={
            "cliente_id": str(cliente.id),
            "items": [{"producto_id": str(producto.id), "cantidad_kilos": "2.500"}],
            "descuentos": "10.00",
            "medio_pago": "efectivo",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["estado"] == "en_curso"
        assert data["tipo_cliente_al_momento"] == "mayorista"
        assert Decimal(data["subtotal"]) == Decimal("2000.00")
        assert Decimal(data["descuentos"]) == Decimal("10.00")
        assert Decimal(data["total"]) == Decimal("1990.00")
        assert len(data["detalles"]) == 1
        assert Decimal(data["detalles"][0]["cantidad_kilos"]) == Decimal("2.500")

    async def test_crear_venta_sin_cliente(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="cajero", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="cajero@basile.app", empresa_id=empresa.id, rol_id=rol.id)
        producto = await _crear_producto(db_session, empresa.id)

        response = await client.post("/venta", headers=_auth_header(usuario, rol_nombre="cajero", empresa_id=empresa.id), json={
            "items": [{"producto_id": str(producto.id), "cantidad_kilos": "1.000"}],
        })
        assert response.status_code == 201
        data = response.json()
        assert data["cliente_id"] is None
        assert data["tipo_cliente_al_momento"] == "publico_general"

    async def test_crear_venta_producto_inexistente(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="cajero", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="cajero@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        response = await client.post("/venta", headers=_auth_header(usuario, rol_nombre="cajero", empresa_id=empresa.id), json={
            "items": [{"producto_id": str(uuid.uuid4()), "cantidad_kilos": "1.000"}],
        })
        assert response.status_code == 404

    async def test_crear_venta_cantidad_cero(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="cajero", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="cajero@basile.app", empresa_id=empresa.id, rol_id=rol.id)
        producto = await _crear_producto(db_session, empresa.id)

        response = await client.post("/venta", headers=_auth_header(usuario, rol_nombre="cajero", empresa_id=empresa.id), json={
            "items": [{"producto_id": str(producto.id), "cantidad_kilos": "0.000"}],
        })
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# 6.4 Test integración: cobro completo genera stock, caja y ticket
# ---------------------------------------------------------------------------
class TestCobrarVenta:
    async def test_cobro_efectivo_genera_movimientos(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="cajero", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="cajero@basile.app", empresa_id=empresa.id, rol_id=rol.id)
        producto = await _crear_producto(db_session, empresa.id, stock_actual=Decimal("10.0000"))
        caja = await _crear_caja_abierta(db_session, empresa.id, usuario.id)

        # Crear venta
        response = await client.post("/venta", headers=_auth_header(usuario, rol_nombre="cajero", empresa_id=empresa.id), json={
            "items": [{"producto_id": str(producto.id), "cantidad_kilos": "2.000"}],
        })
        assert response.status_code == 201
        venta_id = response.json()["id"]

        # Cobrar
        response = await client.post(f"/venta/{venta_id}/cobrar", headers=_auth_header(usuario, rol_nombre="cajero", empresa_id=empresa.id), json={
            "medio_pago": "efectivo",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["venta"]["estado"] == "cobrada"
        assert data["ticket"]["medio_de_pago"] == "efectivo"
        assert len(data["ticket"]["items"]) == 1

        # Verificar movimiento de stock
        result = await db_session.execute(
            select(MovimientoStock).where(
                MovimientoStock.referencia_id == venta_id,
                MovimientoStock.tipo == "salida_venta",
            )
        )
        mov = result.scalar_one()
        assert Decimal(str(mov.cantidad_kilos)) == Decimal("-2.000")

        # Verificar movimiento de caja
        result = await db_session.execute(
            select(MovimientoCaja).where(
                MovimientoCaja.venta_id == uuid.UUID(venta_id),
                MovimientoCaja.tipo == "entrada_venta",
            )
        )
        mov_caja = result.scalar_one()
        assert mov_caja.medio == "efectivo"
        assert Decimal(str(mov_caja.importe)) == Decimal("2000.00")

    async def test_cobro_transferencia_sin_caja_bloqueado(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="cajero", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="cajero@basile.app", empresa_id=empresa.id, rol_id=rol.id)
        producto = await _crear_producto(db_session, empresa.id, stock_actual=Decimal("10.0000"))

        response = await client.post("/venta", headers=_auth_header(usuario, rol_nombre="cajero", empresa_id=empresa.id), json={
            "items": [{"producto_id": str(producto.id), "cantidad_kilos": "1.000"}],
        })
        venta_id = response.json()["id"]

        response = await client.post(f"/venta/{venta_id}/cobrar", headers=_auth_header(usuario, rol_nombre="cajero", empresa_id=empresa.id), json={
            "medio_pago": "transferencia",
        })
        assert response.status_code == 409
        assert "caja" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 6.5 Test integración: suspensión y recuperación de venta
# ---------------------------------------------------------------------------
class TestSuspenderRecuperar:
    async def test_suspender_y_recuperar(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="cajero", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="cajero@basile.app", empresa_id=empresa.id, rol_id=rol.id)
        producto = await _crear_producto(db_session, empresa.id)

        response = await client.post("/venta", headers=_auth_header(usuario, rol_nombre="cajero", empresa_id=empresa.id), json={
            "items": [{"producto_id": str(producto.id), "cantidad_kilos": "1.000"}],
        })
        venta_id = response.json()["id"]

        # Suspender
        response = await client.post(f"/venta/{venta_id}/suspender", headers=_auth_header(usuario, rol_nombre="cajero", empresa_id=empresa.id))
        assert response.status_code == 200
        assert response.json()["estado"] == "suspendida"

        # Recuperar
        response = await client.post(f"/venta/{venta_id}/recuperar", headers=_auth_header(usuario, rol_nombre="cajero", empresa_id=empresa.id))
        assert response.status_code == 200
        assert response.json()["estado"] == "en_curso"


# ---------------------------------------------------------------------------
# 6.6 Test integración: anulación reversión stock, caja, CC + auditoría
# ---------------------------------------------------------------------------
class TestAnularVenta:
    async def test_anulacion_revierte_stock_y_caja(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_admin = await _crear_rol(db_session, nombre="admin", empresa_id=empresa.id)
        usuario_admin = await _crear_usuario(db_session, email="admin@basile.app", empresa_id=empresa.id, rol_id=rol_admin.id)
        producto = await _crear_producto(db_session, empresa.id, stock_actual=Decimal("10.0000"))
        caja = await _crear_caja_abierta(db_session, empresa.id, usuario_admin.id)

        response = await client.post("/venta", headers=_auth_header(usuario_admin, rol_nombre="admin", empresa_id=empresa.id), json={
            "items": [{"producto_id": str(producto.id), "cantidad_kilos": "3.000"}],
        })
        venta_id = response.json()["id"]

        # Cobrar
        await client.post(f"/venta/{venta_id}/cobrar", headers=_auth_header(usuario_admin, rol_nombre="admin", empresa_id=empresa.id), json={
            "medio_pago": "efectivo",
        })

        # Anular
        response = await client.post(f"/venta/{venta_id}/anular", headers=_auth_header(usuario_admin, rol_nombre="admin", empresa_id=empresa.id))
        assert response.status_code == 200
        assert response.json()["estado"] == "anulada"

        # Verificar reversión de stock
        result = await db_session.execute(
            select(MovimientoStock).where(
                MovimientoStock.referencia_id == venta_id,
                MovimientoStock.tipo == "entrada_anulacion",
            )
        )
        mov = result.scalar_one()
        assert Decimal(str(mov.cantidad_kilos)) == Decimal("3.000")

        # Verificar reversión de caja
        result = await db_session.execute(
            select(MovimientoCaja).where(
                MovimientoCaja.venta_id == uuid.UUID(venta_id),
                MovimientoCaja.tipo == "salida_anulacion",
            )
        )
        mov_caja = result.scalar_one()
        assert Decimal(str(mov_caja.importe)) == Decimal("-3000.00")

        # Verificar auditoría
        result = await db_session.execute(
            select(Auditoria).where(
                Auditoria.action == "venta_anulada",
            )
        )
        audit = result.scalar_one()
        assert audit.target_empresa_id == empresa.id

    async def test_anulacion_con_cuenta_corriente(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_admin = await _crear_rol(db_session, nombre="admin", empresa_id=empresa.id)
        usuario_admin = await _crear_usuario(db_session, email="admin@basile.app", empresa_id=empresa.id, rol_id=rol_admin.id)
        producto = await _crear_producto(db_session, empresa.id, stock_actual=Decimal("10.0000"))
        cliente = await _crear_cliente(db_session, empresa.id)

        response = await client.post("/venta", headers=_auth_header(usuario_admin, rol_nombre="admin", empresa_id=empresa.id), json={
            "cliente_id": str(cliente.id),
            "items": [{"producto_id": str(producto.id), "cantidad_kilos": "2.000"}],
        })
        venta_id = response.json()["id"]

        # Cobrar con CC
        await client.post(f"/venta/{venta_id}/cobrar", headers=_auth_header(usuario_admin, rol_nombre="admin", empresa_id=empresa.id), json={
            "medio_pago": "cuenta_corriente",
        })

        # Verificar deuda
        result = await db_session.execute(
            select(CuentaCorriente).where(
                CuentaCorriente.venta_id == uuid.UUID(venta_id),
                CuentaCorriente.tipo == "deuda",
            )
        )
        cc = result.scalar_one()
        assert Decimal(str(cc.importe)) == Decimal("2000.00")

        # Anular
        response = await client.post(f"/venta/{venta_id}/anular", headers=_auth_header(usuario_admin, rol_nombre="admin", empresa_id=empresa.id))
        assert response.status_code == 200

        # Verificar reversión CC
        result = await db_session.execute(
            select(CuentaCorriente).where(
                CuentaCorriente.venta_id == uuid.UUID(venta_id),
                CuentaCorriente.tipo == "pago",
            )
        )
        cc_pago = result.scalar_one()
        assert Decimal(str(cc_pago.importe)) == Decimal("2000.00")

        # Verificar saldo cliente revertido
        result = await db_session.execute(select(Cliente).where(Cliente.id == cliente.id))
        cliente_db = result.scalar_one()
        assert Decimal(str(cliente_db.saldo_actual)) == Decimal("0.00")


# ---------------------------------------------------------------------------
# 6.7 Test integración: stock negativo bloquea cobro (HTTP 409)
# ---------------------------------------------------------------------------
class TestStockNegativoBloqueaCobro:
    async def test_cobro_sin_stock_bloqueado(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="cajero", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="cajero@basile.app", empresa_id=empresa.id, rol_id=rol.id)
        producto = await _crear_producto(db_session, empresa.id, stock_actual=Decimal("0.0000"))
        await _crear_caja_abierta(db_session, empresa.id, usuario.id)

        response = await client.post("/venta", headers=_auth_header(usuario, rol_nombre="cajero", empresa_id=empresa.id), json={
            "items": [{"producto_id": str(producto.id), "cantidad_kilos": "1.000"}],
        })
        venta_id = response.json()["id"]

        response = await client.post(f"/venta/{venta_id}/cobrar", headers=_auth_header(usuario, rol_nombre="cajero", empresa_id=empresa.id), json={
            "medio_pago": "efectivo",
        })
        assert response.status_code == 409
        assert "stock" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 6.8 Test integración: cobro con cuenta_corriente genera deuda automática
# ---------------------------------------------------------------------------
class TestCobroCuentaCorriente:
    async def test_cc_genera_deuda(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="cajero", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="cajero@basile.app", empresa_id=empresa.id, rol_id=rol.id)
        producto = await _crear_producto(db_session, empresa.id, stock_actual=Decimal("10.0000"))
        cliente = await _crear_cliente(db_session, empresa.id)

        response = await client.post("/venta", headers=_auth_header(usuario, rol_nombre="cajero", empresa_id=empresa.id), json={
            "cliente_id": str(cliente.id),
            "items": [{"producto_id": str(producto.id), "cantidad_kilos": "1.500"}],
        })
        venta_id = response.json()["id"]

        response = await client.post(f"/venta/{venta_id}/cobrar", headers=_auth_header(usuario, rol_nombre="cajero", empresa_id=empresa.id), json={
            "medio_pago": "cuenta_corriente",
        })
        assert response.status_code == 200

        result = await db_session.execute(
            select(CuentaCorriente).where(
                CuentaCorriente.venta_id == uuid.UUID(venta_id),
            )
        )
        cc = result.scalar_one()
        assert cc.tipo == "deuda"
        assert Decimal(str(cc.importe)) == Decimal("1500.00")

        await db_session.refresh(cliente)
        result = await db_session.execute(select(Cliente).where(Cliente.id == cliente.id))
        cliente_db = result.scalar_one()
        assert Decimal(str(cliente_db.saldo_actual)) == Decimal("1500.00")

    async def test_cc_sin_cliente_rechazado(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="cajero", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="cajero@basile.app", empresa_id=empresa.id, rol_id=rol.id)
        producto = await _crear_producto(db_session, empresa.id, stock_actual=Decimal("10.0000"))

        response = await client.post("/venta", headers=_auth_header(usuario, rol_nombre="cajero", empresa_id=empresa.id), json={
            "items": [{"producto_id": str(producto.id), "cantidad_kilos": "1.000"}],
        })
        venta_id = response.json()["id"]

        response = await client.post(f"/venta/{venta_id}/cobrar", headers=_auth_header(usuario, rol_nombre="cajero", empresa_id=empresa.id), json={
            "medio_pago": "cuenta_corriente",
        })
        assert response.status_code == 409
        assert "cliente" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 6.9 Test integración: cobro sin caja abierta bloqueado (HTTP 409)
# ---------------------------------------------------------------------------
class TestCobroSinCaja:
    async def test_cobro_efectivo_sin_caja_bloqueado(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="cajero", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="cajero@basile.app", empresa_id=empresa.id, rol_id=rol.id)
        producto = await _crear_producto(db_session, empresa.id, stock_actual=Decimal("10.0000"))

        response = await client.post("/venta", headers=_auth_header(usuario, rol_nombre="cajero", empresa_id=empresa.id), json={
            "items": [{"producto_id": str(producto.id), "cantidad_kilos": "1.000"}],
        })
        venta_id = response.json()["id"]

        response = await client.post(f"/venta/{venta_id}/cobrar", headers=_auth_header(usuario, rol_nombre="cajero", empresa_id=empresa.id), json={
            "medio_pago": "efectivo",
        })
        assert response.status_code == 409
        assert "caja" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 6.10 Test integración: anulación sin permisos de Admin/Encargado (HTTP 403)
# ---------------------------------------------------------------------------
class TestAnulacionPermisos:
    async def test_cajero_no_puede_anular(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_cajero = await _crear_rol(db_session, nombre="cajero", empresa_id=empresa.id)
        cajero = await _crear_usuario(db_session, email="cajero@basile.app", empresa_id=empresa.id, rol_id=rol_cajero.id)
        rol_admin = await _crear_rol(db_session, nombre="admin", empresa_id=empresa.id)
        admin = await _crear_usuario(db_session, email="admin@basile.app", empresa_id=empresa.id, rol_id=rol_admin.id)
        producto = await _crear_producto(db_session, empresa.id, stock_actual=Decimal("10.0000"))
        await _crear_caja_abierta(db_session, empresa.id, admin.id)

        response = await client.post("/venta", headers=_auth_header(cajero, rol_nombre="cajero", empresa_id=empresa.id), json={
            "items": [{"producto_id": str(producto.id), "cantidad_kilos": "1.000"}],
        })
        venta_id = response.json()["id"]

        # Cobrar como cajero
        await client.post(f"/venta/{venta_id}/cobrar", headers=_auth_header(cajero, rol_nombre="cajero", empresa_id=empresa.id), json={
            "medio_pago": "efectivo",
        })

        # Intentar anular como cajero
        response = await client.post(f"/venta/{venta_id}/anular", headers=_auth_header(cajero, rol_nombre="cajero", empresa_id=empresa.id))
        assert response.status_code == 403

    async def test_encargado_puede_anular(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_enc = await _crear_rol(db_session, nombre="encargado", empresa_id=empresa.id)
        encargado = await _crear_usuario(db_session, email="enc@basile.app", empresa_id=empresa.id, rol_id=rol_enc.id)
        producto = await _crear_producto(db_session, empresa.id, stock_actual=Decimal("10.0000"))
        await _crear_caja_abierta(db_session, empresa.id, encargado.id)

        response = await client.post("/venta", headers=_auth_header(encargado, rol_nombre="encargado", empresa_id=empresa.id), json={
            "items": [{"producto_id": str(producto.id), "cantidad_kilos": "1.000"}],
        })
        venta_id = response.json()["id"]

        await client.post(f"/venta/{venta_id}/cobrar", headers=_auth_header(encargado, rol_nombre="encargado", empresa_id=empresa.id), json={
            "medio_pago": "efectivo",
        })

        response = await client.post(f"/venta/{venta_id}/anular", headers=_auth_header(encargado, rol_nombre="encargado", empresa_id=empresa.id))
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# 6.11 Test integración: aislamiento multi-tenant
# ---------------------------------------------------------------------------
class TestAislamientoMultiTenant:
    async def test_usuario_no_ve_ventas_de_otra_empresa(self, client: AsyncClient, db_session: AsyncSession):
        empresa_a = await _crear_empresa(db_session, "Empresa A")
        empresa_b = await _crear_empresa(db_session, "Empresa B")
        rol = await _crear_rol(db_session, "cajero", empresa_id=empresa_a.id)
        usuario_a = await _crear_usuario(db_session, "cajero_a@basile.app", empresa_id=empresa_a.id, rol_id=rol.id)
        producto_b = await _crear_producto(db_session, empresa_b.id, plu="B01")
        rol_b = await _crear_rol(db_session, "cajero", empresa_id=empresa_b.id)
        usuario_b = await _crear_usuario(db_session, "cajero_b@basile.app", empresa_id=empresa_b.id, rol_id=rol_b.id)
        await _crear_caja_abierta(db_session, empresa_b.id, usuario_b.id)

        # Crear venta en empresa B
        response = await client.post("/venta", headers=_auth_header(usuario_b, rol_nombre="cajero", empresa_id=empresa_b.id), json={
            "items": [{"producto_id": str(producto_b.id), "cantidad_kilos": "1.000"}],
        })
        assert response.status_code == 201

        # Listar como A
        response = await client.get("/venta", headers=_auth_header(usuario_a, rol_nombre="cajero", empresa_id=empresa_a.id))
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    async def test_usuario_no_puede_cobrar_venta_de_otra_empresa(self, client: AsyncClient, db_session: AsyncSession):
        empresa_a = await _crear_empresa(db_session, "Empresa A")
        empresa_b = await _crear_empresa(db_session, "Empresa B")
        rol_a = await _crear_rol(db_session, "cajero", empresa_id=empresa_a.id)
        usuario_a = await _crear_usuario(db_session, "cajero_a@basile.app", empresa_id=empresa_a.id, rol_id=rol_a.id)
        producto_b = await _crear_producto(db_session, empresa_b.id, plu="B01")
        rol_b = await _crear_rol(db_session, "cajero", empresa_id=empresa_b.id)
        usuario_b = await _crear_usuario(db_session, "cajero_b@basile.app", empresa_id=empresa_b.id, rol_id=rol_b.id)
        await _crear_caja_abierta(db_session, empresa_b.id, usuario_b.id)

        response = await client.post("/venta", headers=_auth_header(usuario_b, rol_nombre="cajero", empresa_id=empresa_b.id), json={
            "items": [{"producto_id": str(producto_b.id), "cantidad_kilos": "1.000"}],
        })
        venta_id = response.json()["id"]

        response = await client.post(f"/venta/{venta_id}/cobrar", headers=_auth_header(usuario_a, rol_nombre="cajero", empresa_id=empresa_a.id), json={
            "medio_pago": "efectivo",
        })
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Extra: listar con filtros
# ---------------------------------------------------------------------------
class TestListarVentas:
    async def test_listar_por_estado(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "cajero", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, "cajero@basile.app", empresa_id=empresa.id, rol_id=rol.id)
        producto = await _crear_producto(db_session, empresa.id)

        # Crear dos ventas, suspender una
        response = await client.post("/venta", headers=_auth_header(usuario, rol_nombre="cajero", empresa_id=empresa.id), json={
            "items": [{"producto_id": str(producto.id), "cantidad_kilos": "1.000"}],
        })
        venta1_id = response.json()["id"]

        response = await client.post("/venta", headers=_auth_header(usuario, rol_nombre="cajero", empresa_id=empresa.id), json={
            "items": [{"producto_id": str(producto.id), "cantidad_kilos": "2.000"}],
        })
        venta2_id = response.json()["id"]
        await client.post(f"/venta/{venta2_id}/suspender", headers=_auth_header(usuario, rol_nombre="cajero", empresa_id=empresa.id))

        # Listar suspendidas
        response = await client.get("/venta?estado=suspendida", headers=_auth_header(usuario, rol_nombre="cajero", empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["estado"] == "suspendida"
