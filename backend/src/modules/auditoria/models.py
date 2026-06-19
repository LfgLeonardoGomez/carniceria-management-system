import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class Auditoria(SQLModel, table=True):
    __tablename__ = "auditoria"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    action: str = Field(nullable=False, index=True)
    actor_id: Optional[uuid.UUID] = Field(default=None, foreign_key="usuario.id", index=True)
    target_empresa_id: Optional[uuid.UUID] = Field(default=None, foreign_key="empresa.id", index=True)
    target_usuario_id: Optional[uuid.UUID] = Field(default=None, foreign_key="usuario.id", index=True)
    details: Optional[str] = Field(default=None)
    ip_address: Optional[str] = Field(default=None)
    user_agent: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
