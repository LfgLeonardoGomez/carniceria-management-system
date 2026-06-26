import os
import uuid

from sqlalchemy.orm import Session

from src.modules.auth.models import Usuario, Rol
from src.modules.empresa.models import Empresa
from src.core.security import hash_password


SEED_SUPERADMIN_EMAIL = os.environ.get("SEED_SUPERADMIN_EMAIL", "superadmin@basile.app")
SEED_SUPERADMIN_PASSWORD = os.environ.get("SEED_SUPERADMIN_PASSWORD", "BasileSuper123!")


def seed_admin_user(session: Session) -> None:
    """Crea usuario superadmin por defecto sin empresa asociada.

    Idempotente: no crea duplicados si el email ya existe.
    """
    # Buscar rol superadmin
    rol = session.query(Rol).filter(Rol.nombre == "superadmin").first()
    if not rol:
        raise RuntimeError("El rol superadmin no existe. Ejecutar seed_roles primero.")

    # Verificar si ya existe el superadmin
    existing = session.query(Usuario).filter(Usuario.email == SEED_SUPERADMIN_EMAIL).first()
    if existing:
        return

    superadmin = Usuario(
        email=SEED_SUPERADMIN_EMAIL,
        contrasena_hash=hash_password(SEED_SUPERADMIN_PASSWORD),
        nombre="Superadmin",
        apellido="Sistema",
        rol_id=rol.id,
        activo=True,
        empresa_id=None,
    )
    session.add(superadmin)
    session.commit()
