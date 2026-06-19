import pytest
from fastapi import Request
from unittest.mock import MagicMock

from src.common.rbac import PERMISSION_MATRIX, has_permission, require_role
from src.common.exceptions import ForbiddenException
from src.modules.auth.models import Usuario, Rol


class TestPermissionMatrix:
    def test_matrix_has_exactly_five_roles(self):
        assert set(PERMISSION_MATRIX.keys()) == {"superadmin", "admin", "encargado", "cajero", "vendedor"}

    def test_superadmin_has_empresas_and_usuarios(self):
        perms = PERMISSION_MATRIX["superadmin"]
        assert "empresas:create" in perms
        assert "empresas:read" in perms
        assert "usuarios:create" in perms
        assert "soporte:impersonate" in perms

    def test_admin_no_tiene_wildcard(self):
        perms = PERMISSION_MATRIX["admin"]
        assert "*" not in perms
        assert "usuarios:create" in perms
        assert "empresas:admin" in perms

    def test_encargado_has_stock_and_related(self):
        perms = PERMISSION_MATRIX["encargado"]
        assert "stock:read" in perms
        assert "stock:update" in perms
        assert "ventas:create" in perms
        assert "usuarios:create" not in perms
        assert "empresas:create" not in perms

    def test_cajero_has_ventas_y_caja(self):
        perms = PERMISSION_MATRIX["cajero"]
        assert "ventas:create" in perms
        assert "caja:admin" in perms
        assert "stock:read" not in perms

    def test_vendedor_has_ventas_only(self):
        perms = PERMISSION_MATRIX["vendedor"]
        assert "ventas:create" in perms
        assert "ventas:read" in perms
        assert "caja:admin" not in perms
        assert "stock:read" not in perms


class TestHasPermission:
    def test_superadmin_tiene_permiso_explicito(self):
        assert has_permission("superadmin", "usuarios:create") is True
        assert has_permission("superadmin", "empresas:delete") is True

    def test_admin_tiene_permisos_explicitos(self):
        assert has_permission("admin", "usuarios:create") is True
        assert has_permission("admin", "empresas:admin") is True

    def test_admin_no_tiene_empresas_delete(self):
        assert has_permission("admin", "empresas:delete") is False

    def test_encargado_puede_stock(self):
        assert has_permission("encargado", "stock:read") is True

    def test_encargado_no_puede_usuarios(self):
        assert has_permission("encargado", "usuarios:create") is False

    def test_cajero_no_puede_stock(self):
        assert has_permission("cajero", "stock:read") is False

    def test_vendedor_no_puede_caja(self):
        assert has_permission("vendedor", "caja:admin") is False

    def test_rol_inexistente_devuelve_false(self):
        assert has_permission("RolInexistente", "usuarios:create") is False

    def test_permiso_vacio_devuelve_false(self):
        assert has_permission("vendedor", "") is False


class TestRequireRole:
    async def test_permitido_con_permiso_valido(self):
        request = MagicMock(spec=Request)
        usuario = MagicMock(spec=Usuario)
        usuario.rol = MagicMock(spec=Rol)
        usuario.rol.nombre = "superadmin"
        request.state.current_user = usuario

        dep = require_role("usuarios:create")
        await dep(request)  # Should not raise

    async def test_rechazado_sin_permiso(self):
        request = MagicMock(spec=Request)
        usuario = MagicMock(spec=Usuario)
        usuario.rol = MagicMock(spec=Rol)
        usuario.rol.nombre = "vendedor"
        request.state.current_user = usuario

        dep = require_role("usuarios:create")
        with pytest.raises(ForbiddenException) as exc_info:
            await dep(request)
        assert "usuarios:create" in str(exc_info.value.message)

    async def test_rechazado_sin_current_user(self):
        request = MagicMock(spec=Request)
        request.state.current_user = None

        dep = require_role("usuarios:create")
        with pytest.raises(ForbiddenException):
            await dep(request)

    async def test_rechazado_usuario_sin_rol(self):
        request = MagicMock(spec=Request)
        usuario = MagicMock(spec=Usuario)
        usuario.rol = None
        request.state.current_user = usuario

        dep = require_role("usuarios:create")
        with pytest.raises(ForbiddenException):
            await dep(request)

    async def test_encargado_puede_stock(self):
        request = MagicMock(spec=Request)
        usuario = MagicMock(spec=Usuario)
        usuario.rol = MagicMock(spec=Rol)
        usuario.rol.nombre = "encargado"
        request.state.current_user = usuario

        dep = require_role("stock:read")
        await dep(request)  # Should not raise
