import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Index


class Venta(SQLModel, table=True):
    __tablename__ = "venta"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    empresa_id: uuid.UUID = Field(foreign_key="empresa.id", nullable=False, index=True)
    cliente_id: Optional[uuid.UUID] = Field(default=None, foreign_key="cliente.id", index=True)
    tipo_cliente_al_momento: str = Field(nullable=False, default="publico_general")
    estado: str = Field(nullable=False, default="en_curso")
    subtotal: Decimal = Field(nullable=False, decimal_places=2, max_digits=19)
    descuentos: Decimal = Field(default=Decimal("0.00"), decimal_places=2, max_digits=19)
    total: Decimal = Field(nullable=False, decimal_places=2, max_digits=19)
    fecha: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)

    detalles: List["DetalleVenta"] = Relationship(back_populates="venta")
    pagos: List["PagoVenta"] = Relationship(back_populates="venta")

    __table_args__ = (
        Index("ix_venta_empresa_id_fecha", "empresa_id", "fecha"),
        Index("ix_venta_empresa_id_cliente_id", "empresa_id", "cliente_id"),
        Index("ix_venta_empresa_id_estado", "empresa_id", "estado"),
    )


class DetalleVenta(SQLModel, table=True):
    __tablename__ = "detalle_venta"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    venta_id: uuid.UUID = Field(foreign_key="venta.id", nullable=False, index=True)
    producto_id: uuid.UUID = Field(foreign_key="producto.id", nullable=False, index=True)
    cantidad_kilos: Decimal = Field(nullable=False, decimal_places=3, max_digits=19)
    precio_unitario: Decimal = Field(nullable=False, decimal_places=2, max_digits=19)
    importe: Decimal = Field(nullable=False, decimal_places=2, max_digits=19)
    # Cost snapshot at sale time. Nullable because pre-existing rows have no snapshot;
    # their ganancia is "not available" (None), not zero.
    costo_unitario: Optional[Decimal] = Field(
        default=None, nullable=True, decimal_places=2, max_digits=19
    )

    venta: Optional[Venta] = Relationship(back_populates="detalles")


class PagoVenta(SQLModel, table=True):
    __tablename__ = "pago_venta"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    venta_id: uuid.UUID = Field(foreign_key="venta.id", nullable=False, index=True)
    medio_pago: str = Field(nullable=False)
    importe: Decimal = Field(nullable=False, decimal_places=2, max_digits=19)

    venta: Optional[Venta] = Relationship(back_populates="pagos")
