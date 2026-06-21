import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import SQLModel, Field
from sqlalchemy import Index


class CategoriaGasto(SQLModel, table=True):
    """Legacy lookup table — kept for schema compatibility, categories are now a fixed enum."""
    __tablename__ = "categoria_gasto"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    nombre: str = Field(nullable=False, unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Gasto(SQLModel, table=True):
    """Registro de un gasto operativo de una empresa."""
    __tablename__ = "gasto"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    empresa_id: uuid.UUID = Field(foreign_key="empresa.id", nullable=False, index=True)
    fecha: date = Field(nullable=False, index=True)
    categoria: str = Field(nullable=False, index=True)
    descripcion: Optional[str] = Field(default=None, nullable=True)
    importe: Decimal = Field(nullable=False, decimal_places=2, max_digits=19)
    medio_pago: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_gasto_empresa_id_fecha", "empresa_id", "fecha"),
        Index("ix_gasto_empresa_id_categoria", "empresa_id", "categoria"),
    )
