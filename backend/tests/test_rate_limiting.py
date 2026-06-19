import sys
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

from src.modules.auth.models import Usuario, Rol, Empresa
from src.core.security import hash_password


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
# TASK-4.1: Rate limiting
# ---------------------------------------------------------------------------
class TestRateLimiting:
    async def test_login_rate_limit_5_intentos(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await crear_empresa(db_session)
        await crear_usuario(db_session, email="ratelimit@basile.app", empresa_id=empresa.id)

        # 5 attempts should be allowed (even with wrong password)
        for _ in range(5):
            resp = await client.post("/auth/login", json={
                "email": "ratelimit@basile.app",
                "contrasena": "WrongPassword123",
            })
            assert resp.status_code == 401

        # 6th attempt should be rate limited
        resp = await client.post("/auth/login", json={
            "email": "ratelimit@basile.app",
            "contrasena": "WrongPassword123",
        })
        assert resp.status_code == 429

    async def test_recover_rate_limit_5_intentos(self, client: AsyncClient):
        # Use a different email to avoid shared state with login test
        # 5 attempts should be allowed
        for _ in range(5):
            resp = await client.post("/auth/recover", json={"email": "recoverlimit@basile.app"})
            assert resp.status_code == 200

        # 6th attempt should be rate limited
        resp = await client.post("/auth/recover", json={"email": "recoverlimit@basile.app"})
        assert resp.status_code == 429
