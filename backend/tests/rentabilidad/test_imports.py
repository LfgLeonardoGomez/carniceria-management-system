"""Smoke test: rentabilidad module and router import cleanly (Task 1.3).

RED → the module does not exist yet, so this test will fail until
GREEN is implemented in tasks 1.1 and 1.2.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "src"))


def test_rentabilidad_module_imports():
    """Task 1.3 — module package imports without error."""
    from src.modules.rentabilidad import router as rentabilidad_router_module  # noqa: F401
    assert rentabilidad_router_module is not None


def test_rentabilidad_router_importable():
    """Task 1.3 — router attribute is an APIRouter."""
    from fastapi import APIRouter
    from src.modules.rentabilidad.router import router

    assert isinstance(router, APIRouter)


def test_rentabilidad_schemas_importable():
    """Task 1.3 TRIANGULATE — all schema symbols importable."""
    from src.modules.rentabilidad.schemas import (  # noqa: F401
        ProductoRentabilidadRow,
        CorteRentabilidadRow,
        RentabilidadProductosResponse,
        RentabilidadCortesResponse,
        Orden,
    )


def test_rentabilidad_service_importable():
    """Task 1.3 TRIANGULATE — service functions importable."""
    from src.modules.rentabilidad.service import (  # noqa: F401
        ranking_productos,
        margen_cortes,
        _ranking_productos,
        _margen_cortes,
    )
