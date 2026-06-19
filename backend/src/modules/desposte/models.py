import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Literal

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Index, UniqueConstraint, text

# 12 tipos de corte fijos (RN-DESP-02)
TIPOS_CORTE_LITERAL = Literal[
    "asado",
    "vacio",
    "nalga",
    "cuadril",
    "peceto",
    "bola_de_lomo",
    "lomo",
    "matambre",
    "costilla",
    "osobuco",
    "molida",
    "otros",
]


class TipoCorte(SQLModel, table=True):
    """Modelo SQLModel para la tabla tipo_corte (creada en migración 001)."""

    __tablename__ = "tipo_corte"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    nombre: str = Field(nullable=False, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Desposte(SQLModel, table=True):
    __tablename__ = "desposte"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    empresa_id: uuid.UUID = Field(foreign_key="empresa.id", nullable=False, index=True)
    compra_id: uuid.UUID = Field(foreign_key="compra.id", nullable=False, index=True)
    fecha: date = Field(nullable=False)
    operador_id: uuid.UUID = Field(foreign_key="usuario.id", nullable=False, index=True)
    estado: str = Field(
        nullable=False,
        default="en_proceso",
        sa_column_kwargs={"server_default": text("'en_proceso'")},
    )
    rendimiento_total: Decimal = Field(
        nullable=False, default=Decimal("0.000"), decimal_places=3, max_digits=19
    )
    merma: Decimal = Field(
        nullable=False, default=Decimal("0.000"), decimal_places=3, max_digits=19
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    compra: Optional["Compra"] = Relationship()
    operador: Optional["Usuario"] = Relationship()
    cortes: list["CorteDesposte"] = Relationship(back_populates="desposte")

    __table_args__ = (
        Index("ix_desposte_empresa_id_fecha", "empresa_id", "fecha"),
        Index("ix_desposte_empresa_id_compra_id", "empresa_id", "compra_id"),
        Index("ix_desposte_empresa_id_estado", "empresa_id", "estado"),
    )


class CorteDesposte(SQLModel, table=True):
    __tablename__ = "corte_desposte"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    desposte_id: uuid.UUID = Field(foreign_key="desposte.id", nullable=False, index=True)
    tipo_corte: str = Field(nullable=False)
    kilos_obtenidos: Decimal = Field(nullable=False, decimal_places=3, max_digits=19)
    porcentaje_rendimiento: Decimal = Field(
        nullable=False, default=Decimal("0.000"), decimal_places=3, max_digits=19
    )
    costo_asignado: Decimal = Field(
        nullable=False, default=Decimal("0.000"), decimal_places=2, max_digits=19
    )
    costo_final_por_kilo: Decimal = Field(
        nullable=False, default=Decimal("0.000"), decimal_places=2, max_digits=19
    )
    producto_id: Optional[uuid.UUID] = Field(
        default=None, foreign_key="producto.id", index=True
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    desposte: Optional[Desposte] = Relationship(back_populates="cortes")
    producto: Optional["Producto"] = Relationship()

    __table_args__ = (
        UniqueConstraint("desposte_id", "tipo_corte", name="uq_corte_desposte_tipo"),
    )
