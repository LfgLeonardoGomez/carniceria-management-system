import uuid
import re
from decimal import Decimal
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
TIPO_CLIENTE_PUBLICO = "publico_general"
TIPO_CLIENTE_MAYORISTA = "mayorista"
TIPO_CLIENTE_ESPECIAL = "especial"
TIPOS_CLIENTE_VALIDOS = {TIPO_CLIENTE_PUBLICO, TIPO_CLIENTE_MAYORISTA, TIPO_CLIENTE_ESPECIAL}


def _normalizar_cuit(cuit: Optional[str]) -> Optional[str]:
    if not cuit:
        return None
    return re.sub(r"[^\d]", "", cuit)


def _validar_cuit_argentino(cuit: str) -> bool:
    """Valida CUIT/CUIL argentino con dígito verificador."""
    cuit = _normalizar_cuit(cuit)
    if not cuit or len(cuit) != 11:
        return False
    base = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    digits = [int(d) for d in cuit]
    checksum = sum(b * digits[i] for i, b in enumerate(base))
    remainder = checksum % 11
    verifier = 11 - remainder
    if verifier == 11:
        verifier = 0
    elif verifier == 10:
        tipo = int(cuit[:2])
        if tipo in (20, 23, 24, 27):
            verifier = 9
        elif tipo in (30, 33, 34):
            verifier = 4
        else:
            return False
    return verifier == digits[10]


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------
class ClienteCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=255)
    apellido: Optional[str] = None
    razon_social: Optional[str] = None
    cuit: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None
    tipo_cliente: str = TIPO_CLIENTE_PUBLICO
    limite_cuenta_corriente: Decimal = Field(default=Decimal("0.0000"), decimal_places=4, max_digits=19)

    model_config = ConfigDict(extra="forbid")

    @field_validator("tipo_cliente")
    @classmethod
    def _validar_tipo_cliente(cls, v: str) -> str:
        if v not in TIPOS_CLIENTE_VALIDOS:
            raise ValueError(f"tipo_cliente debe ser uno de: {', '.join(TIPOS_CLIENTE_VALIDOS)}")
        return v

    @field_validator("cuit")
    @classmethod
    def _validar_cuit(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        normalizado = _normalizar_cuit(v)
        if normalizado and len(normalizado) != 11:
            raise ValueError("CUIT debe tener 11 dígitos")
        if normalizado and not _validar_cuit_argentino(normalizado):
            raise ValueError("CUIT inválido")
        return normalizado


class ClienteUpdate(BaseModel):
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=255)
    apellido: Optional[str] = None
    razon_social: Optional[str] = None
    cuit: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None
    tipo_cliente: Optional[str] = None
    limite_cuenta_corriente: Optional[Decimal] = Field(default=None, decimal_places=4, max_digits=19)

    model_config = ConfigDict(extra="forbid")

    @field_validator("tipo_cliente")
    @classmethod
    def _validar_tipo_cliente(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if v not in TIPOS_CLIENTE_VALIDOS:
            raise ValueError(f"tipo_cliente debe ser uno de: {', '.join(TIPOS_CLIENTE_VALIDOS)}")
        return v

    @field_validator("cuit")
    @classmethod
    def _validar_cuit(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        normalizado = _normalizar_cuit(v)
        if normalizado and len(normalizado) != 11:
            raise ValueError("CUIT debe tener 11 dígitos")
        if normalizado and not _validar_cuit_argentino(normalizado):
            raise ValueError("CUIT inválido")
        return normalizado


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------
class ClienteResponse(BaseModel):
    id: uuid.UUID
    empresa_id: uuid.UUID
    nombre: str
    apellido: Optional[str] = None
    razon_social: Optional[str] = None
    cuit: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None
    tipo_cliente: str
    limite_cuenta_corriente: Decimal
    saldo_actual: Decimal
    activo: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(extra="forbid")


class ClienteListResponse(BaseModel):
    items: list[ClienteResponse]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Historial schemas
# ---------------------------------------------------------------------------
class VentaResumen(BaseModel):
    id: uuid.UUID
    fecha: datetime
    total: Decimal
    estado: str

    model_config = ConfigDict(extra="forbid")


class ClienteHistorialResponse(BaseModel):
    items: list[VentaResumen]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(extra="forbid")
