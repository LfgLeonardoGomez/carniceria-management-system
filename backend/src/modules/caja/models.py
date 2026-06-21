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

    # --- C-13: cierre calculation columns (KB §Caja). All nullable / additive. ---
    usuario_apertura_id: Optional[uuid.UUID] = Field(
        default=None, foreign_key="usuario.id", index=True
    )
    usuario_cierre_id: Optional[uuid.UUID] = Field(
        default=None, foreign_key="usuario.id", index=True
    )
    efectivo_inicial: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=19)
    efectivo_esperado: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=19)
    efectivo_real: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=19)
    transferencias_esperadas: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=19)
    transferencias_reales: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=19)
    tarjetas_esperadas: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=19)
    tarjetas_reales: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=19)
    diferencia_efectivo: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=19)
    diferencia_transferencias: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=19)
    diferencia_tarjetas: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=19)
    diferencia_total: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=19)

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
    descripcion: Optional[str] = Field(default=None)
    venta_id: Optional[uuid.UUID] = Field(default=None, foreign_key="venta.id", index=True)
    fecha: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
