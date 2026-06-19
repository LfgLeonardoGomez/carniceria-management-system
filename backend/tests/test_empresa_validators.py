import pytest
from src.modules.empresa.validators import validate_cuit


class TestValidateCuit:
    # -----------------------------------------------------------------------
    # Happy path
    # -----------------------------------------------------------------------
    def test_cuit_valido_empresa(self):
        # 30-61687458-2  → tipo 30, dígito verificador 2
        assert validate_cuit("30616874582") == "30616874582"

    def test_cuit_valido_persona_fisica(self):
        # 20-28020634-3 → tipo 20, dígito verificador 3
        assert validate_cuit("20280206343") == "20280206343"

    def test_cuit_valido_digito_verificador_diez_persona(self):
        # Caso especial: verifier calculado = 10 → para persona física se usa 9
        # 20-00000001-9
        assert validate_cuit("20000000019") == "20000000019"

    def test_cuit_valido_digito_verificador_diez_empresa(self):
        # Caso especial: verifier calculado = 10 → para empresa se usa 4
        # 30000000044: checksum = 3*5+0*4+0*3+0*2+0*7+0*6+0*5+0*4+0*3+4*2 = 23
        # 23 % 11 = 1 → 11-1 = 10 → tipo 30 → verifier = 4
        assert validate_cuit("30000000044") == "30000000044"

    # -----------------------------------------------------------------------
    # Edge cases / invalid
    # -----------------------------------------------------------------------
    def test_cuit_digito_verificador_incorrecto(self):
        with pytest.raises(ValueError, match="Dígito verificador de CUIT inválido"):
            validate_cuit("20280206345")  # debería terminar en 3

    def test_cuit_digito_verificador_especial_incorrecto(self):
        # 20000000019 es válido (verifier 9), 20000000015 debería fallar
        with pytest.raises(ValueError, match="Dígito verificador de CUIT inválido"):
            validate_cuit("20000000015")

    def test_cuit_diez_digitos(self):
        with pytest.raises(ValueError, match="exactamente 11 dígitos"):
            validate_cuit("2028020634")

    def test_cuit_doce_digitos(self):
        with pytest.raises(ValueError, match="exactamente 11 dígitos"):
            validate_cuit("202802063434")

    def test_cuit_con_letras(self):
        with pytest.raises(ValueError, match="exactamente 11 dígitos"):
            validate_cuit("20A28020634")

    def test_cuit_string_vacio(self):
        with pytest.raises(ValueError, match="exactamente 11 dígitos"):
            validate_cuit("")

    def test_cuit_none(self):
        with pytest.raises(ValueError, match="CUIT es requerido"):
            validate_cuit(None)  # type: ignore[arg-type]

    def test_cuit_no_string(self):
        with pytest.raises(ValueError, match="CUIT debe ser una cadena de texto"):
            validate_cuit(20280206343)  # type: ignore[arg-type]
