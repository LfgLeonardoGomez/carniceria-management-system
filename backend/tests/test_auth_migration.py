import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

from src.modules.auth.models import RefreshToken, TokenRecuperacion


class TestAuthMigration:
    """TASK-0.3: Verificar migración y metadata."""

    def test_migration_file_exists(self):
        path = PROJECT_ROOT / "backend" / "src" / "database" / "migrations" / "versions" / "000000000002_add_auth_tables.py"
        assert path.exists(), "Migración 000000000002_add_auth_tables.py no existe"

    def test_migration_contains_refresh_token(self):
        path = PROJECT_ROOT / "backend" / "src" / "database" / "migrations" / "versions" / "000000000002_add_auth_tables.py"
        content = path.read_text()
        assert "refresh_token" in content, "Migración no crea refresh_token"
        assert "token_recuperacion" in content, "Migración no crea token_recuperacion"
        assert "jti" in content, "Migración no define jti"
        assert "token_hash" in content, "Migración no define token_hash"

    def test_refresh_token_table_in_metadata(self):
        from sqlmodel import SQLModel
        assert "refresh_token" in SQLModel.metadata.tables, \
            "refresh_token debe estar en SQLModel.metadata"

    def test_token_recuperacion_table_in_metadata(self):
        from sqlmodel import SQLModel
        assert "token_recuperacion" in SQLModel.metadata.tables, \
            "token_recuperacion debe estar en SQLModel.metadata"

    def test_refresh_token_indexes(self):
        table = RefreshToken.__table__
        idx_names = {idx.name for idx in table.indexes}
        assert any("usuario_id" in n for n in idx_names), \
            "refresh_token debe tener índice en usuario_id"
        assert any("jti" in n for n in idx_names), \
            "refresh_token debe tener índice en jti"

    def test_token_recuperacion_indexes(self):
        table = TokenRecuperacion.__table__
        idx_names = {idx.name for idx in table.indexes}
        assert any("usuario_id" in n for n in idx_names), \
            "token_recuperacion debe tener índice en usuario_id"
