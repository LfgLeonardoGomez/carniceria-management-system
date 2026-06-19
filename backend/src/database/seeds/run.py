import os
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

# Fix Windows event loop issue if using async elsewhere
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from database.seeds.roles import seed_roles
from database.seeds.admin_user import seed_admin_user
from database.seeds.categorias_producto import seed_categorias_producto
from database.seeds.tipos_corte import seed_tipos_corte
from database.seeds.categorias_gasto import seed_categorias_gasto

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://basile:basile@localhost:5432/basile",
)

# Use sync driver for seeds
SYNC_DATABASE_URL = DATABASE_URL.replace("postgresql+psycopg", "postgresql")


def run_seeds() -> None:
    engine = create_engine(SYNC_DATABASE_URL, echo=False)
    SQLModel.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as session:
        print("Insertando roles...")
        seed_roles(session)
        print("Insertando usuario admin por defecto...")
        seed_admin_user(session)
        print("Insertando categorías de producto...")
        seed_categorias_producto(session)
        print("Insertando tipos de corte...")
        seed_tipos_corte(session)
        print("Insertando categorías de gasto...")
        seed_categorias_gasto(session)
        print("Seeds completados.")


if __name__ == "__main__":
    run_seeds()
