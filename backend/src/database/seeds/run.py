import os
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

# Fix Windows event loop issue if using async elsewhere
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

# Import all models so SQLAlchemy can resolve relationships
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
from src.modules.compra.models import Compra  # noqa: F401
from src.modules.gasto.models import CategoriaGasto  # noqa: F401

from src.database.seeds.roles import seed_roles
from src.database.seeds.admin_user import seed_admin_user
from src.database.seeds.categorias_producto import seed_categorias_producto
from src.database.seeds.tipos_corte import seed_tipos_corte
from src.database.seeds.categorias_gasto import seed_categorias_gasto
from src.database.seeds.permisos import seed_permisos

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://basile:basile@localhost:5432/basile",
)

# Use sync driver for seeds (psycopg3 sync)
SYNC_DATABASE_URL = DATABASE_URL.replace("postgresql+psycopg", "postgresql+psycopg")


def run_seeds() -> None:
    engine = create_engine(SYNC_DATABASE_URL, echo=False)
    # Tables already created by migrations; skip create_all
    # SQLModel.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as session:
        print("Insertando roles...")
        seed_roles(session)
        print("Insertando usuario admin por defecto...")
        seed_admin_user(session)
        print("Insertando categorías de producto para cada empresa...")
        empresas = session.query(Empresa).all()
        for empresa in empresas:
            seed_categorias_producto(session, empresa_id=empresa.id)
        print(f"Categorías insertadas para {len(empresas)} empresa(s).")
        print("Insertando tipos de corte (catálogo global)...")
        seed_tipos_corte(session)
        print("Insertando categorías de gasto...")
        seed_categorias_gasto(session)
        print("Poblando permisos RBAC por rol...")
        seed_permisos(session)
        print("Seeds completados.")


if __name__ == "__main__":
    run_seeds()
