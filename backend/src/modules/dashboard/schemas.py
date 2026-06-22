from decimal import Decimal
from typing import Optional
import uuid

from pydantic import BaseModel


class IndicadoresResponse(BaseModel):
    """KPIs operativos y financieros del dashboard."""

    model_config = {"extra": "forbid"}

    # Ventas
    ventas_dia: Decimal
    ventas_mes: Decimal
    kilos_vendidos: Decimal
    clientes_atendidos: int
    stock_critico: int
    gastos_mes: Decimal

    # Financieros sensibles — null when user lacks reportes:read or snapshot unavailable
    ganancia_bruta: Optional[Decimal] = None
    ganancia_neta: Optional[Decimal] = None
    ganancia_disponible: bool


class ProductoRankingItem(BaseModel):
    model_config = {"extra": "forbid"}

    producto_id: uuid.UUID
    nombre: str
    kilos: Decimal


class RankingsResponse(BaseModel):
    model_config = {"extra": "forbid"}

    productos_mas_vendidos: list[ProductoRankingItem]


class VentaDiariaItem(BaseModel):
    model_config = {"extra": "forbid"}

    fecha: str  # YYYY-MM-DD
    total: Decimal


class VentaMensualItem(BaseModel):
    model_config = {"extra": "forbid"}

    periodo: str  # YYYY-MM
    total: Decimal


class MedioPagoItem(BaseModel):
    model_config = {"extra": "forbid"}

    medio_pago: str
    total: Decimal


class EvolucionGananciaItem(BaseModel):
    model_config = {"extra": "forbid"}

    periodo: str  # YYYY-MM
    ganancia_bruta: Optional[Decimal] = None


class GraficosResponse(BaseModel):
    model_config = {"extra": "forbid"}

    ventas_diarias: list[VentaDiariaItem]
    ventas_mensuales: list[VentaMensualItem]
    distribucion_medio_pago: list[MedioPagoItem]
    evolucion_ganancias: list[EvolucionGananciaItem]
    ganancia_disponible: bool
