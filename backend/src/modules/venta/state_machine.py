"""Máquina de estados para el ciclo de vida de una Venta."""

from src.common.exceptions import ConflictException


# Transiciones permitidas: estado_origen -> {estados_destino}
TRANSICIONES_PERMITIDAS: dict[str, set[str]] = {
    "en_curso": {"suspendida", "cobrada"},
    "suspendida": {"en_curso", "cobrada"},
    "cobrada": {"anulada"},
    "anulada": set(),  # terminal
}


def puede_transicionar(estado_actual: str, estado_destino: str) -> bool:
    """Verifica si una transición de estado es válida."""
    if estado_actual not in TRANSICIONES_PERMITIDAS:
        return False
    return estado_destino in TRANSICIONES_PERMITIDAS[estado_actual]


def transicionar(estado_actual: str, estado_destino: str) -> str:
    """Valida y retorna el nuevo estado. Lanza ConflictException si es ilegal."""
    if not puede_transicionar(estado_actual, estado_destino):
        raise ConflictException(
            f"Transición ilegal: no se puede pasar de '{estado_actual}' a '{estado_destino}'"
        )
    return estado_destino


def requiere_rol_admin_o_encargado(estado_destino: str) -> bool:
    """Determina si la transición requiere rol Admin o Encargado."""
    # Solo la anulación requiere permisos elevados
    return estado_destino == "anulada"
