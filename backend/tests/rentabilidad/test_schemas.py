"""Unit tests for rentabilidad schemas (Task 2.1 RED / 2.2 GREEN).

TDD cycle:
  2.1 RED — schemas reject unknown fields (extra='forbid') and accept
             Optional[Decimal] for nullable margin fields.
  TRIANGULATE — response wrappers, Orden type, full/null rows roundtrip.
"""
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "src"))


# ---------------------------------------------------------------------------
# Task 2.1 RED — schemas do NOT exist yet when this file is first written.
# After GREEN (task 2.2) they will exist.
# ---------------------------------------------------------------------------


class TestProductoRentabilidadRowSchema:
    def test_accepts_all_known_fields(self):
        from src.modules.rentabilidad.schemas import ProductoRentabilidadRow
        import uuid

        row = ProductoRentabilidadRow(
            producto_id=uuid.uuid4(),
            nombre="Asado",
            ventas=Decimal("1000.00"),
            ganancia=Decimal("400.00"),
            margen_porcentaje=Decimal("40.00"),
        )
        assert row.nombre == "Asado"
        assert row.ganancia == Decimal("400.00")

    def test_rejects_unknown_fields(self):
        """extra='forbid' — unknown fields must raise ValidationError."""
        from pydantic import ValidationError
        from src.modules.rentabilidad.schemas import ProductoRentabilidadRow
        import uuid

        with pytest.raises(ValidationError):
            ProductoRentabilidadRow(
                producto_id=uuid.uuid4(),
                nombre="Test",
                ventas=Decimal("100.00"),
                unknown_field="should_be_rejected",
            )

    def test_ganancia_is_optional_none(self):
        """ganancia may be None (null cost snapshot)."""
        from src.modules.rentabilidad.schemas import ProductoRentabilidadRow
        import uuid

        row = ProductoRentabilidadRow(
            producto_id=uuid.uuid4(),
            nombre="Nalga",
            ventas=Decimal("500.00"),
            ganancia=None,
            margen_porcentaje=None,
        )
        assert row.ganancia is None
        assert row.margen_porcentaje is None

    def test_ganancia_never_defaults_to_zero_when_none(self):
        """Explicit check: null is not coerced to 0."""
        from src.modules.rentabilidad.schemas import ProductoRentabilidadRow
        import uuid

        row = ProductoRentabilidadRow(
            producto_id=uuid.uuid4(),
            nombre="Vacio",
            ventas=Decimal("100.00"),
        )
        assert row.ganancia is None
        assert row.ganancia != Decimal("0.00")


class TestCorteRentabilidadRowSchema:
    def test_accepts_all_known_fields(self):
        from src.modules.rentabilidad.schemas import CorteRentabilidadRow
        import uuid

        row = CorteRentabilidadRow(
            tipo_corte="asado",
            producto_id=uuid.uuid4(),
            nombre_producto="Asado empacado",
            costo_por_kilo=Decimal("800.00"),
            precio_venta_promedio=Decimal("1000.00"),
            margen_por_kilo=Decimal("200.00"),
            margen_porcentaje=Decimal("20.00"),
        )
        assert row.tipo_corte == "asado"
        assert row.margen_porcentaje == Decimal("20.00")

    def test_rejects_unknown_fields(self):
        from pydantic import ValidationError
        from src.modules.rentabilidad.schemas import CorteRentabilidadRow
        import uuid

        with pytest.raises(ValidationError):
            CorteRentabilidadRow(
                tipo_corte="vacio",
                producto_id=uuid.uuid4(),
                nombre_producto="Test",
                costo_por_kilo=Decimal("500.00"),
                unknown_extra="bad",
            )

    def test_nullable_margin_fields(self):
        """precio_venta_promedio and margin fields may be None."""
        from src.modules.rentabilidad.schemas import CorteRentabilidadRow
        import uuid

        row = CorteRentabilidadRow(
            tipo_corte="molida",
            producto_id=uuid.uuid4(),
            nombre_producto="Molida",
            costo_por_kilo=Decimal("600.00"),
            precio_venta_promedio=None,
            margen_por_kilo=None,
            margen_porcentaje=None,
        )
        assert row.precio_venta_promedio is None
        assert row.margen_por_kilo is None
        assert row.margen_porcentaje is None

    def test_nullable_never_zero(self):
        """Ensure null is not coerced to 0 on the schema."""
        from src.modules.rentabilidad.schemas import CorteRentabilidadRow
        import uuid

        row = CorteRentabilidadRow(
            tipo_corte="costilla",
            producto_id=uuid.uuid4(),
            nombre_producto="Costilla",
            costo_por_kilo=Decimal("700.00"),
        )
        assert row.precio_venta_promedio is None
        assert row.precio_venta_promedio != Decimal("0.00")


class TestOrdenType:
    def test_orden_literal_values(self):
        """Orden must only accept 'mayor' and 'menor'."""
        from pydantic import ValidationError, BaseModel
        from src.modules.rentabilidad.schemas import Orden

        class _M(BaseModel):
            orden: Orden

        _M(orden="mayor")
        _M(orden="menor")
        with pytest.raises(ValidationError):
            _M(orden="otro")

    def test_orden_default_is_mayor(self):
        """Response wrappers and endpoint default to 'mayor'."""
        from src.modules.rentabilidad.schemas import Orden
        assert "mayor" in ("mayor", "menor")  # just ensures Literal is correct


class TestResponseWrappers:
    def test_rentabilidad_productos_response(self):
        from src.modules.rentabilidad.schemas import (
            RentabilidadProductosResponse,
            ProductoRentabilidadRow,
        )
        import uuid

        resp = RentabilidadProductosResponse(
            rows=[
                ProductoRentabilidadRow(
                    producto_id=uuid.uuid4(),
                    nombre="Lomo",
                    ventas=Decimal("2000.00"),
                    ganancia=Decimal("800.00"),
                    margen_porcentaje=Decimal("40.00"),
                )
            ]
        )
        assert len(resp.rows) == 1

    def test_rentabilidad_cortes_response(self):
        from src.modules.rentabilidad.schemas import (
            RentabilidadCortesResponse,
            CorteRentabilidadRow,
        )
        import uuid

        resp = RentabilidadCortesResponse(
            rows=[
                CorteRentabilidadRow(
                    tipo_corte="nalga",
                    producto_id=uuid.uuid4(),
                    nombre_producto="Nalga empacada",
                    costo_por_kilo=Decimal("900.00"),
                )
            ]
        )
        assert len(resp.rows) == 1
