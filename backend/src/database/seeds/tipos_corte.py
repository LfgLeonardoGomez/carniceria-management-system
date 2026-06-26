import uuid

from sqlalchemy.orm import Session

from src.modules.desposte.models import TipoCorte

TIPOS_CORTE = [
    (uuid.uuid5(uuid.NAMESPACE_DNS, "basile.corte.Asado"), "Asado"),
    (uuid.uuid5(uuid.NAMESPACE_DNS, "basile.corte.Vacio"), "Vacío"),
    (uuid.uuid5(uuid.NAMESPACE_DNS, "basile.corte.Nalga"), "Nalga"),
    (uuid.uuid5(uuid.NAMESPACE_DNS, "basile.corte.Cuadril"), "Cuadril"),
    (uuid.uuid5(uuid.NAMESPACE_DNS, "basile.corte.Peceto"), "Peceto"),
    (uuid.uuid5(uuid.NAMESPACE_DNS, "basile.corte.BolaDeLomo"), "Bola de lomo"),
    (uuid.uuid5(uuid.NAMESPACE_DNS, "basile.corte.Lomo"), "Lomo"),
    (uuid.uuid5(uuid.NAMESPACE_DNS, "basile.corte.Matambre"), "Matambre"),
    (uuid.uuid5(uuid.NAMESPACE_DNS, "basile.corte.Costilla"), "Costilla"),
    (uuid.uuid5(uuid.NAMESPACE_DNS, "basile.corte.Osobuco"), "Osobuco"),
    (uuid.uuid5(uuid.NAMESPACE_DNS, "basile.corte.Molida"), "Molida"),
    (uuid.uuid5(uuid.NAMESPACE_DNS, "basile.corte.Otros"), "Otros"),
]


def seed_tipos_corte(session: Session) -> None:
    for tc_id, nombre in TIPOS_CORTE:
        tc = TipoCorte(id=tc_id, nombre=nombre)
        session.merge(tc)
    session.commit()
