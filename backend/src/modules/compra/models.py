import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Index, text

from src.modules.proveedor.models import Proveedor


class Compra(SQLModel, table=True):
    __tablename__ = "compra"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    empresa_id: uuid.UUID = Field(foreign_key="empresa.id", nullable=False, index=True)
    proveedor_id: uuid.UUID = Field(foreign_key="proveedor.id", nullable=False, index=True)
    fecha: date = Field(nullable=False)
    cantidad_medias_reses: int = Field(nullable=False, ge=1)
    peso_total: Decimal = Field(nullable=False, decimal_places=3, max_digits=19)
    costo_total: Decimal = Field(nullable=False, decimal_places=3, max_digits=19)
    costo_por_kilo: Decimal = Field(nullable=False, decimal_places=3, max_digits=19)
    costo_promedio_historico: Decimal = Field(
        nullable=False, default=Decimal("0.000"), decimal_places=3, max_digits=19
    )
    observaciones: Optional[str] = Field(default=None)
    estado: str = Field(
        nullable=False,
        default="activa",
        sa_column_kwargs={"server_default": text("'activa'")},
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    proveedor: Optional[Proveedor] = Relationship()
    despostes: list["Desposte"] = Relationship(back_populates="compra")

    __table_args__ = (
        Index("ix_compra_empresa_id_fecha", "empresa_id", "fecha"),
        Index("ix_compra_empresa_id_proveedor_id", "empresa_id", "proveedor_id"),
        Index("ix_compra_fecha", "fecha"),
    )
