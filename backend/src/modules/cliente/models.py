import uuid
import re
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import SQLModel, Field
from sqlalchemy import Index, text


class Cliente(SQLModel, table=True):
    __tablename__ = "cliente"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    empresa_id: uuid.UUID = Field(foreign_key="empresa.id", nullable=False, index=True)
    nombre: str = Field(nullable=False)
    apellido: Optional[str] = Field(default=None)
    razon_social: Optional[str] = Field(default=None)
    cuit: Optional[str] = Field(default=None)
    telefono: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    direccion: Optional[str] = Field(default=None)
    tipo_cliente: str = Field(nullable=False, default="publico_general")
    limite_cuenta_corriente: Decimal = Field(default=Decimal("0.0000"), decimal_places=4, max_digits=19)
    saldo_actual: Decimal = Field(default=Decimal("0.0000"), decimal_places=4, max_digits=19)
    activo: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (
        Index("ix_cliente_empresa_id_cuit", "empresa_id", "cuit", unique=True, postgresql_where=text("cuit IS NOT NULL")),
        Index("ix_cliente_empresa_id_tipo", "empresa_id", "tipo_cliente"),
        Index("ix_cliente_empresa_id_nombre", "empresa_id", text("lower(nombre)")),
    )

    def normalizar_cuit(self) -> Optional[str]:
        """Normaliza el CUIT a 11 dígitos sin guiones."""
        if not self.cuit:
            return None
        return re.sub(r"[^\d]", "", self.cuit)
