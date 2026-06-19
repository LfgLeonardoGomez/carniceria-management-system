import uuid
from datetime import datetime
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.modules.auth.models import Usuario, Rol, Empresa
from src.modules.empresa.models import Empresa as EmpresaModel
from src.core.security import hash_password, create_access_token


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _crear_empresa(db_session: AsyncSession, nombre: str = "Carnicería Test", activa: bool = True, **kwargs) -> Empresa:
    empresa = Empresa(nombre_comercial=nombre, activa=activa, **kwargs)
    db_session.add(empresa)
    await db_session.commit()
    await db_session.refresh(empresa)
    return empresa


async def _crear_rol(db_session: AsyncSession, nombre: str = "Administrador", empresa_id=None) -> Rol:
    rol = Rol(nombre=nombre, empresa_id=empresa_id)
    db_session.add(rol)
    await db_session.commit()
    await db_session.refresh(rol)
    return rol


async def _crear_usuario(
    db_session: AsyncSession,
    email: str = "test@basile.app",
    password: str = "Password123",
    activo: bool = True,
    empresa_id=None,
    rol_id=None,
) -> Usuario:
    if rol_id is None:
        rol = await _crear_rol(db_session, empresa_id=empresa_id)
        rol_id = rol.id
    usuario = Usuario(
        email=email,
        contrasena_hash=hash_password(password),
        nombre="Test",
        apellido="User",
        rol_id=rol_id,
        activo=activo,
        empresa_id=empresa_id,
    )
    db_session.add(usuario)
    await db_session.commit()
    await db_session.refresh(usuario)
    return usuario


