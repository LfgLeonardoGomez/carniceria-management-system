from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.modules.auth.models import Usuario, Rol, Empresa, RefreshToken
from src.core.security import hash_password, create_access_token


async def _crear_empresa(db_session: AsyncSession, nombre: str = "Carnicería Test", activa: bool = True) -> Empresa:
    empresa = Empresa(nombre_comercial=nombre, activa=activa)
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


class TestLoginEmpresaDesactivada:
    async def test_login_rechaza_empresa_desactivada(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session, nombre="Desactivada", activa=False)
        await _crear_usuario(db_session, email="user@basile.app", password="Password123", empresa_id=empresa.id)

        response = await client.post("/auth/login", json={
            "email": "user@basile.app",
            "contrasena": "Password123",
        })
        assert response.status_code == 403
        data = response.json()
        assert "Empresa desactivada" in data["detail"]

    async def test_login_acepta_empresa_activa(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session, nombre="Activa", activa=True)
        await _crear_usuario(db_session, email="active@basile.app", password="Password123", empresa_id=empresa.id)

        response = await client.post("/auth/login", json={
            "email": "active@basile.app",
            "contrasena": "Password123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data


class TestAislamientoMultiTenant:
    async def test_usuario_a_no_ve_datos_empresa_b(self, client: AsyncClient, db_session: AsyncSession):
        empresa_a = await _crear_empresa(db_session, nombre="Empresa A")
        empresa_b = await _crear_empresa(db_session, nombre="Empresa B")
        rol_a = await _crear_rol(db_session, nombre="Administrador", empresa_id=empresa_a.id)
        usuario_a = await _crear_usuario(db_session, email="a@basile.app", empresa_id=empresa_a.id, rol_id=rol_a.id)

        token_a = create_access_token({"sub": str(usuario_a.id), "empresa_id": str(empresa_a.id), "rol": "Administrador"})
        response = await client.get("/empresas/me", headers={"Authorization": f"Bearer {token_a}"})
        assert response.status_code == 200
        data = response.json()
        assert data["nombre_comercial"] == "Empresa A"
        assert data["nombre_comercial"] != "Empresa B"

    async def test_logo_url_relativo(self, client: AsyncClient, db_session: AsyncSession, tmp_path: Path):
        from src.config.settings import settings
        original = settings.upload_path
        settings.upload_path = str(tmp_path / "uploads")
        try:
            empresa = await _crear_empresa(db_session, nombre="Logo Test")
            rol = await _crear_rol(db_session, nombre="Administrador", empresa_id=empresa.id)
            usuario = await _crear_usuario(db_session, email="logo@basile.app", empresa_id=empresa.id, rol_id=rol.id)

            content = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"x" * 100
            response = await client.post(
                "/empresas/me/logo",
                headers={"Authorization": f"Bearer {create_access_token({'sub': str(usuario.id), 'empresa_id': str(empresa.id), 'rol': 'Administrador'})}"},
                files={"file": ("logo.jpg", content, "image/jpeg")},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["logo_url"].startswith("/uploads/")
            assert "C:" not in data["logo_url"]  # Windows path leak prevention
            assert "\\" not in data["logo_url"]
        finally:
            settings.upload_path = original
