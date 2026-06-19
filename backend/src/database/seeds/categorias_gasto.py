import uuid

from sqlalchemy.orm import Session

from modules.gasto.models import CategoriaGasto

CATEGORIAS_GASTO = [
    (uuid.uuid5(uuid.NAMESPACE_DNS, "basile.gasto.Alquiler"), "Alquiler"),
    (uuid.uuid5(uuid.NAMESPACE_DNS, "basile.gasto.Empleados"), "Empleados"),
    (uuid.uuid5(uuid.NAMESPACE_DNS, "basile.gasto.Luz"), "Luz"),
    (uuid.uuid5(uuid.NAMESPACE_DNS, "basile.gasto.Agua"), "Agua"),
    (uuid.uuid5(uuid.NAMESPACE_DNS, "basile.gasto.Gas"), "Gas"),
    (uuid.uuid5(uuid.NAMESPACE_DNS, "basile.gasto.Internet"), "Internet"),
    (uuid.uuid5(uuid.NAMESPACE_DNS, "basile.gasto.Combustible"), "Combustible"),
    (uuid.uuid5(uuid.NAMESPACE_DNS, "basile.gasto.Impuestos"), "Impuestos"),
    (uuid.uuid5(uuid.NAMESPACE_DNS, "basile.gasto.Mantenimiento"), "Mantenimiento"),
    (uuid.uuid5(uuid.NAMESPACE_DNS, "basile.gasto.Insumos"), "Insumos"),
    (uuid.uuid5(uuid.NAMESPACE_DNS, "basile.gasto.Otros"), "Otros"),
]


def seed_categorias_gasto(session: Session) -> None:
    for cg_id, nombre in CATEGORIAS_GASTO:
        cg = CategoriaGasto(id=cg_id, nombre=nombre)
        session.merge(cg)
    session.commit()
