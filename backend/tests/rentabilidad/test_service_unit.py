"""Unit tests for rentabilidad pure aggregation helpers (Tasks 3.1–3.7, 3.4).

No database. In-memory objects mirror ORM models via MagicMock.

TDD cycle:
  3.1 RED — _ranking_productos: formula ganancia = Σ(importe) − Σ(kilos × costo_unitario)
  3.2 GREEN — implement _ranking_productos
  3.3 TRIANGULATE — NULL costo_unitario → ganancia=None; ventas=0 → margin None
  3.4 RED+GREEN — ordering: mayor/menor; null-last; top=N
  3.5 RED — _margen_cortes: cut margin formula
  3.6 GREEN — implement _margen_cortes
  3.7 TRIANGULATE — produto_id IS NULL excluded; linked product no sales → null price
"""
from __future__ import annotations

import sys
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "src"))


# ---------------------------------------------------------------------------
# Helpers: lightweight in-memory mocks that mirror ORM models
# ---------------------------------------------------------------------------

def _make_detalle(
    producto_id: uuid.UUID,
    cantidad_kilos: Decimal,
    costo_unitario: Optional[Decimal],
    importe: Decimal,
) -> MagicMock:
    d = MagicMock()
    d.producto_id = producto_id
    d.cantidad_kilos = cantidad_kilos
    d.costo_unitario = costo_unitario
    d.importe = importe
    return d


def _make_corte(
    tipo_corte: str,
    costo_final_por_kilo: Decimal,
    producto_id: Optional[uuid.UUID] = None,
    nombre_producto: str = "Producto Test",
) -> MagicMock:
    c = MagicMock()
    c.tipo_corte = tipo_corte
    c.costo_final_por_kilo = costo_final_por_kilo
    c.producto_id = producto_id
    # mimic the ORM relationship: corte.producto is an object with .nombre
    producto_mock = MagicMock()
    producto_mock.nombre = nombre_producto
    c.producto = producto_mock if producto_id is not None else None
    return c


# ---------------------------------------------------------------------------
# Task 3.1 RED — _ranking_productos formula
# ---------------------------------------------------------------------------

class TestRankingProductosFormula:
    def test_happy_path_single_product(self):
        """ganancia = 1000 − 600 = 400; margen = 400/1000 × 100 = 40.00"""
        from src.modules.rentabilidad.service import _ranking_productos

        pid = uuid.uuid4()
        detalles = [
            _make_detalle(pid, Decimal("10.000"), Decimal("60.00"), Decimal("1000.00")),
        ]

        rows = _ranking_productos(detalles, product_names={pid: "Asado"})
        assert len(rows) == 1
        row = rows[0]
        assert row.producto_id == pid
        assert row.ventas == Decimal("1000.00")
        assert row.ganancia == Decimal("400.00")
        assert row.margen_porcentaje == Decimal("40.00")

    def test_two_products_aggregated_separately(self):
        """Two products each get their own row with correct aggregation."""
        from src.modules.rentabilidad.service import _ranking_productos

        pid_a = uuid.uuid4()
        pid_b = uuid.uuid4()
        detalles = [
            _make_detalle(pid_a, Decimal("5.000"), Decimal("60.00"), Decimal("600.00")),
            _make_detalle(pid_b, Decimal("3.000"), Decimal("100.00"), Decimal("600.00")),
            _make_detalle(pid_a, Decimal("2.000"), Decimal("60.00"), Decimal("240.00")),
        ]
        names = {pid_a: "Asado", pid_b: "Nalga"}
        rows = _ranking_productos(detalles, product_names=names)
        assert len(rows) == 2
        rows_by_id = {r.producto_id: r for r in rows}

        row_a = rows_by_id[pid_a]
        # ventas: 600 + 240 = 840; costos: (5+2)×60 = 420; ganancia = 420
        assert row_a.ventas == Decimal("840.00")
        assert row_a.ganancia == Decimal("420.00")
        assert row_a.margen_porcentaje == Decimal("50.00")

        row_b = rows_by_id[pid_b]
        # ventas: 600; costos: 3×100 = 300; ganancia = 300
        assert row_b.ventas == Decimal("600.00")
        assert row_b.ganancia == Decimal("300.00")
        assert row_b.margen_porcentaje == Decimal("50.00")


# ---------------------------------------------------------------------------
# Task 3.3 TRIANGULATE — NULL costo_unitario & zero ventas
# ---------------------------------------------------------------------------

