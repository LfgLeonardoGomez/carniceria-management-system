import pytest
from fastapi import Request
from unittest.mock import MagicMock

from src.modules.auth.dependencies import require_superadmin, require_auth
from src.common.exceptions import ForbiddenException
from src.modules.auth.models import Usuario, Rol


class TestRequireSuperadmin:
    async def test_superadmin_pasa(self):
        mock_user = MagicMock(spec=Usuario)
        mock_user.rol = MagicMock(spec=Rol)
        mock_user.rol.nombre = "superadmin"
        request = MagicMock(spec=Request)
        request.state.current_user = mock_user

        await require_superadmin(request)
        assert True

    async def test_admin_recibe_403(self):
        mock_user = MagicMock(spec=Usuario)
        mock_user.rol = MagicMock(spec=Rol)
        mock_user.rol.nombre = "admin"
        request = MagicMock(spec=Request)
        request.state.current_user = mock_user

        with pytest.raises(ForbiddenException, match="superadmin"):
            await require_superadmin(request)

    async def test_encargado_recibe_403(self):
        mock_user = MagicMock(spec=Usuario)
        mock_user.rol = MagicMock(spec=Rol)
        mock_user.rol.nombre = "encargado"
        request = MagicMock(spec=Request)
        request.state.current_user = mock_user

        with pytest.raises(ForbiddenException, match="superadmin"):
            await require_superadmin(request)

    async def test_cajero_recibe_403(self):
        mock_user = MagicMock(spec=Usuario)
        mock_user.rol = MagicMock(spec=Rol)
        mock_user.rol.nombre = "cajero"
        request = MagicMock(spec=Request)
        request.state.current_user = mock_user

        with pytest.raises(ForbiddenException, match="superadmin"):
            await require_superadmin(request)

    async def test_vendedor_recibe_403(self):
        mock_user = MagicMock(spec=Usuario)
        mock_user.rol = MagicMock(spec=Rol)
        mock_user.rol.nombre = "vendedor"
        request = MagicMock(spec=Request)
        request.state.current_user = mock_user

        with pytest.raises(ForbiddenException, match="superadmin"):
            await require_superadmin(request)

    async def test_sin_rol_recibe_403(self):
        mock_user = MagicMock(spec=Usuario)
        mock_user.rol = None
        request = MagicMock(spec=Request)
        request.state.current_user = mock_user

        with pytest.raises(ForbiddenException, match="superadmin"):
            await require_superadmin(request)


class TestRequireAuthInjectsEmpresaId:
    async def test_empresa_id_inyectado(self, client, db_session):
        from src.modules.auth.models import Empresa, Usuario
        from src.core.security import hash_password, create_access_token

        empresa = Empresa(nombre_comercial="Inject Test", activa=True)
        db_session.add(empresa)
        await db_session.commit()
        await db_session.refresh(empresa)

        rol = MagicMock()
        rol.nombre = "admin"
        from src.modules.auth.models import Rol as RolModel
        rol_db = RolModel(nombre="admin", empresa_id=empresa.id)
        db_session.add(rol_db)
        await db_session.commit()
        await db_session.refresh(rol_db)

        usuario = Usuario(
            email="inject@basile.app",
            contrasena_hash=hash_password("Password123"),
            nombre="Test",
            apellido="User",
            rol_id=rol_db.id,
            activo=True,
            empresa_id=empresa.id,
        )
        db_session.add(usuario)
        await db_session.commit()
        await db_session.refresh(usuario)

        token = create_access_token({"sub": str(usuario.id), "empresa_id": str(empresa.id), "rol": "admin"})
        response = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["empresa_id"] == str(empresa.id)
