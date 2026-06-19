import uuid
from datetime import datetime

from sqlmodel import SQLModel, Field


class CategoriaGasto(SQLModel, table=True):
    __tablename__ = "categoria_gasto"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    nombre: str = Field(nullable=False, unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
