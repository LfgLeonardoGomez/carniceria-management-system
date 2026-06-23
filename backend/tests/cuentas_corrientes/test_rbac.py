"""Unit tests for RBAC permissions (C-14 PO Decision — cajero gets cuenta-corriente:*).

These are pure unit tests — no Docker needed.

TDD:
  RED  — cajero lacks cuenta-corriente:* (before the PO decision was applied)
  GREEN — cajero has cuenta-corriente:* (after rbac.py update)
  TRIANGULATE — vendedor still lacks it; admin and encargado unchanged
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "src"))


class TestRbacCuentaCorriente:
    """Verify the RBAC matrix grants for cuenta-corriente permissions."""

    def test_admin_has_cuenta_corriente_update(self):
        from src.common.rbac import has_permission
        assert has_permission("admin", "cuenta-corriente:update") is True

    def test_admin_has_cuenta_corriente_read(self):
        from src.common.rbac import has_permission
        assert has_permission("admin", "cuenta-corriente:read") is True

    def test_encargado_has_cuenta_corriente_update(self):
        from src.common.rbac import has_permission
        assert has_permission("encargado", "cuenta-corriente:update") is True

    def test_encargado_has_cuenta_corriente_read(self):
        from src.common.rbac import has_permission
        assert has_permission("encargado", "cuenta-corriente:read") is True

    # PO Decision: cajero must have both permissions
    def test_cajero_has_cuenta_corriente_update(self):
        """Cajero MUST have cuenta-corriente:update (PO Decision C-14)."""
        from src.common.rbac import has_permission
        assert has_permission("cajero", "cuenta-corriente:update") is True

    def test_cajero_has_cuenta_corriente_read(self):
        """Cajero MUST have cuenta-corriente:read (PO Decision C-14)."""
        from src.common.rbac import has_permission
        assert has_permission("cajero", "cuenta-corriente:read") is True

    # Triangulate: vendedor still lacks both permissions
    def test_vendedor_lacks_cuenta_corriente_update(self):
        from src.common.rbac import has_permission
        assert has_permission("vendedor", "cuenta-corriente:update") is False

    def test_vendedor_lacks_cuenta_corriente_read(self):
        from src.common.rbac import has_permission
        assert has_permission("vendedor", "cuenta-corriente:read") is False

    def test_superadmin_lacks_cuenta_corriente_permissions(self):
        """superadmin has tenant-management perms, not domain-specific ones."""
        from src.common.rbac import has_permission
        # superadmin manages empresas/usuarios, not tenant domain ops
        assert has_permission("superadmin", "cuenta-corriente:update") is False
        assert has_permission("superadmin", "cuenta-corriente:read") is False