class TestRankingProductosNullCost:
    def test_any_null_costo_makes_ganancia_none(self):
        """Product with ONE null-cost line → ganancia=None, never zero."""
        from src.modules.rentabilidad.service import _ranking_productos

        pid = uuid.uuid4()
        detalles = [
            _make_detalle(pid, Decimal("5.000"), Decimal("60.00"), Decimal("500.00")),
            _make_detalle(pid, Decimal("2.000"), None, Decimal("200.00")),  # null cost!
        ]
        rows = _ranking_productos(detalles, product_names={pid: "Asado"})
        assert len(rows) == 1
        row = rows[0]
        assert row.ganancia is None
        assert row.margen_porcentaje is None
        # Ganancia must not be zero (not cost=0 treating null as 0)
        assert row.ganancia != Decimal("0.00")

    def test_null_ganancia_not_zero(self):
        """Explicit check: null is never treated as 0.00 profit."""
        from src.modules.rentabilidad.service import _ranking_productos

        pid = uuid.uuid4()
        detalles = [
            _make_detalle(pid, Decimal("10.000"), None, Decimal("1000.00")),
        ]
        rows = _ranking_productos(detalles, product_names={pid: "Vacio"})
        row = rows[0]
        # If null were treated as 0, ganancia would be 1000 (ventas − 0 cost)
        assert row.ganancia is None
        assert row.ganancia != Decimal("1000.00")

    def test_zero_ventas_makes_margin_none(self):
        """When ventas total is 0, margin is None to avoid division by zero."""
        from src.modules.rentabilidad.service import _ranking_productos

        pid = uuid.uuid4()
        # Edge case: product with zero importe (theoretically possible via returns)
        detalles = [
            _make_detalle(pid, Decimal("0.000"), Decimal("60.00"), Decimal("0.00")),
        ]
        rows = _ranking_productos(detalles, product_names={pid: "Zero"})
        row = rows[0]
        assert row.margen_porcentaje is None


# ---------------------------------------------------------------------------
# Task 3.4 RED+GREEN — ordering and top-N
# ---------------------------------------------------------------------------

class TestRankingProductosOrdering:
    def _make_rows_three_products(self):
        """Helper: three products A (40%), B (20%), C (null margin)."""
        from src.modules.rentabilidad.service import _ranking_productos

        pid_a = uuid.uuid4()
        pid_b = uuid.uuid4()
        pid_c = uuid.uuid4()

        detalles = [
            _make_detalle(pid_a, Decimal("10.000"), Decimal("60.00"), Decimal("1000.00")),  # margin 40%
            _make_detalle(pid_b, Decimal("10.000"), Decimal("80.00"), Decimal("1000.00")),  # margin 20%
            _make_detalle(pid_c, Decimal("5.000"), None, Decimal("500.00")),                # null margin
        ]
        names = {pid_a: "A", pid_b: "B", pid_c: "C"}
        return pid_a, pid_b, pid_c, _ranking_productos(detalles, product_names=names)

    def test_orden_mayor_descending_null_last(self):
        """orden=mayor: highest margin first; null-margin product LAST."""
        from src.modules.rentabilidad.service import _apply_ordering

        pid_a, pid_b, pid_c, rows = self._make_rows_three_products()
        ordered = _apply_ordering(rows, orden="mayor", top=None)

        assert ordered[0].producto_id == pid_a   # 40% first
        assert ordered[1].producto_id == pid_b   # 20% second
        assert ordered[2].producto_id == pid_c   # null LAST

    def test_orden_menor_ascending_null_last(self):
        """orden=menor: lowest margin first; null-margin product still LAST."""
        from src.modules.rentabilidad.service import _apply_ordering

        pid_a, pid_b, pid_c, rows = self._make_rows_three_products()
        ordered = _apply_ordering(rows, orden="menor", top=None)

        assert ordered[0].producto_id == pid_b   # 20% first (least profitable)
        assert ordered[1].producto_id == pid_a   # 40% second
        assert ordered[2].producto_id == pid_c   # null LAST regardless of direction

    def test_top_n_limits_head(self):
        """top=1 returns only the first row of the ordered list."""
        from src.modules.rentabilidad.service import _apply_ordering

        _pid_a, _pid_b, _pid_c, rows = self._make_rows_three_products()
        ordered = _apply_ordering(rows, orden="mayor", top=1)

        assert len(ordered) == 1

    def test_null_margin_not_most_profitable(self):
        """Null-margin product must never appear first in 'mayor' direction."""
        from src.modules.rentabilidad.service import _apply_ordering

        _pid_a, _pid_b, pid_c, rows = self._make_rows_three_products()
        ordered = _apply_ordering(rows, orden="mayor", top=None)

        assert ordered[0].producto_id != pid_c   # null cannot be first

    def test_null_margin_not_least_profitable(self):
        """Null-margin product must never appear first in 'menor' direction."""
        from src.modules.rentabilidad.service import _apply_ordering

        _pid_a, _pid_b, pid_c, rows = self._make_rows_three_products()
        ordered = _apply_ordering(rows, orden="menor", top=None)

        assert ordered[0].producto_id != pid_c   # null cannot be first (not "least")


