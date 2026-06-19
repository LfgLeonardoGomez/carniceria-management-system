from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.modules.empresa.schemas import (
    DatosFiscales,
    ConfiguracionGeneral,
    ParametrosOperativos,
    EmpresaUpdate,
    EmpresaPublic,
    LogoUploadResponse,
)


class TestDatosFiscales:
    def test_instanciacion_valida(self):
        df = DatosFiscales(condicion_iva="Responsable Inscripto", punto_venta=1)
        assert df.condicion_iva == "Responsable Inscripto"
        assert df.punto_venta == 1
        assert df.inicio_actividades is None

    def test_rechazo_campo_extra(self):
        with pytest.raises(ValidationError):
            DatosFiscales(campo_ilegal="no permitido")

    def test_punto_venta_negativo_rechazado(self):
        with pytest.raises(ValidationError):
            DatosFiscales(punto_venta=0)


class TestConfiguracionGeneral:
    def test_valores_por_defecto(self):
        cg = ConfiguracionGeneral()
        assert cg.timezone == "America/Argentina/Buenos_Aires"
        assert cg.moneda == "ARS"
        assert cg.idioma == "es-AR"

    def test_rechazo_campo_extra(self):
        with pytest.raises(ValidationError):
            ConfiguracionGeneral(extra="campo")


class TestParametrosOperativos:
    def test_valores_por_defecto(self):
        po = ParametrosOperativos()
        assert po.alerta_stock_minimo_umbral == Decimal("5.000")
        assert po.alerta_gasto_elevado_umbral == Decimal("100000.00")
        assert po.alerta_deuda_vencida_dias == 30

    def test_rechajo_umbral_negativo(self):
        with pytest.raises(ValidationError):
            ParametrosOperativos(alerta_stock_minimo_umbral=Decimal("-1"))

    def test_rechajo_dias_cero(self):
        with pytest.raises(ValidationError):
            ParametrosOperativos(alerta_deuda_vencida_dias=0)

    def test_rechazo_campo_extra(self):
        with pytest.raises(ValidationError):
            ParametrosOperativos(inexistente=True)


class TestEmpresaUpdate:
    def test_update_parcial_valido(self):
        dto = EmpresaUpdate(nombre_comercial="Nuevo nombre")
        assert dto.nombre_comercial == "Nuevo nombre"
        assert dto.cuit is None

    def test_cuit_valido(self):
        dto = EmpresaUpdate(cuit="30616874582")
        assert dto.cuit == "30616874582"

    def test_cuit_invalido(self):
        with pytest.raises(ValidationError) as exc_info:
            EmpresaUpdate(cuit="123")
        assert "CUIT" in str(exc_info.value)

    def test_email_invalido(self):
        with pytest.raises(ValidationError):
            EmpresaUpdate(email="no-es-email")

    def test_rechazo_campo_extra(self):
        with pytest.raises(ValidationError):
            EmpresaUpdate(campo_ilegal="valor")

    def test_nested_datos_fiscales(self):
        dto = EmpresaUpdate(
            datos_fiscales=DatosFiscales(condicion_iva="Monotributo")
        )
        assert dto.datos_fiscales.condicion_iva == "Monotributo"

    def test_nested_campo_extra_rechazado(self):
        with pytest.raises(ValidationError):
            EmpresaUpdate(
                datos_fiscales={"condicion_iva": "Monotributo", "extra": "campo"}
            )


class TestEmpresaPublic:
    def test_serializacion(self):
        import uuid
        from datetime import datetime

        emp = EmpresaPublic(
            id=uuid.uuid4(),
            nombre_comercial="Test",
            activa=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        assert emp.nombre_comercial == "Test"

    def test_rechazo_campo_extra(self):
        with pytest.raises(ValidationError):
            EmpresaPublic(
                id="not-a-uuid",
                nombre_comercial="Test",
                activa=True,
                created_at="now",
                updated_at="now",
                extra="bad",
            )


class TestLogoUploadResponse:
    def test_instanciacion(self):
        resp = LogoUploadResponse(logo_url="/uploads/logo.jpg", filename="logo.jpg", content_type="image/jpeg")
        assert resp.logo_url == "/uploads/logo.jpg"

    def test_rechazo_campo_extra(self):
        with pytest.raises(ValidationError):
            LogoUploadResponse(logo_url="/logo.jpg", filename="logo.jpg", content_type="image/jpeg", extra="bad")
