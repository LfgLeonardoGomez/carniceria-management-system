import uuid
from typing import Optional

from sqlalchemy.orm import Session

from src.modules.auth.models import Rol
from src.common.rbac import PERMISSION_MATRIX

# Formato del JSON que se persiste en rol.permisos:
#   { "recurso": ["operacion", ...], ... }
# Ejemplo:
#   { "productos": ["read", "create", "update", "delete"],
#     "desposte":  ["read", "create", "update"] }


def _permissions_to_dict(perm_set: set[str]) -> dict[str, list[str]]:
    """Convierte un set de strings 'recurso:operacion' a dict agrupado por recurso."""
    grouped: dict[str, list[str]] = {}
    for perm in sorted(perm_set):
        recurso, _, operacion = perm.partition(":")
        if not operacion:
            continue
        grouped.setdefault(recurso, []).append(operacion)
    return grouped


def seed_permisos(session: Session, rol_nombre: Optional[str] = None) -> None:
    """Pobla `rol.permisos` (JSON) a partir de PERMISSION_MATRIX.

    Args:
        session: sesión SQLAlchemy.
        rol_nombre: si se pasa, solo actualiza ese rol. Si es None, actualiza
            todos los roles definidos en PERMISSION_MATRIX.

    Idempotente: si el rol ya tenía permisos, los sobreescribe con el valor
    actual de la matriz (los seeds son la fuente de verdad en runtime).
    """
    targets: list[Rol]
    if rol_nombre is not None:
        rol = session.query(Rol).filter(Rol.nombre == rol_nombre).first()
        if rol is None:
            return
        targets = [rol]
    else:
        targets = (
            session.query(Rol)
            .filter(Rol.nombre.in_(list(PERMISSION_MATRIX.keys())))
            .all()
        )

    for rol in targets:
        if rol.nombre not in PERMISSION_MATRIX:
            continue
        rol.permisos = _permissions_to_dict(PERMISSION_MATRIX[rol.nombre])
    session.commit()
