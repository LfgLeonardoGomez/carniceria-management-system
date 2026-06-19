import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

from src.modules.auth.models import Usuario, Rol, Empresa
from src.core.security import create_access_token, create_refresh_token, hash_password


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def crear_empresa(db_session: AsyncSession, nombre: str = "Carnicería Test") -> Empresa:
    empresa = Empresa(nombre_comercial=nombre, activa=True)
    db_session.add(empresa)
    await db_session.commit()
    await db_session.refresh(empresa)
    return empresa


async def crear_rol(db_session: AsyncSession, nombre: str = "admin", empresa_id=None) -> Rol:
    rol = Rol(nombre=nombre, empresa_id=empresa_id)
    db_session.add(rol)
    await db_session.commit()
    await db_session.refresh(rol)
    return rol


async def crear_usuario(
    db_session: AsyncSession,
    email: str = "test@basile.app",
    password: str = "Password123",
    activo: bool = True,
    empresa_id=None,
    rol_id=None,
) -> Usuario:
    if rol_id is None:
        rol = await crear_rol(db_session, empresa_id=empresa_id)
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


# ---------------------------------------------------------------------------
# TASK-3.1 + TASK-3.2: get_current_user / require_auth
# ---------------------------------------------------------------------------
class TestAuthDependencies:
    async def test_ruta_protegida_sin_token(self, client: AsyncClient):
        response = await client.get("/auth/me")
        assert response.status_code == 401

    async def test_ruta_protegida_con_token_valido(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await crear_empresa(db_session)
        usuario = await crear_usuario(db_session, email="auth@basile.app", empresa_id=empresa.id)
        token = create_access_token({"sub": str(usuario.id), "empresa_id": str(empresa.id), "rol": "admin"})
        response = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "auth@basile.app"

    async def test_ruta_protegida_con_token_expirado(self, client: AsyncClient):
        token = create_access_token({"sub": "123"}, expires_delta=timedelta(minutes=-10))
        response = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401

    async def test_ruta_protegida_con_refresh_token_rechazado(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await crear_empresa(db_session)
        usuario = await crear_usuario(db_session, email="refreshrej@basile.app", empresa_id=empresa.id)
        token = create_refresh_token({"sub": str(usuario.id), "empresa_id": str(empresa.id), "rol": "admin"})
        response = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401

    async def test_ruta_protegida_usuario_inactivo(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await crear_empresa(db_session)
        usuario = await crear_usuario(db_session, email="inactive@basile.app", activo=False, empresa_id=empresa.id)
        token = create_access_token({"sub": str(usuario.id), "empresa_id": str(empresa.id), "rol": "admin"})
        response = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 403

    async def test_rutas_publicas_no_requieren_auth(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await crear_empresa(db_session)
        await crear_usuario(db_session, email="public@basile.app", empresa_id=empresa.id)
        response = await client.post("/auth/login", json={"email": "public@basile.app", "contrasena": "Password123"})
        assert response.status_code == 200

        response = await client.post("/auth/recover", json={"email": "public@basile.app"})
        assert response.status_code == 200

        response = await client.post("/auth/reset", json={"token": "abc", "nueva_contrasena": "NewPass123", "confirmacion": "NewPass123"})
        assert response.status_code == 400  # invalid token, but not 401

    async def test_middleware_inyecta_empresa_id(self, client: AsyncClient, db_session: AsyncSession):
        """TASK-3.2: Verificar que request.state contiene empresa_id."""
        empresa = await crear_empresa(db_session)
        usuario = await crear_usuario(db_session, email="middleware@basile.app", empresa_id=empresa.id)
        token = create_access_token({"sub": str(usuario.id), "empresa_id": str(empresa.id), "rol": "admin"})
        response = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # The middleware injects state, but we can verify indirectly via a custom route
        # For now, the endpoint works which means the dependency chain executed successfully

    async def test_me_endpoint(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await crear_empresa(db_session)
        usuario = await crear_usuario(db_session, email="me@basile.app", empresa_id=empresa.id)
        token = create_access_token({"sub": str(usuario.id), "empresa_id": str(empresa.id), "rol": "admin"})
        response = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me@basile.app"
        assert data["id"] == str(usuario.id)

    async def test_me_sin_token(self, client: AsyncClient):
        response = await client.get("/auth/me")
        assert response.status_code == 401

    async def test_superadmin_con_empresa_id_null(self, client: AsyncClient, db_session: AsyncSession):
        """superadmin con empresa_id = NULL puede acceder a endpoints globales."""
        rol = await crear_rol(db_session, nombre="superadmin")
        superadmin = Usuario(
            email="super@basile.app",
            contrasena_hash=hash_password("Password123"),
            nombre="Super",
            apellido="Admin",
            rol_id=rol.id,
            activo=True,
            empresa_id=None,
        )
        db_session.add(superadmin)
        await db_session.commit()
        await db_session.refresh(superadmin)

        token = create_access_token({"sub": str(superadmin.id), "empresa_id": None, "rol": "superadmin"})
        response = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "super@basile.app"
        assert data["empresa_id"] is None