def _auth_header(usuario: Usuario, rol_nombre: str = "Administrador", empresa_id=None):
    token = create_access_token({
        "sub": str(usuario.id),
        "empresa_id": str(empresa_id or usuario.empresa_id),
        "rol": rol_nombre,
    })
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# TASK-2.1: GET /empresas/me
# ---------------------------------------------------------------------------
class TestGetEmpresaMe:
    async def test_get_datos_propia_empresa(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session, nombre="Mi Carnicería")
        usuario = await _crear_usuario(db_session, email="admin@basile.app", empresa_id=empresa.id)

        response = await client.get("/empresas/me", headers=_auth_header(usuario, empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        assert data["nombre_comercial"] == "Mi Carnicería"
        assert data["id"] == str(empresa.id)
        assert data["activa"] is True

    async def test_get_nested_json_serializado(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session, nombre="Con Config")
        empresa.datos_fiscales = {"condicion_iva": "Responsable Inscripto", "punto_venta": 1}
        empresa.configuracion_general = {"timezone": "America/Argentina/Buenos_Aires"}
        await db_session.commit()

        usuario = await _crear_usuario(db_session, email="config@basile.app", empresa_id=empresa.id)
        response = await client.get("/empresas/me", headers=_auth_header(usuario, empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        assert data["datos_fiscales"]["condicion_iva"] == "Responsable Inscripto"
        assert data["configuracion_general"]["timezone"] == "America/Argentina/Buenos_Aires"

    async def test_get_sin_token(self, client: AsyncClient):
        response = await client.get("/empresas/me")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# TASK-2.2: PUT /empresas/me
# ---------------------------------------------------------------------------
class TestPutEmpresaMe:
    async def test_update_nombre_comercial_y_cuit(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session, nombre="Viejo Nombre")
        rol = await _crear_rol(db_session, nombre="Administrador", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="admin@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        response = await client.put("/empresas/me", headers=_auth_header(usuario, empresa_id=empresa.id), json={
            "nombre_comercial": "Nuevo Nombre",
            "cuit": "30616874582",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["nombre_comercial"] == "Nuevo Nombre"
        assert data["cuit"] == "30616874582"

    async def test_update_parcial_no_borra_otros_campos(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session, nombre="Empresa", cuit="30616874582", domicilio="Av Siempre Viva 123")
        rol = await _crear_rol(db_session, nombre="Administrador", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="admin2@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        response = await client.put("/empresas/me", headers=_auth_header(usuario, empresa_id=empresa.id), json={
            "telefono": "123456789",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["telefono"] == "123456789"
        assert data["cuit"] == "30616874582"
        assert data["domicilio"] == "Av Siempre Viva 123"

    async def test_cuit_invalido(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="Administrador", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="badcuit@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        response = await client.put("/empresas/me", headers=_auth_header(usuario, empresa_id=empresa.id), json={
            "cuit": "123",
        })
        assert response.status_code == 422

    async def test_email_invalido(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="Administrador", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="bademail@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        response = await client.put("/empresas/me", headers=_auth_header(usuario, empresa_id=empresa.id), json={
            "email": "no-es-email",
        })
        assert response.status_code == 422

    async def test_campo_extra_en_json_anidado_rechazado(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="Administrador", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="extra@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        response = await client.put("/empresas/me", headers=_auth_header(usuario, empresa_id=empresa.id), json={
            "datos_fiscales": {"condicion_iva": "Monotributo", "extra": "campo"},
        })
        assert response.status_code == 422

    async def test_no_admin_recibe_403(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="Cajero", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="cajero@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        response = await client.put("/empresas/me", headers=_auth_header(usuario, rol_nombre="Cajero", empresa_id=empresa.id), json={
            "nombre_comercial": "Intento",
        })
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# TASK-2.3: PATCH /empresas/me/desactivar
# ---------------------------------------------------------------------------
class TestDesactivarEmpresa:
    async def test_desactivar_empresa(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session, nombre="A Desactivar")
        rol = await _crear_rol(db_session, nombre="Administrador", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="admin@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        response = await client.patch("/empresas/me/desactivar", headers=_auth_header(usuario, empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        assert data["activa"] is False

        # Verificar en DB que sigue existiendo
        await db_session.refresh(empresa)
        assert empresa.activa is False

    async def test_desactivar_no_admin(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="Vendedor", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="vendedor@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        response = await client.patch("/empresas/me/desactivar", headers=_auth_header(usuario, rol_nombre="Vendedor", empresa_id=empresa.id))
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# TASK-2.3b: PATCH /empresas/me/reactivar
# ---------------------------------------------------------------------------
class TestReactivarEmpresa:
    async def test_reactivar_empresa_desactivada(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session, nombre="A Reactivar", activa=False)
        rol = await _crear_rol(db_session, nombre="Administrador", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="admin@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        response = await client.patch("/empresas/me/reactivar", headers=_auth_header(usuario, empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        assert data["activa"] is True

    async def test_reactivar_idempotente(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session, nombre="Ya Activa", activa=True)
        rol = await _crear_rol(db_session, nombre="Administrador", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="admin@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        response = await client.patch("/empresas/me/reactivar", headers=_auth_header(usuario, empresa_id=empresa.id))
        assert response.status_code == 200
        data = response.json()
        assert data["activa"] is True

    async def test_reactivar_no_admin(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session, activa=False)
        rol = await _crear_rol(db_session, nombre="Encargado", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="encargado@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        response = await client.patch("/empresas/me/reactivar", headers=_auth_header(usuario, rol_nombre="Encargado", empresa_id=empresa.id))
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# TASK-2.4: POST /empresas/me/logo
# ---------------------------------------------------------------------------
class TestUploadLogo:
    async def test_subir_jpg_valido(self, client: AsyncClient, db_session: AsyncSession, tmp_path: Path):
        from src.config.settings import settings
        original = settings.upload_path
        settings.upload_path = str(tmp_path / "uploads")
        try:
            empresa = await _crear_empresa(db_session, nombre="Con Logo")
            rol = await _crear_rol(db_session, nombre="Administrador", empresa_id=empresa.id)
            usuario = await _crear_usuario(db_session, email="admin@basile.app", empresa_id=empresa.id, rol_id=rol.id)

            content = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"x" * 100
            response = await client.post(
                "/empresas/me/logo",
                headers=_auth_header(usuario, empresa_id=empresa.id),
                files={"file": ("logo.jpg", content, "image/jpeg")},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["logo_url"] == f"/uploads/empresas/{empresa.id}/logo.jpg"
            assert (tmp_path / "uploads" / "empresas" / str(empresa.id) / "logo.jpg").exists()
        finally:
            settings.upload_path = original

    async def test_subir_png_valido(self, client: AsyncClient, db_session: AsyncSession, tmp_path: Path):
        from src.config.settings import settings
        original = settings.upload_path
        settings.upload_path = str(tmp_path / "uploads")
        try:
            empresa = await _crear_empresa(db_session, nombre="Con Logo PNG")
            rol = await _crear_rol(db_session, nombre="Administrador", empresa_id=empresa.id)
            usuario = await _crear_usuario(db_session, email="admin@basile.app", empresa_id=empresa.id, rol_id=rol.id)

            content = (
                b"\x89PNG\r\n\x1a\n"
                b"\x00\x00\x00\x0dIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
                b"\x00\x00\x00\x00IEND\xaeB`\x82"
            )
            response = await client.post(
                "/empresas/me/logo",
                headers=_auth_header(usuario, empresa_id=empresa.id),
                files={"file": ("logo.png", content, "image/png")},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["logo_url"] == f"/uploads/empresas/{empresa.id}/logo.png"
        finally:
            settings.upload_path = original

    async def test_subir_svg_rechazado(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="Administrador", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="admin@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        content = b"<svg xmlns='http://www.w3.org/2000/svg'></svg>"
        response = await client.post(
            "/empresas/me/logo",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            files={"file": ("logo.svg", content, "image/svg+xml")},
        )
        assert response.status_code == 400

    async def test_subir_exe_renombrado_rechazado(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="Administrador", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="admin@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        content = b"MZ\x90\x00" + b"x" * 100
        response = await client.post(
            "/empresas/me/logo",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            files={"file": ("logo.jpg", content, "image/jpeg")},
        )
        assert response.status_code == 400

    async def test_subir_tamano_excedido(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="Administrador", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="admin@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        content = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"x" * (2 * 1024 * 1024 + 10)
        response = await client.post(
            "/empresas/me/logo",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            files={"file": ("logo.jpg", content, "image/jpeg")},
        )
        assert response.status_code == 413

    async def test_subir_bmp_rechazado(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="Administrador", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="admin@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        content = b"BM" + b"\x00" * 100
        response = await client.post(
            "/empresas/me/logo",
            headers=_auth_header(usuario, empresa_id=empresa.id),
            files={"file": ("logo.bmp", content, "image/bmp")},
        )
        assert response.status_code == 400

    async def test_upload_no_admin(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="Cajero", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, email="cajero@basile.app", empresa_id=empresa.id, rol_id=rol.id)

        content = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"x" * 100
        response = await client.post(
            "/empresas/me/logo",
            headers=_auth_header(usuario, rol_nombre="Cajero", empresa_id=empresa.id),
            files={"file": ("logo.jpg", content, "image/jpeg")},
        )
        assert response.status_code == 403
