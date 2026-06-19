import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_ROOT = PROJECT_ROOT / "backend"


def test_alembic_migration_sql_offline():
    """Task 4.7: Verificar migración generando SQL offline (sin DB activa)."""
    env = os.environ.copy()
    env["DATABASE_URL"] = "postgresql+psycopg://dummy:dummy@localhost/dummy"
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head", "--sql"],
        cwd=str(BACKEND_ROOT),
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"alembic offline SQL generation failed: {result.stderr}"
    sql = result.stdout
    assert "CREATE TABLE empresa" in sql, "SQL no contiene CREATE TABLE empresa"
    assert "CREATE TABLE rol" in sql, "SQL no contiene CREATE TABLE rol"
    assert "CREATE TABLE usuario" in sql, "SQL no contiene CREATE TABLE usuario"
    assert "CREATE UNIQUE INDEX ix_usuario_email" in sql, "SQL no contiene índice usuario.email"
    assert "CREATE INDEX ix_usuario_empresa_id" in sql, "SQL no contiene índice usuario.empresa_id"
