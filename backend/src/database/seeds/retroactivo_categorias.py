"""Script retroactivo para crear categorías seed en empresas existentes."""
import uuid
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import select

from modules.empresa.models import Empresa
from modules.producto.models import CategoriaProducto
from database.seeds.categorias_producto import seed_categorias_para_empresa


def seed_categorias_empresas_existentes(session: Session) -> int:
    """Crea categorías seed para todas las empresas que aún no las tengan.

    Returns:
        int: Cantidad de empresas a las que se les crearon categorías.
    """
    empresas = session.execute(select(Empresa)).scalars().all()
    count = 0
    for empresa in empresas:
        existing = session.execute(
            select(CategoriaProducto).where(
                CategoriaProducto.empresa_id == empresa.id
            )
        ).scalars().first()
        if not existing:
            seed_categorias_para_empresa(session, empresa.id)
            count += 1
    return count
