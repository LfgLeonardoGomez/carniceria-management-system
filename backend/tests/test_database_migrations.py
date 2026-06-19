import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def test_migration_file_exists():
    """Task 4.6: Migración inicial generada y referencia tablas."""
    migrations_dir = PROJECT_ROOT / "backend" / "src" / "database" / "migrations" / "versions"
    assert migrations_dir.exists(), "Falta directorio de migraciones"
    migration_files = list(migrations_dir.glob("*.py"))
    assert len(migration_files) > 0, "No hay archivos de migración"

    content = migration_files[0].read_text()
    assert "empresa" in content, "Migración no referencia tabla empresa"
    assert "rol" in content, "Migración no referencia tabla rol"
    assert "usuario" in content, "Migración no referencia tabla usuario"


def test_migration_syntax():
    """Triangulate Task 4.6: migración compila como Python válido."""
    migrations_dir = PROJECT_ROOT / "backend" / "src" / "database" / "migrations" / "versions"
    migration_files = list(migrations_dir.glob("*.py"))
    assert len(migration_files) > 0
    for f in migration_files:
        compile(f.read_text(), str(f), "exec")
