from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator


class UsuarioPublic(BaseModel):
    id: str
    email: str
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    rol: Optional[str] = None
    empresa_id: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class LoginRequest(BaseModel):
    email: EmailStr
    contrasena: str

    model_config = ConfigDict(extra="forbid")


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioPublic

    model_config = ConfigDict(extra="forbid")


class RecoverRequest(BaseModel):
    email: EmailStr

    model_config = ConfigDict(extra="forbid")


class GenericMessageResponse(BaseModel):
    message: str

    model_config = ConfigDict(extra="forbid")


class ResetRequest(BaseModel):
    token: str
    nueva_contrasena: str = Field(..., min_length=8)
    confirmacion: str

    model_config = ConfigDict(extra="forbid")

    @field_validator("nueva_contrasena")
    @classmethod
    def _password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("La contraseña debe contener al menos una mayúscula")
        if not any(c.islower() for c in v):
            raise ValueError("La contraseña debe contener al menos una minúscula")
        if not any(c.isdigit() for c in v):
            raise ValueError("La contraseña debe contener al menos un número")
        return v
