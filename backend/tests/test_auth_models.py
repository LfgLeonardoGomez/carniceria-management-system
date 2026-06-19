import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

from src.modules.auth.models import RefreshToken, TokenRecuperacion, Usuario, Rol
from src.config.database import AsyncSessionLocal, engine
from src.modules.empresa.models import Empresa


@pytest.fixture(scope="module")
def event_loop():
    import asyncio
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def db():
    async with engine.begin() as conn:
        # Create tables for test
        await conn.run_sync(lambda sync_conn: None)  # placeholder
    async with AsyncSessionLocal() as session:
        yield session


class TestRefreshTokenModel:
    """TASK-0.1: Tests para modelo RefreshToken."""

    def test_refresh_token_columns_exist(self):
        cols = {c.name for c in RefreshToken.__table__.columns}
        required = {
            "id", "usuario_id", "jti", "exp", "revoked",
            "created_at", "updated_at",
        }
        assert required.issubset(cols), f"RefreshToken falta columnas: {required - cols}"

    def test_refresh_token_jti_unique(self):
        assert RefreshToken.__table__.columns["jti"].unique, "jti debe ser único"

    def test_refresh_token_revoked_default(self):
        from sqlalchemy import false
        col = RefreshToken.__table__.columns["revoked"]
        assert col.default is not None or col.server_default is not None, \
            "revoked debe tener default=False"

    def test_refresh_token_instance_creation(self):
        now = datetime.now(timezone.utc)
        token = RefreshToken(
            usuario_id="12345678-1234-5678-1234-567812345678",
            jti="test-jti-123",
            exp=now + timedelta(days=7),
            revoked=False,
        )
        assert token.jti == "test-jti-123"
        assert token.revoked is False
        assert token.usuario_id is not None


class TestTokenRecuperacionModel:
    """TASK-0.2: Tests para modelo TokenRecuperacion."""

    def test_token_recuperacion_columns_exist(self):
        cols = {c.name for c in TokenRecuperacion.__table__.columns}
        required = {
            "id", "usuario_id", "token_hash", "expiracion",
            "usado", "created_at",
        }
        assert required.issubset(cols), f"TokenRecuperacion falta columnas: {required - cols}"

    def test_token_recuperacion_usado_default(self):
        col = TokenRecuperacion.__table__.columns["usado"]
        assert col.default is not None or col.server_default is not None, \
            "usado debe tener default=False"

    def test_token_recuperacion_instance_creation(self):
        now = datetime.now(timezone.utc)
        tr = TokenRecuperacion(
            usuario_id="12345678-1234-5678-1234-567812345678",
            token_hash="sha256-hash",
            expiracion=now + timedelta(hours=1),
            usado=False,
        )
        assert tr.token_hash == "sha256-hash"
        assert tr.usado is False
        assert tr.expiracion > now
