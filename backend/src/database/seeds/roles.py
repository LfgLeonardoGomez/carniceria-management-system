import uuid

from sqlalchemy.orm import Session

from src.modules.auth.models import Rol

ROLES = [
    (uuid.uuid5(uuid.NAMESPACE_DNS, "basile.rol.superadmin"), "superadmin"),
    (uuid.uuid5(uuid.NAMESPACE_DNS, "basile.rol.admin"), "admin"),
    (uuid.uuid5(uuid.NAMESPACE_DNS, "basile.rol.encargado"), "encargado"),
    (uuid.uuid5(uuid.NAMESPACE_DNS, "basile.rol.cajero"), "cajero"),
    (uuid.uuid5(uuid.NAMESPACE_DNS, "basile.rol.vendedor"), "vendedor"),
    (uuid.uuid5(uuid.NAMESPACE_DNS, "basile.rol.desposte"), "desposte"),
]


def seed_roles(session: Session) -> None:
    for rol_id, nombre in ROLES:
        rol = Rol(id=rol_id, nombre=nombre)
        session.merge(rol)
    session.commit()
