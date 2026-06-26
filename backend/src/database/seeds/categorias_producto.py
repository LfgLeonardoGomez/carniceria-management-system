import uuid
from typing import Optional

from sqlalchemy.orm import Session

from src.modules.producto.models import CategoriaProducto

CATEGORIAS = [
    "Carne vacuna",
    "Carne de cerdo",
    "Pollo",
    "Embutidos",
    "Otros",
]


def seed_categorias_producto(session: Session, empresa_id: Optional[uuid.UUID] = None) -> None:
    """Crea las 5 categorías seed para una empresa (o globales si empresa_id es None).

    Idempotente: no duplica categorías para la misma empresa.
    """
    for nombre in CATEGORIAS:
        # Generar un id determinístico basado en empresa_id + nombre
        if empresa_id is not None:
            cat_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"basile.categoria.{empresa_id}.{nombre}")
        else:
            cat_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"basile.categoria.{nombre}")

        existing = session.query(CategoriaProducto).filter(
            CategoriaProducto.empresa_id == empresa_id,
            CategoriaProducto.nombre == nombre,
        ).first()

        if not existing:
            cat = CategoriaProducto(id=cat_id, nombre=nombre, empresa_id=empresa_id)
            session.add(cat)
    session.commit()


def seed_categorias_para_empresa(session: Session, empresa_id: uuid.UUID) -> None:
    """Convenience wrapper para crear categorías seed para una empresa específica."""
    seed_categorias_producto(session, empresa_id=empresa_id)
