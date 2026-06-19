import re


def validate_cuit(cuit: str) -> str:
    """Valida un CUIT argentino (11 dígitos + dígito verificador AFIP).

    Args:
        cuit: Cadena de 11 dígitos numéricos.

    Returns:
        El CUIT validado.

    Raises:
        ValueError: Si el formato es incorrecto o el dígito verificador no coincide.
    """
    if cuit is None:
        raise ValueError("CUIT es requerido")
    if not isinstance(cuit, str):
        raise ValueError("CUIT debe ser una cadena de texto")
    if not re.fullmatch(r"^\d{11}$", cuit):
        raise ValueError("CUIT debe contener exactamente 11 dígitos numéricos")

    base = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    digits = [int(d) for d in cuit]
    checksum = sum(b * d for b, d in zip(base, digits[:-1]))
    remainder = checksum % 11
    verifier = 11 - remainder

    if verifier == 11:
        verifier = 0
    elif verifier == 10:
        # Tipos de persona física (20, 23, 24, 27) → 9
        # Tipos de empresa (30, 33, 34) → 4
        tipo = int(cuit[:2])
        if tipo in {20, 23, 24, 27}:
            verifier = 9
        elif tipo in {30, 33, 34}:
            verifier = 4
        else:
            # Otros tipos no contemplados en la norma; mantenemos 10 como inválido
            raise ValueError("Dígito verificador de CUIT inválido")

    if verifier != digits[-1]:
        raise ValueError("Dígito verificador de CUIT inválido")

    return cuit
