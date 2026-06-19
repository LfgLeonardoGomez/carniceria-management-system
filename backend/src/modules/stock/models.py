import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import SQLModel, Field


class MovimientoStock(SQLModel, table=True):
    __tablename__ = "movimiento_stock"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    empresa_id: uuid.UUID = Field(foreign_key="empresa.id", nullable=False, index=True)
    producto_id: uuid.UUID = Field(foreign_key="producto.id", nullable=False, index=True)
    tipo: str = Field(nullable=False)  # entrada_compra, entrada_desposte, salida_venta, ajuste
    cantidad_kilos: Decimal = Field(nullable=False, decimal_places=3, max_digits=19)
    stock_resultante: Decimal = Field(nullable=False, decimal_places=3, max_digits=19)
    referencia_id: Optional[str] = Field(default=None)
    referencia_tipo: Optional[str] = Field(default=None)
    motivo: Optional[str] = Field(default=None)
    operador_id: Optional[uuid.UUID] = Field(default=None, foreign_key="usuario.id")
    fecha: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
