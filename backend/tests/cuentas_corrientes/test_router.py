"""Router tests for cuenta_corriente (Tasks 5.1, 5.6 — RED→GREEN).

These are integration tests that require Docker+testcontainers (real PostgreSQL).
They will ERROR when Docker is not running.

TDD cycle:
  5.1 RED  — POST /cuentas-corrientes/{cliente_id}/pagos happy path returns movement + balance
  5.6 RED→GREEN — RBAC: role lacking cuenta-corriente:update → 403 on payment
"""
from __future__ import annotations

import uuid
from decimal import Decimal
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.models import Empresa, Rol, Usuario
from src.modules.cliente.models import Cliente
from src.core.security import hash_password, create_access_token


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _crear_empresa(db: AsyncSession, nombre: str = "Router Test") -> Empresa:
    e = Empresa(nombre_comercial=nombre, activa=True)
    db.add(e)
    await db.commit()
    await db.refresh(e)
    return e


async def _crear_rol(db: AsyncSession, nombre: str = "admin") -> Rol:
    r = Rol(nombre=nombre)
    db.add(r)
    await db.commit()
    await db.refresh(r)
    return r


async def _crear_usuario(
    db: AsyncSession,
    email: str,
    rol_id: uuid.UUID,
    empresa_id: uuid.UUID,
    rol_nombre: str = "admin",
) -> Usuario:
    u = Usuario(
        email=email,
        contrasena_hash=hash_password("Password123"),
        nombre="Test",
        apellido="User",
        rol_id=rol_id,
        activo=True,
        empresa_id=empresa_id,
    )
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


async def _crear_cliente(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    saldo: Decimal = Decimal("1000.00"),
    nombre: str = "Test Client",
) -> Cliente:
    c = Cliente(
        empresa_id=empresa_id,
        nombre=nombre,
        tipo_cliente="cuenta_corriente",
        limite_cuenta_corriente=Decimal("0.0000"),
        saldo_actual=saldo,
    )
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return c


def _auth_header(usuario: Usuario, rol_nombre: str = "admin") -> dict:
    """Mint a JWT directly — avoids HTTP login roundtrip and field-name coupling."""
    token = create_access_token({
        "sub": str(usuario.id),
        "empresa_id": str(usuario.empresa_id),
        "rol": rol_nombre,
    })
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Task 5.1 RED → 5.2 GREEN: POST /cuentas-corrientes/{id}/pagos happy path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestRegistrarPagoEndpoint:
    async def test_post_pago_happy_path(self, client: AsyncClient, db_session: AsyncSession):
        """POST /cuentas-corrientes/{id}/pagos with valid data returns 200 + new balance."""
        empresa = await _crear_empresa(db_session, "RT Empresa A")
        rol_admin = await _crear_rol(db_session, "admin")
        usuario = await _crear_usuario(db_session, "admin_rt@test.com", rol_admin.id, empresa.id)
        cliente = await _crear_cliente(db_session, empresa.id, saldo=Decimal("1000.00"))

        resp = await client.post(
            f"/cuentas-corrientes/{cliente.id}/pagos",
            json={"importe": "300.00"},
            headers=_auth_header(usuario, "admin"),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["movimiento"]["tipo"] == "pago"
        assert body["saldo_actual"] == "700.00"

    async def test_post_pago_overpayment_returns_409(self, client: AsyncClient, db_session: AsyncSession):
        """POST /cuentas-corrientes/{id}/pagos with overpayment returns 409."""
        empresa = await _crear_empresa(db_session, "RT Empresa B")
        rol_admin = await _crear_rol(db_session, "admin")
        usuario = await _crear_usuario(db_session, "admin_rt2@test.com", rol_admin.id, empresa.id)
        cliente = await _crear_cliente(db_session, empresa.id, saldo=Decimal("500.00"))

        resp = await client.post(
            f"/cuentas-corrientes/{cliente.id}/pagos",
            json={"importe": "800.00"},
            headers=_auth_header(usuario, "admin"),
        )
        assert resp.status_code == 409

    async def test_post_pago_zero_importe_returns_422(self, client: AsyncClient, db_session: AsyncSession):
        """POST /cuentas-corrientes/{id}/pagos with importe=0 returns 422."""
        empresa = await _crear_empresa(db_session, "RT Empresa C")
        rol_admin = await _crear_rol(db_session, "admin")
        usuario = await _crear_usuario(db_session, "admin_rt3@test.com", rol_admin.id, empresa.id)
        cliente = await _crear_cliente(db_session, empresa.id, saldo=Decimal("500.00"))

        resp = await client.post(
            f"/cuentas-corrientes/{cliente.id}/pagos",
            json={"importe": "0"},
            headers=_auth_header(usuario, "admin"),
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Task 5.6 RED→GREEN: RBAC tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestRbacEndpoint:
    async def test_vendedor_cannot_register_payment(self, client: AsyncClient, db_session: AsyncSession):
        """Role 'vendedor' lacks cuenta-corriente:update → 403."""
        empresa = await _crear_empresa(db_session, "RT RBAC A")
        rol_vendedor = await _crear_rol(db_session, "vendedor")
        usuario = await _crear_usuario(db_session, "vendedor_rbac@test.com", rol_vendedor.id, empresa.id)
        cliente = await _crear_cliente(db_session, empresa.id, saldo=Decimal("500.00"))

        resp = await client.post(
            f"/cuentas-corrientes/{cliente.id}/pagos",
            json={"importe": "100.00"},
            headers=_auth_header(usuario, "vendedor"),
        )
        assert resp.status_code == 403

    async def test_cajero_can_register_payment(self, client: AsyncClient, db_session: AsyncSession):
        """Role 'cajero' has cuenta-corriente:update (PO Decision) → 200."""
        empresa = await _crear_empresa(db_session, "RT RBAC B")
        rol_cajero = await _crear_rol(db_session, "cajero")
        usuario = await _crear_usuario(db_session, "cajero_rbac@test.com", rol_cajero.id, empresa.id)
        cliente = await _crear_cliente(db_session, empresa.id, saldo=Decimal("500.00"))

        resp = await client.post(
            f"/cuentas-corrientes/{cliente.id}/pagos",
            json={"importe": "100.00"},
            headers=_auth_header(usuario, "cajero"),
        )
        assert resp.status_code == 200

    async def test_vendedor_cannot_view_history(self, client: AsyncClient, db_session: AsyncSession):
        """Role 'vendedor' lacks cuenta-corriente:read → 403 on GET history."""
        empresa = await _crear_empresa(db_session, "RT RBAC C")
        rol_vendedor = await _crear_rol(db_session, "vendedor")
        usuario = await _crear_usuario(db_session, "vendedor_hist@test.com", rol_vendedor.id, empresa.id)
        cliente = await _crear_cliente(db_session, empresa.id, saldo=Decimal("0.00"))

        resp = await client.get(
            f"/cuentas-corrientes/{cliente.id}",
            headers=_auth_header(usuario, "vendedor"),
        )
        assert resp.status_code == 403
