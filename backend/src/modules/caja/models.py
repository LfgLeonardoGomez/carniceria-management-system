import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal, Optional

from sqlalchemy import Index, text
from sqlmodel import SQLModel, Field

# All movement types that may appear in movimiento_caja.tipo (RN-CAJA-01).
# Entries written by the system (not by the API request schema): entrada_venta,
# salida_anulacion. Entries written by manual movimiento endpoint: retiro,
# ingreso_manual.
TIPOS_MOVIMIENTO_LITERAL = Literal[
    "entrada_venta",
    "salida_anulacion",
    "retiro",
    "ingreso_manual",
]

# Payment medios allowed in movimiento_caja.medio (aligned with PagoVenta.medio_pago
# minus cuenta_corriente, which never creates a movimiento_caja row).
MEDIOS_PAGO_LITERAL = Literal[
    "efectivo",
    "transferencia",
    "debito",
    "credito",
]


class Caja(SQLModel, table=True):
    __tablename__ = "caja"

    # Caja scope is per CAJERO (operador), not per empresa (KB IN-06, resolved for
    # multi-cajero): several cajeros in the same empresa may each hold one open caja
    # at the same time, but a single cajero may not hold two. A Postgres partial unique
    # index on (empresa_id, operador_id) WHERE estado='abierta' enforces this at the DB
    # layer, closing the apertura TOCTOU race where two concurrent aperturas by the same
    # cajero both pass the in-app `_obtener_caja_abierta is None` check.
    __table_args__ = (
        Index(
            "uq_caja_una_abierta_por_cajero",
            "empresa_id",
            "operador_id",
            unique=True,
            postgresql_where=text("estado = 'abierta'"),
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    empresa_id: uuid.UUID = Field(foreign_key="empresa.id", nullable=False, index=True)
    operador_id: uuid.UUID = Field(foreign_key="usuario.id", nullable=False, index=True)
    fecha_apertura: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    fecha_cierre: Optional[datetime] = Field(default=None)
    # efectivo_inicial: amount of cash the cajero starts with at apertura.
    # Renamed/unified from the original `monto_inicial` (migration 012) + the redundant
    # nullable `efectivo_inicial` (migration 013). Migration 016 drops monto_inicial and
    # sets this column NOT NULL. Both the apertura path and the cierre calculation use
    # this single field.
    efectivo_inicial: Decimal = Field(nullable=False, decimal_places=2, max_digits=19)
    monto_final: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=19)
    estado: str = Field(nullable=False, default="abierta")

    # --- C-13: cierre calculation columns (KB §Caja). All nullable / additive. ---
    usuario_apertura_id: Optional[uuid.UUID] = Field(
        default=None, foreign_key="usuario.id", index=True
    )
    usuario_cierre_id: Optional[uuid.UUID] = Field(
        default=None, foreign_key="usuario.id", index=True
    )
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

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)


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
    # Set on a cross-day `salida_anulacion`: the closed caja that held the original
    # `entrada_venta`. The reversal is posted to the acting cajero's current open caja
    # (this row's caja_id), never to the closed origin, which stays immutable.
    caja_origen_id: Optional[uuid.UUID] = Field(
        default=None, foreign_key="caja.id", index=True
    )
    fecha: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
