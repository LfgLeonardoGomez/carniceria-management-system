import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import SQLModel, Field


class Caja(SQLModel, table=True):
    __tablename__ = "caja"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    empresa_id: uuid.UUID = Field(foreign_key="empresa.id", nullable=False, index=True)
    operador_id: uuid.UUID = Field(foreign_key="usuario.id", nullable=False, index=True)
    fecha_apertura: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    fecha_cierre: Optional[datetime] = Field(default=None)
    monto_inicial: Decimal = Field(nullable=False, decimal_places=2, max_digits=19)
    monto_final: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=19)
    estado: str = Field(nullable=False, default="abierta")
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class MovimientoCaja(SQLModel, table=True):
    __tablename__ = "movimiento_caja"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    caja_id: uuid.UUID = Field(foreign_key="caja.id", nullable=False, index=True)
    empresa_id: uuid.UUID = Field(foreign_key="empresa.id", nullable=False, index=True)
    tipo: str = Field(nullable=False)
    medio: Optional[str] = Field(default=None)
    importe: Decimal = Field(nullable=False, decimal_places=2, max_digits=19)
    venta_id: Optional[uuid.UUID] = Field(default=None, foreign_key="venta.id", index=True)
    fecha: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
