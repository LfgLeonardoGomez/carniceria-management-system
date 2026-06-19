import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "src"))


def test_alembic_ini_exists():
    """Task 4.1: alembic.ini apunta a DATABASE_URL."""
    path = PROJECT_ROOT / "backend" / "alembic.ini"
    assert path.exists(), "backend/alembic.ini no existe"
    content = path.read_text()
    assert "sqlalchemy.url" in content, "alembic.ini no define sqlalchemy.url"


def test_alembic_env_py_exists():
    """Task 4.2: env.py con AsyncEngine y metadata de SQLModel."""
    path = PROJECT_ROOT / "backend" / "src" / "database" / "migrations" / "env.py"
    assert path.exists(), "src/database/migrations/env.py no existe"
    content = path.read_text()
    assert "AsyncEngine" in content or "asyncio" in content, "env.py no configura async"
    assert "SQLModel" in content or "MetaData" in content, "env.py no referencia metadata"


def test_empresa_model_exists():
    """Task 4.3: Modelo SQLModel Empresa."""
    from modules.empresa.models import Empresa

    cols = {c.name for c in Empresa.__table__.columns}
    required = {
        "id", "nombre_comercial", "razon_social", "cuit",
        "domicilio", "telefono", "email", "logo_url",
        "datos_fiscales", "configuracion_general", "parametros_operativos",
        "activa", "created_at", "updated_at",
    }
    assert required.issubset(cols), f"Empresa falta columnas: {required - cols}"


def test_rol_model_exists():
    """Task 4.4: Modelo SQLModel Rol."""
    from modules.auth.models import Rol

    cols = {c.name for c in Rol.__table__.columns}
    required = {"id", "nombre", "permisos", "created_at", "updated_at"}
    assert required.issubset(cols), f"Rol falta columnas: {required - cols}"
    assert "empresa_id" in cols, "Rol debería tener empresa_id (nullable para globales)"


def test_usuario_model_exists():
    """Task 4.5: Modelo SQLModel Usuario."""
    from modules.auth.models import Usuario

    cols = {c.name for c in Usuario.__table__.columns}
    required = {
        "id", "empresa_id", "email", "contrasena_hash",
        "nombre", "apellido", "rol_id", "activo",
        "ultimo_acceso", "created_at", "updated_at",
    }
    assert required.issubset(cols), f"Usuario falta columnas: {required - cols}"


def test_usuario_email_unique():
    """Task 4.8: email único en usuario."""
    from modules.auth.models import Usuario

    idxs = {idx.name for idx in Usuario.__table__.indexes}
    assert any("email" in i for i in idxs) or Usuario.__table__.columns["email"].unique, \
        "Usuario.email no tiene constraint de unicidad"


def test_usuario_empresa_id_index():
    """Task 4.8: índice en empresa_id en usuario."""
    from modules.auth.models import Usuario

    idxs = {idx.name for idx in Usuario.__table__.indexes}
    assert any("empresa_id" in i for i in idxs), \
        "Usuario no tiene índice en empresa_id"
