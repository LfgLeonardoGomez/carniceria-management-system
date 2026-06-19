import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class Proveedor(SQLModel, table=True):
    __tablename__ = "proveedor"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    empresa_id: uuid.UUID = Field(foreign_key="empresa.id", nullable=False, index=True)
    nombre: str = Field(nullable=False)
    cuit: Optional[str] = Field(default=None, index=True)
    telefono: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    direccion: Optional[str] = Field(default=None)
    activo: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
