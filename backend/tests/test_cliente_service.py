import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.modules.auth.models import Usuario, Rol, Empresa
from src.modules.cliente.models import Cliente
from src.modules.cliente.schemas import ClienteCreate, ClienteUpdate
from src.modules.cliente import service
from src.core.security import hash_password
from src.common.exceptions import NotFoundException, ConflictException


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _crear_empresa(db: AsyncSession, nombre: str = "Carnicería Test") -> Empresa:
    empresa = Empresa(nombre_comercial=nombre, activa=True)
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


# ---------------------------------------------------------------------------
# Tests: create_cliente
# ---------------------------------------------------------------------------
class TestCrearCliente:
    async def test_crear_cliente_exitoso(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session)
        admin = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)

        data = ClienteCreate(
            nombre="Carlos",
            apellido="Gómez",
            cuit="20123456786",
            tipo_cliente="mayorista",
        )
        cliente = await service.create_cliente(db_session, admin, data)

        assert cliente.nombre == "Carlos"
        assert cliente.apellido == "Gómez"
        assert cliente.cuit == "20123456786"
        assert cliente.tipo_cliente == "mayorista"
        assert cliente.empresa_id == empresa.id
        assert cliente.activo is True
        assert cliente.saldo_actual == Decimal("0.0000")

    async def test_crear_cliente_sin_cuit(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session)
        admin = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)

        data = ClienteCreate(nombre="Sin CUIT")
        cliente = await service.create_cliente(db_session, admin, data)
        assert cliente.cuit is None

    async def test_crear_cliente_cuit_duplicado(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session)
        admin = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)
        await _crear_cliente(db_session, empresa.id, cuit="20123456786")

        data = ClienteCreate(nombre="Otro", cuit="20123456786")
        with pytest.raises(ConflictException) as exc:
            await service.create_cliente(db_session, admin, data)
        assert "cuit" in str(exc.value.message).lower()

    async def test_crear_cliente_cuit_diferente_empresa_ok(self, db_session: AsyncSession):
        empresa_a = await _crear_empresa(db_session, "A")
        empresa_b = await _crear_empresa(db_session, "B")
        rol = await _crear_rol(db_session)
        admin_a = await _crear_usuario(db_session, "admin_a@basile.app", rol.id, empresa_a.id)
        await _crear_cliente(db_session, empresa_b.id, cuit="20123456786")

        data = ClienteCreate(nombre="Otro", cuit="20123456786")
        cliente = await service.create_cliente(db_session, admin_a, data)
        assert cliente.cuit == "20123456786"


