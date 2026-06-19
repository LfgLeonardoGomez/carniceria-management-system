import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.modules.auth.models import Usuario, Rol, RefreshToken, TokenRecuperacion, Empresa
from src.core.security import hash_password, create_access_token

REFRESH_COOKIE_NAME = "refresh_token"


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
# TASK-2.1: POST /auth/login
# ---------------------------------------------------------------------------
class TestLogin:
    async def test_login_exitoso(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await crear_empresa(db_session)
        await crear_usuario(db_session, email="login@basile.app", password="Password123", empresa_id=empresa.id)

        response = await client.post("/auth/login", json={
            "email": "login@basile.app",
            "contrasena": "Password123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["usuario"]["email"] == "login@basile.app"
        # Verify refresh token cookie
        cookies = response.cookies
        assert "refresh_token" in cookies

        # Verify refresh token persisted in DB
        result = await db_session.execute(select(RefreshToken))
        tokens = result.scalars().all()
        assert len(tokens) == 1
        assert tokens[0].revoked is False

    async def test_login_contrasena_incorrecta(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await crear_empresa(db_session)
        await crear_usuario(db_session, email="badpass@basile.app", password="Password123", empresa_id=empresa.id)

        response = await client.post("/auth/login", json={
            "email": "badpass@basile.app",
            "contrasena": "WrongPassword123",
        })
        assert response.status_code == 401

    async def test_login_usuario_inactivo(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await crear_empresa(db_session)
        await crear_usuario(db_session, email="inactive@basile.app", password="Password123", activo=False, empresa_id=empresa.id)

        response = await client.post("/auth/login", json={
            "email": "inactive@basile.app",
            "contrasena": "Password123",
        })
        assert response.status_code == 403

    async def test_login_email_inexistente(self, client: AsyncClient):
        response = await client.post("/auth/login", json={
            "email": "noexiste@basile.app",
            "contrasena": "Password123",
        })
        assert response.status_code == 401

    async def test_login_request_extra_fields_rejected(self, client: AsyncClient):
        response = await client.post("/auth/login", json={
            "email": "test@basile.app",
            "contrasena": "Password123",
            "extra_field": "should_fail",
        })
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# TASK-2.3: POST /auth/recover
# ---------------------------------------------------------------------------
class TestRecover:
    async def test_recover_email_existente(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await crear_empresa(db_session)
        await crear_usuario(db_session, email="recover@basile.app", empresa_id=empresa.id)

        response = await client.post("/auth/recover", json={
            "email": "recover@basile.app",
        })
        assert response.status_code == 200
        # Generic message, should not reveal existence
        data = response.json()
        assert "message" in data

        # Verify token was generated in DB
        result = await db_session.execute(select(TokenRecuperacion))
        tokens = result.scalars().all()
        assert len(tokens) == 1
        assert tokens[0].usado is False
        assert tokens[0].expiracion > datetime.utcnow()

    async def test_recover_email_inexistente(self, client: AsyncClient):
        response = await client.post("/auth/recover", json={
            "email": "nope@basile.app",
        })
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    async def test_recover_request_extra_fields_rejected(self, client: AsyncClient):
        response = await client.post("/auth/recover", json={
            "email": "test@basile.app",
            "extra": "field",
        })
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# TASK-2.4: POST /auth/reset
# ---------------------------------------------------------------------------
class TestReset:
    async def test_reset_exitoso(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await crear_empresa(db_session)
        usuario = await crear_usuario(db_session, email="reset@basile.app", password="OldPass123", empresa_id=empresa.id)
        # Create recovery token
        from secrets import token_urlsafe
        raw_token = token_urlsafe(32)
        import hashlib
        tr = TokenRecuperacion(
            usuario_id=usuario.id,
            token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
            expiracion=datetime.utcnow() + timedelta(hours=1),
            usado=False,
        )
        db_session.add(tr)
        await db_session.commit()

        response = await client.post("/auth/reset", json={
            "token": raw_token,
            "nueva_contrasena": "NewPass123",
            "confirmacion": "NewPass123",
        })
        assert response.status_code == 200

        # Verify password changed
        await db_session.refresh(usuario)
        from src.core.security import verify_password
        assert verify_password("NewPass123", usuario.contrasena_hash)  # password was updated
        # Verify token marked as used
        await db_session.refresh(tr)
        assert tr.usado is True

    async def test_reset_token_expirado(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await crear_empresa(db_session)
        usuario = await crear_usuario(db_session, email="resetexp@basile.app", password="OldPass123", empresa_id=empresa.id)
        from secrets import token_urlsafe
        raw_token = token_urlsafe(32)
        import hashlib
        tr = TokenRecuperacion(
            usuario_id=usuario.id,
            token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
            expiracion=datetime.utcnow() - timedelta(hours=1),
            usado=False,
        )
        db_session.add(tr)
        await db_session.commit()

        response = await client.post("/auth/reset", json={
            "token": raw_token,
            "nueva_contrasena": "NewPass123",
            "confirmacion": "NewPass123",
        })
        assert response.status_code == 400

    async def test_reset_token_ya_usado(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await crear_empresa(db_session)
        usuario = await crear_usuario(db_session, email="resetused@basile.app", password="OldPass123", empresa_id=empresa.id)
        from secrets import token_urlsafe
        raw_token = token_urlsafe(32)
        import hashlib
        tr = TokenRecuperacion(
            usuario_id=usuario.id,
            token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
            expiracion=datetime.utcnow() + timedelta(hours=1),
            usado=True,
        )
        db_session.add(tr)
        await db_session.commit()

        response = await client.post("/auth/reset", json={
            "token": raw_token,
            "nueva_contrasena": "NewPass123",
            "confirmacion": "NewPass123",
        })
        assert response.status_code == 400

    async def test_reset_contrasena_debil(self, client: AsyncClient):
        response = await client.post("/auth/reset", json={
            "token": "sometoken",
            "nueva_contrasena": "weak",
            "confirmacion": "weak",
        })
        assert response.status_code == 422

    async def test_reset_confirmacion_no_coincide(self, client: AsyncClient):
        response = await client.post("/auth/reset", json={
            "token": "sometoken",
            "nueva_contrasena": "NewPass123",
            "confirmacion": "Different456",
        })
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# TASK-2.5: POST /auth/refresh
# ---------------------------------------------------------------------------
class TestRefresh:
    async def test_refresh_exitoso(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await crear_empresa(db_session)
        usuario = await crear_usuario(db_session, email="refresh@basile.app", empresa_id=empresa.id)

        # Login to get refresh token
        login_resp = await client.post("/auth/login", json={
            "email": "refresh@basile.app",
            "contrasena": "Password123",
        })
        assert login_resp.status_code == 200
        old_refresh_cookie = login_resp.cookies["refresh_token"]

        # Refresh
        refresh_resp = await client.post("/auth/refresh", cookies={"refresh_token": old_refresh_cookie})
        assert refresh_resp.status_code == 200
        data = refresh_resp.json()
        assert "access_token" in data
        new_refresh_cookie = refresh_resp.cookies["refresh_token"]
        assert new_refresh_cookie != old_refresh_cookie

        # Verify old token revoked
        result = await db_session.execute(select(RefreshToken).where(RefreshToken.revoked == True))
        revoked = result.scalars().all()
        assert len(revoked) >= 1

    async def test_refresh_token_reutilizado(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await crear_empresa(db_session)
        usuario = await crear_usuario(db_session, email="refresh2@basile.app", empresa_id=empresa.id)

        login_resp = await client.post("/auth/login", json={
            "email": "refresh2@basile.app",
            "contrasena": "Password123",
        })
        old_refresh_cookie = login_resp.cookies["refresh_token"]

        # First refresh
        await client.post("/auth/refresh", cookies={"refresh_token": old_refresh_cookie})

        # Reuse same refresh token
        second = await client.post("/auth/refresh", cookies={"refresh_token": old_refresh_cookie})
        assert second.status_code == 401


# ---------------------------------------------------------------------------
# TASK-2.6: POST /auth/logout
# ---------------------------------------------------------------------------
class TestLogout:
    async def test_logout_borra_cookie_y_revoca(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await crear_empresa(db_session)
        await crear_usuario(db_session, email="logout@basile.app", empresa_id=empresa.id)

        login_resp = await client.post("/auth/login", json={
            "email": "logout@basile.app",
            "contrasena": "Password123",
        })
        refresh_cookie = login_resp.cookies["refresh_token"]

        logout_resp = await client.post("/auth/logout", cookies={"refresh_token": refresh_cookie})
        assert logout_resp.status_code == 204
        set_cookie = logout_resp.headers.get("set-cookie", "")
        assert REFRESH_COOKIE_NAME in set_cookie
        assert "Max-Age=0" in set_cookie or "max-age=0" in set_cookie

        # Verify revoked in DB
        result = await db_session.execute(select(RefreshToken).where(RefreshToken.revoked == True))
        revoked = result.scalars().all()
        assert len(revoked) >= 1

    async def test_logout_sin_cookie(self, client: AsyncClient):
        response = await client.post("/auth/logout")
        assert response.status_code == 204

    async def test_refresh_sin_cookie(self, client: AsyncClient):
        response = await client.post("/auth/refresh")
        assert response.status_code == 401

    async def test_refresh_cookie_invalido(self, client: AsyncClient):
        response = await client.post("/auth/refresh", cookies={"refresh_token": "not.a.valid.token"})
        assert response.status_code == 401

    async def test_refresh_usuario_inactivo(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await crear_empresa(db_session)
        usuario = await crear_usuario(db_session, email="refreshinactive@basile.app", activo=False, empresa_id=empresa.id)

        login_resp = await client.post("/auth/login", json={
            "email": "refreshinactive@basile.app",
            "contrasena": "Password123",
        })
        # Login itself should fail with 403 because user is inactive
        assert login_resp.status_code == 403
