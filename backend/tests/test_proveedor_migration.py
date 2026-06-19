import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def test_proveedor_migration_exists():
    """Verify proveedor migration exists and references correct table."""
    migrations_dir = PROJECT_ROOT / "backend" / "src" / "database" / "migrations" / "versions"
    migration_files = list(migrations_dir.glob("*.py"))
    
    proveedor_migration = None
    for f in migration_files:
        if "proveedor" in f.name:
            proveedor_migration = f
            break
    
    assert proveedor_migration is not None, "No proveedor migration found"
    
    content = proveedor_migration.read_text()
    assert "proveedor" in content
    assert "empresa_id" in content
    assert "cuit" in content
    assert "activo" in content
    assert "ix_proveedor_empresa_id_nombre" in content
    assert "ix_proveedor_empresa_id_cuit_unique" in content
    assert "ENABLE ROW LEVEL SECURITY" in content
    assert "proveedor_empresa_isolation" in content


def test_proveedor_migration_compiles():
    """Verify migration is valid Python."""
    migrations_dir = PROJECT_ROOT / "backend" / "src" / "database" / "migrations" / "versions"
    for f in migrations_dir.glob("*proveedor*.py"):
        compile(f.read_text(), str(f), "exec")
