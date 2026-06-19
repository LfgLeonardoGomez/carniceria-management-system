import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import SQLModel, Field


class CuentaCorriente(SQLModel, table=True):
    __tablename__ = "cuenta_corriente"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    empresa_id: uuid.UUID = Field(foreign_key="empresa.id", nullable=False, index=True)
    cliente_id: uuid.UUID = Field(foreign_key="cliente.id", nullable=False, index=True)
    tipo: str = Field(nullable=False)
    importe: Decimal = Field(nullable=False, decimal_places=2, max_digits=19)
    saldo_resultante: Decimal = Field(nullable=False, decimal_places=2, max_digits=19)
    venta_id: Optional[uuid.UUID] = Field(default=None, foreign_key="venta.id", index=True)
    fecha: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
