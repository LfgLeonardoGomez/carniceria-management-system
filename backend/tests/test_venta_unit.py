from decimal import Decimal

import pytest

from src.modules.venta import state_machine
from src.modules.venta.service import _calcular_precio_unitario, _calcular_totales
from src.modules.producto.models import Producto
from src.modules.venta.models import DetalleVenta


# ---------------------------------------------------------------------------
# State Machine
# ---------------------------------------------------------------------------
class TestStateMachine:
    def test_en_curso_a_suspendida(self):
        assert state_machine.puede_transicionar("en_curso", "suspendida")

    def test_en_curso_a_cobrada(self):
        assert state_machine.puede_transicionar("en_curso", "cobrada")

    def test_suspendida_a_en_curso(self):
        assert state_machine.puede_transicionar("suspendida", "en_curso")

    def test_suspendida_a_cobrada(self):
        assert state_machine.puede_transicionar("suspendida", "cobrada")

    def test_cobrada_a_anulada(self):
        assert state_machine.puede_transicionar("cobrada", "anulada")

    def test_anulada_es_terminal(self):
        assert not state_machine.puede_transicionar("anulada", "en_curso")
        assert not state_machine.puede_transicionar("anulada", "cobrada")
        assert not state_machine.puede_transicionar("anulada", "suspendida")

    def test_transicion_ilegal_cobrada_a_suspendida(self):
        assert not state_machine.puede_transicionar("cobrada", "suspendida")

    def test_transicionar_lanza_excepcion(self):
        from src.common.exceptions import ConflictException
        with pytest.raises(ConflictException):
            state_machine.transicionar("cobrada", "suspendida")

    def test_requiere_rol_admin_anulada(self):
        assert state_machine.requiere_rol_admin_o_encargado("anulada")

    def test_no_requiere_rol_admin_otros(self):
        assert not state_machine.requiere_rol_admin_o_encargado("cobrada")
        assert not state_machine.requiere_rol_admin_o_encargado("suspendida")


# ---------------------------------------------------------------------------
# Cálculo de precios
# ---------------------------------------------------------------------------
class TestCalcularPrecioUnitario:
    def test_publico_general(self):
        p = Producto(
            empresa_id=__import__("uuid").uuid4(),
            plu="001",
            nombre="Asado",
            precio_publico=Decimal("1000.0000"),
            precio_mayorista=Decimal("800.0000"),
            costo_por_kilo=Decimal("600.0000"),
            stock_actual=Decimal("10.0000"),
        )
        assert _calcular_precio_unitario(p, "publico_general") == Decimal("1000.00")

    def test_mayorista(self):
        p = Producto(
            empresa_id=__import__("uuid").uuid4(),
            plu="001",
            nombre="Asado",
            precio_publico=Decimal("1000.0000"),
            precio_mayorista=Decimal("800.0000"),
            costo_por_kilo=Decimal("600.0000"),
            stock_actual=Decimal("10.0000"),
        )
        assert _calcular_precio_unitario(p, "mayorista") == Decimal("800.00")

    def test_especial_usa_precio_publico(self):
        p = Producto(
            empresa_id=__import__("uuid").uuid4(),
            plu="001",
            nombre="Asado",
            precio_publico=Decimal("1000.0000"),
            precio_mayorista=Decimal("800.0000"),
            costo_por_kilo=Decimal("600.0000"),
            stock_actual=Decimal("10.0000"),
        )
        assert _calcular_precio_unitario(p, "especial") == Decimal("1000.00")


# ---------------------------------------------------------------------------
# Cálculo de totales
# ---------------------------------------------------------------------------
class TestCalcularTotales:
    def test_calculo_basico(self):
        items = [
            DetalleVenta(
                producto_id=__import__("uuid").uuid4(),
                cantidad_kilos=Decimal("2.000"),
                precio_unitario=Decimal("100.00"),
                importe=Decimal("200.00"),
            ),
            DetalleVenta(
                producto_id=__import__("uuid").uuid4(),
                cantidad_kilos=Decimal("1.500"),
                precio_unitario=Decimal("100.00"),
                importe=Decimal("150.00"),
            ),
        ]
        subtotal, total = _calcular_totales(items, Decimal("0.00"))
        assert subtotal == Decimal("350.00")
        assert total == Decimal("350.00")

    def test_calculo_con_descuento(self):
        items = [
            DetalleVenta(
                producto_id=__import__("uuid").uuid4(),
                cantidad_kilos=Decimal("1.000"),
                precio_unitario=Decimal("100.00"),
                importe=Decimal("100.00"),
            ),
            DetalleVenta(
                producto_id=__import__("uuid").uuid4(),
                cantidad_kilos=Decimal("0.500"),
                precio_unitario=Decimal("100.00"),
                importe=Decimal("50.00"),
            ),
        ]
        subtotal, total = _calcular_totales(items, Decimal("10.00"))
        assert subtotal == Decimal("150.00")
        assert total == Decimal("140.00")

    def test_total_no_negativo(self):
        items = [
            DetalleVenta(
                producto_id=__import__("uuid").uuid4(),
                cantidad_kilos=Decimal("1.000"),
                precio_unitario=Decimal("10.00"),
                importe=Decimal("10.00"),
            ),
        ]
        subtotal, total = _calcular_totales(items, Decimal("20.00"))
        assert subtotal == Decimal("10.00")
        assert total == Decimal("0.00")
