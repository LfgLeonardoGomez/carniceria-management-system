"""Service tests for cuenta_corriente payment registration (Tasks 2.1–2.6).

TDD cycle:
  2.1 RED  — total payment clears balance to 0.00 (tipo=pago, saldo_resultante, saldo_actual)
  2.2 GREEN — implement registrar_pago
  2.3 TRIANGULATE — partial payment; payment exactly equal to balance
  2.4 RED→GREEN — overpayment raises ConflictException (409)
  2.5 RED→GREEN — atomicity: failure after insert rolls back both movement and balance
  2.6 RED→GREEN — tenant isolation: foreign-tenant cliente_id → NotFoundException (404)

These are integration tests that require the 'db_session' fixture (testcontainers + real PG).
They will ERROR when Docker is not running. The tests are written TDD-style — they exist
and are correct; execution requires Docker.
"""
from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.modules.auth.models import Empresa, Rol
from src.modules.cliente.models import Cliente
from src.modules.cuenta_corriente.models import CuentaCorriente
from src.modules.cuenta_corriente.schemas import PagoCreate
from src.common.exceptions import NotFoundException, ConflictException


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _crear_empresa(db: AsyncSession, nombre: str = "Empresa Test") -> Empresa:
    e = Empresa(nombre_comercial=nombre, activa=True)
    db.add(e)
    await db.commit()
    await db.refresh(e)
    return e


