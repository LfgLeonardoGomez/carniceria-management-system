import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from src.modules.empresa.validators import validate_cuit


class DatosFiscales(BaseModel):
    condicion_iva: Optional[str] = None
    inicio_actividades: Optional[date] = None
    punto_venta: Optional[int] = Field(default=None, ge=1)

    model_config = ConfigDict(extra="forbid")


class ConfiguracionGeneral(BaseModel):
    timezone: str = "America/Argentina/Buenos_Aires"
    moneda: str = "ARS"
    idioma: str = "es-AR"

    model_config = ConfigDict(extra="forbid")


class ParametrosOperativos(BaseModel):
    alerta_stock_minimo_umbral: Decimal = Field(default=Decimal("5.000"), ge=0)
    alerta_gasto_elevado_umbral: Decimal = Field(default=Decimal("100000.00"), ge=0)
    alerta_deuda_vencida_dias: int = Field(default=30, ge=1)

    model_config = ConfigDict(extra="forbid")


class EmpresaUpdate(BaseModel):
    nombre_comercial: Optional[str] = Field(default=None, min_length=1, max_length=255)
    razon_social: Optional[str] = Field(default=None, max_length=255)
    cuit: Optional[str] = None
    domicilio: Optional[str] = Field(default=None, max_length=255)
    telefono: Optional[str] = Field(default=None, max_length=50)
    email: Optional[EmailStr] = None
    datos_fiscales: Optional[DatosFiscales] = None
    configuracion_general: Optional[ConfiguracionGeneral] = None
    parametros_operativos: Optional[ParametrosOperativos] = None
    admin_id: Optional[uuid.UUID] = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("cuit")
    @classmethod
    def check_cuit(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_cuit(v)
        return v


class EmpresaPublic(BaseModel):
    id: uuid.UUID
    nombre_comercial: str
    razon_social: Optional[str] = None
    cuit: Optional[str] = None
    domicilio: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    logo_url: Optional[str] = None
    datos_fiscales: Optional[DatosFiscales] = None
    configuracion_general: Optional[ConfiguracionGeneral] = None
    parametros_operativos: Optional[ParametrosOperativos] = None
    admin_id: Optional[uuid.UUID] = None
    activa: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(extra="forbid")


class LogoUploadResponse(BaseModel):
    logo_url: str
    filename: str
    content_type: str

    model_config = ConfigDict(extra="forbid")
