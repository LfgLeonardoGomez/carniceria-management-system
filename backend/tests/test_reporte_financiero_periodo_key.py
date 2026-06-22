"""Tests for C-18 periodo_key helper.

TDD cycle:
  2.1 RED  — pure function tests for each group_by; edge cases (year boundaries)
  2.3 TRIANGULATE — second case per group_by; venta datetime vs gasto date alignment
"""
from __future__ import annotations

import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "src"))

from src.modules.reporte.service import periodo_key


# ---------------------------------------------------------------------------
# Task 2.1 RED — basic cases per group_by
# ---------------------------------------------------------------------------


class TestPeriodoKeyDia:
    def test_dia_formats_as_yyyy_mm_dd(self):
        dt = datetime(2026, 6, 22, 10, 30, tzinfo=timezone.utc)
        assert periodo_key(dt, "dia") == "2026-06-22"

    def test_dia_triangulate_different_date(self):
        dt = datetime(2025, 12, 31, 23, 59, tzinfo=timezone.utc)
        assert periodo_key(dt, "dia") == "2025-12-31"

    def test_dia_accepts_date_object(self):
        d = date(2026, 1, 1)
        assert periodo_key(d, "dia") == "2026-01-01"

    def test_dia_venta_datetime_and_gasto_date_same_period(self):
        """A venta datetime and a gasto date on the same day → same key."""
        venta_dt = datetime(2026, 6, 22, 14, 0, tzinfo=timezone.utc)
        gasto_d = date(2026, 6, 22)
        assert periodo_key(venta_dt, "dia") == periodo_key(gasto_d, "dia")


class TestPeriodoKeySemana:
    def test_semana_formats_as_iso_week(self):
        # 2026-06-22 is Monday of ISO week 26
        dt = datetime(2026, 6, 22, tzinfo=timezone.utc)
        assert periodo_key(dt, "semana") == "2026-W26"

    def test_semana_triangulate_year_boundary(self):
        # 2025-12-29 is in ISO week 1 of 2026
        dt = datetime(2025, 12, 29, tzinfo=timezone.utc)
        key = periodo_key(dt, "semana")
        # ISO week 1 of 2026 (year-week: 2026-W01)
        assert key == "2026-W01"

    def test_semana_year_end_different_week(self):
        # 2025-12-31 — what ISO week is it?
        dt = datetime(2025, 12, 31, tzinfo=timezone.utc)
        key = periodo_key(dt, "semana")
        # 2025-12-31 is Wednesday of ISO week 1, 2026
        assert key == "2026-W01"

    def test_semana_date_alignment_with_datetime(self):
        """A gasto date and venta datetime in the same ISO week → same key."""
        venta_dt = datetime(2026, 6, 22, 9, 0, tzinfo=timezone.utc)  # Mon W26
        gasto_d = date(2026, 6, 26)  # Fri same week W26
        assert periodo_key(venta_dt, "semana") == periodo_key(gasto_d, "semana")


class TestPeriodoKeyMes:
    def test_mes_formats_as_yyyy_mm(self):
        dt = datetime(2026, 6, 22, tzinfo=timezone.utc)
        assert periodo_key(dt, "mes") == "2026-06"

    def test_mes_triangulate_january(self):
        dt = datetime(2026, 1, 1, tzinfo=timezone.utc)
        assert periodo_key(dt, "mes") == "2026-01"

    def test_mes_date_alignment(self):
        venta_dt = datetime(2026, 6, 15, 8, 0, tzinfo=timezone.utc)
        gasto_d = date(2026, 6, 30)
        assert periodo_key(venta_dt, "mes") == periodo_key(gasto_d, "mes") == "2026-06"


class TestPeriodoKeyAnio:
    def test_anio_formats_as_yyyy(self):
        dt = datetime(2026, 6, 22, tzinfo=timezone.utc)
        assert periodo_key(dt, "anio") == "2026"

    def test_anio_triangulate_year_boundary(self):
        dt_end = datetime(2025, 12, 31, tzinfo=timezone.utc)
        dt_start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        assert periodo_key(dt_end, "anio") == "2025"
        assert periodo_key(dt_start, "anio") == "2026"

    def test_anio_date_alignment(self):
        venta_dt = datetime(2026, 3, 15, tzinfo=timezone.utc)
        gasto_d = date(2026, 11, 1)
        assert periodo_key(venta_dt, "anio") == periodo_key(gasto_d, "anio") == "2026"


class TestPeriodoKeyNaiveDatetime:
    """Naive datetimes (no tzinfo) should be treated as UTC."""

    def test_naive_datetime_dia(self):
        dt = datetime(2026, 6, 22, 12, 0)  # no tzinfo
        assert periodo_key(dt, "dia") == "2026-06-22"

    def test_naive_datetime_mes(self):
        dt = datetime(2026, 6, 1, 0, 0)
        assert periodo_key(dt, "mes") == "2026-06"
