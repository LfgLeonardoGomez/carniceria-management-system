import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "src"))


def test_import_settings():
    """Triangulate Task 2.5: settings module es importable y tiene campos obligatorios."""
    from src.config.settings import Settings

    # Con variables mínimas
    s = Settings(
        database_url="postgresql+psycopg://u:p@localhost/db",
        jwt_secret="super-secret-jwt-key-for-testing-only-do-not-use-in-production",
        refresh_token_secret="super-secret-refresh-key-for-testing-only-do-not-use-in-production",
        email_host="smtp.example.com",
        email_user="user",
        email_pass="pass",
        email_from="from@example.com",
    )
    assert s.database_url == "postgresql+psycopg://u:p@localhost/db"
    assert s.cors_origin == "http://localhost:5173"
    assert s.port == 8000


def test_import_database():
    """Triangulate Task 2.6: database module es importable."""
    from src.config.database import engine, AsyncSessionLocal, get_db, Base

    assert engine is not None
    assert AsyncSessionLocal is not None


def test_import_logging():
    """Triangulate Task 2.7: logging setup es importable y no falla."""
    from src.common.logging import setup_logging

    setup_logging()


def test_import_exceptions():
    """Triangulate Task 2.8: excepciones son instanciables."""
    from src.common.exceptions import (
        BasileException,
        NotFoundException,
        UnauthorizedException,
        ForbiddenException,
        ConflictException,
    )

    exc = NotFoundException()
    assert exc.status_code == 404
    assert exc.message == "Recurso no encontrado"

    exc2 = ForbiddenException("Acceso denegado")
    assert exc2.status_code == 403


def test_import_main_app():
    """Triangulate Task 2.4: main app es importable sin errores."""
    from src.main import app

    assert app.title == "BASILE API"
    assert app.version == "0.1.0"