# ---------------------------------------------------------------------------
# Task 3.5 RED — _margen_cortes formula
# ---------------------------------------------------------------------------

class TestMargenCortesFormula:
    def test_happy_path_cut_margin(self):
        """costo=800, precio=1000 → margen_por_kilo=200, margen_porcentaje=20."""
        from src.modules.rentabilidad.service import _margen_cortes

        pid = uuid.uuid4()
        corte = _make_corte("asado", Decimal("800.00"), producto_id=pid)
        # detalles for the linked product: 2 kilo at 1000 importe
        detalles = [
            _make_detalle(pid, Decimal("1.000"), Decimal("600.00"), Decimal("1000.00")),
        ]
        rows = _margen_cortes([corte], detalles, product_names={pid: "Asado empacado"})
        assert len(rows) == 1
        row = rows[0]
        assert row.tipo_corte == "asado"
        assert row.costo_por_kilo == Decimal("800.00")
        assert row.precio_venta_promedio == Decimal("1000.00")  # 1000/1 kilo
        assert row.margen_por_kilo == Decimal("200.00")
        assert row.margen_porcentaje == Decimal("20.00")

    def test_formula_verification(self):
        """Verify: 2 kilos at 1500 importe → avg_price=750; costo=500; margen=250; %=33.33."""
        from src.modules.rentabilidad.service import _margen_cortes

        pid = uuid.uuid4()
        corte = _make_corte("vacio", Decimal("500.00"), producto_id=pid)
        detalles = [
            _make_detalle(pid, Decimal("2.000"), Decimal("400.00"), Decimal("1500.00")),
        ]
        rows = _margen_cortes([corte], detalles, product_names={pid: "Vacio"})
        row = rows[0]
        # avg_price = 1500/2 = 750; margen = 750 - 500 = 250; % = 250/750*100 = 33.33
        assert row.precio_venta_promedio == Decimal("750.00")
        assert row.margen_por_kilo == Decimal("250.00")
        assert row.margen_porcentaje == Decimal("33.33")


# ---------------------------------------------------------------------------
# Task 3.7 TRIANGULATE — producto_id IS NULL excluded; no sales → null price
# ---------------------------------------------------------------------------

class TestMargenCortesTriangulate:
    def test_cut_with_no_producto_id_excluded(self):
        """Cuts with producto_id IS NULL must not appear in results."""
        from src.modules.rentabilidad.service import _margen_cortes

        corte_null = _make_corte("asado", Decimal("800.00"), producto_id=None)
        corte_linked = _make_corte("vacio", Decimal("600.00"), producto_id=uuid.uuid4())

        pid = corte_linked.producto_id
        detalles = [
            _make_detalle(pid, Decimal("1.000"), Decimal("500.00"), Decimal("900.00")),
        ]
        rows = _margen_cortes([corte_null, corte_linked], detalles, product_names={pid: "Vacio"})
        # Only the linked cut appears
        assert len(rows) == 1
        assert rows[0].tipo_corte == "vacio"

    def test_linked_product_no_sales_yields_null_price(self):
        """Cut linked to a product with no sales → precio_venta_promedio=None (never 0)."""
        from src.modules.rentabilidad.service import _margen_cortes

        pid = uuid.uuid4()
        corte = _make_corte("nalga", Decimal("900.00"), producto_id=pid)
        # No detalles for this product in range
        rows = _margen_cortes([corte], detalles=[], product_names={pid: "Nalga"})
        assert len(rows) == 1
        row = rows[0]
        assert row.precio_venta_promedio is None
        assert row.margen_por_kilo is None
        assert row.margen_porcentaje is None
        # Must NOT be 0
        assert row.precio_venta_promedio != Decimal("0.00")

    def test_all_null_cuts_returns_empty(self):
        """All cuts have no producto_id → empty result."""
        from src.modules.rentabilidad.service import _margen_cortes

        corte_a = _make_corte("asado", Decimal("800.00"), producto_id=None)
        corte_b = _make_corte("vacio", Decimal("600.00"), producto_id=None)
        rows = _margen_cortes([corte_a, corte_b], detalles=[], product_names={})
        assert rows == []
