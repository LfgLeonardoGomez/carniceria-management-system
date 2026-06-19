import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.models import Usuario, Rol, Empresa
from src.modules.cliente.models import Cliente
from src.core.security import hash_password, create_access_token


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _crear_empresa(db: AsyncSession, nombre: str = "Carnicería Test", activa: bool = True) -> Empresa:
    empresa = Empresa(nombre_comercial=nombre, activa=activa)
    db.add(empresa)
    await db.commit()
    await db.refresh(empresa)
    return empresa


async def _crear_rol(db: AsyncSession, nombre: str = "Administrador") -> Rol:
    rol = Rol(nombre=nombre)
    db.add(rol)
    await db.commit()
    await db.refresh(rol)
    return rol


async def _crear_usuario(
    db: AsyncSession,
    email: str,
    rol_id: uuid.UUID,
    empresa_id: uuid.UUID,
    activo: bool = True,
    nombre: str = "Test",
    apellido: str = "User",
) -> Usuario:
    u = Usuario(
        email=email,
        contrasena_hash=hash_password("Password123"),
        nombre=nombre,
        apellido=apellido,
        rol_id=rol_id,
        activo=activo,
        empresa_id=empresa_id,
    )
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


async def _crear_cliente(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    nombre: str = "Juan",
    apellido: str = "Pérez",
    cuit: str | None = None,
    tipo_cliente: str = "publico_general",
    activo: bool = True,
) -> Cliente:
    c = Cliente(
        empresa_id=empresa_id,
        nombre=nombre,
        apellido=apellido,
        cuit=cuit,
        tipo_cliente=tipo_cliente,
        limite_cuenta_corriente=Decimal("0.0000"),
        saldo_actual=Decimal("0.0000"),
        activo=activo,
    )
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return c


