import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.models import Usuario, Rol, Empresa
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


async def _crear_rol(db: AsyncSession, nombre: str = "admin") -> Rol:
    rol = Rol(nombre=nombre)
    db.add(rol)
    await db.commit()
    await db.refresh(rol)
    return rol


async def _crear_usuario(
    db: AsyncSession,
    email: str,
    rol_id: uuid.UUID,
    empresa_id: uuid.UUID | None,
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


async def _crear_superadmin(db: AsyncSession, email: str = "superadmin@basile.app") -> Usuario:
    rol = Rol(nombre="superadmin")
    db.add(rol)
    await db.commit()
    await db.refresh(rol)
    u = Usuario(
        email=email,
        contrasena_hash=hash_password("Password123"),
        nombre="Super",
        apellido="Admin",
        rol_id=rol.id,
        activo=True,
        empresa_id=None,
    )
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


def _auth_header(usuario: Usuario, rol_nombre: str = "admin", empresa_id=None):
    token = create_access_token({
        "sub": str(usuario.id),
        "empresa_id": str(empresa_id or usuario.empresa_id) if (empresa_id or usuario.empresa_id) else None,
        "rol": rol_nombre,
    })
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# RBAC Integration Tests
# ---------------------------------------------------------------------------
class TestSuperadminPuedeCrearEmpresa:
    async def test_superadmin_puede_crear_empresa(self, client: AsyncClient, db_session: AsyncSession):
        superadmin = await _crear_superadmin(db_session)

        response = await client.post("/empresas", headers=_auth_header(superadmin, rol_nombre="superadmin"), json={
            "nombre_comercial": "Nueva Empresa SA",
            "cuit": "30-12345678-9",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["nombre_comercial"] == "Nueva Empresa SA"


class TestAdminNoPuedeCrearEmpresa:
    async def test_admin_no_puede_crear_empresa(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_admin = await _crear_rol(db_session, "admin")
        admin = await _crear_usuario(db_session, "admin@basile.app", rol_admin.id, empresa.id)

        response = await client.post("/empresas", headers=_auth_header(admin, rol_nombre="admin", empresa_id=empresa.id), json={
            "nombre_comercial": "Hack",
        })
        assert response.status_code == 403


class TestSuperadminPuedeCrearAdmin:
    async def test_superadmin_puede_crear_admin(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        superadmin = await _crear_superadmin(db_session)
        rol_admin = await _crear_rol(db_session, "admin")

        response = await client.post("/usuarios", headers=_auth_header(superadmin, rol_nombre="superadmin"), json={
            "nombre": "Nuevo",
            "apellido": "Admin",
            "email": "nuevo_admin@basile.app",
            "rol_id": str(rol_admin.id),
            "empresa_id": str(empresa.id),
        })
        assert response.status_code == 201
        data = response.json()
        assert data["usuario"]["rol"] == "admin"


class TestAdminNoPuedeCrearOtroAdmin:
    async def test_admin_no_puede_crear_otro_admin(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_admin = await _crear_rol(db_session, "admin")
        admin = await _crear_usuario(db_session, "admin@basile.app", rol_admin.id, empresa.id)

        response = await client.post("/usuarios", headers=_auth_header(admin, rol_nombre="admin", empresa_id=empresa.id), json={
            "nombre": "Otro",
            "apellido": "Admin",
            "email": "otro_admin@basile.app",
            "rol_id": str(rol_admin.id),
            "empresa_id": str(empresa.id),
        })
        assert response.status_code == 403


class TestAdminPuedeCrearCajero:
    async def test_admin_puede_crear_cajero(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_admin = await _crear_rol(db_session, "admin")
        rol_cajero = await _crear_rol(db_session, "cajero")
        admin = await _crear_usuario(db_session, "admin@basile.app", rol_admin.id, empresa.id)

        response = await client.post("/usuarios", headers=_auth_header(admin, rol_nombre="admin", empresa_id=empresa.id), json={
            "nombre": "Nuevo",
            "apellido": "Cajero",
            "email": "nuevo_cajero@basile.app",
            "rol_id": str(rol_cajero.id),
        })
        assert response.status_code == 201
        data = response.json()
        assert data["usuario"]["rol"] == "cajero"
        assert "contrasena_temporal" in data


class TestSuperadminPuedeImpersonar:
    async def test_superadmin_puede_impersonar(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        superadmin = await _crear_superadmin(db_session)

        response = await client.post("/soporte/impersonate", headers=_auth_header(superadmin, rol_nombre="superadmin"), json={
            "empresa_id": str(empresa.id),
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"


class TestAdminNoPuedeImpersonar:
    async def test_admin_no_puede_impersonar(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol_admin = await _crear_rol(db_session, "admin")
        admin = await _crear_usuario(db_session, "admin@basile.app", rol_admin.id, empresa.id)

        response = await client.post("/soporte/impersonate", headers=_auth_header(admin, rol_nombre="admin", empresa_id=empresa.id), json={
            "empresa_id": str(empresa.id),
        })
        assert response.status_code == 403


class TestImpersonateTokenTieneOriginalRole:
    async def test_impersonate_token_tiene_original_role(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        superadmin = await _crear_superadmin(db_session)

        response = await client.post("/soporte/impersonate", headers=_auth_header(superadmin, rol_nombre="superadmin"), json={
            "empresa_id": str(empresa.id),
        })
        assert response.status_code == 200
        data = response.json()
        token = data["access_token"]

        from src.core.security import decode_token
        from src.config.settings import settings
        payload = decode_token(token, secret=settings.jwt_secret, token_type="access")
        assert payload["original_role"] == "superadmin"
        assert payload["rol"] == "admin"
        assert payload["empresa_id"] == str(empresa.id)
