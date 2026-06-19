import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.models import Empresa, Rol, Usuario
from src.modules.proveedor.models import Proveedor
from src.modules.proveedor.service import (
    create,
    get_by_id,
    list_by_empresa,
    update,
    delete_logic,
)
from src.common.exceptions import NotFoundException, ConflictException
from src.core.security import hash_password


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _crear_empresa(db: AsyncSession, nombre: str = "Carnicería Test") -> Empresa:
    empresa = Empresa(nombre_comercial=nombre, activa=True)
    db.add(empresa)
    await db.commit()
    await db.refresh(empresa)
    return empresa


async def _crear_proveedor(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    nombre: str = "Proveedor Test",
    cuit: str = None,
    activo: bool = True,
) -> Proveedor:
    proveedor = Proveedor(
        empresa_id=empresa_id,
        nombre=nombre,
        cuit=cuit,
        activo=activo,
    )
    db.add(proveedor)
    await db.commit()
    await db.refresh(proveedor)
    return proveedor


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
) -> Usuario:
    u = Usuario(
        email=email,
        contrasena_hash=hash_password("Password123"),
        nombre="Test",
        apellido="User",
        rol_id=rol_id,
        activo=True,
        empresa_id=empresa_id,
    )
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


# ---------------------------------------------------------------------------
# Tests: create
# ---------------------------------------------------------------------------
class TestCrearProveedor:
    async def test_crear_exitoso(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        proveedor = await create(
            db=db_session,
            empresa_id=empresa.id,
            nombre="Carnes del Sur",
            cuit="30616874582",
        )
        assert proveedor.nombre == "Carnes del Sur"
        assert proveedor.cuit == "30616874582"
        assert proveedor.empresa_id == empresa.id
        assert proveedor.activo is True

    async def test_crear_sin_cuit(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        proveedor = await create(
            db=db_session,
            empresa_id=empresa.id,
            nombre="Proveedor Informal",
        )
        assert proveedor.cuit is None

    async def test_crear_cuit_duplicado(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        await _crear_proveedor(db_session, empresa.id, "Proveedor A", "30616874582")

        with pytest.raises(ConflictException) as exc:
            await create(
                db=db_session,
                empresa_id=empresa.id,
                nombre="Proveedor B",
                cuit="30616874582",
            )
        assert "cuit" in str(exc.value.message).lower()

    async def test_crear_cuit_duplicado_otra_empresa_ok(self, db_session: AsyncSession):
        empresa_a = await _crear_empresa(db_session, "Empresa A")
        empresa_b = await _crear_empresa(db_session, "Empresa B")
        await _crear_proveedor(db_session, empresa_a.id, "Proveedor A", "30616874582")

        proveedor_b = await create(
            db=db_session,
            empresa_id=empresa_b.id,
            nombre="Proveedor B",
            cuit="30616874582",
        )
        assert proveedor_b.cuit == "30616874582"


# ---------------------------------------------------------------------------
# Tests: get_by_id
# ---------------------------------------------------------------------------
class TestGetById:
    async def test_obtener_existente(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        proveedor = await _crear_proveedor(db_session, empresa.id, "Carnes del Sur")

        result = await get_by_id(db_session, empresa.id, proveedor.id)
        assert result.id == proveedor.id

    async def test_no_encontrado(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        with pytest.raises(NotFoundException):
            await get_by_id(db_session, empresa.id, uuid.uuid4())

    async def test_aislamiento_empresa(self, db_session: AsyncSession):
        empresa_a = await _crear_empresa(db_session, "A")
        empresa_b = await _crear_empresa(db_session, "B")
        proveedor_b = await _crear_proveedor(db_session, empresa_b.id, "Proveedor B")

        with pytest.raises(NotFoundException):
            await get_by_id(db_session, empresa_a.id, proveedor_b.id)


# ---------------------------------------------------------------------------
# Tests: list_by_empresa
# ---------------------------------------------------------------------------
class TestListarProveedores:
    async def test_listar_filtra_por_empresa(self, db_session: AsyncSession):
        empresa_a = await _crear_empresa(db_session, "Empresa A")
        empresa_b = await _crear_empresa(db_session, "Empresa B")
        await _crear_proveedor(db_session, empresa_a.id, "Proveedor A1")
        await _crear_proveedor(db_session, empresa_a.id, "Proveedor A2")
        await _crear_proveedor(db_session, empresa_b.id, "Proveedor B1")

        resultados, total = await list_by_empresa(db_session, empresa_a.id)
        assert total == 2
        assert all(r.empresa_id == empresa_a.id for r in resultados)

    async def test_listar_excluye_inactivos(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        await _crear_proveedor(db_session, empresa.id, "Activo", activo=True)
        await _crear_proveedor(db_session, empresa.id, "Inactivo", activo=False)

        resultados, total = await list_by_empresa(db_session, empresa.id)
        assert total == 1
        assert resultados[0].nombre == "Activo"

    async def test_listar_incluye_inactivos(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        await _crear_proveedor(db_session, empresa.id, "Activo", activo=True)
        await _crear_proveedor(db_session, empresa.id, "Inactivo", activo=False)

        resultados, total = await list_by_empresa(
            db_session, empresa.id, incluir_inactivos=True
        )
        assert total == 2

    async def test_listar_busqueda_nombre(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        await _crear_proveedor(db_session, empresa.id, "Carnes del Sur")
        await _crear_proveedor(db_session, empresa.id, "Pollos del Norte")
        await _crear_proveedor(db_session, empresa.id, "Carnes del Oeste")

        resultados, total = await list_by_empresa(
            db_session, empresa.id, nombre="carne"
        )
        assert total == 2
        assert all("carne" in r.nombre.lower() for r in resultados)

    async def test_listar_paginacion(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        for i in range(5):
            await _crear_proveedor(db_session, empresa.id, f"Proveedor {i}")

        resultados, total = await list_by_empresa(db_session, empresa.id, skip=0, limit=3)
        assert total == 5
        assert len(resultados) == 3

        resultados, total = await list_by_empresa(db_session, empresa.id, skip=3, limit=3)
        assert len(resultados) == 2


# ---------------------------------------------------------------------------
# Tests: update
# ---------------------------------------------------------------------------
class TestActualizarProveedor:
    async def test_actualizar_nombre(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        proveedor = await _crear_proveedor(db_session, empresa.id, "Viejo Nombre")

        actualizado = await update(
            db=db_session,
            empresa_id=empresa.id,
            proveedor_id=proveedor.id,
            nombre="Nuevo Nombre",
        )
        assert actualizado.nombre == "Nuevo Nombre"

    async def test_actualizar_cuit_a_duplicado(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        await _crear_proveedor(db_session, empresa.id, "Proveedor A", "30616874582")
        proveedor_b = await _crear_proveedor(db_session, empresa.id, "Proveedor B", "30712345678")

        with pytest.raises(ConflictException):
            await update(
                db=db_session,
                empresa_id=empresa.id,
                proveedor_id=proveedor_b.id,
                cuit="30616874582",
            )

    async def test_actualizar_cuit_mismo_proveedor_ok(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        proveedor = await _crear_proveedor(db_session, empresa.id, "Proveedor A", "30616874582")

        actualizado = await update(
            db=db_session,
            empresa_id=empresa.id,
            proveedor_id=proveedor.id,
            cuit="30616874582",
        )
        assert actualizado.cuit == "30616874582"


# ---------------------------------------------------------------------------
# Tests: delete_logic
# ---------------------------------------------------------------------------
class TestBajaLogica:
    async def test_baja_logica(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        proveedor = await _crear_proveedor(db_session, empresa.id, "A Dar de Baja")

        await delete_logic(db_session, empresa.id, proveedor.id)
        await db_session.refresh(proveedor)
        assert proveedor.activo is False

    async def test_baja_logica_no_encontrado(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        with pytest.raises(NotFoundException):
            await delete_logic(db_session, empresa.id, uuid.uuid4())

    async def test_baja_logica_aislamiento(self, db_session: AsyncSession):
        empresa_a = await _crear_empresa(db_session, "A")
        empresa_b = await _crear_empresa(db_session, "B")
        proveedor_b = await _crear_proveedor(db_session, empresa_b.id, "Proveedor B")

        with pytest.raises(NotFoundException):
            await delete_logic(db_session, empresa_a.id, proveedor_b.id)
