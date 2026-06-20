import uuid
from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.modules.auth.models import Usuario, Rol, Empresa
from src.modules.proveedor.models import Proveedor
from src.core.security import hash_password, create_access_token


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


def _auth_header(usuario: Usuario, rol_nombre: str = "Administrador", empresa_id=None):
    token = create_access_token({
        "sub": str(usuario.id),
        "empresa_id": str(empresa_id or usuario.empresa_id),
        "rol": rol_nombre,
    })
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Tests: GET /proveedores
# ---------------------------------------------------------------------------
class TestListProveedores:
    async def test_listar_proveedores(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        usuario = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)
        await _crear_proveedor(db_session, empresa.id, "Carnes del Sur")
        await _crear_proveedor(db_session, empresa.id, "Pollos del Norte")

        response = await client.get("/proveedores", headers=_auth_header(usuario, empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    async def test_listar_paginado(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        usuario = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)
        for i in range(5):
            await _crear_proveedor(db_session, empresa.id, f"Proveedor {i}")

        response = await client.get("/proveedores?skip=0&limit=3", headers=_auth_header(usuario, empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 3

    async def test_listar_busqueda(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        usuario = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)
        await _crear_proveedor(db_session, empresa.id, "Carnes del Sur")
        await _crear_proveedor(db_session, empresa.id, "Pollos del Norte")

        response = await client.get("/proveedores?nombre=carne", headers=_auth_header(usuario, empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["nombre"] == "Carnes del Sur"

    async def test_listar_excluye_inactivos(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        usuario = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)
        await _crear_proveedor(db_session, empresa.id, "Activo", activo=True)
        await _crear_proveedor(db_session, empresa.id, "Inactivo", activo=False)

        response = await client.get("/proveedores", headers=_auth_header(usuario, empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["nombre"] == "Activo"

    async def test_listar_incluye_inactivos(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        usuario = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)
        await _crear_proveedor(db_session, empresa.id, "Activo", activo=True)
        await _crear_proveedor(db_session, empresa.id, "Inactivo", activo=False)

        response = await client.get("/proveedores?incluir_inactivos=true", headers=_auth_header(usuario, empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    async def test_listar_sin_token(self, client: AsyncClient):
        response = await client.get("/proveedores")
        assert response.status_code == 401

    async def test_listar_rol_sin_permiso(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Cajero")
        usuario = await _crear_usuario(db_session, "cajero@basile.app", rol.id, empresa.id)

        response = await client.get("/proveedores", headers=_auth_header(usuario, rol_nombre="Cajero", empresa_id=empresa.id))
        assert response.status_code == 403

    async def test_listar_aislamiento(self, client: AsyncClient, db_session: AsyncSession):
        empresa_a = await _crear_empresa(db_session, "Empresa A")
        empresa_b = await _crear_empresa(db_session, "Empresa B")
        rol = await _crear_rol(db_session, "Administrador")
        usuario_a = await _crear_usuario(db_session, "admin_a@basile.app", rol.id, empresa_a.id)
        await _crear_proveedor(db_session, empresa_a.id, "Proveedor A")
        await _crear_proveedor(db_session, empresa_b.id, "Proveedor B")

        response = await client.get("/proveedores", headers=_auth_header(usuario_a, empresa_id=empresa_a.id))
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["nombre"] == "Proveedor A"


# ---------------------------------------------------------------------------
# Tests: POST /proveedores
# ---------------------------------------------------------------------------
class TestCreateProveedor:
    async def test_crear_proveedor(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        usuario = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)

        response = await client.post("/proveedores", headers=_auth_header(usuario, empresa_id=empresa.id), json={
            "nombre": "Carnes del Sur",
            "cuit": "30616874582",
            "telefono": "123456789",
            "email": "contacto@carne.com",
            "direccion": "Av Siempre Viva 123",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["nombre"] == "Carnes del Sur"
        assert data["cuit"] == "30616874582"
        assert data["empresa_id"] == str(empresa.id)

    async def test_crear_cuit_invalido(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        usuario = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)

        response = await client.post("/proveedores", headers=_auth_header(usuario, empresa_id=empresa.id), json={
            "nombre": "Carnes del Sur",
            "cuit": "123",
        })
        assert response.status_code == 422

    async def test_crear_cuit_duplicado(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        usuario = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)
        await _crear_proveedor(db_session, empresa.id, "Proveedor A", "30616874582")

        response = await client.post("/proveedores", headers=_auth_header(usuario, empresa_id=empresa.id), json={
            "nombre": "Proveedor B",
            "cuit": "30616874582",
        })
        assert response.status_code == 409

    async def test_crear_campos_extra_rechazados(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        usuario = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)

        response = await client.post("/proveedores", headers=_auth_header(usuario, empresa_id=empresa.id), json={
            "nombre": "Carnes del Sur",
            "campo_extra": "no permitido",
        })
        assert response.status_code == 422

    async def test_crear_rol_sin_permiso(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Cajero")
        usuario = await _crear_usuario(db_session, "cajero@basile.app", rol.id, empresa.id)

        response = await client.post("/proveedores", headers=_auth_header(usuario, rol_nombre="Cajero", empresa_id=empresa.id), json={
            "nombre": "Carnes del Sur",
        })
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# Tests: GET /proveedores/{id}
# ---------------------------------------------------------------------------
class TestGetProveedor:
    async def test_obtener_proveedor(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        usuario = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)
        proveedor = await _crear_proveedor(db_session, empresa.id, "Carnes del Sur", "30616874582")

        response = await client.get(f"/proveedores/{proveedor.id}", headers=_auth_header(usuario, empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        assert data["nombre"] == "Carnes del Sur"
        assert data["cuit"] == "30616874582"

    async def test_obtener_proveedor_otra_empresa_404(self, client: AsyncClient, db_session: AsyncSession):
        empresa_a = await _crear_empresa(db_session, "Empresa A")
        empresa_b = await _crear_empresa(db_session, "Empresa B")
        rol = await _crear_rol(db_session, "Administrador")
        usuario_a = await _crear_usuario(db_session, "admin_a@basile.app", rol.id, empresa_a.id)
        proveedor_b = await _crear_proveedor(db_session, empresa_b.id, "Proveedor B")

        response = await client.get(f"/proveedores/{proveedor_b.id}", headers=_auth_header(usuario_a, empresa_id=empresa_a.id))
        assert response.status_code == 404

    async def test_obtener_proveedor_no_existente(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        usuario = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)

        response = await client.get(f"/proveedores/{uuid.uuid4()}", headers=_auth_header(usuario, empresa_id=empresa.id))
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Tests: PUT /proveedores/{id}
# ---------------------------------------------------------------------------
class TestUpdateProveedor:
    async def test_actualizar_proveedor(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        usuario = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)
        proveedor = await _crear_proveedor(db_session, empresa.id, "Viejo Nombre", "30616874582")

        response = await client.put(f"/proveedores/{proveedor.id}", headers=_auth_header(usuario, empresa_id=empresa.id), json={
            "nombre": "Nuevo Nombre",
            "telefono": "987654321",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["nombre"] == "Nuevo Nombre"
        assert data["telefono"] == "987654321"
        assert data["cuit"] == "30616874582"

    async def test_actualizar_cuit_duplicado(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        usuario = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)
        await _crear_proveedor(db_session, empresa.id, "Proveedor A", "30616874582")
        proveedor_b = await _crear_proveedor(db_session, empresa.id, "Proveedor B", "30712345678")

        response = await client.put(f"/proveedores/{proveedor_b.id}", headers=_auth_header(usuario, empresa_id=empresa.id), json={
            "cuit": "30616874582",
        })
        assert response.status_code == 409

    async def test_actualizar_proveedor_otra_empresa_404(self, client: AsyncClient, db_session: AsyncSession):
        empresa_a = await _crear_empresa(db_session, "Empresa A")
        empresa_b = await _crear_empresa(db_session, "Empresa B")
        rol = await _crear_rol(db_session, "Administrador")
        usuario_a = await _crear_usuario(db_session, "admin_a@basile.app", rol.id, empresa_a.id)
        proveedor_b = await _crear_proveedor(db_session, empresa_b.id, "Proveedor B")

        response = await client.put(f"/proveedores/{proveedor_b.id}", headers=_auth_header(usuario_a, empresa_id=empresa_a.id), json={
            "nombre": "Hack",
        })
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Tests: DELETE /proveedores/{id}
# ---------------------------------------------------------------------------
class TestDeleteProveedor:
    async def test_baja_logica(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        usuario = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)
        proveedor = await _crear_proveedor(db_session, empresa.id, "A Dar de Baja")

        response = await client.delete(f"/proveedores/{proveedor.id}", headers=_auth_header(usuario, empresa_id=empresa.id))
        assert response.status_code == 204

        # Verify in DB — refresh the object to see committed changes
        await db_session.refresh(proveedor)
        assert proveedor.activo is False

    async def test_baja_logica_proveedor_otra_empresa_404(self, client: AsyncClient, db_session: AsyncSession):
        empresa_a = await _crear_empresa(db_session, "Empresa A")
        empresa_b = await _crear_empresa(db_session, "Empresa B")
        rol = await _crear_rol(db_session, "Administrador")
        usuario_a = await _crear_usuario(db_session, "admin_a@basile.app", rol.id, empresa_a.id)
        proveedor_b = await _crear_proveedor(db_session, empresa_b.id, "Proveedor B")

        response = await client.delete(f"/proveedores/{proveedor_b.id}", headers=_auth_header(usuario_a, empresa_id=empresa_a.id))
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Tests: GET /proveedores/{id}/historial
# ---------------------------------------------------------------------------
class TestHistorialProveedor:
    async def test_historial_vacio(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Administrador")
        usuario = await _crear_usuario(db_session, "admin@basile.app", rol.id, empresa.id)
        proveedor = await _crear_proveedor(db_session, empresa.id, "Carnes del Sur")

        response = await client.get(f"/proveedores/{proveedor.id}/historial", headers=_auth_header(usuario, empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_historial_proveedor_otra_empresa_404(self, client: AsyncClient, db_session: AsyncSession):
        empresa_a = await _crear_empresa(db_session, "Empresa A")
        empresa_b = await _crear_empresa(db_session, "Empresa B")
        rol = await _crear_rol(db_session, "Administrador")
        usuario_a = await _crear_usuario(db_session, "admin_a@basile.app", rol.id, empresa_a.id)
        proveedor_b = await _crear_proveedor(db_session, empresa_b.id, "Proveedor B")

        response = await client.get(f"/proveedores/{proveedor_b.id}/historial", headers=_auth_header(usuario_a, empresa_id=empresa_a.id))
        assert response.status_code == 404

    async def test_historial_rol_sin_permiso(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, "Cajero")
        usuario = await _crear_usuario(db_session, "cajero@basile.app", rol.id, empresa.id)
        proveedor = await _crear_proveedor(db_session, empresa.id, "Carnes del Sur")

        response = await client.get(f"/proveedores/{proveedor.id}/historial", headers=_auth_header(usuario, rol_nombre="Cajero", empresa_id=empresa.id))
        assert response.status_code == 403
