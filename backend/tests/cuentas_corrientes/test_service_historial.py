"""Service tests for obtener_historial and obtener_estado_cuenta (Tasks 3.1–3.3, 4.1–4.4).

TDD cycle:
  3.1 RED  — obtener_historial returns deuda + pago movements ordered by fecha with envelope
  3.2 GREEN — implement obtener_historial
  3.3 TRIANGULATE — customer with no movements; tenant isolation on history
  4.1 RED  — obtener_estado_cuenta returns customer header + movements + balance
  4.3 GREEN — generar_xlsx/csv/pdf — see test_service_unit.py
  4.4 TRIANGULATE — csv/pdf non-empty, xlsx valid workbook (see test_service_unit.py)

These tests require testcontainers (Docker). They will ERROR when Docker is not running.
"""
from __future__ import annotations

import uuid
from decimal import Decimal
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.models import Empresa
from src.modules.cliente.models import Cliente
from src.modules.cuenta_corriente.models import CuentaCorriente
from src.modules.cuenta_corriente.schemas import PagoCreate
from src.common.exceptions import NotFoundException


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
# Task 3.1 RED → 3.2 GREEN: history returns movements with envelope
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestObtenerHistorial:
    async def test_returns_deuda_and_pago_movements(self, db_session: AsyncSession):
        """History includes both deuda and pago movements ordered by fecha."""
        from src.modules.cuenta_corriente import service

        empresa = await _crear_empresa(db_session, "Hist A")
        cliente = await _crear_cliente(db_session, empresa.id, saldo=Decimal("600.00"))

        await _crear_movimiento(db_session, empresa.id, cliente.id, "deuda", Decimal("1000.00"), Decimal("1000.00"))
        await _crear_movimiento(db_session, empresa.id, cliente.id, "pago", Decimal("400.00"), Decimal("600.00"))

        result = await service.obtener_historial(db_session, empresa.id, cliente.id)

        assert result.total == 2
        assert len(result.items) == 2
        assert result.items[0].tipo == "deuda"
        assert result.items[1].tipo == "pago"
        assert result.saldo_actual == Decimal("600.00")
        assert result.skip == 0
        assert result.limit == 50

    # 3.3 TRIANGULATE — customer with no movements
    async def test_customer_with_no_movements_returns_empty(self, db_session: AsyncSession):
        """Customer with no movements: empty items, total=0, balance=0.00."""
        from src.modules.cuenta_corriente import service

        empresa = await _crear_empresa(db_session, "Hist B")
        cliente = await _crear_cliente(db_session, empresa.id, saldo=Decimal("0.00"))

        result = await service.obtener_historial(db_session, empresa.id, cliente.id)

        assert result.total == 0
        assert result.items == []
        assert result.saldo_actual == Decimal("0.00")

    # 3.3 TRIANGULATE — tenant isolation on history
    async def test_foreign_tenant_history_raises_404(self, db_session: AsyncSession):
        """History for a foreign-tenant customer raises NotFoundException (404)."""
        from src.modules.cuenta_corriente import service

        empresa_a = await _crear_empresa(db_session, "Hist Tenant A")
        empresa_b = await _crear_empresa(db_session, "Hist Tenant B")
        cliente_b = await _crear_cliente(db_session, empresa_b.id, saldo=Decimal("200.00"))

        with pytest.raises(NotFoundException):
            await service.obtener_historial(db_session, empresa_a.id, cliente_b.id)


# ---------------------------------------------------------------------------
# Task 4.1 RED → 4.2 GREEN: estado_cuenta returns movements + balance + customer
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestObtenerEstadoCuenta:
    async def test_returns_customer_info_and_movements(self, db_session: AsyncSession):
        """Estado cuenta includes customer name, all movements, and current balance."""
        from src.modules.cuenta_corriente import service

        empresa = await _crear_empresa(db_session, "Estado A")
        cliente = await _crear_cliente(db_session, empresa.id, nombre="Maria", saldo=Decimal("500.00"))
        await _crear_movimiento(db_session, empresa.id, cliente.id, "deuda", Decimal("500.00"), Decimal("500.00"))

        result = await service.obtener_estado_cuenta(db_session, empresa.id, cliente.id)

        assert result.cliente_id == cliente.id
        assert "Maria" in result.cliente_nombre
        assert len(result.movimientos) == 1
        assert result.saldo_actual == Decimal("500.00")

    async def test_foreign_tenant_estado_cuenta_raises_404(self, db_session: AsyncSession):
        """Estado cuenta for foreign tenant raises NotFoundException."""
        from src.modules.cuenta_corriente import service

        empresa_a = await _crear_empresa(db_session, "Estado Tenant A")
        empresa_b = await _crear_empresa(db_session, "Estado Tenant B")
        cliente_b = await _crear_cliente(db_session, empresa_b.id, saldo=Decimal("300.00"))

        with pytest.raises(NotFoundException):
            await service.obtener_estado_cuenta(db_session, empresa_a.id, cliente_b.id)
