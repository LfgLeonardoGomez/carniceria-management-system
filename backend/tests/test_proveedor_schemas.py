import pytest
from pydantic import ValidationError

from src.modules.proveedor.schemas import ProveedorCreate, ProveedorUpdate


class TestProveedorCreate:
    def test_cuit_valido(self):
        data = ProveedorCreate(nombre="Carnes del Sur", cuit="30616874582")
        assert data.cuit == "30616874582"

    def test_cuit_invalido_formato(self):
        with pytest.raises(ValidationError) as exc:
            ProveedorCreate(nombre="Carnes del Sur", cuit="123")
        assert "cuit" in str(exc.value)

    def test_cuit_invalido_letras(self):
        with pytest.raises(ValidationError) as exc:
            ProveedorCreate(nombre="Carnes del Sur", cuit="abcdefghijk")
        assert "cuit" in str(exc.value)

    def test_cuit_opcional(self):
        data = ProveedorCreate(nombre="Carnes del Sur")
        assert data.cuit is None

    def test_campos_extra_rechazados(self):
        with pytest.raises(ValidationError) as exc:
            ProveedorCreate(nombre="Carnes del Sur", campo_extra="no permitido")
        assert "extra" in str(exc.value).lower() or "forbidden" in str(exc.value).lower()

    def test_nombre_obligatorio(self):
        with pytest.raises(ValidationError) as exc:
            ProveedorCreate(nombre="")
        assert "nombre" in str(exc.value)

    def test_email_valido(self):
        data = ProveedorCreate(nombre="Carnes del Sur", email="contacto@carne.com")
        assert data.email == "contacto@carne.com"

    def test_email_invalido(self):
        with pytest.raises(ValidationError) as exc:
            ProveedorCreate(nombre="Carnes del Sur", email="no-es-email")
        assert "email" in str(exc.value)


class TestProveedorUpdate:
    def test_cuit_valido(self):
        data = ProveedorUpdate(cuit="30616874582")
        assert data.cuit == "30616874582"

    def test_cuit_invalido(self):
        with pytest.raises(ValidationError) as exc:
            ProveedorUpdate(cuit="123")
        assert "cuit" in str(exc.value)

    def test_campos_extra_rechazados(self):
        with pytest.raises(ValidationError) as exc:
            ProveedorUpdate(nombre="Nuevo", campo_extra="no permitido")
        assert "extra" in str(exc.value).lower() or "forbidden" in str(exc.value).lower()

    def test_update_parcial(self):
        data = ProveedorUpdate(telefono="123456789")
        assert data.telefono == "123456789"
        assert data.nombre is None