# ---------------------------------------------------------------------------
# Tests: update_cliente
# ---------------------------------------------------------------------------
class TestActualizarCliente:
    async def test_actualizar_nombre_y_apellido(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cliente = await _crear_cliente(db_session, empresa.id)

        data = ClienteUpdate(nombre="Nuevo", apellido="Apellido")
        actualizado = await service.update_cliente(db_session, empresa.id, cliente.id, data)
        assert actualizado.nombre == "Nuevo"
        assert actualizado.apellido == "Apellido"

    async def test_actualizar_cuit_a_otro_cliente_falla(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        c1 = await _crear_cliente(db_session, empresa.id, cuit="20123456786")
        await _crear_cliente(db_session, empresa.id, nombre="Otro", cuit="27123456780")

        data = ClienteUpdate(cuit="27123456780")
        with pytest.raises(ConflictException):
            await service.update_cliente(db_session, empresa.id, c1.id, data)

    async def test_actualizar_tipo_cliente(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cliente = await _crear_cliente(db_session, empresa.id)

        data = ClienteUpdate(tipo_cliente="especial")
        actualizado = await service.update_cliente(db_session, empresa.id, cliente.id, data)
        assert actualizado.tipo_cliente == "especial"


# ---------------------------------------------------------------------------
# Tests: soft_delete_cliente
# ---------------------------------------------------------------------------
class TestDesactivarCliente:
    async def test_desactivar_cliente(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cliente = await _crear_cliente(db_session, empresa.id)

        resultado = await service.soft_delete_cliente(db_session, empresa.id, cliente.id)
        assert resultado.activo is False

    async def test_desactivar_cliente_otra_empresa_falla(self, db_session: AsyncSession):
        empresa_a = await _crear_empresa(db_session, "A")
        empresa_b = await _crear_empresa(db_session, "B")
        cliente_b = await _crear_cliente(db_session, empresa_b.id)

        with pytest.raises(NotFoundException):
            await service.soft_delete_cliente(db_session, empresa_a.id, cliente_b.id)


# ---------------------------------------------------------------------------
# Tests: get_cliente_by_id
# ---------------------------------------------------------------------------
class TestObtenerCliente:
    async def test_obtener_cliente_por_id(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cliente = await _crear_cliente(db_session, empresa.id)

        resultado = await service.get_cliente_by_id(db_session, empresa.id, cliente.id)
        assert resultado.id == cliente.id

    async def test_obtener_cliente_otra_empresa_falla(self, db_session: AsyncSession):
        empresa_a = await _crear_empresa(db_session, "A")
        empresa_b = await _crear_empresa(db_session, "B")
        cliente_b = await _crear_cliente(db_session, empresa_b.id)

        with pytest.raises(NotFoundException):
            await service.get_cliente_by_id(db_session, empresa_a.id, cliente_b.id)


# ---------------------------------------------------------------------------
# Tests: list_clientes
# ---------------------------------------------------------------------------
class TestListarClientes:
    async def test_listar_filtra_por_empresa(self, db_session: AsyncSession):
        empresa_a = await _crear_empresa(db_session, "A")
        empresa_b = await _crear_empresa(db_session, "B")
        await _crear_cliente(db_session, empresa_a.id, nombre="A1")
        await _crear_cliente(db_session, empresa_a.id, nombre="A2")
        await _crear_cliente(db_session, empresa_b.id, nombre="B1")

        resultados, total = await service.list_clientes(db_session, empresa_a.id)
        assert total == 2
        assert all(c.empresa_id == empresa_a.id for c in resultados)

    async def test_listar_filtro_tipo(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        await _crear_cliente(db_session, empresa.id, tipo_cliente="mayorista")
        await _crear_cliente(db_session, empresa.id, nombre="Otro", tipo_cliente="publico_general")

        resultados, total = await service.list_clientes(db_session, empresa.id, tipo_cliente="mayorista")
        assert total == 1
        assert resultados[0].tipo_cliente == "mayorista"

    async def test_listar_filtro_activo(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        await _crear_cliente(db_session, empresa.id, activo=True)
        await _crear_cliente(db_session, empresa.id, nombre="Inactivo", activo=False)

        resultados, total = await service.list_clientes(db_session, empresa.id, activo=True)
        assert total == 1
        assert resultados[0].activo is True

    async def test_listar_paginacion(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        for i in range(5):
            await _crear_cliente(db_session, empresa.id, nombre=f"C{i}")

        resultados, total = await service.list_clientes(db_session, empresa.id, skip=0, limit=3)
        assert total == 5
        assert len(resultados) == 3

        resultados, total = await service.list_clientes(db_session, empresa.id, skip=3, limit=3)
        assert len(resultados) == 2


# ---------------------------------------------------------------------------
# Tests: search_clientes
# ---------------------------------------------------------------------------
class TestBuscarClientes:
    async def test_buscar_por_nombre(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        await _crear_cliente(db_session, empresa.id, nombre="Carlos")
        await _crear_cliente(db_session, empresa.id, nombre="Ana")

        resultados, total = await service.search_clientes(db_session, empresa.id, "Car")
        assert total == 1
        assert resultados[0].nombre == "Carlos"

    async def test_buscar_por_apellido(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        await _crear_cliente(db_session, empresa.id, nombre="A", apellido="Gómez")
        await _crear_cliente(db_session, empresa.id, nombre="B", apellido="Pérez")

        resultados, total = await service.search_clientes(db_session, empresa.id, "Gómez")
        assert total == 1
        assert resultados[0].apellido == "Gómez"

    async def test_buscar_por_cuit(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        await _crear_cliente(db_session, empresa.id, cuit="20123456786")
        await _crear_cliente(db_session, empresa.id, nombre="Otro", cuit="27123456780")

        resultados, total = await service.search_clientes(db_session, empresa.id, "20123456786")
        assert total == 1
        assert resultados[0].cuit == "20123456786"


# ---------------------------------------------------------------------------
# Tests: saldo_actual
# ---------------------------------------------------------------------------
class TestSaldoCliente:
    async def test_saldo_default_cero(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cliente = await _crear_cliente(db_session, empresa.id)
        assert cliente.saldo_actual == Decimal("0.0000")

    async def test_saldo_incluido_en_lectura(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        cliente = await _crear_cliente(db_session, empresa.id)
        # Simular update de saldo
        cliente.saldo_actual = Decimal("1500.5000")
        await db_session.commit()
        await db_session.refresh(cliente)

        resultado = await service.get_cliente_by_id(db_session, empresa.id, cliente.id)
        assert resultado.saldo_actual == Decimal("1500.5000")


# ---------------------------------------------------------------------------
# Tests: tenant isolation
# ---------------------------------------------------------------------------
class TestAislamientoMultiTenant:
    async def test_no_puede_actualizar_cliente_de_otra_empresa(self, db_session: AsyncSession):
        empresa_a = await _crear_empresa(db_session, "A")
        empresa_b = await _crear_empresa(db_session, "B")
        cliente_b = await _crear_cliente(db_session, empresa_b.id)

        with pytest.raises(NotFoundException):
            await service.update_cliente(
                db_session, empresa_a.id, cliente_b.id, ClienteUpdate(nombre="Hack")
            )

    async def test_no_puede_desactivar_cliente_de_otra_empresa(self, db_session: AsyncSession):
        empresa_a = await _crear_empresa(db_session, "A")
        empresa_b = await _crear_empresa(db_session, "B")
        cliente_b = await _crear_cliente(db_session, empresa_b.id)

        with pytest.raises(NotFoundException):
            await service.soft_delete_cliente(db_session, empresa_a.id, cliente_b.id)

    async def test_no_puede_listar_clientes_de_otra_empresa(self, db_session: AsyncSession):
        empresa_a = await _crear_empresa(db_session, "A")
        empresa_b = await _crear_empresa(db_session, "B")
        await _crear_cliente(db_session, empresa_b.id, nombre="B")

        resultados, total = await service.list_clientes(db_session, empresa_a.id)
        assert total == 0
