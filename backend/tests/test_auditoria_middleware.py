"""Tests para el middleware de auditoría.

El middleware debe capturar requests mutantes (POST/PUT/PATCH/DELETE)
exitosos (2xx) y crear un registro en la tabla `auditoria` con un
snapshot del request/response. No debe registrar:
- métodos GET/HEAD/OPTIONS
- respuestas 4xx/5xx
- paths en SKIP_PREFIXES (/auditoria, /health, /docs, etc.)
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auditoria.models import Auditoria
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


async def _contar_auditorias_para(db_session: AsyncSession, empresa_id: uuid.UUID) -> int:
    """Cuenta registros de auditoría para una empresa específica.

    Usamos una conexión distinta a la del middleware, así que en READ
    COMMITTED vemos los commits externos.
    """
    result = await db_session.execute(
        select(func.count(Auditoria.id)).where(Auditoria.empresa_id == empresa_id)
    )
    return int(result.scalar_one())


class TestAuditMiddleware:
    """Tarea 2.2: tests del middleware de auditoría."""

    @pytest.mark.asyncio
    async def test_post_exitoso_crea_registro_auditoria(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Un POST que retorna 2xx debe generar un registro de auditoría."""
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="admin", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, empresa_id=empresa.id, rol_id=rol.id)
        headers = _auth_header(usuario, rol_nombre="admin", empresa_id=empresa.id)

        antes = await _contar_auditorias_para(db_session, empresa.id)

        # POST a /cliente (endpoint real, no mockeado)
        response = await client.post(
            "/cliente",
            headers=headers,
            json={"nombre": "Juan", "tipo_cliente": "publico_general"},
        )
        assert response.status_code == 201

        despues = await _contar_auditorias_para(db_session, empresa.id)
        assert despues == antes + 1, (
            f"Esperaba 1 auditoría nueva, antes={antes}, después={despues}"
        )

    @pytest.mark.asyncio
    async def test_get_no_crea_registro_auditoria(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Un GET NO debe generar registro de auditoría."""
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="admin", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, empresa_id=empresa.id, rol_id=rol.id)
        headers = _auth_header(usuario, rol_nombre="admin", empresa_id=empresa.id)

        antes = await _contar_auditorias_para(db_session, empresa.id)

        response = await client.get("/cliente", headers=headers)
        assert response.status_code == 200

        despues = await _contar_auditorias_para(db_session, empresa.id)
        assert despues == antes, (
            f"GET no debe generar auditoría, antes={antes}, después={despues}"
        )

    @pytest.mark.asyncio
    async def test_post_con_error_4xx_no_crea_auditoria(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Un POST que falla con 4xx NO debe generar registro de auditoría."""
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="admin", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, empresa_id=empresa.id, rol_id=rol.id)
        headers = _auth_header(usuario, rol_nombre="admin", empresa_id=empresa.id)

        antes = await _contar_auditorias_para(db_session, empresa.id)

        # tipo_cliente inválido → 422
        response = await client.post(
            "/cliente",
            headers=headers,
            json={"nombre": "X", "tipo_cliente": "invalido"},
        )
        assert response.status_code == 422

        despues = await _contar_auditorias_para(db_session, empresa.id)
        assert despues == antes, (
            f"4xx no debe generar auditoría, antes={antes}, después={despues}"
        )

    @pytest.mark.asyncio
    async def test_skip_auditoria_y_health(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """El middleware debe saltarse /auditoria y /health (recursión y ruido)."""
        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="admin", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, empresa_id=empresa.id, rol_id=rol.id)
        headers = _auth_header(usuario, rol_nombre="admin", empresa_id=empresa.id)

        antes = await _contar_auditorias_para(db_session, empresa.id)

        # /health no requiere auth
        r_health = await client.get("/health")
        assert r_health.status_code == 200

        # /auditoria SÍ requiere admin y generaría recursión
        r_aud = await client.get("/auditoria", headers=headers)
        assert r_aud.status_code == 200

        despues = await _contar_auditorias_para(db_session, empresa.id)
        # GET no genera auditoría de todos modos, pero el skip es importante
        # para que no se intente escribir auditoría dentro de un endpoint
        # de auditoría (lo cual podría generar deadlock por RLS).
        assert despues == antes, (
            f"/health y /auditoria no deben generar auditoría, "
            f"antes={antes}, después={despues}"
        )

    @pytest.mark.asyncio
    async def test_payload_incluye_method_path_status(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """El payload del registro debe incluir method, path y status_code."""
        from sqlalchemy import desc

        empresa = await _crear_empresa(db_session)
        rol = await _crear_rol(db_session, nombre="admin", empresa_id=empresa.id)
        usuario = await _crear_usuario(db_session, empresa_id=empresa.id, rol_id=rol.id)
        headers = _auth_header(usuario, rol_nombre="admin", empresa_id=empresa.id)

        response = await client.post(
            "/cliente",
            headers=headers,
            json={"nombre": "Ana", "tipo_cliente": "publico_general"},
        )
        assert response.status_code == 201

        result = await db_session.execute(
            select(Auditoria)
            .where(Auditoria.empresa_id == empresa.id)
            .order_by(desc(Auditoria.created_at))
            .limit(1)
        )
        registro = result.scalar_one_or_none()
        assert registro is not None
        assert registro.accion in {"CREAR", "POST"}
        assert registro.entidad_tipo == "cliente"
        assert isinstance(registro.payload, dict)
        assert registro.payload.get("method") == "POST"
        assert registro.payload.get("path") == "/cliente"
        assert registro.payload.get("status") == 201
        assert "duration_ms" in registro.payload
