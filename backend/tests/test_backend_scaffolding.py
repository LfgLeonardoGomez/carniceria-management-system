import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_ROOT = PROJECT_ROOT / "backend"


def test_requirements_txt_exists():
    """Task 2.1: requirements.txt con dependencias de producción."""
    path = BACKEND_ROOT / "requirements.txt"
    assert path.exists(), "requirements.txt no existe"
    content = path.read_text()
    packages = [
        "fastapi>=0.100",
        "uvicorn[standard]",
        "sqlmodel>=0.0.14",
        "sqlalchemy>=2.0",
        "psycopg[binary,pool]>=3.1",
        "alembic",
        "pydantic[email]",
        "python-dotenv",
        "python-json-logger",
    ]
    for pkg in packages:
        assert pkg.split(">=")[0].split("[")[0] in content, f"Falta paquete {pkg} en requirements.txt"


def test_requirements_dev_txt_exists():
    """Task 2.2: requirements-dev.txt con dependencias de desarrollo."""
    path = BACKEND_ROOT / "requirements-dev.txt"
    assert path.exists(), "requirements-dev.txt no existe"
    content = path.read_text()
    dev_packages = [
        "pytest>=7.0",
        "pytest-asyncio",
        "httpx",
        "factory-boy",
        "testcontainers",
        "ruff",
        "mypy",
    ]
    for pkg in dev_packages:
        assert pkg.split(">=")[0] in content, f"Falta paquete {pkg} en requirements-dev.txt"


def test_backend_directory_structure():
    """Task 2.3: Estructura de directorios por dominio."""
    modules = BACKEND_ROOT / "src" / "modules"
    domains = [
        "auth", "empresa", "usuario", "producto", "cliente",
        "proveedor", "compra", "desposte", "stock", "venta",
        "caja", "gasto", "cuenta_corriente", "reporte", "auditoria", "notificacion",
    ]
    for domain in domains:
        assert (modules / domain).is_dir(), f"Falta directorio modules/{domain}"
        # Cada dominio debe tener al menos router.py y models.py
        assert (modules / domain / "router.py").exists(), f"Falta modules/{domain}/router.py"
        assert (modules / domain / "models.py").exists(), f"Falta modules/{domain}/models.py"

    common = BACKEND_ROOT / "src" / "common"
    assert common.is_dir(), "Falta src/common"
    assert (common / "__init__.py").exists(), "Falta src/common/__init__.py"

    config = BACKEND_ROOT / "src" / "config"
    assert config.is_dir(), "Falta src/config"
    assert (config / "__init__.py").exists(), "Falta src/config/__init__.py"

    database = BACKEND_ROOT / "src" / "database"
    assert database.is_dir(), "Falta src/database"
    assert (database / "__init__.py").exists(), "Falta src/database/__init__.py"


def test_main_py_exists_and_imports():
    """Task 2.4: main.py con FastAPI."""
    path = BACKEND_ROOT / "src" / "main.py"
    assert path.exists(), "src/main.py no existe"
    content = path.read_text()
    assert "FastAPI" in content, "main.py no importa FastAPI"
    assert "CORSMiddleware" in content, "main.py no importa CORSMiddleware"


def test_config_settings_exists():
    """Task 2.5: config/settings.py con Pydantic Settings."""
    path = BACKEND_ROOT / "src" / "config" / "settings.py"
    assert path.exists(), "src/config/settings.py no existe"
    content = path.read_text()
    assert "BaseSettings" in content or "SettingsConfigDict" in content, \
        "settings.py no usa Pydantic BaseSettings"
    assert "database_url" in content, "settings.py no define database_url (mapea a DATABASE_URL)"
    assert "JWT_SECRET" in content or "jwt_secret" in content, "settings.py no define jwt_secret"
    assert "CORS_ORIGIN" in content or "cors_origin" in content, "settings.py no define cors_origin"


def test_config_database_exists():
    """Task 2.6: config/database.py con engine async y get_db."""
    path = BACKEND_ROOT / "src" / "config" / "database.py"
    assert path.exists(), "src/config/database.py no existe"
    content = path.read_text()
    assert "create_async_engine" in content, "database.py no usa create_async_engine"
    assert "AsyncSession" in content, "database.py no usa AsyncSession"
    assert "get_db" in content, "database.py no define get_db"


def test_common_logging_exists():
    """Task 2.7: common/logging.py con formatter JSON."""
    path = BACKEND_ROOT / "src" / "common" / "logging.py"
    assert path.exists(), "src/common/logging.py no existe"
    content = path.read_text()
    assert "json" in content.lower() or "JsonFormatter" in content, \
        "logging.py no parece usar formato JSON"


def test_common_exceptions_exists():
    """Task 2.8: common/exceptions.py con excepciones base y handler."""
    path = BACKEND_ROOT / "src" / "common" / "exceptions.py"
    assert path.exists(), "src/common/exceptions.py no existe"
    content = path.read_text()
    assert "Exception" in content, "exceptions.py no define excepciones"
    assert "handler" in content.lower() or "add_exception_handler" in content.lower(), \
        "exceptions.py no prepara handler global"


def test_pyproject_toml_pytest_config():
    """Task 2.9: pyproject.toml con asyncio_mode = auto."""
    path = BACKEND_ROOT / "pyproject.toml"
    assert path.exists(), "pyproject.toml no existe"
    content = path.read_text()
    assert "asyncio_mode" in content, "pyproject.toml no define asyncio_mode"
    assert "auto" in content, "pyproject.toml no usa asyncio_mode = auto"