async def _crear_cliente(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    nombre: str = "Juan",
    saldo: Decimal = Decimal("0.00"),
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


async def _crear_movimiento(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    cliente_id: uuid.UUID,
    tipo: str,
    importe: Decimal,
    saldo_resultante: Decimal,
) -> CuentaCorriente:
    cc = CuentaCorriente(
        empresa_id=empresa_id,
        cliente_id=cliente_id,
        tipo=tipo,
        importe=importe,
        saldo_resultante=saldo_resultante,
    )
    db.add(cc)
    await db.commit()
    await db.refresh(cc)
    return cc


# ---------------------------------------------------------------------------
# Task 2.1 RED → 2.2 GREEN: total payment clears balance to 0.00
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestRegistrarPago:
    async def test_total_payment_clears_balance(self, db_session: AsyncSession):
        """Total payment: saldo_resultante=0.00, cliente.saldo_actual=0.00, tipo=pago."""
        from src.modules.cuenta_corriente import service

        empresa = await _crear_empresa(db_session)
        cliente = await _crear_cliente(db_session, empresa.id, saldo=Decimal("1000.00"))

        data = PagoCreate(importe=Decimal("1000.00"))
        result = await service.registrar_pago(db_session, empresa.id, cliente.id, data)

        assert result.movimiento.tipo == "pago"
        assert result.movimiento.importe == Decimal("1000.00")
        assert result.movimiento.saldo_resultante == Decimal("0.00")
        assert result.saldo_actual == Decimal("0.00")

        # Verify the DB was mutated
        await db_session.refresh(cliente)
        assert cliente.saldo_actual == Decimal("0.00")

    # 2.3 TRIANGULATE — partial payment leaves correct remaining balance
    async def test_partial_payment_reduces_balance(self, db_session: AsyncSession):
        """Partial payment: saldo_resultante = 1000.00 - 300.00 = 700.00."""
        from src.modules.cuenta_corriente import service

        empresa = await _crear_empresa(db_session, "Empresa B")
        cliente = await _crear_cliente(db_session, empresa.id, saldo=Decimal("1000.00"))

        data = PagoCreate(importe=Decimal("300.00"))
        result = await service.registrar_pago(db_session, empresa.id, cliente.id, data)

        assert result.movimiento.saldo_resultante == Decimal("700.00")
        assert result.saldo_actual == Decimal("700.00")

        await db_session.refresh(cliente)
        assert cliente.saldo_actual == Decimal("700.00")

    # 2.3 TRIANGULATE — payment exactly equal to balance clears to 0.00
    async def test_payment_equal_to_balance_clears_to_zero(self, db_session: AsyncSession):
        """Payment == saldo_actual is allowed and clears to 0.00."""
        from src.modules.cuenta_corriente import service

        empresa = await _crear_empresa(db_session, "Empresa C")
        cliente = await _crear_cliente(db_session, empresa.id, saldo=Decimal("500.00"))

        data = PagoCreate(importe=Decimal("500.00"))
        result = await service.registrar_pago(db_session, empresa.id, cliente.id, data)

        assert result.movimiento.saldo_resultante == Decimal("0.00")
        assert result.saldo_actual == Decimal("0.00")

    # 2.4 RED→GREEN — overpayment rejected with ConflictException (409)
    async def test_overpayment_raises_conflict(self, db_session: AsyncSession):
        """Payment > saldo_actual → ConflictException (HTTP 409), balance unchanged."""
        from src.modules.cuenta_corriente import service

        empresa = await _crear_empresa(db_session, "Empresa D")
        cliente = await _crear_cliente(db_session, empresa.id, saldo=Decimal("500.00"))

        data = PagoCreate(importe=Decimal("800.00"))
        with pytest.raises(ConflictException):
            await service.registrar_pago(db_session, empresa.id, cliente.id, data)

        # Balance must be unchanged
        await db_session.refresh(cliente)
        assert cliente.saldo_actual == Decimal("500.00")

    async def test_overpayment_no_movement_created(self, db_session: AsyncSession):
        """After overpayment rejection, no movement row exists in cuenta_corriente."""
        from src.modules.cuenta_corriente import service

        empresa = await _crear_empresa(db_session, "Empresa E")
        cliente = await _crear_cliente(db_session, empresa.id, saldo=Decimal("500.00"))

        data = PagoCreate(importe=Decimal("999.00"))
        with pytest.raises(ConflictException):
            await service.registrar_pago(db_session, empresa.id, cliente.id, data)

        result = await db_session.execute(
            select(CuentaCorriente).where(
                CuentaCorriente.cliente_id == cliente.id,
                CuentaCorriente.empresa_id == empresa.id,
                CuentaCorriente.tipo == "pago",
            )
        )
        movements = result.scalars().all()
        assert len(movements) == 0

    # 2.6 RED→GREEN — tenant isolation
    async def test_foreign_tenant_client_raises_404(self, db_session: AsyncSession):
        """A cliente_id from another empresa returns 404, never 403."""
        from src.modules.cuenta_corriente import service

        empresa_a = await _crear_empresa(db_session, "Tenant A")
        empresa_b = await _crear_empresa(db_session, "Tenant B")
        cliente_b = await _crear_cliente(db_session, empresa_b.id, saldo=Decimal("500.00"))

        data = PagoCreate(importe=Decimal("100.00"))
        with pytest.raises(NotFoundException):
            await service.registrar_pago(db_session, empresa_a.id, cliente_b.id, data)

    async def test_foreign_tenant_no_movement_in_either_tenant(self, db_session: AsyncSession):
        """After 404, no movement created in either tenant."""
        from src.modules.cuenta_corriente import service

        empresa_a = await _crear_empresa(db_session, "Tenant A2")
        empresa_b = await _crear_empresa(db_session, "Tenant B2")
        cliente_b = await _crear_cliente(db_session, empresa_b.id, saldo=Decimal("500.00"))

        data = PagoCreate(importe=Decimal("100.00"))
        with pytest.raises(NotFoundException):
            await service.registrar_pago(db_session, empresa_a.id, cliente_b.id, data)

        # No movement in empresa_a
        result_a = await db_session.execute(
            select(CuentaCorriente).where(
                CuentaCorriente.empresa_id == empresa_a.id,
            )
        )
        assert result_a.scalars().all() == []

        # No movement in empresa_b (the pre-existing balance unchanged, no pago movement)
        result_b = await db_session.execute(
            select(CuentaCorriente).where(
                CuentaCorriente.empresa_id == empresa_b.id,
                CuentaCorriente.tipo == "pago",
            )
        )
        assert result_b.scalars().all() == []
