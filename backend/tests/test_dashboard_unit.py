"""Unit tests for dashboard service — pure aggregation logic.

TDD cycle: RED (written before production code) → GREEN → TRIANGULATE → REFACTOR

These tests exercise pure functions that perform aggregation calculations without
requiring a real DB. Date windowing helpers and permission-gate logic are tested here.
"""
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional
import pytest

# Import the functions under test — these will FAIL (RED) until the service is written.
from src.modules.dashboard.service import (
    calcular_rango_dia,
    calcular_rango_mes,
    tiene_permiso_reportes,
    verificar_snapshot_disponible,
)


# ---------------------------------------------------------------------------
# Helper stubs for testing permission checks
# ---------------------------------------------------------------------------
class _StubRol:
    def __init__(self, nombre: str):
        self.nombre = nombre


class _StubUsuario:
    def __init__(self, rol_nombre: str):
        self.rol = _StubRol(rol_nombre)


# ===========================================================================
# Task 2.8 — Date range helpers
# ===========================================================================
class TestRangoFechas:
    """Tests for date-range helper functions (day/month window)."""

    def test_rango_dia_incluye_inicio_y_fin(self):
        """calcular_rango_dia returns a (start, end) tuple spanning the full UTC day."""
        ref = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        inicio, fin = calcular_rango_dia(ref)
        assert inicio.date() == date(2024, 3, 15)
        assert fin.date() == date(2024, 3, 15)
        assert inicio < fin

    def test_rango_dia_diferente_fecha(self):
        """Triangulation: different reference date produces correct boundaries."""
        ref = datetime(2024, 12, 31, 23, 0, 0, tzinfo=timezone.utc)
        inicio, fin = calcular_rango_dia(ref)
        assert inicio.date() == date(2024, 12, 31)
        assert fin.date() == date(2024, 12, 31)

    def test_rango_mes_incluye_primer_dia(self):
        """calcular_rango_mes starts from the 1st of the current month."""
        ref = datetime(2024, 6, 20, 14, 0, 0, tzinfo=timezone.utc)
        inicio, fin = calcular_rango_mes(ref)
        assert inicio.date() == date(2024, 6, 1)
        assert fin >= ref

    def test_rango_mes_diferente_mes(self):
        """Triangulation: January — month start is Jan 1st."""
        ref = datetime(2025, 1, 15, 8, 0, 0, tzinfo=timezone.utc)
        inicio, fin = calcular_rango_mes(ref)
        assert inicio.date() == date(2025, 1, 1)


# ===========================================================================
# Task 3.1 — Permission gate for financial KPIs
# ===========================================================================
class TestPermisoReportes:
    """Tests for the reportes:read permission gate."""

    def test_admin_tiene_permiso(self):
        """Admin role has reportes:read."""
        usuario = _StubUsuario("admin")
        assert tiene_permiso_reportes(usuario) is True

    def test_encargado_tiene_permiso(self):
        """Encargado also has reportes:read."""
        usuario = _StubUsuario("encargado")
        assert tiene_permiso_reportes(usuario) is True

    def test_cajero_no_tiene_permiso(self):
        """Cajero does NOT have reportes:read — must return False."""
        usuario = _StubUsuario("cajero")
        assert tiene_permiso_reportes(usuario) is False

    def test_vendedor_no_tiene_permiso(self):
        """Triangulation: vendedor also lacks reportes:read."""
        usuario = _StubUsuario("vendedor")
        assert tiene_permiso_reportes(usuario) is False

    def test_usuario_sin_rol_no_tiene_permiso(self):
        """User with no rol at all does not crash, returns False."""

        class _NoRol:
            rol = None

        assert tiene_permiso_reportes(_NoRol()) is False


# ===========================================================================
# Task 3.2 — Snapshot availability detection
# ===========================================================================
class TestSnapshotDisponible:
    """Tests for verificar_snapshot_disponible — detects if costo_unitario is present."""

    def test_sin_lineas_snapshot_no_disponible(self):
        """Empty list → snapshot unavailable (no data to confirm)."""
        # According to the design: ganancia_disponible = False when no snapshot evidence
        assert verificar_snapshot_disponible([]) is False

    def test_lineas_con_costo_disponible(self):
        """All lines have costo_unitario → snapshot available."""
        lineas = [
            {"costo_unitario": Decimal("500.00")},
            {"costo_unitario": Decimal("300.00")},
        ]
        assert verificar_snapshot_disponible(lineas) is True

    def test_lineas_con_costo_none_no_disponible(self):
        """Any line with NULL costo_unitario → snapshot NOT available."""
        lineas = [
            {"costo_unitario": Decimal("500.00")},
            {"costo_unitario": None},
        ]
        assert verificar_snapshot_disponible(lineas) is False

    def test_todas_lineas_none_no_disponible(self):
        """Triangulation: all NULLs → not available."""
        lineas = [{"costo_unitario": None}]
        assert verificar_snapshot_disponible(lineas) is False