def _auth_header(usuario: Usuario, rol_nombre: str = "Administrador", empresa_id=None):
    token = create_access_token({
        "sub": str(usuario.id),
        "empresa_id": str(empresa_id or usuario.empresa_id),
        "rol": rol_nombre,
    })
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Tests: CRUD con Administrador
# ---------------------------------------------------------------------------
class TestCRUDClientesAdmin:
    async def test_crear_cliente_como_admin(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_admin = await _crear_rol(db_session, "Administrador")
        admin = await _crear_usuario(db_session, "admin@basile.app", rol_admin.id, empresa.id)

        response = await client.post("/cliente", headers=_auth_header(admin, empresa_id=empresa.id), json={
            "nombre": "Carlos",
            "apellido": "Gómez",
            "cuit": "20123456786",
            "tipo_cliente": "mayorista",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["nombre"] == "Carlos"
        assert data["tipo_cliente"] == "mayorista"
        assert data["saldo_actual"] == "0.0000"

    async def test_listar_clientes_como_admin(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        admin = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)
        await _crear_cliente(db_session, empresa.id, nombre="C1")
        await _crear_cliente(db_session, empresa.id, nombre="C2")

        response = await client.get("/cliente", headers=_auth_header(admin, empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    async def test_actualizar_cliente_como_admin(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        admin = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)
        c = await _crear_cliente(db_session, empresa.id)

        response = await client.put(f"/cliente/{c.id}", headers=_auth_header(admin, empresa_id=empresa.id), json={
            "nombre": "Nuevo",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["nombre"] == "Nuevo"

    async def test_desactivar_cliente_como_admin(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_admin = await _crear_rol(db_session, "Administrador")
        admin = await _crear_usuario(db_session, "admin@basile.app", rol_admin.id, empresa.id)
        c = await _crear_cliente(db_session, empresa.id)

        response = await client.delete(f"/cliente/{c.id}", headers=_auth_header(admin, empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        assert data["activo"] is False


# ---------------------------------------------------------------------------
# Tests: CRUD con Encargado (CRU, no delete)
# ---------------------------------------------------------------------------
class TestCRUDClientesEncargado:
    async def test_encargado_puede_crear_cliente(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_encargado = await _crear_rol(db_session, "Encargado")
        encargado = await _crear_usuario(db_session, "enc@basile.app", rol_encargado.id, empresa.id)

        response = await client.post("/cliente", headers=_auth_header(encargado, rol_nombre="Encargado", empresa_id=empresa.id), json={
            "nombre": "Cliente",
        })
        assert response.status_code == 201

    async def test_encargado_puede_listar_clientes(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_encargado = await _crear_rol(db_session, "Encargado")
        encargado = await _crear_usuario(db_session, "enc@basile.app", rol_encargado.id, empresa.id)

        response = await client.get("/cliente", headers=_auth_header(encargado, rol_nombre="Encargado", empresa_id=empresa.id))
        assert response.status_code == 200

    async def test_encargado_no_puede_desactivar_cliente(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_encargado = await _crear_rol(db_session, "Encargado")
        encargado = await _crear_usuario(db_session, "enc@basile.app", rol_encargado.id, empresa.id)
        c = await _crear_cliente(db_session, empresa.id)

        response = await client.delete(f"/cliente/{c.id}", headers=_auth_header(encargado, rol_nombre="Encargado", empresa_id=empresa.id))
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# Tests: CRUD con Cajero (CRU, no delete)
# ---------------------------------------------------------------------------
class TestCRUDClientesCajero:
    async def test_cajero_puede_crear_cliente(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_cajero = await _crear_rol(db_session, "Cajero")
        cajero = await _crear_usuario(db_session, "cajero@basile.app", rol_cajero.id, empresa.id)

        response = await client.post("/cliente", headers=_auth_header(cajero, rol_nombre="Cajero", empresa_id=empresa.id), json={
            "nombre": "Cliente",
        })
        assert response.status_code == 201

    async def test_cajero_no_puede_desactivar_cliente(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_cajero = await _crear_rol(db_session, "Cajero")
        cajero = await _crear_usuario(db_session, "cajero@basile.app", rol_cajero.id, empresa.id)
        c = await _crear_cliente(db_session, empresa.id)

        response = await client.delete(f"/cliente/{c.id}", headers=_auth_header(cajero, rol_nombre="Cajero", empresa_id=empresa.id))
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# Tests: Vendedor denied
# ---------------------------------------------------------------------------
class TestCRUDClientesVendedor:
    async def test_vendedor_no_puede_crear_cliente(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_vendedor = await _crear_rol(db_session, "Vendedor")
        vendedor = await _crear_usuario(db_session, "vend@basile.app", rol_vendedor.id, empresa.id)

        response = await client.post("/cliente", headers=_auth_header(vendedor, rol_nombre="Vendedor", empresa_id=empresa.id), json={
            "nombre": "Cliente",
        })
        assert response.status_code == 403

    async def test_vendedor_no_puede_listar_clientes(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_vendedor = await _crear_rol(db_session, "Vendedor")
        vendedor = await _crear_usuario(db_session, "vend@basile.app", rol_vendedor.id, empresa.id)

        response = await client.get("/cliente", headers=_auth_header(vendedor, rol_nombre="Vendedor", empresa_id=empresa.id))
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# Tests: tenant isolation
# ---------------------------------------------------------------------------
class TestAislamientoMultiTenant:
    async def test_admin_a_no_ve_clientes_de_b(self, client: AsyncClient, db_session: AsyncSession):
        empresa_a = await _crear_empresa(db_session, "A")
        empresa_b = await _crear_empresa(db_session, "B")
        rol = await _crear_rol(db_session, "Administrador")
        admin_a = await _crear_usuario(db_session, "admin_a@basile.app", rol.id, empresa_a.id)
        await _crear_cliente(db_session, empresa_b.id, nombre="B")

        response = await client.get("/cliente", headers=_auth_header(admin_a, empresa_id=empresa_a.id))
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    async def test_admin_a_no_puede_modificar_cliente_b(self, client: AsyncClient, db_session: AsyncSession):
        empresa_a = await _crear_empresa(db_session, "A")
        empresa_b = await _crear_empresa(db_session, "B")
        rol = await _crear_rol(db_session, "Administrador")
        admin_a = await _crear_usuario(db_session, "admin_a@basile.app", rol.id, empresa_a.id)
        cliente_b = await _crear_cliente(db_session, empresa_b.id)

        response = await client.put(f"/cliente/{cliente_b.id}", headers=_auth_header(admin_a, empresa_id=empresa_a.id), json={
            "nombre": "Hack",
        })
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Tests: search
# ---------------------------------------------------------------------------
class TestBuscarClientes:
    async def test_buscar_por_nombre(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        admin = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)
        await _crear_cliente(db_session, empresa.id, nombre="Carlos")
        await _crear_cliente(db_session, empresa.id, nombre="Ana")

        response = await client.get("/cliente?q=Car", headers=_auth_header(admin, empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["nombre"] == "Carlos"

    async def test_buscar_por_cuit(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        admin = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)
        await _crear_cliente(db_session, empresa.id, cuit="20123456786")
        await _crear_cliente(db_session, empresa.id, nombre="Otro", cuit="27123456780")

        response = await client.get("/cliente?q=20123456786", headers=_auth_header(admin, empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["cuit"] == "20123456786"


# ---------------------------------------------------------------------------
# Tests: filter by tipo
# ---------------------------------------------------------------------------
class TestFiltrarPorTipo:
    async def test_filtrar_mayorista(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        admin = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)
        await _crear_cliente(db_session, empresa.id, tipo_cliente="mayorista")
        await _crear_cliente(db_session, empresa.id, nombre="Otro", tipo_cliente="publico_general")

        response = await client.get("/cliente?tipo_cliente=mayorista", headers=_auth_header(admin, empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["tipo_cliente"] == "mayorista"


# ---------------------------------------------------------------------------
# Tests: extra='forbid'
# ---------------------------------------------------------------------------
class TestSchemaExtraForbid:
    async def test_crear_cliente_con_campo_extra_rechazado(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        admin = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)

        response = await client.post("/cliente", headers=_auth_header(admin, empresa_id=empresa.id), json={
            "nombre": "Test",
            "extra_field": "should_fail",
        })
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Tests: historial
# ---------------------------------------------------------------------------
class TestHistorialCliente:
    async def test_historial_cliente_no_existente(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        admin = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)
        fake_id = str(uuid.uuid4())

        response = await client.get(f"/cliente/{fake_id}/historial", headers=_auth_header(admin, empresa_id=empresa.id))
        assert response.status_code == 404

    async def test_historial_cliente_otra_empresa(self, client: AsyncClient, db_session: AsyncSession):
        empresa_a = await _crear_empresa(db_session, "A")
        empresa_b = await _crear_empresa(db_session, "B")
        rol = await _crear_rol(db_session, "Administrador")
        admin_a = await _crear_usuario(db_session, "admin_a@basile.app", rol.id, empresa_a.id)
        cliente_b = await _crear_cliente(db_session, empresa_b.id)

        response = await client.get(f"/cliente/{cliente_b.id}/historial", headers=_auth_header(admin_a, empresa_id=empresa_a.id))
        assert response.status_code == 404

    async def test_historial_cliente_existente_sin_ventas(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        admin = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)
        c = await _crear_cliente(db_session, empresa.id)

        response = await client.get(f"/cliente/{c.id}/historial", headers=_auth_header(admin, empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []


# ---------------------------------------------------------------------------
# Tests: saldo
# ---------------------------------------------------------------------------
class TestSaldoResponse:
    async def test_saldo_incluido_en_detalle(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        admin = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)
        c = await _crear_cliente(db_session, empresa.id)

        response = await client.get(f"/cliente/{c.id}", headers=_auth_header(admin, empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        assert data["saldo_actual"] == "0.0000"

    async def test_saldo_incluido_en_lista(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        admin = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)
        await _crear_cliente(db_session, empresa.id)

        response = await client.get("/cliente", headers=_auth_header(admin, empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        assert data["items"][0]["saldo_actual"] == "0.0000"
