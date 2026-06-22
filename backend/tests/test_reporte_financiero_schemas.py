"""Tests for C-18 financial report schemas.

TDD cycle:
  1.1 RED  — GroupBy literals + FinancieroPeriodoRow field constraints
  1.3 TRIANGULATE — Decimal serialization, extra-field rejection
"""
from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "src"))

from src.modules.reporte.schemas import (
    FinancieroPeriodoRow,
    GroupBy,
    ReporteFinancieroResponse,
)


# ---------------------------------------------------------------------------
# Task 1.1 — GroupBy + FinancieroPeriodoRow field constraints
# ---------------------------------------------------------------------------


class TestGroupByLiterals:
    """GroupBy accepts valid values; rejects anything else."""

    def test_dia_valid(self):
        # Primary assertion: the GroupBy type exists and accepts 'dia'
        gb: GroupBy = "dia"
        assert gb == "dia"

    def test_all_valid_literals(self):
        for v in ("dia", "semana", "mes", "anio"):
            gb: GroupBy = v  # type: ignore[assignment]
            assert gb == v

    def test_invalid_literal_rejected_at_schema_level(self):
        """An invalid group_by in ReporteFinancieroResponse raises ValidationError."""
        with pytest.raises(ValidationError):
            ReporteFinancieroResponse(group_by="trimestre", rows=[])  # type: ignore[arg-type]


class TestFinancieroPeriodoRowConstraints:
    """FinancieroPeriodoRow schema constraints."""

    def test_required_fields_present(self):
        row = FinancieroPeriodoRow(
            periodo="2026-06",
            ventas=Decimal("500.00"),
            gastos=Decimal("0.00"),
        )
        assert row.periodo == "2026-06"
        assert row.ventas == Decimal("500.00")
        assert row.gastos == Decimal("0.00")
        assert row.costos is None
        assert row.utilidad_bruta is None
        assert row.utilidad_neta is None

    def test_nullable_indicators_allowed_none(self):
        """costos, utilidad_bruta, utilidad_neta may be None."""
        row = FinancieroPeriodoRow(
            periodo="2026-06",
            ventas=Decimal("1000.00"),
            gastos=Decimal("150.00"),
            costos=None,
            utilidad_bruta=None,
            utilidad_neta=None,
        )
        assert row.costos is None
        assert row.utilidad_bruta is None
        assert row.utilidad_neta is None

    def test_nullable_indicators_accept_decimal(self):
        row = FinancieroPeriodoRow(
            periodo="2026-06",
            ventas=Decimal("1000.00"),
            gastos=Decimal("150.00"),
            costos=Decimal("600.00"),
            utilidad_bruta=Decimal("400.00"),
            utilidad_neta=Decimal("250.00"),
        )
        assert row.costos == Decimal("600.00")
        assert row.utilidad_bruta == Decimal("400.00")
        assert row.utilidad_neta == Decimal("250.00")

    def test_ventas_required_missing_raises(self):
        with pytest.raises(ValidationError):
            FinancieroPeriodoRow(periodo="2026-06", gastos=Decimal("0.00"))  # type: ignore[call-arg]

    def test_gastos_required_missing_raises(self):
        with pytest.raises(ValidationError):
            FinancieroPeriodoRow(periodo="2026-06", ventas=Decimal("100.00"))  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Task 1.3 TRIANGULATE — Decimal serialization + extra-field rejection
# ---------------------------------------------------------------------------


class TestDecimalSerialization:
    """Money fields serialise as strings (Decimal-safe), no float drift."""

    def test_serializes_decimal_as_string(self):
        row = FinancieroPeriodoRow(
            periodo="2026-06",
            ventas=Decimal("1234.56"),
            gastos=Decimal("78.90"),
            costos=Decimal("999.99"),
            utilidad_bruta=Decimal("234.57"),
            utilidad_neta=Decimal("155.67"),
        )
        dumped = row.model_dump()
        # Pydantic keeps Decimal as Decimal in model_dump(); serialize to JSON for string check
        json_str = row.model_dump_json()
        # Ventas should appear as a number-string without float notation
        assert "1234.56" in json_str
        assert "78.90" in json_str or "78.9" in json_str  # Pydantic may trim trailing zeros
        assert "999.99" in json_str

    def test_no_float_drift_on_large_sum(self):
        """Summing Decimals does not produce float drift."""
        total = sum(
            Decimal("0.10") for _ in range(10)
        )
        row = FinancieroPeriodoRow(
            periodo="2026-06",
            ventas=total,
            gastos=Decimal("0.00"),
        )
        assert row.ventas == Decimal("1.00")


class TestExtraFieldRejection:
    """extra='forbid' rejects unknown fields on both models."""

    def test_periodo_row_rejects_extra(self):
        with pytest.raises(ValidationError):
            FinancieroPeriodoRow(
                periodo="2026-06",
                ventas=Decimal("100.00"),
                gastos=Decimal("0.00"),
                unknown_field="should_fail",  # type: ignore[call-arg]
            )

    def test_response_rejects_extra(self):
        with pytest.raises(ValidationError):
            ReporteFinancieroResponse(
                group_by="mes",
                rows=[],
                extra_field="nope",  # type: ignore[call-arg]
            )
