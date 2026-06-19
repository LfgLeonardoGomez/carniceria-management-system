import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from testcontainers.postgres import PostgresContainer

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Prevent SQLModel metadata conflicts by aliasing modules.* to src.modules.*
# (existing tests use modules.* imports via sys.path.insert)
import importlib
for _mod_name in ["empresa.models", "auth.models", "usuario.models", "producto.models", "desposte.models", "gasto.models", "compra.models", "stock.models", "cliente.models", "proveedor.models", "venta.models", "caja.models", "auditoria.models"]:
    try:
        _src_mod = importlib.import_module(f"src.modules.{_mod_name}")
        sys.modules[f"modules.{_mod_name}"] = _src_mod
    except Exception:
        pass

# Fix Windows ProactorEventLoop incompatibility with psycopg async
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@pytest.fixture(scope="session")
def postgres_url():
    postgres = PostgresContainer("postgres:14-alpine")
    postgres.start()
    url = postgres.get_connection_url().replace("postgresql+psycopg2", "postgresql+psycopg")
    yield url
    postgres.stop()


@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def db_engine(postgres_url: str):
    engine = create_async_engine(
        postgres_url,
        echo=False,
        future=True,
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def init_db(db_engine):
    from sqlmodel import SQLModel
    async with db_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield


@pytest_asyncio.fixture
async def db_connection(db_engine, init_db):
    """Provide a single connection per test with an open transaction.
    Everything rolls back at the end of the test.
    """
    async with db_engine.connect() as conn:
        trans = await conn.begin()
        yield conn
        await trans.rollback()


@pytest_asyncio.fixture
async def db_session(db_connection) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(
        db_connection,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_connection, init_db) -> AsyncGenerator[AsyncClient, None]:
    """Async httpx client with DB dependency overridden to use the same transaction."""
    os.environ["DATABASE_URL"] = str(db_connection.engine.url)

    from src.main import app
    from src.config.database import get_db

    session_factory = async_sessionmaker(
        db_connection,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
