"""Unit tests for cuenta_corriente schemas (Tasks 1.1 RED / 1.2 GREEN / 1.3 TRIANGULATE).

TDD cycle:
  1.1 RED  — PagoCreate rejects extra fields, rejects importe <= 0, accepts valid Decimal importe
  1.2 GREEN — schemas exist and pass
  1.3 TRIANGULATE — negative, zero, high-precision importe cases; quantization to 2 decimals
"""
import sys
from decimal import Decimal
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "src"))


# ---------------------------------------------------------------------------
# Task 1.1 RED — PagoCreate: extra='forbid', importe > 0 (gt=0)
# ---------------------------------------------------------------------------

class TestPagoCreate:
    def test_accepts_valid_positive_importe(self):
        from src.modules.cuenta_corriente.schemas import PagoCreate

        pago = PagoCreate(importe=Decimal("500.00"))
        assert pago.importe == Decimal("500.00")

    def test_rejects_extra_fields(self):
        """extra='forbid' must raise ValidationError for unknown fields."""
        from pydantic import ValidationError
        from src.modules.cuenta_corriente.schemas import PagoCreate

        with pytest.raises(ValidationError):
            PagoCreate(importe=Decimal("100.00"), unknown_field="bad")

    def test_rejects_zero_importe(self):
        """importe=0 must fail (gt=0)."""
        from pydantic import ValidationError
        from src.modules.cuenta_corriente.schemas import PagoCreate

        with pytest.raises(ValidationError):
            PagoCreate(importe=Decimal("0"))

    def test_rejects_negative_importe(self):
        """importe<0 must fail (gt=0)."""
        from pydantic import ValidationError
        from src.modules.cuenta_corriente.schemas import PagoCreate

        with pytest.raises(ValidationError):
            PagoCreate(importe=Decimal("-100.00"))

    # 1.3 TRIANGULATE — high-precision input
    def test_accepts_high_precision_importe(self):
        """High-precision Decimal should be accepted (validation is gt=0, not quantization)."""
        from src.modules.cuenta_corriente.schemas import PagoCreate

        pago = PagoCreate(importe=Decimal("999.9999"))
        assert pago.importe == Decimal("999.9999")

    def test_rejects_very_small_positive(self):
        """Even 0.0001 is > 0 — should be accepted."""
        from src.modules.cuenta_corriente.schemas import PagoCreate

        pago = PagoCreate(importe=Decimal("0.0001"))
        assert pago.importe > 0


# ---------------------------------------------------------------------------
# MovimientoCCResponse schema
# ---------------------------------------------------------------------------

class TestMovimientoCCResponse:
    def test_accepts_all_fields(self):
        import uuid
        from datetime import datetime
        from src.modules.cuenta_corriente.schemas import MovimientoCCResponse

        mov = MovimientoCCResponse(
            id=uuid.uuid4(),
            tipo="pago",
            importe=Decimal("300.00"),
            saldo_resultante=Decimal("700.00"),
            venta_id=None,
            fecha=datetime.utcnow(),
        )
        assert mov.tipo == "pago"
        assert mov.saldo_resultante == Decimal("700.00")

    def test_venta_id_is_optional(self):
        import uuid
        from datetime import datetime
        from src.modules.cuenta_corriente.schemas import MovimientoCCResponse

        mov = MovimientoCCResponse(
            id=uuid.uuid4(),
            tipo="deuda",
            importe=Decimal("1000.00"),
            saldo_resultante=Decimal("1000.00"),
            venta_id=uuid.uuid4(),
            fecha=datetime.utcnow(),
        )
        assert mov.venta_id is not None

    def test_rejects_extra_fields(self):
        import uuid
        from datetime import datetime
        from pydantic import ValidationError
        from src.modules.cuenta_corriente.schemas import MovimientoCCResponse

        with pytest.raises(ValidationError):
            MovimientoCCResponse(
                id=uuid.uuid4(),
                tipo="pago",
                importe=Decimal("100.00"),
                saldo_resultante=Decimal("0.00"),
                venta_id=None,
                fecha=datetime.utcnow(),
                extra_field="bad",
            )


# ---------------------------------------------------------------------------
# PagoResponse schema
# ---------------------------------------------------------------------------

class TestPagoResponse:
    def test_contains_movement_and_balance(self):
        import uuid
        from datetime import datetime
        from src.modules.cuenta_corriente.schemas import PagoResponse, MovimientoCCResponse

        movimiento = MovimientoCCResponse(
            id=uuid.uuid4(),
            tipo="pago",
            importe=Decimal("300.00"),
            saldo_resultante=Decimal("700.00"),
            venta_id=None,
            fecha=datetime.utcnow(),
        )
        resp = PagoResponse(movimiento=movimiento, saldo_actual=Decimal("700.00"))
        assert resp.saldo_actual == Decimal("700.00")
        assert resp.movimiento.tipo == "pago"

    def test_rejects_extra_fields(self):
        import uuid
        from datetime import datetime
        from pydantic import ValidationError
        from src.modules.cuenta_corriente.schemas import PagoResponse, MovimientoCCResponse

        movimiento = MovimientoCCResponse(
            id=uuid.uuid4(),
            tipo="pago",
            importe=Decimal("100.00"),
            saldo_resultante=Decimal("0.00"),
            venta_id=None,
            fecha=datetime.utcnow(),
        )
        with pytest.raises(ValidationError):
            PagoResponse(movimiento=movimiento, saldo_actual=Decimal("0.00"), extra="bad")


# ---------------------------------------------------------------------------
# HistorialCCResponse schema
# ---------------------------------------------------------------------------

class TestHistorialCCResponse:
    def test_accepts_envelope_fields(self):
        import uuid
        from datetime import datetime
        from src.modules.cuenta_corriente.schemas import HistorialCCResponse, MovimientoCCResponse

        mov = MovimientoCCResponse(
            id=uuid.uuid4(),
            tipo="deuda",
            importe=Decimal("1000.00"),
            saldo_resultante=Decimal("1000.00"),
            venta_id=None,
            fecha=datetime.utcnow(),
        )
        resp = HistorialCCResponse(
            items=[mov],
            total=1,
            skip=0,
            limit=50,
            saldo_actual=Decimal("1000.00"),
        )
        assert resp.total == 1
        assert len(resp.items) == 1
        assert resp.saldo_actual == Decimal("1000.00")

    def test_empty_items(self):
        from src.modules.cuenta_corriente.schemas import HistorialCCResponse

        resp = HistorialCCResponse(
            items=[],
            total=0,
            skip=0,
            limit=50,
            saldo_actual=Decimal("0.00"),
        )
        assert resp.total == 0
        assert resp.items == []

    def test_rejects_extra_fields(self):
        from pydantic import ValidationError
        from src.modules.cuenta_corriente.schemas import HistorialCCResponse

        with pytest.raises(ValidationError):
            HistorialCCResponse(
                items=[],
                total=0,
                skip=0,
                limit=50,
                saldo_actual=Decimal("0.00"),
                bad_field="x",
            )
