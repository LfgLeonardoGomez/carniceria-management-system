import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import UniqueConstraint, Index, text


class CategoriaProducto(SQLModel, table=True):
    __tablename__ = "categoria_producto"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    empresa_id: Optional[uuid.UUID] = Field(default=None, foreign_key="empresa.id")
    nombre: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    productos: list["Producto"] = Relationship(back_populates="categoria")

    __table_args__ = (
        UniqueConstraint("empresa_id", "nombre", name="uq_categoria_producto_empresa_nombre"),
        Index("ix_categoria_producto_empresa_id", "empresa_id"),
    )


class Producto(SQLModel, table=True):
    __tablename__ = "producto"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    empresa_id: uuid.UUID = Field(foreign_key="empresa.id", nullable=False, index=True)
    plu: str = Field(nullable=False)
    nombre: str = Field(nullable=False)
    categoria_id: Optional[uuid.UUID] = Field(default=None, foreign_key="categoria_producto.id")
    precio_publico: Decimal = Field(nullable=False, decimal_places=4, max_digits=19)
    precio_mayorista: Decimal = Field(nullable=False, decimal_places=4, max_digits=19)
    costo_por_kilo: Decimal = Field(nullable=False, decimal_places=4, max_digits=19)
    margen: Decimal = Field(nullable=False, decimal_places=4, max_digits=19)
    stock_actual: Decimal = Field(nullable=False, decimal_places=4, max_digits=19)
    stock_minimo: Optional[Decimal] = Field(default=None, decimal_places=4, max_digits=19)
    activo: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    categoria: Optional[CategoriaProducto] = Relationship(back_populates="productos")

    __table_args__ = (
        UniqueConstraint("empresa_id", "plu", name="uq_producto_empresa_plu"),
        Index("ix_producto_nombre_lower", text("lower(nombre)")),
        Index("ix_producto_activo", "activo"),
        Index("ix_producto_categoria_id", "categoria_id"),
    )

    def calcular_margen(self) -> Decimal:
        """Calcula el margen como (precio_publico - costo_por_kilo) / precio_publico.

        Returns:
            Decimal: Margen expresado como decimal (ej: 0.4000 para 40%).
            Si precio_publico es 0, devuelve 0.
        """
        if self.precio_publico == 0:
            return Decimal("0.0000")
        margen = (self.precio_publico - self.costo_por_kilo) / self.precio_publico
        # Ensure 4 decimal places
        return Decimal(str(margen)).quantize(Decimal("0.0001"))

    def recalcular_margen(self) -> None:
        """Recalcula y asigna el margen basado en precio_publico y costo_por_kilo."""
        self.margen = self.calcular_margen()
