import asyncio
import os
import sys
from logging.config import fileConfig

# Add project root to path so 'src' package is importable
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from sqlmodel import SQLModel

# Import all models to register them in SQLModel.metadata
from src.modules.empresa.models import Empresa  # noqa: F401
from src.modules.auth.models import Rol, Usuario, RefreshToken, TokenRecuperacion  # noqa: F401
from src.modules.producto.models import CategoriaProducto, Producto  # noqa: F401
from src.modules.cliente.models import Cliente  # noqa: F401
from src.modules.proveedor.models import Proveedor  # noqa: F401
from src.modules.auditoria.models import Auditoria  # noqa: F401
from src.modules.notificacion.models import Notificacion  # noqa: F401
from src.modules.desposte.models import Desposte, CorteDesposte  # noqa: F401
from src.modules.venta.models import Venta, DetalleVenta, PagoVenta  # noqa: F401
from src.modules.caja.models import Caja, MovimientoCaja  # noqa: F401
from src.modules.cuenta_corriente.models import CuentaCorriente  # noqa: F401

# Fix Windows ProactorEventLoop incompatibility with psycopg async
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# target_metadata for 'autogenerate' support
target_metadata = SQLModel.metadata

def get_database_url() -> str:
    """Read DATABASE_URL from environment or alembic.ini."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        db_url = config.get_main_option("sqlalchemy.url")
    return db_url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Synchronous migration runner."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode using async engine."""
    url = get_database_url()
    connectable = create_async_engine(url, poolclass=pool.NullPool, future=True)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
