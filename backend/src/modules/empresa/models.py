import uuid
from datetime import datetime
from typing import Optional, Any

from sqlmodel import SQLModel, Field
from sqlalchemy import JSON


class Empresa(SQLModel, table=True):
    __tablename__ = "empresa"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    nombre_comercial: str = Field(nullable=False)
    razon_social: Optional[str] = Field(default=None)
    cuit: Optional[str] = Field(default=None, index=True)
    domicilio: Optional[str] = Field(default=None)
    telefono: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    logo_url: Optional[str] = Field(default=None)
    datos_fiscales: Optional[dict[str, Any]] = Field(default=None, sa_type=JSON)
    configuracion_general: Optional[dict[str, Any]] = Field(default=None, sa_type=JSON)
    parametros_operativos: Optional[dict[str, Any]] = Field(default=None, sa_type=JSON)
    admin_id: Optional[uuid.UUID] = Field(
        default=None, foreign_key="usuario.id", index=True
    )
    activa: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
