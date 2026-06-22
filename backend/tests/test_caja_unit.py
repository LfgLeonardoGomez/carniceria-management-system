from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.modules.caja.service import (
    _calcular_esperado,
    _calcular_diferencias,
    EsperadoCaja,
    UMBRAL_DIFERENCIA_SIGNIFICATIVA,
)


def _mov(tipo, importe, medio=None):
    """Lightweight movement stand-in: only the fields the calculator reads."""
    from src.modules.caja.models import MovimientoCaja
    import uuid

    return MovimientoCaja(
        caja_id=uuid.uuid4(),
        empresa_id=uuid.uuid4(),
        tipo=tipo,
        medio=medio,
        importe=Decimal(str(importe)),
    )


# ---------------------------------------------------------------------------
# Esperado
# ---------------------------------------------------------------------------
class TestCalcularEsperado:
    def test_efectivo_formula(self):
        # inicial 100 + ventas efectivo 50 + ingreso manual 20 - retiro 30 = 140
        movs = [
            _mov("entrada_venta", "50.00", medio="efectivo"),
            _mov("ingreso_manual", "20.00"),
            _mov("retiro", "30.00"),
        ]
        esperado = _calcular_esperado(Decimal("100.00"), movs)
        assert esperado.efectivo == Decimal("140.00")

    def test_tarjetas_suma_debito_y_credito(self):
        movs = [
            _mov("entrada_venta", "80.00", medio="debito"),
            _mov("entrada_venta", "120.00", medio="credito"),
        ]
        esperado = _calcular_esperado(Decimal("0.00"), movs)
        assert esperado.tarjetas == Decimal("200.00")

    def test_transferencias(self):
        movs = [
            _mov("entrada_venta", "75.50", medio="transferencia"),
            _mov("entrada_venta", "24.50", medio="transferencia"),
        ]
        esperado = _calcular_esperado(Decimal("0.00"), movs)
        assert esperado.transferencias == Decimal("100.00")

    def test_anulacion_negativa_resta_efectivo(self):
        # entrada 100 efectivo, luego salida_anulacion -100 efectivo => neto 0
        movs = [
            _mov("entrada_venta", "100.00", medio="efectivo"),
            _mov("salida_anulacion", "-100.00", medio="efectivo"),
        ]
        esperado = _calcular_esperado(Decimal("50.00"), movs)
        assert esperado.efectivo == Decimal("50.00")

    def test_sin_movimientos_solo_inicial(self):
        esperado = _calcular_esperado(Decimal("200.00"), [])
        assert esperado.efectivo == Decimal("200.00")
        assert esperado.transferencias == Decimal("0.00")
        assert esperado.tarjetas == Decimal("0.00")


# ---------------------------------------------------------------------------
# Diferencias
# ---------------------------------------------------------------------------
class TestCalcularDiferencias:
    def test_sin_diferencia(self):
        esperado = EsperadoCaja(
            efectivo=Decimal("140.00"),
            transferencias=Decimal("50.00"),
            tarjetas=Decimal("200.00"),
        )
        dif = _calcular_diferencias(
            esperado,
            efectivo_real=Decimal("140.00"),
            transferencias_real=Decimal("50.00"),
            tarjetas_real=Decimal("200.00"),
        )
        assert dif.diferencia_efectivo == Decimal("0.00")
        assert dif.diferencia_total == Decimal("0.00")
        assert dif.tiene_diferencia is False
        assert dif.diferencia_significativa is False

    def test_faltante_efectivo_significativo(self):
        esperado = EsperadoCaja(
            efectivo=Decimal("140.00"),
            transferencias=Decimal("0.00"),
            tarjetas=Decimal("0.00"),
        )
        dif = _calcular_diferencias(
            esperado,
            efectivo_real=Decimal("130.00"),
            transferencias_real=Decimal("0.00"),
            tarjetas_real=Decimal("0.00"),
        )
        assert dif.diferencia_efectivo == Decimal("-10.00")
        assert dif.diferencia_total == Decimal("-10.00")
        assert dif.tiene_diferencia is True
        assert dif.diferencia_significativa is True

    def test_sobrante_total_suma_medios(self):
        esperado = EsperadoCaja(
            efectivo=Decimal("100.00"),
            transferencias=Decimal("50.00"),
            tarjetas=Decimal("30.00"),
        )
        dif = _calcular_diferencias(
            esperado,
            efectivo_real=Decimal("105.00"),
            transferencias_real=Decimal("52.00"),
            tarjetas_real=Decimal("30.00"),
        )
        assert dif.diferencia_efectivo == Decimal("5.00")
        assert dif.diferencia_transferencias == Decimal("2.00")
        assert dif.diferencia_tarjetas == Decimal("0.00")
        assert dif.diferencia_total == Decimal("7.00")
        assert dif.diferencia_significativa is True

    def test_umbral_es_un_centavo(self):
        assert UMBRAL_DIFERENCIA_SIGNIFICATIVA == Decimal("0.01")


# ---------------------------------------------------------------------------
# Polish-3: tipo/medio constraints on MovimientoCajaRequest
# ---------------------------------------------------------------------------
class TestTipoMedioConstraints:
    def test_tipo_invalido_rechazado_en_schema(self):
        """An invalid tipo must raise a Pydantic ValidationError at the schema layer."""
        from src.modules.caja.schemas import MovimientoCajaRequest

        with pytest.raises(ValidationError):
            MovimientoCajaRequest(tipo="tipo_inventado", importe=Decimal("10.00"))

    def test_tipo_sistema_rechazado_en_request_schema(self):
        """System tipos (entrada_venta, salida_anulacion) must NOT be accepted via the
        manual movimiento request schema — they are written by the service internally."""
        from src.modules.caja.schemas import MovimientoCajaRequest

        with pytest.raises(ValidationError):
            MovimientoCajaRequest(tipo="entrada_venta", importe=Decimal("10.00"))
        with pytest.raises(ValidationError):
            MovimientoCajaRequest(tipo="salida_anulacion", importe=Decimal("10.00"))

    def test_tipo_valido_aceptado(self):
        """Valid manual tipos must be accepted by the schema."""
        from src.modules.caja.schemas import MovimientoCajaRequest

        req = MovimientoCajaRequest(tipo="retiro", importe=Decimal("10.00"))
        assert req.tipo == "retiro"
        req2 = MovimientoCajaRequest(tipo="ingreso_manual", importe=Decimal("5.00"))
        assert req2.tipo == "ingreso_manual"


# ---------------------------------------------------------------------------
# Polish-4: caja:operate permission rename
# ---------------------------------------------------------------------------
class TestCajaPermisoRenombrado:
    def test_caja_operate_en_cajero(self):
        """cajero role must have 'caja:operate' permission after rename."""
        from src.common.rbac import has_permission

        assert has_permission("cajero", "caja:operate") is True

    def test_caja_operate_en_encargado(self):
        """encargado role must have 'caja:operate' permission after rename."""
        from src.common.rbac import has_permission

        assert has_permission("encargado", "caja:operate") is True

    def test_caja_operate_en_admin(self):
        """admin role must have 'caja:operate' permission after rename."""
        from src.common.rbac import has_permission

        assert has_permission("admin", "caja:operate") is True

    def test_caja_admin_no_existe(self):
        """After rename, 'caja:admin' must NOT exist in any role."""
        from src.common.rbac import PERMISSION_MATRIX

        for rol, perms in PERMISSION_MATRIX.items():
            assert "caja:admin" not in perms, f"Role '{rol}' still has caja:admin"
