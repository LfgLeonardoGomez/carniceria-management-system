import uuid
from decimal import Decimal
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.modules.notificacion.models import Notificacion
from src.modules.notificacion import service as notificacion_service
from src.modules.auth.models import Usuario, Rol, Empresa
from src.core.security import hash_password, create_access_token


async def _crear_empresa(db_session: AsyncSession, nombre: str = "Carnicería Test") -> Empresa:
    empresa = Empresa(nombre_comercial=nombre, activa=True)
    db_session.add(empresa)
    await db_session.commit()
    await db_session.refresh(empresa)
    return empresa


async def _crear_rol(db_session: AsyncSession, nombre: str = "admin", empresa_id=None) -> Rol:
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


def _auth_header(usuario: Usuario, rol_nombre: str = "admin", empresa_id=None):
    token = create_access_token({
        "sub": str(usuario.id),
        "empresa_id": str(empresa_id or usuario.empresa_id),
        "rol": rol_nombre,
    })
    return {"Authorization": f"Bearer {token}"}


class TestNotificacionIntegration:
    @pytest.mark.asyncio
    async def test_list_notificaciones_filtrado(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="admin", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, empresa_id=empresa.id, rol_id=rol.id)
        headers = _auth_header(usuario, rol_nombre="admin", empresa_id=empresa.id)

        await notificacion_service._crear_notificacion(
            db_session, empresa.id, "stock_bajo", "Stock bajo", "producto", uuid.uuid4()
        )
        await notificacion_service._crear_notificacion(
            db_session, empresa.id, "diferencia_caja", "Diferencia", "caja", uuid.uuid4()
        )

        response = await client.get("/notificacion?leida=false", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    @pytest.mark.asyncio
    async def test_marcar_notificacion_leida(self, client: AsyncClient, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="admin", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, empresa_id=empresa.id, rol_id=rol.id)
        headers = _auth_header(usuario, rol_nombre="admin", empresa_id=empresa.id)

        notif = await notificacion_service._crear_notificacion(
            db_session, empresa.id, "stock_bajo", "Stock bajo", "producto", uuid.uuid4()
        )

        response = await client.patch(f"/notificacion/{notif.id}/leida", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["leida"] is True
        assert data["fecha_lectura"] is not None

    @pytest.mark.asyncio
    async def test_marcar_notificacion_otra_empresa_404(self, client: AsyncClient, db_session: AsyncSession):
        empresa_a = await _crear_empresa(db_session, "Empresa A")
        empresa_b = await _crear_empresa(db_session, "Empresa B")
        rol = await _crear_rol(db_session, nombre="admin", empresa_id=empresa_a.id)
        usuario_a = await _crear_usuario(db_session, empresa_id=empresa_a.id, rol_id=rol.id)
        headers_a = _auth_header(usuario_a, rol_nombre="admin", empresa_id=empresa_a.id)

        notif_b = await notificacion_service._crear_notificacion(
            db_session, empresa_b.id, "stock_bajo", "Stock bajo", "producto", uuid.uuid4()
        )

        response = await client.patch(f"/notificacion/{notif_b.id}/leida", headers=headers_a)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_notificacion_tenant_isolation(self, client: AsyncClient, db_session: AsyncSession):
        empresa_a = await _crear_empresa(db_session, "Empresa A")
        empresa_b = await _crear_empresa(db_session, "Empresa B")
        rol = await _crear_rol(db_session, nombre="admin", empresa_id=empresa_a.id)
        usuario_a = await _crear_usuario(db_session, empresa_id=empresa_a.id, rol_id=rol.id)
        headers_a = _auth_header(usuario_a, rol_nombre="admin", empresa_id=empresa_a.id)

        await notificacion_service._crear_notificacion(
            db_session, empresa_a.id, "stock_bajo", "Stock bajo A", "producto", uuid.uuid4()
        )
        await notificacion_service._crear_notificacion(
            db_session, empresa_b.id, "stock_bajo", "Stock bajo B", "producto", uuid.uuid4()
        )

        response = await client.get("/notificacion", headers=headers_a)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["mensaje"] == "Stock bajo A"

    @pytest.mark.asyncio
    async def test_generar_stock_bajo(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        notif = await notificacion_service.generar_stock_bajo(
            db_session, empresa.id, uuid.uuid4(), "Carne", Decimal("2.0"), Decimal("5.0")
        )
        assert notif is not None
        assert notif.tipo == "stock_bajo"
        assert notif.leida is False

    @pytest.mark.asyncio
    async def test_generar_gasto_elevado_sin_umbral(self, db_session: AsyncSession):
        empresa = await _crear_empresa(db_session)
        notif = await notificacion_service.generar_gasto_elevado(
            db_session, empresa.id, uuid.uuid4(), Decimal("1000.00"), Decimal("500.00")
        )
        assert notif is not None
        assert notif.tipo == "gasto_elevado"

    @pytest.mark.asyncio
    async def test_generar_gasto_elevado_por_debajo_umbral(self, db_session: AsyncSession):
        notif = await notificacion_service.generar_gasto_elevado(
            db_session, uuid.uuid4(), uuid.uuid4(), Decimal("100.00"), Decimal("500.00")
        )
        assert notif is None
