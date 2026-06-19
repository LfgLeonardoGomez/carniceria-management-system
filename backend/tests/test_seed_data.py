import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "src"))


def test_seed_roles():
    """Task 5.2: Seed data de roles."""
    from database.seeds.roles import seed_roles

    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as session:
        seed_roles(session)
        from modules.auth.models import Rol
        count = session.query(Rol).count()
        assert count == 5, f"Esperaba 5 roles, hay {count}"


def test_seed_categorias_producto():
    """Task 5.3: Seed data de categorías de producto."""
    from database.seeds.categorias_producto import seed_categorias_producto
    from modules.empresa.models import Empresa

    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as session:
        # Crear una empresa primero para asociar las categorías
        empresa = Empresa(nombre_comercial="Test", activa=True)
        session.add(empresa)
        session.commit()
        session.refresh(empresa)

        seed_categorias_producto(session, empresa_id=empresa.id)
        from modules.producto.models import CategoriaProducto
        count = session.query(CategoriaProducto).filter(
            CategoriaProducto.empresa_id == empresa.id
        ).count()
        assert count == 5, f"Esperaba 5 categorías, hay {count}"


def test_seed_tipos_corte():
    """Task 5.4: Seed data de tipos de corte."""
    from database.seeds.tipos_corte import seed_tipos_corte

    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as session:
        seed_tipos_corte(session)
        from modules.desposte.models import TipoCorte
        count = session.query(TipoCorte).count()
        assert count == 12, f"Esperaba 12 tipos de corte, hay {count}"


def test_seed_categorias_gasto():
    """Task 5.5: Seed data de categorías de gasto."""
    from database.seeds.categorias_gasto import seed_categorias_gasto

    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as session:
        seed_categorias_gasto(session)
        from modules.gasto.models import CategoriaGasto
        count = session.query(CategoriaGasto).count()
        assert count == 11, f"Esperaba 11 categorías de gasto, hay {count}"


def test_seed_idempotency():
    """Task 5.5: Ejecutar seeds dos veces no duplica registros."""
    from database.seeds.roles import seed_roles
    from database.seeds.categorias_producto import seed_categorias_producto

    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as session:
        seed_roles(session)
        seed_roles(session)
        from modules.auth.models import Rol
        count = session.query(Rol).count()
        assert count == 5, f"Idempotencia falló: {count} roles tras doble ejecución"

    with SessionLocal() as session:
        from modules.empresa.models import Empresa
        empresa = Empresa(nombre_comercial="Test", activa=True)
        session.add(empresa)
        session.commit()
        session.refresh(empresa)

        seed_categorias_producto(session, empresa_id=empresa.id)
        seed_categorias_producto(session, empresa_id=empresa.id)
        from modules.producto.models import CategoriaProducto
        count = session.query(CategoriaProducto).filter(
            CategoriaProducto.empresa_id == empresa.id
        ).count()
        assert count == 5, f"Idempotencia falló: {count} categorías tras doble ejecución"


def test_seed_admin_user():
    """Task 6.7: Seed data crea superadmin por defecto y es idempotente."""
    from database.seeds.roles import seed_roles
    from database.seeds.admin_user import seed_admin_user
    from modules.auth.models import Usuario, Rol

    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    with SessionLocal() as session:
        seed_roles(session)
        seed_admin_user(session)

        superadmin = session.query(Usuario).filter(Usuario.email == "superadmin@basile.local").first()
        assert superadmin is not None, "Superadmin no creado"
        assert superadmin.activo is True
        assert superadmin.rol is not None
        assert superadmin.rol.nombre == "superadmin"
        assert superadmin.empresa_id is None


def test_seed_admin_idempotency():
    """Task 6.7: Ejecutar seed admin dos veces no duplica."""
    from database.seeds.roles import seed_roles
    from database.seeds.admin_user import seed_admin_user
    from modules.auth.models import Usuario

    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    with SessionLocal() as session:
        seed_roles(session)
        seed_admin_user(session)
        seed_admin_user(session)

        count = session.query(Usuario).count()
        assert count == 1, f"Esperaba 1 superadmin, hay {count}"
